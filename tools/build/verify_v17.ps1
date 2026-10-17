param(
    [Parameter(Mandatory=$false)]
    [string]$MapPath
)
# Authoritative v1.7-K-VisualSkillFix gate: MPQ readback hash + semantic assertions +
# MDX/BLP structural parse. Exits non-zero on any failure.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
$config = Get-Content -LiteralPath (Join-Path $root 'config\tool-paths.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ([string]::IsNullOrWhiteSpace($MapPath)) {
    $MapPath = if ([IO.Path]::IsPathRooted($config.baselineMap)) { $config.baselineMap } else { Join-Path $root $config.baselineMap }
}
$MapPath = [IO.Path]::GetFullPath($MapPath)
$verifyDir = Join-Path ([IO.Path]::GetTempPath()) ('v17verify-' + [guid]::NewGuid().ToString('N'))
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
$abilData = [IO.File]::ReadAllText((Extract-FromMpq 'Units\AbilityData.slk'), [Text.Encoding]::UTF8)
$uiSlk = [IO.File]::ReadAllText((Extract-FromMpq 'Units\UnitUI.slk'), [Text.Encoding]::UTF8)
$unitStr = [IO.File]::ReadAllText((Extract-FromMpq 'Units\CampaignUnitStrings.txt'), [Text.Encoding]::UTF8)
$abilStr = [IO.File]::ReadAllText((Extract-FromMpq 'Units\CampaignAbilityStrings.txt'), [Text.Encoding]::UTF8)

# ---- w3i binary hard assertions: fixed 806B, equal-length label x2, byte-diff vs a1c1de1 only in slots ----
$w3iLocal = Extract-FromMpq 'war3map.w3i'
$w3iBytes = [IO.File]::ReadAllBytes($w3iLocal)
$checks['w3i:fixed-806'] = ($w3iBytes.Length -eq 806)
$newLabel = [Text.Encoding]::ASCII.GetBytes('OMG IMBA v1.7.1-W3IFix  ')
$oldLabel = [Text.Encoding]::ASCII.GetBytes('OMG IMBA v1.6-K-Visible ')
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
$checks['w3i:new-label-x2'] = ((Count-Sub $w3iBytes $newLabel) -eq 2)
$checks['w3i:old-label-x0'] = ((Count-Sub $w3iBytes $oldLabel) -eq 0)
# byte-diff vs a1c1de1 baseline: changed indices must live only inside slots 0x0C(12) len24 and 0xEA(234) len24
$baselineW3i = $null
$tmpBlob = Join-Path $verifyDir 'baseline-w3i.bin'
cmd /c "git show a1c1de1:src/war3map.w3i > `"$tmpBlob`""
if (Test-Path $tmpBlob) { $baselineW3i = [IO.File]::ReadAllBytes($tmpBlob) }
$allow = New-Object System.Collections.Generic.HashSet[int]
foreach ($s in 12,234) { for ($k = 0; $k -lt 24; $k++) { [void]$allow.Add($s + $k) } }
$diffOk = $true
if ($baselineW3i -and $baselineW3i.Length -eq 806) {
    for ($i = 0; $i -lt 806; $i++) {
        if ($w3iBytes[$i] -ne $baselineW3i[$i] -and -not $allow.Contains($i)) { $diffOk = $false; break }
    }
} else { $diffOk = $false }
$checks['w3i:byte-equal-baseline-outside-slots'] = $diffOk

function Get-Block($text, $id) {
    $m = [regex]::Match($text, ('(?s)C;X1;Y\d+;K"' + [regex]::Escape($id) + '".*?(?=C;X1;Y\d+;K"|\z)'))
    return $m.Value
}

# ---- 2. version ----
$checks['version:xomg'] = ([regex]::Matches($jass, 'constant string XOMG_VERSION="v1\.7\.1-K-W3IFix"')).Count -eq 1
$checks['version:setmapname'] = ([regex]::Matches($jass, 'SetMapName\("OMG IMBA v1\.7\.1-K-W3IFix"\)')).Count -eq 1

# ---- 3. KA skill templates: four distinct basecodes, distinct orders ----
$ka = @{}
foreach ($c in 'KA01','KA02','KA03','KA04') { $ka[$c] = Get-Block $abilData $c }
$base = @{}
foreach ($c in $ka.Keys) { $base[$c] = ([regex]::Match($ka[$c], 'C;X2;K"([^"]+)"')).Groups[1].Value }
$checks['ka:four-distinct-basecode'] = (($base.Values | Select-Object -Unique).Count -eq 4)
$checks['ka:no-aamk'] = -not ($ka.Values -join "`n" -match 'K"Aamk"')
$checks['ka:no-ancl'] = -not ($ka.Values -join "`n" -match 'K"ANcl"')
$checks['ka:no-aowk'] = -not ($ka.Values -join "`n" -match 'AOwk')
$checks['ka:no-achl'] = -not ($ka.Values -join "`n" -match 'Achl')
# expected templates
$checks['ka:ka01-ahad'] = ($base['KA01'] -eq 'AHad')
$checks['ka:ka02-aev'] = ($base['KA02'] -eq 'AEev')
$checks['ka:ka03-ahds'] = ($base['KA03'] -eq 'AHds')
$checks['ka:ka04-ando'] = ($base['KA04'] -eq 'ANdo')

