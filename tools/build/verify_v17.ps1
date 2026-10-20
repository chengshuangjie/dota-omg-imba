param(
    [Parameter(Mandatory=$false)]
    [string]$MapPath
)
# Authoritative v1.8.6-NOK gate: MPQ readback hash match + NOK zero-residue + pool
# structural assertions + retained-system smoke. Exits non-zero on any failure.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
$localConfig = Join-Path $root 'config\tool-paths.json'
$configPath = if (Test-Path -LiteralPath $localConfig -PathType Leaf) { $localConfig } else { Join-Path $root 'config\tool-paths.example.json' }
$config = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
function Resolve-ProjectPath([string]$value) {
    if ([IO.Path]::IsPathRooted($value)) { return $value }
    return [IO.Path]::GetFullPath((Join-Path $root $value))
}
$config.mpqEditor = Resolve-ProjectPath $config.mpqEditor
if ([string]::IsNullOrWhiteSpace($MapPath)) {
    $MapPath = if ([IO.Path]::IsPathRooted($config.baselineMap)) { $config.baselineMap } else { Join-Path $root $config.baselineMap }
}
$MapPath = [IO.Path]::GetFullPath($MapPath)
$baselineMap = if ([IO.Path]::IsPathRooted($config.baselineMap)) { $config.baselineMap } else { Join-Path $root $config.baselineMap }
$baselineMap = [IO.Path]::GetFullPath($baselineMap)
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
    @{arc='units\campaignabilitystrings.txt'; src='src\data\Units\CampaignAbilityStrings.txt'},
    @{arc='units\campaignunitstrings.txt'; src='src\data\Units\CampaignUnitStrings.txt'},
    @{arc='units\unitabilities.slk'; src='src\data\Units\UnitAbilities.slk'},
    @{arc='units\unitbalance.slk'; src='src\data\Units\UnitBalance.slk'},
    @{arc='units\unitdata.slk'; src='src\data\Units\UnitData.slk'},
    @{arc='units\unitui.slk'; src='src\data\Units\UnitUI.slk'},
    @{arc='units\unitweapons.slk'; src='src\data\Units\UnitWeapons.slk'},
    @{arc='units\abilitydata.slk'; src='src\data\Units\AbilityData.slk'}
)
foreach ($p in $textPairs) {
    $local = Extract-FromMpq $p.arc
    $h1=(Get-FileHash -LiteralPath $local -Algorithm SHA256).Hash.ToLowerInvariant()
    $h2=(Get-FileHash -LiteralPath (Join-Path $root $p.src) -Algorithm SHA256).Hash.ToLowerInvariant()
    $checks["hash:$($p.arc)"] = ($h1 -eq $h2)
}

$jass = [IO.File]::ReadAllText((Extract-FromMpq 'war3map.j'), [Text.Encoding]::UTF8)
$jass = $jass -replace "`r`n","`n"
$abilData = [IO.File]::ReadAllText((Extract-FromMpq 'units\abilitydata.slk'), [Text.Encoding]::UTF8)
$uiSlk = [IO.File]::ReadAllText((Extract-FromMpq 'units\unitui.slk'), [Text.Encoding]::UTF8)
$unitStr = [IO.File]::ReadAllText((Extract-FromMpq 'units\campaignunitstrings.txt'), [Text.Encoding]::UTF8)
$abilStr = [IO.File]::ReadAllText((Extract-FromMpq 'units\campaignabilitystrings.txt'), [Text.Encoding]::UTF8)
$abilStr = $abilStr -replace "`r`n","`n"
$impBytes = [IO.File]::ReadAllBytes((Extract-FromMpq 'war3map.imp'))
$dooReadback = Extract-FromMpq 'war3map.doo'
$w3eReadback = Extract-FromMpq 'war3map.w3e'
$checks['environment:doo-frozen-sha256'] = ((Get-FileHash -LiteralPath $dooReadback -Algorithm SHA256).Hash -eq 'F6EA5428531D04AC680F9D51B318BE5B65E776B58BC342BB5004E32B2F0BF915')
$checks['environment:w3e-frozen-sha256'] = ((Get-FileHash -LiteralPath $w3eReadback -Algorithm SHA256).Hash -eq '55962DAE4021A0ECA6DAD6011E9A37B00459362BC062725260D6799FB8E9F593')

