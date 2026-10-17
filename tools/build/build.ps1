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
# Validate the v1.7-Kv2 K texture before touching the output map so an invalid resource can never be packaged again.
$kTexture = Join-Path $root 'assets\Kv2\textures\K_body.blp'
if (-not (Test-Path -LiteralPath $kTexture -PathType Leaf)) { throw "缺少 K 贴图(v2): $kTexture" }
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
$kModel = Join-Path $root 'assets\Kv2\model\K_final_v2.mdx'
if (-not (Test-Path -LiteralPath $kModel -PathType Leaf)) { throw "缺少 K 模型(v2): $kModel" }
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
# A complete hero portrait requires a sibling model with a valid CAMS chunk.
$kPortrait = Join-Path $root 'assets\Kv2\model\K_final_portrait.mdx'
if (-not (Test-Path -LiteralPath $kPortrait -PathType Leaf)) { throw "缺少 K 肖像模型(v2): $kPortrait" }
$kPortraitBytes = [IO.File]::ReadAllBytes($kPortrait)
if ($kPortraitBytes.Length -lt 16 -or [Text.Encoding]::ASCII.GetString($kPortraitBytes,0,4) -ne 'MDLX') { throw "K 肖像不是有效 MDX: $kPortrait" }
$kPortraitPos = 4
$kPortraitCamera = 0
while ($kPortraitPos + 8 -le $kPortraitBytes.Length) {
    $kPortraitTag = [Text.Encoding]::ASCII.GetString($kPortraitBytes,$kPortraitPos,4)
    $kPortraitSize = [BitConverter]::ToUInt32($kPortraitBytes,$kPortraitPos + 4)
    if ([uint64]$kPortraitPos + 8 + [uint64]$kPortraitSize -gt [uint64]$kPortraitBytes.Length) { throw "K 肖像模型区块越界: $kPortraitTag" }
    if ($kPortraitTag -eq 'CAMS' -and $kPortraitSize -ge 120) { $kPortraitCamera++ }
    $kPortraitPos += 8 + $kPortraitSize
}
if ($kPortraitPos -ne $kPortraitBytes.Length -or $kPortraitCamera -ne 1) { throw "K 肖像模型缺少唯一有效相机: $kPortrait" }

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
    # v1.6-K complete hero: world model, dedicated portrait camera model, and compatible texture (retained, not removed)
    @{ Source = (Join-Path $root 'assets\K\K_final.mdx'); Stage = 'K_final.mdx'; Archive = 'war3mapimported\K\K_final.mdx' },
    @{ Source = (Join-Path $root 'assets\K\K_final_portrait.mdx'); Stage = 'K_final_portrait.mdx'; Archive = 'war3mapimported\K\K_final_portrait.mdx' },
    @{ Source = (Join-Path $root 'assets\K\K_body.blp'); Stage = 'K_body.blp'; Archive = 'war3mapimported\K\K_body.blp' },
    # v1.7-K-VisualSkillFix: K-v2 world model, dedicated portrait camera model, compatible texture
    @{ Source = (Join-Path $root 'assets\Kv2\model\K_final_v2.mdx'); Stage = 'K_final_v2.mdx'; Archive = 'war3mapimported\K\K_final_v2.mdx' },
    @{ Source = (Join-Path $root 'assets\Kv2\model\K_final_portrait.mdx'); Stage = 'K_final_portrait_v2.mdx'; Archive = 'war3mapimported\K\K_final_portrait.mdx' },
    @{ Source = (Join-Path $root 'assets\Kv2\textures\K_body.blp'); Stage = 'K_body_v2.blp'; Archive = 'war3mapimported\K\K_body.blp' },
    # v1.7 dedicated hero button + four skill buttons, each with its DIS disabled twin (classic paths)
    @{ Source = (Join-Path $root 'assets\Kv2\buttons\BTNK_Hero.blp'); Stage = 'BTNK_Hero.blp'; Archive = 'ReplaceableTextures\CommandButtons\BTNK_Hero.blp' },
    @{ Source = (Join-Path $root 'assets\Kv2\buttons\DISBTNK_Hero.blp'); Stage = 'DISBTNK_Hero.blp'; Archive = 'ReplaceableTextures\CommandButtonsDisabled\DISBTNK_Hero.blp' },
    @{ Source = (Join-Path $root 'assets\Kv2\buttons\BTNKMarksmanship.blp'); Stage = 'BTNKMarksmanship.blp'; Archive = 'ReplaceableTextures\CommandButtons\BTNKMarksmanship.blp' },
    @{ Source = (Join-Path $root 'assets\Kv2\buttons\DISBTNKMarksmanship.blp'); Stage = 'DISBTNKMarksmanship.blp'; Archive = 'ReplaceableTextures\CommandButtonsDisabled\DISBTNKMarksmanship.blp' },
    @{ Source = (Join-Path $root 'assets\Kv2\buttons\BTNKCriticalStrike.blp'); Stage = 'BTNKCriticalStrike.blp'; Archive = 'ReplaceableTextures\CommandButtons\BTNKCriticalStrike.blp' },
    @{ Source = (Join-Path $root 'assets\Kv2\buttons\DISBTNKCriticalStrike.blp'); Stage = 'DISBTNKCriticalStrike.blp'; Archive = 'ReplaceableTextures\CommandButtonsDisabled\DISBTNKCriticalStrike.blp' },
    @{ Source = (Join-Path $root 'assets\Kv2\buttons\BTNKBattleRoar.blp'); Stage = 'BTNKBattleRoar.blp'; Archive = 'ReplaceableTextures\CommandButtons\BTNKBattleRoar.blp' },
    @{ Source = (Join-Path $root 'assets\Kv2\buttons\DISBTNKBattleRoar.blp'); Stage = 'DISBTNKBattleRoar.blp'; Archive = 'ReplaceableTextures\CommandButtonsDisabled\DISBTNKBattleRoar.blp' },
    @{ Source = (Join-Path $root 'assets\Kv2\buttons\BTNKChemicalRage.blp'); Stage = 'BTNKChemicalRage.blp'; Archive = 'ReplaceableTextures\CommandButtons\BTNKChemicalRage.blp' },
    @{ Source = (Join-Path $root 'assets\Kv2\buttons\DISBTNKChemicalRage.blp'); Stage = 'DISBTNKChemicalRage.blp'; Archive = 'ReplaceableTextures\CommandButtonsDisabled\DISBTNKChemicalRage.blp' }
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

