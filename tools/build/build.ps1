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
if (-not (Test-Path -LiteralPath $src -PathType Leaf)) { throw "缺少主源码: $src" }
if (-not (Test-Path -LiteralPath $config.mpqEditor -PathType Leaf)) { throw "缺少 MPQEditor: $($config.mpqEditor)" }

# Warcraft III 1.24 cannot load palette BLP1 resources whose pictureType/encoding is 0.
# Validate the K texture before touching the output map so an invalid resource can never be packaged again.
$kTexture = Join-Path $root 'assets\K\K_body.blp'
if (-not (Test-Path -LiteralPath $kTexture -PathType Leaf)) { throw "缺少 K 贴图: $kTexture" }
$kBlp = [IO.File]::ReadAllBytes($kTexture)
if ($kBlp.Length -lt 156 -or [Text.Encoding]::ASCII.GetString($kBlp,0,4) -ne 'BLP1') { throw "K 贴图不是有效 BLP1: $kTexture" }
$kBlpCompression = [BitConverter]::ToUInt32($kBlp,4)
$kBlpPictureType = [BitConverter]::ToUInt32($kBlp,20)
$kBlpWidth = [BitConverter]::ToUInt32($kBlp,12)
$kBlpHeight = [BitConverter]::ToUInt32($kBlp,16)
$kBlpOffset0 = [BitConverter]::ToUInt32($kBlp,28)
$kBlpSize0 = [BitConverter]::ToUInt32($kBlp,92)
if ($kBlpCompression -ne 1 -or ($kBlpPictureType -ne 4 -and $kBlpPictureType -ne 5) -or $kBlpWidth -eq 0 -or $kBlpHeight -eq 0 -or ([uint64]$kBlpOffset0 + [uint64]$kBlpSize0) -gt [uint64]$kBlp.Length) {
    throw "K 贴图 BLP1 与 Warcraft III 1.24 不兼容: compression=$kBlpCompression pictureType=$kBlpPictureType size=$($kBlpWidth)x$($kBlpHeight) mip0=$kBlpOffset0+$kBlpSize0 file=$($kBlp.Length)"
}

# Classic Warcraft III requires a non-empty MODL model name. The first K model was
# structurally parseable but had 80 zero bytes here and crashed before script init.
$kModel = Join-Path $root 'assets\K\K_final.mdx'
if (-not (Test-Path -LiteralPath $kModel -PathType Leaf)) { throw "缺少 K 模型: $kModel" }
$kMdx = [IO.File]::ReadAllBytes($kModel)
if ($kMdx.Length -lt 16 -or [Text.Encoding]::ASCII.GetString($kMdx,0,4) -ne 'MDLX') { throw "K 模型不是有效 MDX: $kModel" }
$kMdxPos = 4
$kMdxName = ''
while ($kMdxPos + 8 -le $kMdx.Length) {
    $kMdxTag = [Text.Encoding]::ASCII.GetString($kMdx,$kMdxPos,4)
    $kMdxSize = [BitConverter]::ToUInt32($kMdx,$kMdxPos + 4)
    if ([uint64]$kMdxPos + 8 + [uint64]$kMdxSize -gt [uint64]$kMdx.Length) { throw "K 模型区块越界: $kMdxTag" }
    if ($kMdxTag -eq 'MODL' -and $kMdxSize -ge 80) {
        $kMdxName = [Text.Encoding]::ASCII.GetString($kMdx,$kMdxPos + 8,80).Trim([char]0)
    }
    $kMdxPos += 8 + $kMdxSize
}
if ($kMdxPos -ne $kMdx.Length -or [string]::IsNullOrWhiteSpace($kMdxName)) { throw "K 模型 MODL 名称为空或结构不完整: $kModel" }

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
    @{ Source = (Join-Path $unitDir 'AbilityData.slk'); Stage = 'AbilityData.slk'; Archive = 'Units\AbilityData.slk' },
    @{ Source = (Join-Path $assetDir 'LoadingScreenTL.blp'); Stage = 'LoadingScreenTL.blp'; Archive = 'LoadingScreenTL.blp' },
    @{ Source = (Join-Path $assetDir 'LoadingScreenTR.blp'); Stage = 'LoadingScreenTR.blp'; Archive = 'LoadingScreenTR.blp' },
    @{ Source = (Join-Path $assetDir 'LoadingScreenBL.blp'); Stage = 'LoadingScreenBL.blp'; Archive = 'LoadingScreenBL.blp' },
    @{ Source = (Join-Path $assetDir 'LoadingScreenBR.blp'); Stage = 'LoadingScreenBR.blp'; Archive = 'LoadingScreenBR.blp' },
    @{ Source = (Join-Path $assetDir 'war3mapPreview.tga'); Stage = 'war3mapPreview.tga'; Archive = 'war3mapPreview.tga' },
    # v1.4-K hero K custom model + texture (independent; not part of v1.3 baseline)
    @{ Source = (Join-Path $root 'assets\K\K_final.mdx'); Stage = 'K_final.mdx'; Archive = 'war3mapimported\K\K_final.mdx' },
    @{ Source = (Join-Path $root 'assets\K\K_body.blp'); Stage = 'K_body.blp'; Archive = 'war3mapimported\K\K_body.blp' }
)

foreach ($entry in $sourceEntries) {
    if (-not (Test-Path -LiteralPath $entry.Source -PathType Leaf)) { throw "缺少待写入文件: $($entry.Source)" }
    Copy-Item -LiteralPath $entry.Source -Destination (Join-Path $stageDir $entry.Stage) -Force
}

# v1.4-K root-cause generator: relocate H0K0 blocks before E and zero KA native effects (idempotent).
# Only runs when the v1.4-K hero marker exists; v1.3 default build is untouched.
$kGen = Join-Path $root 'tools\transform\build_k_hero.py'
$markerAbil = Join-Path $unitDir 'UnitAbilities.slk'
$kActive = (Test-Path -LiteralPath $kGen -PathType Leaf) -and (Test-Path -LiteralPath $markerAbil -PathType Leaf) -and ((Select-String -Path $markerAbil -Pattern 'H0K0' -Quiet -Encoding UTF8))
if ($kActive) {
    $genProc = Start-Process -FilePath 'python' -ArgumentList ('"' + $kGen + '"') -Wait -PassThru -NoNewWindow
    if ($genProc.ExitCode -ne 0) { throw "v1.4-K SLK 生成脚本失败，退出码 $($genProc.ExitCode)" }
    # re-stage SLKs regenerated by the script
    foreach ($entry in $sourceEntries) {
        if ($entry.Archive -like 'Units\*.slk') {
            Copy-Item -LiteralPath $entry.Source -Destination (Join-Path $stageDir $entry.Stage) -Force
        }
    }
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
# MPQEditor 句柄释放存在短暂延迟，回读验证带重试吸收锁竞争
$verifyOk = $false
for ($attempt = 1; $attempt -le 3 -and -not $verifyOk; $attempt++) {
    Start-Sleep -Seconds 3
    & (Join-Path $root 'tools\build\verify.ps1') -MapPath $output
    if ($LASTEXITCODE -eq 0) { $verifyOk = $true }
}
if (-not $verifyOk) { throw "地图回读验证失败（3次重试后仍失败）" }

Write-Output "构建完成: $output"