# SLK tail-deletion safety: declared B;Y must exactly match the largest actual C;...;Y row.
# Warcraft III 1.27 may exit during object preload before map logging when these diverge.
function Test-SlkDeclaredMaxY([string]$archive) {
    $bytes = [IO.File]::ReadAllBytes((Extract-FromMpq $archive))
    $text = [Text.Encoding]::ASCII.GetString($bytes)
    $decl = [regex]::Match($text, '(?m)^B;[^\r\n]*;Y(\d+);')
    $actual = [regex]::Matches($text, '(?m)^C;[^\r\n]*;Y(\d+)(?:;|$)')
    if (-not $decl.Success -or $actual.Count -eq 0) { return $false }
    $maxY = 0
    foreach ($m in $actual) { $y = [int]$m.Groups[1].Value; if ($y -gt $maxY) { $maxY = $y } }
    return ([int]$decl.Groups[1].Value -eq $maxY) -and ($text -match '(?m)^E\s*$')
}
foreach ($arc in @('units\abilitydata.slk','units\unitabilities.slk','units\unitbalance.slk','units\unitdata.slk','units\unitui.slk','units\unitweapons.slk')) {
    $checks["slk:declared-maxY:$arc"] = Test-SlkDeclaredMaxY $arc
}

# ---- 2. w3i binary: fixed 806B, exact 24B label x2, prior labels x0,
# and every byte outside the two fixed name slots equal to the project-local noskin19 baseline. ----
$w3iBytes = [IO.File]::ReadAllBytes((Extract-FromMpq 'war3map.w3i'))
$checks['w3i:fixed-806'] = ($w3iBytes.Length -eq 806)
$slotALabel = [Text.Encoding]::ASCII.GetBytes(('v6.90a-OMG-AI-1.0').PadRight(24,' '))
$slotBLabel = [Text.Encoding]::ASCII.GetBytes(('Dota v6.90a OMG AI 1.0').PadRight(24,' '))
$checks['w3i:art683-slots-24b'] = ($slotALabel.Length -eq 24) -and ($slotBLabel.Length -eq 24)
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
function Compare-Slot($hay, $off, $expect) {
    for ($k = 0; $k -lt 24; $k++) { if ($hay[$off + $k] -ne $expect[$k]) { return $false } }
    return $true
}
$checks['w3i:slotA-12-art683'] = (Compare-Slot $w3iBytes 12 $slotALabel)
$checks['w3i:slotB-234-art683'] = (Compare-Slot $w3iBytes 234 $slotBLabel)
foreach ($pl in @('OMG IMBA v1.8.5-SYNCF001','OMG IMBA v1.7.1-W3IFix','v1.6-K','K-W3IFix','v1.7.1-K','v6.9-ART683-T10','6.9 OMG IMBA ART683-T10')) {
    $pb = [Text.Encoding]::ASCII.GetBytes($pl)
    $checks["w3i:prior-x0:$pl"] = ((Count-Sub $w3iBytes $pb) -eq 0)
}
$baselineExtractDir = Join-Path $verifyDir 'baseline'
[IO.Directory]::CreateDirectory($baselineExtractDir) | Out-Null
$baselineW3iPath = Join-Path $baselineExtractDir 'war3map.w3i'
& $config.mpqEditor extract $baselineMap 'war3map.w3i' $baselineExtractDir /fp | Out-Null
if (-not (Test-Path -LiteralPath $baselineW3iPath -PathType Leaf)) { throw "无法从项目内稳定基线回读 war3map.w3i: $baselineMap" }
$baselineW3i = [IO.File]::ReadAllBytes($baselineW3iPath)
$allow = New-Object System.Collections.Generic.HashSet[int]
foreach ($s in 12,234) { for ($k = 0; $k -lt 24; $k++) { [void]$allow.Add($s + $k) } }
$diffOk = $false
if ($baselineW3i.Length -eq 806) {
    $diffOk = $true
    for ($i = 0; $i -lt 806; $i++) {
        if ($w3iBytes[$i] -ne $baselineW3i[$i] -and -not $allow.Contains($i)) { $diffOk = $false; break }
    }
}
$checks['w3i:byte-equal-baseline-outside-slots'] = $diffOk