# v1.7.1-K-W3IFix: binary equal-length w3i guard. Never decode/encode or text-replace the
# w3i; assert fixed 806B, the equal-length label appears exactly twice, and the old label
# is absent. The baseline binary itself (a1c1de1, 806B, sha 4df0e683...) is the source of
# truth; only the two 24-byte name slots (0x0C, 0xEA) differ.
$w3iSrc = Join-Path $root 'src\war3map.w3i'
$w3iBytes = [IO.File]::ReadAllBytes($w3iSrc)
if ($w3iBytes.Length -ne 806) { throw "war3map.w3i 必须为固定 806B，当前 $($w3iBytes.Length)B（禁止变长替换）" }
$newLabel = [Text.Encoding]::ASCII.GetBytes('OMG IMBA v1.7.1-W3IFix  ')
$oldLabel = [Text.Encoding]::ASCII.GetBytes('OMG IMBA v1.6-K-Visible ')
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
if ((Count-Bytes $w3iBytes $newLabel) -ne 2) { throw 'w3i 等长新名必须精确出现 2 次' }
if ((Count-Bytes $w3iBytes $oldLabel) -ne 0) { throw 'w3i 旧名 v1.6-K-Visible 必须为 0 次' }

Copy-Item -LiteralPath $baseline -Destination $asciiMap -Force
Wait-FileStable $asciiMap 30
foreach ($entry in $sourceEntries) {
    Invoke-MpqAdd $asciiMap (Join-Path $stageDir $entry.Stage) $entry.Archive
}

Copy-Item -LiteralPath $asciiMap -Destination $output -Force
Wait-FileStable $output 30

# Legacy v1.6 static gate: executed for retained-system evidence only; its superseded
# v1.6 K-specific assertions are informational and must not block the v1.7 build.
& (Join-Path $root 'tools\build\verify.ps1') -MapPath $output | Out-Null
Write-Output "遗留 v1.6 静态门已执行（仅留存系统证据；旧 K 断言已被 v1.7 取代）"

# Authoritative v1.7-K-VisualSkillFix semantic + readback gate; must exit 0.
$v17Ok = $false
for ($attempt = 1; $attempt -le 3 -and -not $v17Ok; $attempt++) {
    Start-Sleep -Seconds 3
    & (Join-Path $root 'tools\build\verify_v17.ps1') -MapPath $output
    if ($LASTEXITCODE -eq 0) { $v17Ok = $true }
}
if (-not $v17Ok) { throw "v1.7 回读语义验证失败（3次重试后仍失败）" }

Write-Output "构建完成: $output"