# learn rules: normals reqLevel1 levels4; ult req6 skip5 levels3
$checks['ka:ka02-lvl4-req1'] = ($ka['KA02'] -match 'C;X72;K4') -and ($ka['KA02'] -match 'C;X75;K1')
$checks['ka:ka03-lvl4-req1'] = ($ka['KA03'] -match 'C;X72;K4') -and ($ka['KA03'] -match 'C;X75;K1')
$checks['ka:ka03-cd10'] = (([regex]::Matches($ka['KA03'], 'C;X1[6-9];K10\.0')).Count -eq 4)
$checks['ka:ka04-ult'] = ($ka['KA04'] -match 'C;X72;K3') -and ($ka['KA04'] -match 'C;X73;K5') -and ($ka['KA04'] -match 'C;X75;K6')
$checks['ka:ka04-cd'] = ($ka['KA04'] -match 'C;X16;K80\.0') -and ($ka['KA04'] -match 'C;X17;K65\.0') -and ($ka['KA04'] -match 'C;X18;K50\.0')

# strings: orders, dedicated icons, no PASBTN, no chemicalrage on KA04
$kaStr = @{}
foreach ($c in 'KA01','KA02','KA03','KA04') {
    $m=[regex]::Match($abilStr,('(?ms)^\['+$c+'\].*?(?=^\[|\z)'))
    $kaStr[$c]=$m.Value
}
$checks['ka:order-divineshield'] = ($kaStr['KA03'] -match '(?m)^Order=divineshield$')
$checks['ka:order-doom'] = ($kaStr['KA04'] -match '(?m)^Order=doom$')
$checks['ka:ka01-no-order'] = ($kaStr['KA01'] -notmatch '(?m)^Order=')
$checks['ka:ka02-no-order'] = ($kaStr['KA02'] -notmatch '(?m)^Order=')
# Prohibit the alchemist chemicalrage ORDER/chain on KA04; our own BTNKChemicalRage button filename is allowed.
$checks['ka:no-chemicalrage'] = ($kaStr['KA04'] -notmatch '(?m)^Order=chemicalrage$') -and ($ka['KA04'] -notmatch 'chemicalrage') -and ($kaStr['KA04'] -notmatch 'BTNChemicalRage\.blp')
$checks['ka:no-pasbtn'] = -not ($kaStr.Values -join "`n" -match 'PASBTN')
foreach ($c in 'KA01','KA02','KA03','KA04') {
    $checks["icon:$c-art"] = ($kaStr[$c] -match '(?m)^Art=ReplaceableTextures\\CommandButtons\\BTNK')
    $checks["icon:$c-researchart"] = ($kaStr[$c] -match '(?m)^ResearchArt=ReplaceableTextures\\CommandButtons\\BTNK')
}

# ---- 4. compat chain double insurance ----
$checks['guard:compat-apply'] = ($jass -match "SuijiMode_ChemicalRageCompatApply") -and ($jass -match "GetUnitTypeId\(u\)==KK_HERO or GetUnitAbilityLevel\(u,'KA04'\)>0")
$checks['guard:setvisualform'] = ($jass -match "SuijiMode_SetVisualForm") -and ([regex]::Matches($jass,"GetUnitTypeId\(u\)==KK_HERO or GetUnitAbilityLevel\(u,'KA04'\)>0").Count -ge 2)