# ---- 3. version, clean-system and lottery-house gates ----
$checks['version:xomg-v690a'] = (([regex]::Matches($jass,'constant string XOMG_VERSION="v6\.90a-OMG-AI-1\.0"')).Count -eq 1)
$checks['version:setmapname-v690a'] = (([regex]::Matches($jass,'SetMapName\("Dota v6\.90a OMG AI 1\.0"\)')).Count -eq 1)
$checks['version:no-art683-t10-xomg'] = ($jass -notmatch [regex]::Escape('XOMG_VERSION="v6.9-ART683-T10"'))
$checks['version:no-art683-t10-setmapname'] = ($jass -notmatch [regex]::Escape('SetMapName("6.9 OMG IMBA ART683-T10")'))
$checks['ui:fissure-selection-actual-damage'] = ($unitStr -match '(?s)\[v025\].*?\[IMBA实际值\].*?造成220伤害，1秒眩晕.*?造成320伤害，1\.25秒眩晕.*?造成420伤害，1\.5秒眩晕.*?造成520伤害，1\.75秒眩晕')
$checks['ui:fissure-selection-no-base-damage'] = ($unitStr -notmatch '(?s)\[v025\].*?造成110伤害，1秒眩晕.*?\[v026\]')
$checks['ui:broadcast-message'] = (([regex]::Matches($jass,'开局可免费幸运大抽奖，打野10%概率掉装备')).Count -eq 2) -and ($jass -match '可鼠标左键双击快速售出，多余的钱可用来抽英雄全属性')
$checks['ui:no-old-broadcast-message'] = ($jass -notmatch '游戏最重要的是抱团防守，抱团杀人的经验和经济')
$checks['lottery:init-call'] = ($jass -match '(?m)^\s*call LOTTERY_Init\(\)')
$checks['lottery:house-created'] = ($jass -match "CreateUnit\(Player\(PLAYER_NEUTRAL_PASSIVE\),'nAS6',-5728\.,-6816\.,270\.\)")
$checks['lottery:selection-sync'] = ($jass -match 'DzSyncData\("LOTOPEN",""\)') -and ($jass -match 'DzTriggerRegisterSyncData\(lotOpenTrigger,"LOTOPEN",false\)')
$checks['lottery:three-buttons'] = ($jass -match '幸运大抽奖（免费1次）') -and ($jass -match '1000抽属性（无限次）') -and ($jass -match '梭哈抽属性')
$checks['lottery:handlers'] = ($jass -match 'TriggerAddAction\(lotDialogTrigger,function LOTTERY_Click\)') -and ($jass -match 'TriggerAddAction\(lotSelectTrigger,function LOTTERY_Selected\)')
# ---- ART683-T6 permanent colored floating title above nAS6 (visual, sync-safe, once) ----
$checks['t6:title-text-x1'] = (([regex]::Matches($jass,[regex]::Escape('|cffff66cc抽|r|cffffff66奖|r|cff66ffff屋|r'))).Count -eq 1)
$checks['t6:title-create-once'] = (([regex]::Matches($jass,'B836LotteryTitle=CreateTextTag\(\)')).Count -eq 1)
$checks['t6:title-positioned'] = ($jass -match [regex]::Escape('call SetTextTagPos(B836LotteryTitle,GetUnitX(B836ArcHut)-128.,GetUnitY(B836ArcHut),256.)')) -and ($jass -notmatch 'SetTextTagPosUnit\(B836LotteryTitle') -and ($jass -notmatch [regex]::Escape('GetUnitX(B836ArcHut)-96.,GetUnitY(B836ArcHut),256.)'))
$checks['t6:title-permanent'] = ($jass -match 'SetTextTagPermanent\(B836LotteryTitle,true\)') -and ($jass -match 'SetTextTagLifespan\(B836LotteryTitle,0\)') -and ($jass -match 'SetTextTagFadepoint\(B836LotteryTitle,0\)')
$checks['t6:title-all-visible'] = ($jass -match 'SetTextTagVisibility\(B836LotteryTitle,true\)')
$t6block = [regex]::Match($jass,'if B836LotteryTitle==null then(.*?)endif','Singleline').Groups[1].Value
$checks['t6:title-no-local-branch'] = ($t6block -notmatch 'GetLocalPlayer')
$checks['lottery:no-archive-chat'] = ($jass -notmatch 'TriggerRegisterPlayerChatEvent\([^\r\n]*"-archive"')
$checks['clean:no-archive-init-call'] = ($jass -notmatch '(?m)^\s*call B836ArcInit\(\)')
$checks['clean:no-mastery-init-call'] = ($jass -notmatch '(?m)^\s*call B1031Init\(\)')
$checks['clean:no-skin-init-call'] = ($jass -notmatch '(?m)^\s*call B1032Init\(\)')
$checks['clean:no-realm-init-call'] = ($jass -notmatch '(?m)^\s*call B1035Init\(\)')
$checks['clean:no-tip-init-call'] = ($jass -notmatch '(?m)^\s*call B1042Init\(\)')
$checks['clean:no-recharge-routing'] = ($jass -notmatch 'ExecuteFunc\("B1131Recharge"\)')
$checks['clean:no-old-debug-account'] = ($jass -notmatch '狂扁大帅比#2254|狂扁AI')
$checks['clean:give-current-gold'] = ($jass -match 'function B1043Give') -and ($jass -match 'AdjustPlayerStateBJ\(giveGold1043,givePlayer1043,PLAYER_STATE_RESOURCE_GOLD\)') -and ($jass -notmatch 'B894PlayerIdentity\[giveAuthor1043\]!="小生我怕怕#7351"')
$checks['clean:xiaosheng-prefix'] = ($jass -match 'function B1132StartsWithXiaoSheng') -and ($jass -match 'SubString\(fuzzyText1132,0,StringLength\("小生"\)\)=="小生"')
$checks['clean:no-entry-gift-write'] = ($jass -notmatch 'GIFT_CANDIDATE|giftCoins1130|15\*86400')
$checks['clean:no-legacy-skin-download-write'] = ($jass -notmatch 'PreloadGenEnd\("save\\\\DotaAI6\.9_Download\.txt"\)')
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

