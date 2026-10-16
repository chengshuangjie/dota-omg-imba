param(
    [switch]$SkipSyntaxCheck
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
$configPath = Join-Path $root 'config\tool-paths.json'
$config = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json

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
            if ($stable -ge 4) { return }
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

$baseline = Resolve-ProjectPath $config.baselineMap
$output = Resolve-ProjectPath $config.outputMap
$src = Join-Path $root 'src\war3map.j'
$imp = Join-Path $root 'src\war3map.imp'
$unitDir = Join-Path $root 'src\data\Units'
$assetDir = Join-Path $root 'assets\loading-screen'
$tempRoot = Join-Path ([IO.Path]::GetTempPath()) 'DotaOmgImbaLightBuild'
$stageDir = Join-Path $tempRoot 'stage'
$asciiMap = Join-Path $tempRoot 'map_work.w3x'

if (-not (Test-Path -LiteralPath $baseline -PathType Leaf)) { throw "缺少基线地图: $baseline" }
if (-not (Test-Path -LiteralPath $src -PathType Leaf)) { throw "缺少主源码: $src" }
if (-not (Test-Path -LiteralPath $config.mpqEditor -PathType Leaf)) { throw "缺少 MPQEditor: $($config.mpqEditor)" }

[IO.Directory]::CreateDirectory($stageDir) | Out-Null
[IO.Directory]::CreateDirectory((Split-Path -Parent $output)) | Out-Null

$sourceEntries = @(
    @{ Source = $src; Stage = 'war3map.j'; Archive = 'war3map.j' },
    @{ Source = (Join-Path $root 'src\war3map.w3i'); Stage = 'war3map.w3i'; Archive = 'war3map.w3i' },
    @{ Source = $imp; Stage = 'war3map.imp'; Archive = 'war3map.imp' },
    @{ Source = (Join-Path $unitDir 'CampaignAbilityStrings.txt'); Stage = 'CampaignAbilityStrings.txt'; Archive = 'Units\CampaignAbilityStrings.txt' },
    @{ Source = (Join-Path $unitDir 'CampaignUnitStrings.txt'); Stage = 'CampaignUnitStrings.txt'; Archive = 'Units\CampaignUnitStrings.txt' },
    @{ Source = (Join-Path $unitDir 'UnitAbilities.slk'); Stage = 'UnitAbilities.slk'; Archive = 'Units\UnitAbilities.slk' },
    @{ Source = (Join-Path $unitDir 'UnitBalance.slk'); Stage = 'UnitBalance.slk'; Archive = 'Units\UnitBalance.slk' },
    @{ Source = (Join-Path $unitDir 'UnitData.slk'); Stage = 'UnitData.slk'; Archive = 'Units\UnitData.slk' },
    @{ Source = (Join-Path $unitDir 'UnitUI.slk'); Stage = 'UnitUI.slk'; Archive = 'Units\UnitUI.slk' },
    @{ Source = (Join-Path $unitDir 'UnitWeapons.slk'); Stage = 'UnitWeapons.slk'; Archive = 'Units\UnitWeapons.slk' },
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

Copy-Item -LiteralPath $baseline -Destination $asciiMap -Force
Wait-FileStable $asciiMap 30
foreach ($entry in $sourceEntries) {
    Invoke-MpqAdd $asciiMap (Join-Path $stageDir $entry.Stage) $entry.Archive
}

Copy-Item -LiteralPath $asciiMap -Destination $output -Force
Wait-FileStable $output 30
& (Join-Path $root 'tools\build\verify.ps1') -MapPath $output
if ($LASTEXITCODE -ne 0) { throw "地图回读验证失败" }

Write-Output "构建完成: $output"