# ---- 5. hero UI / preview wiring ----
$checks['ui:model-v2'] = ($uiSlk -match 'C;X10;K"war3mapimported\\K\\K_final_v2\.mdx"')
$checks['ui:scale-1'] = ($uiSlk -match '(?s)C;X1;Y\d+;K"H0K0".*?C;X20;K1\.0')
$h0k0 = [regex]::Match($unitStr,'(?ms)^\[H0K0\].*?(?=^\[|\z)').Value
$checks['ui:hero-icon'] = ($h0k0 -match '(?m)^Art=ReplaceableTextures\\CommandButtons\\BTNK_Hero\.blp$') -and ($h0k0 -match '(?m)^ScoreScreenIcon=ReplaceableTextures\\CommandButtons\\BTNK_Hero\.blp$')
$checks['ui:preview-icon'] = ($jass -match 'set MH4\[118\]="ReplaceableTextures\\\\CommandButtons\\\\BTNK_Hero\.blp"')

# ---- 6. KK recovery chain retained ----
$checks['kk:register'] = ([regex]::Matches($jass,"call R1X\('H0K0',0,'KA01','KA02','KA03','KA04'\)")).Count -eq 1
$checks['kk:ensure'] = ($jass -match 'function KK_EnsureHeroAbilities takes unit u returns nothing')
$checks['kk:apply-bypass'] = ($jass -match 'if GetUnitTypeId\(u\)==KK_HERO then')
$checks['kk:index-skills'] = ($jass -match "set HN4\[118\]='KA02'") -and ($jass -match "set HO4\[118\]='KA03'") -and ($jass -match "set HP4\[118\]='KA04'")

# ---- 7. retained-system smoke ----
$checks['retain:imba-gate'] = ($jass -match 'constant boolean XOMG_IMBA_ENABLED=true')
$checks['retain:lottery-floor'] = ($jass -match 'GetRandomInt\(1000,1500\)')
$checks['retain:no-skin-path'] = ($jass -notmatch '(?i)skins\\')
$checks['retain:no-defense-impl'] = ($jass -notmatch '(?m)^function KKDefense_(?!IsWaveType)')
$checks['retain:no-wheel-impl'] = ($jass -notmatch '(?m)^function B1004(?!ControlUnit)')
$checks['retain:a088-present'] = ($jass -match 'A088')
$checks['retain:xomg1'] = ($jass -match 'XOMG1')

