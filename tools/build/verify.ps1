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
    @{ Archive = 'war3map.w3i'; Expected = (Join-Path $root 'src\war3map.w3i') },
    @{ Archive = 'war3map.imp'; Expected = (Join-Path $root 'src\war3map.imp') },
    @{ Archive = 'Units\CampaignAbilityStrings.txt'; Expected = (Join-Path $root 'src\data\Units\CampaignAbilityStrings.txt') },
    @{ Archive = 'Units\CampaignUnitStrings.txt'; Expected = (Join-Path $root 'src\data\Units\CampaignUnitStrings.txt') },
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
$runtimeImbaGate = ([regex]::Matches($scriptText, 'constant boolean XOMG_IMBA_ENABLED=true')).Count
$runtimeMultTwo = ([regex]::Matches($scriptText, '(?m)^integer imbaMult=2$')).Count
$runtimeMultReset = ([regex]::Matches($scriptText, '(?m)^set imbaMult=1$')).Count
$lotteryFloor = ([regex]::Matches($scriptText, 'GetRandomInt\(1000,1500\)')).Count
$oldLotteryLowGold = ([regex]::Matches($scriptText, 'GetRandomInt\(50,80\)')).Count
$versionName = ([regex]::Matches($scriptText, 'constant string XOMG_VERSION="v1\.2-dropfix"')).Count
$lotteryRuntimeGate = ([regex]::Matches($scriptText, 'CHOUJIANGSTATE\[rJ\]==1 and XOMG_IMBA_ENABLED')).Count
$legacyLotteryGate = ([regex]::Matches($scriptText, 'CHOUJIANGSTATE\[rJ\]==1 and XM_MODE')).Count
$dropCheapUsesFinishedItems = ([regex]::Matches($scriptText, 'B1063CheapPool\[B1063CheapCount\]=ZU\[i\]')).Count
$dropLotteryUsesFinishedItems = ([regex]::Matches($scriptText, 'B1063LotteryPool\[B1063LotteryCount\]=ZU\[i\]')).Count
$dropChanceFixedTen = ([regex]::Matches($scriptText, 'set roll=GetRandomInt\(1,10\)')).Count
$dropPriceCap = ([regex]::Matches($scriptText, 'p>0 and p<=1000 and B1063ItemEligible\(ZU\[i\]\)')).Count
$dropMissingCreepsCovered = ([regex]::Matches($scriptText, "wardType=='nmrl'.*wardType=='nmrm'.*wardType=='nmrr'")).Count
$dropInitLog = ([regex]::Matches($scriptText, 'DROP_INIT ver=')).Count
$dropRollLog = ([regex]::Matches($scriptText, 'DROP_ROLL eligible=')).Count
$dropSuccessLog = ([regex]::Matches($scriptText, 'DROP_OK count=')).Count
$dropTestCommand = ([regex]::Matches($scriptText, 'HD9=="-droptest"')).Count
$fissureDuration = ([regex]::Matches($scriptText, 'CreateDestructable\(skill,x,y,GetRandomReal\(0,360\),\.5,GetRandomInt\(0,2\)\),16')).Count
$fissureStunScale = ([regex]::Matches($scriptText, "YDWESetUnitAbilityDataReal\(fissureDummy,'A0SJ',fissureLevel,ABILITY_DATA_DUR,\(\.75\+\.25\*fissureLevel\)\*IMBA_POWER\)")).Count
$unitText = [IO.File]::ReadAllText((Join-Path $verifyDir 'units\campaignunitstrings.txt'), [Text.Encoding]::UTF8)
$abilityText = [IO.File]::ReadAllText((Join-Path $verifyDir 'units\campaignabilitystrings.txt'), [Text.Encoding]::UTF8)
$utf8 = [Text.Encoding]::UTF8
$heroTipNewPattern = $utf8.GetString([Convert]::FromBase64String('KD9tKV5UaXA9KOiigeWKoOWHr3znqIvlj4zmnbB85Zyf6bihfOWHr+WTpSlccj8k'))
$heroTipLegacyPattern = $utf8.GetString([Convert]::FromBase64String('KD9tKV5UaXA9KOiDluWtkHzlvbHprZR854K86YeR5pyv5aOrfOWcsOeyvuW3peeoi+W4iClccj8k'))
$fissureResearchPattern = $utf8.GetString([Convert]::FromBase64String('6YCg5oiQMjIw5Lyk5a6z77yMMuenkuecqeaZlQ=='))
$fissureUberPattern = $utf8.GetString([Convert]::FromBase64String('6YCg5oiQMjIw54K55Lyk5a6z77yM5pmV55ypMuenkg=='))
$fissureUiDistancePattern = $utf8.GetString([Convert]::FromBase64String('5pa95rOV6Led56a777yaXHxyMTQwMA=='))
$fissureUiDurationPattern = $utf8.GetString([Convert]::FromBase64String('MTbnp5LlhoXkuI3og73pgJrooYw='))
$heroTipNewCount = ([regex]::Matches($unitText, $heroTipNewPattern)).Count
$heroTipLegacyCount = ([regex]::Matches($unitText, $heroTipLegacyPattern)).Count
$fissureResearchActual = ([regex]::Matches($abilityText, $fissureResearchPattern)).Count
$fissureUberActual = ([regex]::Matches($abilityText, $fissureUberPattern)).Count
$fissureUiDistance = ([regex]::Matches($abilityText, $fissureUiDistancePattern)).Count
$fissureUiDuration = ([regex]::Matches($abilityText, $fissureUiDurationPattern)).Count

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
        runtimeImbaGate = $runtimeImbaGate
        runtimeMultiplierTwo = $runtimeMultTwo
        runtimeMultiplierReset = $runtimeMultReset
        lotteryGoldFloor = $lotteryFloor
        legacyLowLotteryGold = $oldLotteryLowGold
        uniqueVersionName = $versionName
        lotteryRuntimeGate = $lotteryRuntimeGate
        legacyLotteryGate = $legacyLotteryGate
        dropCheapUsesFinishedItems = $dropCheapUsesFinishedItems
        dropLotteryUsesFinishedItems = $dropLotteryUsesFinishedItems
        dropChanceFixedTenPercent = $dropChanceFixedTen
        dropPriceCap1000 = $dropPriceCap
        dropPreviouslyMissingCreepsCovered = $dropMissingCreepsCovered
        dropInitLog = $dropInitLog
        dropRollLog = $dropRollLog
        dropSuccessLog = $dropSuccessLog
        dropTestCommand = $dropTestCommand
        fissureDurationScaled = $fissureDuration
        fissureStunScaled = $fissureStunScale
        heroVisibleTips = $heroTipNewCount
        legacyHeroTips = $heroTipLegacyCount
        fissureUiResearchActual = $fissureResearchActual
        fissureUiUberActual = $fissureUberActual
        fissureUiDistanceUnchanged = $fissureUiDistance
        fissureUiDuration = $fissureUiDuration
    }
    passed = (($results | Where-Object { -not $_.match }).Count -eq 0 -and $skinPathCount -eq 0 -and $defenseImplCount -eq 0 -and $wheelImplCount -eq 0 -and $rechargeCount -eq 1 -and $loggerCount -eq 1 -and $runtimeImbaGate -eq 1 -and $runtimeMultTwo -eq 1 -and $runtimeMultReset -eq 0 -and $lotteryFloor -eq 1 -and $oldLotteryLowGold -eq 0 -and $versionName -eq 1 -and $lotteryRuntimeGate -eq 1 -and $legacyLotteryGate -eq 0 -and $dropCheapUsesFinishedItems -eq 1 -and $dropLotteryUsesFinishedItems -eq 1 -and $dropChanceFixedTen -eq 1 -and $dropPriceCap -eq 1 -and $dropMissingCreepsCovered -eq 1 -and $dropInitLog -eq 1 -and $dropRollLog -eq 1 -and $dropSuccessLog -eq 1 -and $dropTestCommand -eq 1 -and $fissureDuration -eq 1 -and $fissureStunScale -eq 1 -and $heroTipNewCount -eq 11 -and $heroTipLegacyCount -eq 0 -and $fissureResearchActual -ge 1 -and $fissureUberActual -ge 1 -and $fissureUiDistance -ge 2 -and $fissureUiDuration -ge 2)
}

$reportPath = Join-Path $root 'reports\verification-latest.json'
$json = $report | ConvertTo-Json -Depth 8
$json | Set-Content -LiteralPath $reportPath -Encoding UTF8
Write-Output $json
if (-not $report.passed) { exit 1 }
