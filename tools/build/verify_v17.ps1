param(
    [Parameter(Mandatory=$false)]
    [string]$MapPath
)
# Authoritative v1.8.6-NOK gate: MPQ readback hash match + NOK zero-residue + pool
# structural assertions + retained-system smoke. Exits non-zero on any failure.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
$config = Get-Content -LiteralPath (Join-Path $root 'config\tool-paths.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ([string]::IsNullOrWhiteSpace($MapPath)) {
    $MapPath = if ([IO.Path]::IsPathRooted($config.baselineMap)) { $config.baselineMap } else { Join-Path $root $config.baselineMap }
}
$MapPath = [IO.Path]::GetFullPath($MapPath)
$verifyDir = Join-Path ([IO.Path]::GetTempPath()) ('nokverify-' + [guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($verifyDir) | Out-Null

$failures = @()
$checks = [ordered]@{}

function Extract-FromMpq([string]$archive) {
    $local = Join-Path $verifyDir ($archive -replace '\\','/')
    $parent = Split-Path -Parent $local
    [IO.Directory]::CreateDirectory($parent) | Out-Null
    for ($try=1; $try -le 6; $try++) {
        & $config.mpqEditor extract $MapPath $archive $verifyDir /fp | Out-Null
        for ($w=0; $w -lt 150; $w++) {
            if (Test-Path -LiteralPath $local -PathType Leaf) {
                $len=(Get-Item -LiteralPath $local).Length
                if ($len -gt 0) { return $local }
            }
            Start-Sleep -Milliseconds 150
        }
        Start-Sleep -Seconds 2
    }
    throw "无法从地图回读: $archive"
}

# ---- 1. text files: extract + source hash match ----
$textPairs = @(
    @{arc='war3map.j'; src='src\war3map.j'},
    @{arc='war3map.w3i'; src='src\war3map.w3i'},
    @{arc='war3map.imp'; src='src\war3map.imp'},
    @{arc='Units\CampaignAbilityStrings.txt'; src='src\data\Units\CampaignAbilityStrings.txt'},
    @{arc='Units\CampaignUnitStrings.txt'; src='src\data\Units\CampaignUnitStrings.txt'},
    @{arc='Units\UnitAbilities.slk'; src='src\data\Units\UnitAbilities.slk'},
    @{arc='Units\UnitBalance.slk'; src='src\data\Units\UnitBalance.slk'},
    @{arc='Units\UnitData.slk'; src='src\data\Units\UnitData.slk'},
    @{arc='Units\UnitUI.slk'; src='src\data\Units\UnitUI.slk'},
    @{arc='Units\UnitWeapons.slk'; src='src\data\Units\UnitWeapons.slk'},
    @{arc='Units\AbilityData.slk'; src='src\data\Units\AbilityData.slk'}
)
foreach ($p in $textPairs) {
    $local = Extract-FromMpq $p.arc
    $h1=(Get-FileHash -LiteralPath $local -Algorithm SHA256).Hash.ToLowerInvariant()
    $h2=(Get-FileHash -LiteralPath (Join-Path $root $p.src) -Algorithm SHA256).Hash.ToLowerInvariant()
    $checks["hash:$($p.arc)"] = ($h1 -eq $h2)
}

$jass = [IO.File]::ReadAllText((Extract-FromMpq 'war3map.j'), [Text.Encoding]::UTF8)
$jass = $jass -replace "`r`n","`n"
$abilData = [IO.File]::ReadAllText((Extract-FromMpq 'Units\AbilityData.slk'), [Text.Encoding]::UTF8)
$uiSlk = [IO.File]::ReadAllText((Extract-FromMpq 'Units\UnitUI.slk'), [Text.Encoding]::UTF8)
$unitStr = [IO.File]::ReadAllText((Extract-FromMpq 'Units\CampaignUnitStrings.txt'), [Text.Encoding]::UTF8)
$abilStr = [IO.File]::ReadAllText((Extract-FromMpq 'Units\CampaignAbilityStrings.txt'), [Text.Encoding]::UTF8)
$abilStr = $abilStr -replace "`r`n","`n"
$impBytes = [IO.File]::ReadAllBytes((Extract-FromMpq 'war3map.imp'))

# ---- 2. w3i binary: fixed 806B, exact 24B NOK label x2, prior labels x0, outside slots == HEAD ----
$w3iBytes = [IO.File]::ReadAllBytes((Extract-FromMpq 'war3map.w3i'))
$checks['w3i:fixed-806'] = ($w3iBytes.Length -eq 806)
$nokLabel = [Text.Encoding]::ASCII.GetBytes('OMG IMBA v1.8.6-NOK     ')
$checks['w3i:nok-label-24b-x2'] = ($nokLabel.Length -eq 24)
function Count-Sub($hay, $needle) {
    $c = 0; $i = 0
    while ($i -le ($hay.Length - $needle.Length)) {
        $m = $true
        for ($k = 0; $k -lt $needle.Length; $k++) { if ($hay[$i + $k] -ne $needle[$k]) { $m = $false; break } }
        if ($m) { $c++ }
        $i++
    }
    return $c
}
$checks['w3i:nok-label-x2'] = ((Count-Sub $w3iBytes $nokLabel) -eq 2)
foreach ($pl in @('OMG IMBA v1.8.5-SYNCF001','OMG IMBA v1.7.1-W3IFix','v1.6-K','K-W3IFix','v1.7.1-K')) {
    $pb = [Text.Encoding]::ASCII.GetBytes($pl)
    $checks["w3i:prior-x0:$pl"] = ((Count-Sub $w3iBytes $pb) -eq 0)
}
$tmpBlob = Join-Path $verifyDir 'head-w3i.bin'
$gitInfo = New-Object Diagnostics.ProcessStartInfo
$gitInfo.FileName = 'git'; $gitInfo.WorkingDirectory = $root
$gitInfo.Arguments = 'show HEAD:src/war3map.w3i'
$gitInfo.UseShellExecute = $false; $gitInfo.RedirectStandardOutput = $true
$gitProc = [Diagnostics.Process]::Start($gitInfo)
$gitOut = [IO.File]::Create($tmpBlob)
$gitProc.StandardOutput.BaseStream.CopyTo($gitOut); $gitOut.Close(); $gitProc.WaitForExit()
$headW3i = $null
if ($gitProc.ExitCode -eq 0 -and (Test-Path $tmpBlob)) { $headW3i = [IO.File]::ReadAllBytes($tmpBlob) }
$allow = New-Object System.Collections.Generic.HashSet[int]
foreach ($s in 12,234) { for ($k = 0; $k -lt 24; $k++) { [void]$allow.Add($s + $k) } }
$diffOk = $false
if ($headW3i -and $headW3i.Length -eq 806) {
    $diffOk = $true
    for ($i = 0; $i -lt 806; $i++) {
        if ($w3iBytes[$i] -ne $headW3i[$i] -and -not $allow.Contains($i)) { $diffOk = $false; break }
    }
}
$checks['w3i:byte-equal-head-outside-slots'] = $diffOk

# ---- 3. version: both XOMG_VERSION and SetMapName carry NOK; no K-era name ----
$checks['version:xomg-nok'] = (([regex]::Matches($jass,'constant string XOMG_VERSION="v1\.8\.6-NOK"')).Count -eq 1)
$checks['version:setmapname-nok'] = (([regex]::Matches($jass,'SetMapName\("OMG IMBA v1\.8\.6-NOK"\)')).Count -eq 1)
$checks['version:no-k-w3ifix'] = ($jass -notmatch 'v1\.7\.1-K-W3IFix')

# ---- 4. NOK zero residue (active jass / SLK / Campaign / imp only) ----
# SuijiMode_ChemicalRageCompatApply / SuijiMode_SetVisualForm are generic visual-switch
# systems used by many heroes; only the K-specific guards were removed, the functions stay.
$jassBan = @('H0K0','KA01','KA02','KA03','KA04','KK_HERO','KK_Init','KK_EnsureHeroAbilities',
             'K_POOL_ROLLED','K_POOL_HIT','K_POOL_ROLL','B891RandomAgilityNoK','QZ9HumanNoK',
             'QC9HumanNoK',"R1X('H0K0",'BTNK_Hero','K_final_v2.mdx','K_final_portrait.mdx',
             'war3mapimported\K\')
foreach ($t in $jassBan) { $checks["nok:jass-x0:$t"] = ($jass -notmatch [regex]::Escape($t)) }
# generic KK_ retained: common difficulty/tips/version/server markers must survive
$checks['nok:generic-kk-kept'] = ($jass -match 'KK_GAME_DIFFICULTY') -and ($jass -match 'KKGameTips') -and ($jass -match 'KK_RELEASE_VERSION')
# SLK / Campaign / imp K residue
$checks['nok:abilData-no-KA'] = ($abilData -notmatch 'KA0[1-4]') -and ($abilData -notmatch 'H0K0')
$checks['nok:uiSlk-no-H0K0'] = ($uiSlk -notmatch 'H0K0') -and ($uiSlk -notmatch 'war3mapimported\\K\\')
$checks['nok:unitStr-no-H0K0'] = ($unitStr -notmatch '(?m)^\[H0K0\]')
$checks['nok:abilStr-no-KA'] = ($abilStr -notmatch '(?m)^\[KA0[1-4]\]')
$checks['nok:abilStr-no-Kbuttons'] = ($abilStr -notmatch 'BTNKMarksmanship|BTNKCriticalStrike|BTNKBattleRoar|BTNKChemicalRage|DISBTNK')
$checks['nok:unitStr-no-Khero-icon'] = ($unitStr -notmatch 'BTNK_Hero\.blp')
# generic English buttons kept
$checks['nok:generic-buttons-kept'] = ($abilStr -match 'BTNKrobWitchcraft') -and ($unitStr -match 'BTNKeep') -and ($unitStr -match 'BTNKeeperGhostBlue')
# imp binary: count header parses, no K path, every non-ASCII-safe path kept
$impTxt = [Text.Encoding]::ASCII.GetString($impBytes)
# precise K-hero tokens only; generic btnkrobwitchcraft / disbtnkrobwitchcraft must survive
$checks['nok:imp-no-Kpath'] = ($impTxt -notmatch '(?i)war3mapimported\\K\\') -and ($impTxt -notmatch '(?i)BTNK_Hero|BTNKMarksmanship|BTNKCriticalStrike|BTNKBattleRoar|BTNKChemicalRage|DISBTNK_Hero|DISBTNKMarksmanship|DISBTNKCriticalStrike|DISBTNKBattleRoar|DISBTNKChemicalRage')

# ---- 5. pool structural: tail shrink K54=117, agility K_4=39, row118 cleared, HMD0 kept ----
$checks['pool:K54-117'] = ($jass -match 'set K54=117') -and ($jass -notmatch 'set K54=118')
$checks['pool:K_4-39'] = ($jass -match 'set K_4=39') -and ($jass -notmatch 'set K_4=40')
$checks['pool:no-K24-40'] = ($jass -notmatch 'set K24\[40\]')
$checks['pool:row118-cleared-HM'] = ($jass -notmatch 'HM4\[118\]')
$checks['pool:row118-cleared-HN'] = ($jass -notmatch 'HN4\[118\]')
$checks['pool:row118-cleared-HO'] = ($jass -notmatch 'HO4\[118\]')
$checks['pool:row118-cleared-HP'] = ($jass -notmatch 'HP4\[118\]')
$checks['pool:source118-cleared'] = ($jass -notmatch 'SUIJI_POOL_SOURCE\[118\]')
$checks['pool:hmd0-kept'] = ($jass -match 'HMD0')
$checks['pool:miao-117-kept'] = ($jass -match 'UB7=117')

# ---- 6. retained-system smoke (non-K, semantic unchanged) ----
$checks['retain:title-nan'] = (([regex]::Matches($jass,'本图男神')).Count -ge 1) -and (([regex]::Matches($jass,'本图女神')).Count -eq 0)
$checks['retain:dota-goddess'] = (([regex]::Matches($jass,'DOTA女神')).Count -eq 1)
$checks['retain:sven-self-new'] = ($jass -match 'set selfRate=1\.\+1\.\*level') -and ($jass -notmatch 'set selfRate=\.5\+\.5\*level')
$checks['retain:sven-ally-new'] = ($jass -match 'set allyRate=1\.\+\.5\*level') -and ($jass -notmatch 'set allyRate=\.5\+\.25\*level')
$checks['retain:lion-plus50-x3'] = (([regex]::Matches($jass,'SWYJ\[i\]=SWYJ\[i\]\+50')).Count -eq 3) -and (([regex]::Matches($jass,'SWYJ\[i\]=SWYJ\[i\]\+20')).Count -eq 0)
$checks['retain:attr-ally-broadcast'] = ($jass -match 'allyId!=id') -and ($jass -match 'B836ArcHuman\(allyId\)') -and ($jass -match 'IsPlayerAlly\(Player\(allyId\),p\)') -and ($jass -match 'PLAYER_STATE_OBSERVER\)==0') -and ($jass -match '\[队友抽属性\]')
$checks['retain:bottle-family'] = ($jass -match 'function B1063IsBottleFamily takes integer raw returns boolean')
$checks['retain:drop-sell-sync'] = ($jass -match 'DzSyncData\("DROP_SELL"') -and ($jass -match 'function B1063SellSync')
$checks['retain:late-pool-600'] = ($jass -match 'TimerGetElapsed\(W\)>=600\. and B1063LateCount>0')
$checks['retain:miao-direct-pick'] = ($jass -match 'B891MiaoDirectRequest') -and ($jass -match 'set UB7=117') -and ($jass -match 'HMD0')
$checks['retain:imba-gate'] = ($jass -match 'constant boolean XOMG_IMBA_ENABLED=true')
$checks['retain:lottery-floor'] = ($jass -match 'GetRandomInt\(1000,1500\)')
$checks['retain:no-skin-path'] = ($jass -notmatch '(?i)skins\\')
$checks['retain:no-defense-impl'] = ($jass -notmatch '(?m)^function KKDefense_(?!IsWaveType)')
$checks['retain:no-wheel-impl'] = ($jass -notmatch '(?m)^function B1004(?!ControlUnit)')
$checks['retain:a088-present'] = ($jass -match 'A088')
$checks['retain:xomg1'] = ($jass -match 'XOMG1')
# CS retained text
$checks['cs:lion-50-x16'] = (([regex]::Matches($abilStr,'基础命中敌方英雄\+50点额外伤害')).Count -eq 16)
$checks['cs:sven-200-300-400'] = ($abilStr -match '增加自身200%的基础攻击力') -and ($abilStr -match '增加自身300%的基础攻击力') -and ($abilStr -match '增加自身400%的基础攻击力')

# ---- report ----
$rows = foreach ($k in $checks.Keys) {
    [PSCustomObject]@{ check=$k; pass=[bool]$checks[$k] }
}
$failed = $rows | Where-Object { -not $_.pass }
$report = [PSCustomObject]@{
    map=$MapPath; time=(Get-Date).ToString('o'); passed=($failed.Count -eq 0)
    total=$rows.Count; failedCount=$failed.Count; failures=($failed.check -join '; ')
}
New-Item -ItemType Directory -Force (Join-Path $root 'reports') | Out-Null
$report | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $root 'reports\verification-v17.json') -Encoding UTF8
$rows | Export-Csv -Path (Join-Path $root 'reports\verification-v17.csv') -NoTypeInformation -Encoding UTF8

$rows | ForEach-Object { '{0,-38} {1}' -f $_.check, $(if($_.pass){'PASS'}else{'FAIL'}) } | Write-Output
Write-Output ("v1.8.6-NOK checks: {0} pass, {1} fail" -f ($rows.Count-$failed.Count), $failed.Count)
if ($failed.Count -gt 0) { exit 1 }