# ---- 8. asset readback hash + structural parse ----
$assetPairs = @(
    @{arc='war3mapimported\K\K_final_v2.mdx'; src='assets\Kv2\model\K_final_v2.mdx'; kind='world'},
    @{arc='war3mapimported\K\K_final_portrait.mdx'; src='assets\Kv2\model\K_final_portrait.mdx'; kind='portrait'},
    @{arc='war3mapimported\K\K_body.blp'; src='assets\Kv2\textures\K_body.blp'; kind='blp'},
    @{arc='ReplaceableTextures\CommandButtons\BTNK_Hero.blp'; src='assets\Kv2\buttons\BTNK_Hero.blp'; kind='blp'},
    @{arc='ReplaceableTextures\CommandButtonsDisabled\DISBTNK_Hero.blp'; src='assets\Kv2\buttons\DISBTNK_Hero.blp'; kind='blp'},
    @{arc='ReplaceableTextures\CommandButtons\BTNKMarksmanship.blp'; src='assets\Kv2\buttons\BTNKMarksmanship.blp'; kind='blp'},
    @{arc='ReplaceableTextures\CommandButtonsDisabled\DISBTNKMarksmanship.blp'; src='assets\Kv2\buttons\DISBTNKMarksmanship.blp'; kind='blp'},
    @{arc='ReplaceableTextures\CommandButtons\BTNKCriticalStrike.blp'; src='assets\Kv2\buttons\BTNKCriticalStrike.blp'; kind='blp'},
    @{arc='ReplaceableTextures\CommandButtonsDisabled\DISBTNKCriticalStrike.blp'; src='assets\Kv2\buttons\DISBTNKCriticalStrike.blp'; kind='blp'},
    @{arc='ReplaceableTextures\CommandButtons\BTNKBattleRoar.blp'; src='assets\Kv2\buttons\BTNKBattleRoar.blp'; kind='blp'},
    @{arc='ReplaceableTextures\CommandButtonsDisabled\DISBTNKBattleRoar.blp'; src='assets\Kv2\buttons\DISBTNKBattleRoar.blp'; kind='blp'},
    @{arc='ReplaceableTextures\CommandButtons\BTNKChemicalRage.blp'; src='assets\Kv2\buttons\BTNKChemicalRage.blp'; kind='blp'},
    @{arc='ReplaceableTextures\CommandButtonsDisabled\DISBTNKChemicalRage.blp'; src='assets\Kv2\buttons\DISBTNKChemicalRage.blp'; kind='blp'}
)
foreach ($a in $assetPairs) {
    $local = Extract-FromMpq $a.arc
    $h1=(Get-FileHash -LiteralPath $local -Algorithm SHA256).Hash.ToLowerInvariant()
    $h2=(Get-FileHash -LiteralPath (Join-Path $root $a.src) -Algorithm SHA256).Hash.ToLowerInvariant()
    $checks["hash:$($a.arc)"] = ($h1 -eq $h2)
    $bytes=[IO.File]::ReadAllBytes($local)
    if ($a.kind -eq 'blp') {
        $sig=[Text.Encoding]::ASCII.GetString($bytes,0,4)
        $comp=[BitConverter]::ToUInt32($bytes,4)
        $pic=[BitConverter]::ToUInt32($bytes,20)
        $off0=[BitConverter]::ToUInt32($bytes,28); $size0=[BitConverter]::ToUInt32($bytes,92)
        $checks["blp:$($a.arc)"] = ($sig -eq 'BLP1' -and $comp -eq 1 -and $pic -eq 5 -and ($off0+$size0) -le $bytes.Length)
    }
}

# MDX structural parse (world + portrait)
foreach ($pair in @(@{arc='war3mapimported\K\K_final_v2.mdx';kind='world'},@{arc='war3mapimported\K\K_final_portrait.mdx';kind='portrait'})) {
    $local = Extract-FromMpq $pair.arc
    $bytes=[IO.File]::ReadAllBytes($local)
    $ok = ($bytes.Length -ge 16) -and ([Text.Encoding]::ASCII.GetString($bytes,0,4) -eq 'MDLX')
    $pos=4; $vers=0; $modl=''; $seqs=$false; $cams=0
    while ($pos+8 -le $bytes.Length) {
        $tag=[Text.Encoding]::ASCII.GetString($bytes,$pos,4)
        $size=[BitConverter]::ToUInt32($bytes,$pos+4)
        if ([uint64]$pos+8+[uint64]$size -gt $bytes.Length) { $ok=$false; break }
        if ($tag -eq 'VERS') { $vers=[BitConverter]::ToUInt32($bytes,$pos+8) }
        if ($tag -eq 'MODL') { $modl=[Text.Encoding]::ASCII.GetString($bytes,$pos+8,80).Trim([char]0) }
        if ($tag -eq 'SEQS') { $seqs=$true }
        if ($tag -eq 'CAMS' -and $size -ge 120) { $cams++ }
        $pos += 8+$size
    }
    if ($pair.kind -eq 'world') {
        $checks['mdx:world-vers800'] = ($vers -eq 800)
        $checks['mdx:world-modl'] = (-not [string]::IsNullOrWhiteSpace($modl))
        $checks['mdx:world-seqs'] = $seqs
        $checks['mdx:world-bounds'] = $ok
    } else {
        $checks['mdx:portrait-vers800'] = ($vers -eq 800)
        $checks['mdx:portrait-cams1'] = ($cams -eq 1)
        $checks['mdx:portrait-bounds'] = $ok
    }
}

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

$rows | ForEach-Object { '{0,-34} {1}' -f $_.check, $(if($_.pass){'PASS'}else{'FAIL'}) } | Write-Output
Write-Output ("v1.7 checks: {0} pass, {1} fail" -f ($rows.Count-$failed.Count), $failed.Count)
if ($failed.Count -gt 0) { exit 1 }
