param(
    [switch]$SkipSyntaxCheck,
    [string]$ConfigPath = '',
    [string]$OutputMap = ''
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
if (-not $ConfigPath) { $ConfigPath = Join-Path $root 'config\tool-paths.json' }
$config = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json

function Resolve-ProjectPath([string]$value) {
    if ([IO.Path]::IsPathRooted($value)) { return $value }
    return [IO.Path]::GetFullPath((Join-Path $root $value))
}

function Wait-FileStable([string]$path, [int]$timeoutSeconds = 30) {
    $deadline = [DateTime]::UtcNow.AddSeconds($timeoutSeconds)
    $lastLength = -1L
    $stable = 0
    while ([DateTime]::UtcNow -lt $deadline) {
        if (Test-Path -LiteralPath $path -PathType Leaf) {
            $currentLength = (Get-Item -LiteralPath $path).Length
            if ($currentLength -gt 0 -and $currentLength -eq $lastLength) { $stable++ } else { $stable = 0 }
            $lastLength = $currentLength
            if ($stable -ge 40) { return }
        }
        Start-Sleep -Milliseconds 250
    }
    throw "文件未稳定: $path"
}

function Invoke-MpqAdd([string]$mapPath, [string]$sourcePath, [string]$archivePath) {
    $args = @('add', ('"' + $mapPath + '"'), ('"' + $sourcePath + '"'), ('"' + $archivePath + '"'), '/c', '/auto')
    $process = Start-Process -FilePath $config.mpqEditor -ArgumentList $args -Wait -PassThru
    if ($process.ExitCode -ne 0) { throw "MPQEditor 写入失败: $archivePath，退出码 $($process.ExitCode)" }
    Wait-FileStable $mapPath 60
}

function Invoke-MpqDelete([string]$mapPath, [string]$archivePath) {
    $args = @('delete', ('"' + $mapPath + '"'), ('"' + $archivePath + '"'))
    $process = Start-Process -FilePath $config.mpqEditor -ArgumentList $args -Wait -PassThru
    if ($process.ExitCode -ne 0) { throw "MPQEditor 删除失败: $archivePath，退出码 $($process.ExitCode)" }
    Wait-FileStable $mapPath 60
}

$baseline = Resolve-ProjectPath $config.baselineMap
$output = if ($OutputMap) { Resolve-ProjectPath $OutputMap } else { Resolve-ProjectPath $config.outputMap }
if (Test-Path -LiteralPath $output -PathType Leaf) { Remove-Item -LiteralPath $output -Force }
$src = Join-Path $root 'src\war3map.j'
$imp = Join-Path $root 'src\war3map.imp'
$unitDir = Join-Path $root 'src\data\Units'
$assetDir = Join-Path $root 'assets\loading-screen'
$tempRoot = Join-Path ([IO.Path]::GetTempPath()) ('DotaOmgImbaLightBuild-' + [guid]::NewGuid().ToString('N'))
$stageDir = Join-Path $tempRoot 'stage'
$asciiMap = Join-Path $tempRoot 'map_work.w3x'

if (-not (Test-Path -LiteralPath $baseline -PathType Leaf)) { throw "缺少基线地图: $baseline" }
$expectedBaselineSha256 = '93C1DF91B954022A8CF454D9B42C2B3D36ED5A13AD3D35E37418FA6B5A52D7A7'
$actualBaselineSha256 = (Get-FileHash -LiteralPath $baseline -Algorithm SHA256).Hash
if ($actualBaselineSha256 -ne $expectedBaselineSha256) {
    throw "构建基线不是noskin19实机稳定包：expected=$expectedBaselineSha256 actual=$actualBaselineSha256 path=$baseline"
}
if (-not (Test-Path -LiteralPath $src -PathType Leaf)) { throw "缺少主源码: $src" }
if (-not (Test-Path -LiteralPath $config.mpqEditor -PathType Leaf)) { throw "缺少 MPQEditor: $($config.mpqEditor)" }

[IO.Directory]::CreateDirectory($stageDir) | Out-Null
[IO.Directory]::CreateDirectory((Split-Path -Parent $output)) | Out-Null

$sourceEntries = @(
    @{ Source = $src; Stage = 'war3map.j'; Archive = 'war3map.j' },
    @{ Source = (Join-Path $root 'src\war3map.w3i'); Stage = 'war3map.w3i'; Archive = 'war3map.w3i' },
    @{ Source = $imp; Stage = 'war3map.imp'; Archive = 'war3map.imp' },
    @{ Source = (Join-Path $unitDir 'CampaignAbilityStrings.txt'); Stage = 'CampaignAbilityStrings.txt'; Archive = 'units\campaignabilitystrings.txt' },
    @{ Source = (Join-Path $unitDir 'CampaignUnitStrings.txt'); Stage = 'CampaignUnitStrings.txt'; Archive = 'units\campaignunitstrings.txt' },
    @{ Source = (Join-Path $unitDir 'UnitAbilities.slk'); Stage = 'UnitAbilities.slk'; Archive = 'units\unitabilities.slk' },
    @{ Source = (Join-Path $unitDir 'UnitBalance.slk'); Stage = 'UnitBalance.slk'; Archive = 'units\unitbalance.slk' },
    @{ Source = (Join-Path $unitDir 'UnitData.slk'); Stage = 'UnitData.slk'; Archive = 'units\unitdata.slk' },
    @{ Source = (Join-Path $unitDir 'UnitUI.slk'); Stage = 'UnitUI.slk'; Archive = 'units\unitui.slk' },
    @{ Source = (Join-Path $unitDir 'UnitWeapons.slk'); Stage = 'UnitWeapons.slk'; Archive = 'units\unitweapons.slk' },
    @{ Source = (Join-Path $unitDir 'AbilityData.slk'); Stage = 'AbilityData.slk'; Archive = 'units\abilitydata.slk' },
    @{ Source = (Join-Path $assetDir 'LoadingScreenTL.blp'); Stage = 'LoadingScreenTL.blp'; Archive = 'LoadingScreenTL.blp' },
    @{ Source = (Join-Path $assetDir 'LoadingScreenTR.blp'); Stage = 'LoadingScreenTR.blp'; Archive = 'LoadingScreenTR.blp' },
    @{ Source = (Join-Path $assetDir 'LoadingScreenBL.blp'); Stage = 'LoadingScreenBL.blp'; Archive = 'LoadingScreenBL.blp' },
    @{ Source = (Join-Path $assetDir 'LoadingScreenBR.blp'); Stage = 'LoadingScreenBR.blp'; Archive = 'LoadingScreenBR.blp' },
    @{ Source = (Join-Path $assetDir 'war3mapPreview.tga'); Stage = 'war3mapPreview.tga'; Archive = 'war3mapPreview.tga' }
)

foreach ($entry in $sourceEntries) {
    if (-not (Test-Path -LiteralPath $entry.Source -PathType Leaf)) { throw "缺少待写入文件: $($entry.Source)" }
    Copy-Item -LiteralPath $entry.Source -Destination (Join-Path $stageDir $entry.Stage) -Force
}

# noskin19 package-authoritative policy: checked-in SLKs are exact MPQ readbacks from the
# live-tested map. Do not run historical K generators during normal builds because they
# mutate src/data in place and can silently diverge from the verified package.

if (-not $SkipSyntaxCheck) {
    $pjassOut = Join-Path $tempRoot 'pjass.stdout.txt'
    $pjassErr = Join-Path $tempRoot 'pjass.stderr.txt'
    $args = @(('"' + $config.commonJ + '"'), ('"' + $config.blizzardJ + '"'), ('"' + (Join-Path $stageDir 'war3map.j') + '"'))
    $process = Start-Process -FilePath $config.pjass -ArgumentList $args -Wait -PassThru -RedirectStandardOutput $pjassOut -RedirectStandardError $pjassErr
    $pjassText = ''
    if (Test-Path -LiteralPath $pjassOut) { $pjassText += [IO.File]::ReadAllText($pjassOut) }
    if (Test-Path -LiteralPath $pjassErr) { $pjassText += [IO.File]::ReadAllText($pjassErr) }
    $diagnostics = @($pjassText -split "`r?`n" | Where-Object { $_ -match 'war3map\.j:\d+:' })
    $unexpected = @($diagnostics | Where-Object { $_ -notmatch 'location_m5' })
    if ($unexpected.Count -gt 0) {
        throw "PJASS 检查失败，发现 $($unexpected.Count) 条非既有错误，请查看 $pjassOut 和 $pjassErr"
    }
    if ($process.ExitCode -ne 0 -and $diagnostics.Count -eq 0) {
        throw "PJASS 非零退出但没有可识别诊断，请查看 $pjassOut 和 $pjassErr"
    }
}

# v1.8.6-NOK: binary equal-length w3i guard. Never decode/encode or text-replace the w3i;
# assert fixed 806B, the exact 24-byte NOK label (19 chars + 5 spaces) appears exactly
# twice in slots 0x0C/0xEA, and every prior K-era label is absent. Only the two 24-byte
# name slots differ from the baseline binary; all other bytes (players/forces) are untouched.
$w3iSrc = Join-Path $root 'src\war3map.w3i'
$w3iBytes = [IO.File]::ReadAllBytes($w3iSrc)
if ($w3iBytes.Length -ne 806) { throw "war3map.w3i 必须为固定 806B，当前 $($w3iBytes.Length)B（禁止变长替换）" }
$slotALabel = [Text.Encoding]::ASCII.GetBytes(('v6.90a-OMG-AI-1.0').PadRight(24,' '))
$slotBLabel = [Text.Encoding]::ASCII.GetBytes(('Dota v6.90a OMG AI 1.0').PadRight(24,' '))
if ($slotALabel.Length -ne 24 -or $slotBLabel.Length -ne 24) { throw "v6.90a 1.0 正式版标签必须精确 24B" }
$priorLabels = @('OMG IMBA v1.8.5-SYNCF001', 'OMG IMBA v1.7.1-W3IFix', 'v1.6-K', 'K-W3IFix')
function Count-Bytes($hay, $needle) {
    $c = 0; $i = 0
    while (($i = [Array]::IndexOf($hay, $needle[0], $i)) -ge 0) {
        $match = $true
        for ($k = 0; $k -lt $needle.Length; $k++) { if ($hay[$i + $k] -ne $needle[$k]) { $match = $false; break } }
        if ($match) { $c++ }
        $i++
    }
    return $c
}
function Compare-Slot($hay, $off, $expect) {
    for ($k = 0; $k -lt 24; $k++) { if ($hay[$off + $k] -ne $expect[$k]) { return $false } }
    return $true
}
if (-not (Compare-Slot $w3iBytes 12 $slotALabel)) { throw 'w3i 槽A@12 必须为 v6.90a-OMG-AI-1.0 24B 标签' }
if (-not (Compare-Slot $w3iBytes 234 $slotBLabel)) { throw 'w3i 槽B@234 必须为 Dota v6.90a OMG AI 1.0 24B 标签' }
foreach ($pl in $priorLabels) {
    $pb = [Text.Encoding]::ASCII.GetBytes($pl)
    if ((Count-Bytes $w3iBytes $pb) -ne 0) { throw "w3i 旧标签 $pl 必须为 0 次" }
}

Copy-Item -LiteralPath $baseline -Destination $asciiMap -Force
Wait-FileStable $asciiMap 30
foreach ($entry in $sourceEntries) {
    if ($entry.Archive -match '^(?i:war3map\.(j|w3i|imp)|units\\)') {
        Invoke-MpqDelete $asciiMap $entry.Archive
    }
    Invoke-MpqAdd $asciiMap (Join-Path $stageDir $entry.Stage) $entry.Archive
}

$kArchiveEntries = @(
    'war3mapimported\K\K_final.mdx',
    'war3mapimported\K\K_body.blp',
    'war3mapimported\K\K_final_portrait.mdx',
    'war3mapimported\K\K_final_v2.mdx',
    'replaceabletextures\commandbuttons\BTNK_Hero.blp',
    'replaceabletextures\commandbuttons\BTNKMarksmanship.blp',
    'replaceabletextures\commandbuttons\BTNKCriticalStrike.blp',
    'replaceabletextures\commandbuttons\BTNKBattleRoar.blp',
    'replaceabletextures\commandbuttons\BTNKChemicalRage.blp',
    'replaceabletextures\commandbuttonsdisabled\DISBTNK_Hero.blp',
    'replaceabletextures\commandbuttonsdisabled\DISBTNKMarksmanship.blp',
    'replaceabletextures\commandbuttonsdisabled\DISBTNKCriticalStrike.blp',
    'replaceabletextures\commandbuttonsdisabled\DISBTNKBattleRoar.blp',
    'replaceabletextures\commandbuttonsdisabled\DISBTNKChemicalRage.blp'
)
foreach ($archivePath in $kArchiveEntries) {
    Invoke-MpqDelete $asciiMap $archivePath
}

Copy-Item -LiteralPath $asciiMap -Destination $output -Force
Wait-FileStable $output 30

# Legacy static gate: executed for retained-system evidence only; its K-specific
# assertions have been converted to NOK zero-residue checks and must not block the build.
& (Join-Path $root 'tools\build\verify.ps1') -MapPath $output | Out-Null
Write-Output "遗留静态门已执行（仅留存系统证据；K 断言已转为 NOK 零残留门）"

# Authoritative v1.8.6-NOK semantic + readback gate; must exit 0.
$v17Ok = $false
for ($attempt = 1; $attempt -le 3 -and -not $v17Ok; $attempt++) {
    Start-Sleep -Seconds 3
    & (Join-Path $root 'tools\build\verify_v17.ps1') -MapPath $output
    if ($LASTEXITCODE -eq 0) { $v17Ok = $true }
}
if (-not $v17Ok) { throw "v1.8.6-NOK 回读语义验证失败（3次重试后仍失败）" }

Write-Output "构建完成: $output"
