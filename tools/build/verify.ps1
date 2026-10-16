param(
    [Parameter(Mandatory=$false)]
    [string]$MapPath
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
$config = Get-Content -LiteralPath (Join-Path $root 'config\tool-paths.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ([string]::IsNullOrWhiteSpace($MapPath)) {
    $MapPath = if ([IO.Path]::IsPathRooted($config.baselineMap)) { $config.baselineMap } else { Join-Path $root $config.baselineMap }
}
$MapPath = [IO.Path]::GetFullPath($MapPath)
$verifyRoot = Join-Path ([IO.Path]::GetTempPath()) 'DotaOmgImbaLightVerify'
$verifyDir = Join-Path $verifyRoot ('verify-' + [guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($verifyDir) | Out-Null

$checks = @(
    @{ Archive = 'war3map.j'; Expected = (Join-Path $root 'src\war3map.j') },
    @{ Archive = 'war3map.imp'; Expected = (Join-Path $root 'src\war3map.imp') },
    @{ Archive = 'Units\UnitAbilities.slk'; Expected = (Join-Path $root 'src\data\Units\UnitAbilities.slk') },
    @{ Archive = 'Units\UnitBalance.slk'; Expected = (Join-Path $root 'src\data\Units\UnitBalance.slk') },
    @{ Archive = 'Units\UnitData.slk'; Expected = (Join-Path $root 'src\data\Units\UnitData.slk') },
    @{ Archive = 'Units\UnitUI.slk'; Expected = (Join-Path $root 'src\data\Units\UnitUI.slk') },
    @{ Archive = 'Units\UnitWeapons.slk'; Expected = (Join-Path $root 'src\data\Units\UnitWeapons.slk') }
)

$results = @()
foreach ($check in $checks) {
    $relativeLocal = $check.Archive.ToLowerInvariant()
    $local = Join-Path $verifyDir $relativeLocal
    $localParent = Split-Path -Parent $local
    [IO.Directory]::CreateDirectory($localParent) | Out-Null
    & $config.mpqEditor extract $MapPath $check.Archive $verifyDir /fp
    $extractExit = $LASTEXITCODE
    $lastLength = -1L
    $stable = 0
    for ($wait = 0; $wait -lt 40; $wait++) {
        if (Test-Path -LiteralPath $local -PathType Leaf) {
            $currentLength = (Get-Item -LiteralPath $local).Length
            if ($currentLength -gt 0 -and $currentLength -eq $lastLength) { $stable++ } else { $stable = 0 }
            $lastLength = $currentLength
            if ($stable -ge 2) { break }
        }
        Start-Sleep -Milliseconds 100
    }
    if ($extractExit -ne 0 -or -not (Test-Path -LiteralPath $local -PathType Leaf)) {
        throw "无法从地图回读: $($check.Archive)"
    }
    $actual = (Get-FileHash -LiteralPath $local -Algorithm SHA256).Hash.ToLowerInvariant()
    $expected = (Get-FileHash -LiteralPath $check.Expected -Algorithm SHA256).Hash.ToLowerInvariant()
    $results += [PSCustomObject]@{ file=$check.Archive; expected=$expected; actual=$actual; match=($actual -eq $expected) }
}

$scriptText = [IO.File]::ReadAllText((Join-Path $verifyDir 'war3map.j'), [Text.Encoding]::UTF8)
$skinPathCount = ([regex]::Matches($scriptText, '(?i)skins\\')).Count
$defenseImplCount = ([regex]::Matches($scriptText, '(?m)^function KKDefense_(?!IsWaveType)')).Count
$wheelImplCount = ([regex]::Matches($scriptText, '(?m)^function B1004(?!ControlUnit)')).Count
$rechargeCount = ([regex]::Matches($scriptText, '(?m)^function B1131Recharge takes')).Count
$loggerCount = ([regex]::Matches($scriptText, '(?m)^function B1133LogAppend takes')).Count

$report = [ordered]@{
    map = $MapPath
    mapBytes = (Get-Item -LiteralPath $MapPath).Length
    mapSha256 = (Get-FileHash -LiteralPath $MapPath -Algorithm SHA256).Hash.ToLowerInvariant()
    files = $results
    scriptChecks = [ordered]@{
        skinPaths = $skinPathCount
        defenseImplementationFunctions = $defenseImplCount
        wheelImplementationFunctions = $wheelImplCount
        rechargeCommandFunctions = $rechargeCount
        diagnosticLoggerFunctions = $loggerCount
    }
    passed = (($results | Where-Object { -not $_.match }).Count -eq 0 -and $skinPathCount -eq 0 -and $defenseImplCount -eq 0 -and $wheelImplCount -eq 0 -and $rechargeCount -eq 1 -and $loggerCount -eq 1)
}

$reportPath = Join-Path $root 'reports\verification-latest.json'
$json = $report | ConvertTo-Json -Depth 8
$json | Set-Content -LiteralPath $reportPath -Encoding UTF8
Write-Output $json
if (-not $report.passed) { exit 1 }