$checks['ui:lottery-title-short'] = (([regex]::Matches($jass,'DialogSetMessage\(LOTTERY_DIALOG\[lotPid\],"抽奖屋"\)')).Count -eq 1)
$checks['ui:lottery-free-label'] = (([regex]::Matches($jass,'幸运大抽奖（免费1次）')).Count -eq 1)
$checks['ui:no-old-faction-name'] = ($jass -notmatch '达拉然势力') -and ($abilStr -notmatch '达拉然势力') -and ($unitStr -notmatch '达拉然势力')
$checks['ui:new-faction-name'] = ($jass -match '近卫军团') -and ($abilStr -match '近卫军团') -and ($unitStr -match '近卫军团')

# ---- report ----
$rows = foreach ($k in $checks.Keys) {
    [PSCustomObject]@{ check=$k; pass=[bool]$checks[$k] }
}
$failed = @($rows | Where-Object { -not $_.pass })
$failedCount = $failed.Count
$reportMap = $MapPath
$rootPrefix = $root.TrimEnd('\') + '\'
if ($MapPath.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    $reportMap = $MapPath.Substring($rootPrefix.Length).Replace('\','/')
}
$report = [PSCustomObject]@{
    map=$reportMap; passed=($failedCount -eq 0)
    total=$rows.Count; failedCount=$failedCount; failures=($failed.check -join '; ')
}
New-Item -ItemType Directory -Force (Join-Path $root 'reports') | Out-Null
$reportJson = $report | ConvertTo-Json -Depth 5
[IO.File]::WriteAllText((Join-Path $root 'reports\verification-v17.json'), $reportJson, (New-Object Text.UTF8Encoding $false))
$rows | Export-Csv -Path (Join-Path $root 'reports\verification-v17.csv') -NoTypeInformation -Encoding UTF8

$rows | ForEach-Object { '{0,-38} {1}' -f $_.check, $(if($_.pass){'PASS'}else{'FAIL'}) } | Write-Output
Write-Output ("v6.90a 1.0 checks: {0} pass, {1} fail" -f ($rows.Count-$failedCount), $failedCount)
if ($failedCount -gt 0) { exit 1 }
