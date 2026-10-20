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
    @{ Archive = 'units\campaignabilitystrings.txt'; Expected = (Join-Path $root 'src\data\Units\CampaignAbilityStrings.txt') },
    @{ Archive = 'units\campaignunitstrings.txt'; Expected = (Join-Path $root 'src\data\Units\CampaignUnitStrings.txt') },
    @{ Archive = 'units\unitabilities.slk'; Expected = (Join-Path $root 'src\data\Units\UnitAbilities.slk') },
    @{ Archive = 'units\unitbalance.slk'; Expected = (Join-Path $root 'src\data\Units\UnitBalance.slk') },
    @{ Archive = 'units\unitdata.slk'; Expected = (Join-Path $root 'src\data\Units\UnitData.slk') },
    @{ Archive = 'units\unitui.slk'; Expected = (Join-Path $root 'src\data\Units\UnitUI.slk') },
    @{ Archive = 'units\unitweapons.slk'; Expected = (Join-Path $root 'src\data\Units\UnitWeapons.slk') },
    @{ Archive = 'units\abilitydata.slk'; Expected = (Join-Path $root 'src\data\Units\AbilityData.slk') }
)

$results = @()
foreach ($check in $checks) {
    $relativeLocal = $check.Archive.ToLowerInvariant()
    $local = Join-Path $verifyDir $relativeLocal
    $localParent = Split-Path -Parent $local
    [IO.Directory]::CreateDirectory($localParent) | Out-Null
    $extracted = $false
    for ($try = 1; $try -le 5 -and -not $extracted; $try++) {
        & $config.mpqEditor extract $MapPath $check.Archive $verifyDir /fp
        $lastLength = -1L
        $stable = 0
        for ($wait = 0; $wait -lt 150; $wait++) {
            if (Test-Path -LiteralPath $local -PathType Leaf) {
                $currentLength = (Get-Item -LiteralPath $local).Length
                if ($currentLength -gt 0 -and $currentLength -eq $lastLength) { $stable++ } else { $stable = 0 }
                $lastLength = $currentLength
                if ($stable -ge 4) { $extracted = $true; break }
            }
            Start-Sleep -Milliseconds 150
        }
        if (-not $extracted) { Start-Sleep -Seconds 3 }
    }
    if (-not $extracted) { throw "无法从地图回读: $($check.Archive)" }
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
$versionName = ([regex]::Matches($scriptText, 'constant string XOMG_VERSION="v1\.8\.6-NOK"')).Count
$versionLegacyName = ([regex]::Matches($scriptText, 'constant string XOMG_VERSION="v1\.2-dropfix"')).Count
$versionOldFuwu = ([regex]::Matches($scriptText, 'constant string XOMG_VERSION="v1\.3-fuwu"')).Count
$lotteryRuntimeGate = ([regex]::Matches($scriptText, 'CHOUJIANGSTATE\[rJ\]==1 and XOMG_IMBA_ENABLED')).Count
$legacyLotteryGate = ([regex]::Matches($scriptText, 'CHOUJIANGSTATE\[rJ\]==1 and XM_MODE')).Count
# v1.3 welfare button (凯哥发福利)
$welfareRoll = ([regex]::Matches($scriptText, 'set roll=GetRandomInt\(1,1000\)')).Count
$welfareClaimMark = ([regex]::Matches($scriptText, 'set LOTTERY_CLAIMED\[id\]=true')).Count
$welfareRepeatHint = ([regex]::Matches($scriptText, '本局福利已领取')).Count
$welfareOpenLog = ([regex]::Matches($scriptText, 'LOTTERY_OPEN pid=')).Count
$welfareOkLog = ([regex]::Matches($scriptText, 'LOTTERY_OK pid=')).Count
$welfareRepeatLog = ([regex]::Matches($scriptText, 'LOTTERY_REPEAT pid=')).Count
$lotteryPoolCall = ([regex]::Matches($scriptText, 'B1063BuildLotteryPool\(\)')).Count
$poolDefinitionRetained = ([regex]::Matches($scriptText, 'function B1063BuildLotteryPool takes')).Count
$welfareFunctionMatch = [regex]::Match($scriptText, '(?s)function WELFARE_Claim takes integer id returns nothing(.*?)endfunction')
$welfareFunctionBody = $welfareFunctionMatch.Groups[1].Value
$fountainFunctionMatch = [regex]::Match($scriptText, '(?s)function CHOUJIANG takes nothing returns nothing(.*?)endfunction')
$fountainFunctionBody = $fountainFunctionMatch.Groups[1].Value
$welfareTouchesFountainState = ([regex]::Matches($welfareFunctionBody, 'CHOUJIANGSTATE|A4DK|B1063BuildLotteryPool')).Count
$fountainUsesPool = ([regex]::Matches($fountainFunctionBody, 'B1063BuildLotteryPool\(\)')).Count
$fountainTouchesWelfareState = ([regex]::Matches($fountainFunctionBody, 'LOTTERY_CLAIMED|WELFARE_Claim')).Count
$archiveWrites = ([regex]::Matches($scriptText, 'SaveServerValue')).Count
# v1.3 attribute button (双杰抽属性)
$attrRoll = ([regex]::Matches($scriptText, 'set roll=GetRandomInt\(1,100\)')).Count
$attrJackpotCond = ([regex]::Matches($scriptText, 'if roll<=10 then')).Count
$attrJackpotGain = ([regex]::Matches($scriptText, 'set gain=20')).Count
$attrNormalGain = ([regex]::Matches($scriptText, 'set gain=1\+\(roll-11\)/9')).Count
$attrCharge = ([regex]::Matches($scriptText, 'SetPlayerState\(p,PLAYER_STATE_RESOURCE_GOLD,gold-1000\)')).Count
$attrInsufficient = ([regex]::Matches($scriptText, '金币不足，需要1000金币')).Count
$attrStr = ([regex]::Matches($scriptText, 'SetHeroStr\(hero,strBase\+gain,true\)')).Count
$attrAgi = ([regex]::Matches($scriptText, 'SetHeroAgi\(hero,agiBase\+gain,true\)')).Count
$attrInt = ([regex]::Matches($scriptText, 'SetHeroInt\(hero,intBase\+gain,true\)')).Count
$attrRollLog = ([regex]::Matches($scriptText, 'ATTR_ROLL pid=')).Count
$attrRejectLog = ([regex]::Matches($scriptText, 'ATTR_REJECT pid=')).Count
$attrJackpotVisual = ([regex]::Matches($scriptText, 'YW7\("恭喜发财"')).Count
# v1.3 A088 probability-tree EUD bans and literals
$a088ForbiddenCountMul = ([regex]::Matches($scriptText, 'set r=IMinBJ\(')).Count
$a088SetSix = ([regex]::Matches($scriptText, 'set r=6')).Count
$a088PrdScepter = ([regex]::Matches($scriptText, "GetPrdRandom\(ZX7,'A088'\+5,10\)")).Count
$a088PrdL1NoScepter = ([regex]::Matches($scriptText, "GetPrdRandom\(ZX7,'A088'\+2,80\)")).Count
$a088PrdL2NoScepter = ([regex]::Matches($scriptText, "GetPrdRandom\(ZX7,'A088'\+3,50\)")).Count
$a088PrdL2Scepter3 = ([regex]::Matches($scriptText, "GetPrdRandom\(ZX7,'A088'\+3,60\)")).Count
$a088PrdL3NoScepter4 = ([regex]::Matches($scriptText, "GetPrdRandom\(ZX7,'A088'\+4,30\)")).Count
$a088PrdL3Scepter4 = ([regex]::Matches($scriptText, "GetPrdRandom\(ZX7,'A088'\+4,40\)")).Count
$a088PrdL3Scepter3 = ([regex]::Matches($scriptText, "GetPrdRandom\(ZX7,'A088'\+3,80\)")).Count
$a088R5 = ([regex]::Matches($scriptText, '(?m)^[ \t]*set r=5$')).Count
$a088R4 = ([regex]::Matches($scriptText, '(?m)^[ \t]*set r=4$')).Count
$a088R3 = ([regex]::Matches($scriptText, '(?m)^[ \t]*set r=3$')).Count
$a088R2 = ([regex]::Matches($scriptText, '(?m)^[ \t]*set r=2$')).Count
$distJackpot = 0
$distNormal = @{}
for ($roll = 1; $roll -le 100; $roll++) {
    if ($roll -le 10) { $distJackpot++ }
    else { $g = [int](1 + [math]::Floor(($roll - 11) / 9)); $distNormal[$g] = [int]$distNormal[$g] + 1 }
}
$distOk = ($distJackpot -eq 10)
foreach ($g in 1..10) { $distOk = $distOk -and ([int]$distNormal[$g] -eq 9) }
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
$welfareName = ([regex]::Matches($abilityText, '(?m)^Name=凯哥发福利$')).Count
$oldLotteryName = ([regex]::Matches($abilityText, '(?m)^Name=抽奖$')).Count
$welfareDialogRow = ([regex]::Matches($scriptText, 'DialogAddButton\(B836ArcDialog\[arcPid\],"凯哥发福利：每局一次领1-1000金币（无存档）"')).Count
$attrDialogRow = ([regex]::Matches($scriptText, 'DialogAddButton\(B836ArcDialog\[arcPid\],"双杰抽属性：1000金币抽全属性')).Count
$welfareDispatch = ([regex]::Matches($scriptText, 'call WELFARE_Claim\(arcPid\)')).Count
$attrDispatch = ([regex]::Matches($scriptText, 'call ATTR_Core\(arcPid\)')).Count
$openMatch = [regex]::Match($scriptText, '(?s)function B836ArcOpen takes integer arcPid returns nothing(.*?)endfunction')
$openBody = $openMatch.Groups[1].Value
$welfareAddIdx = [regex]::Match($openBody, 'set B836WelfareButton\[arcPid\]=DialogAddButton').Index
$attrAddIdx = [regex]::Match($openBody, 'set B836AttrButton\[arcPid\]=DialogAddButton').Index
$welfarePreNull = ([regex]::Matches($openBody.Substring(0,[Math]::Max(0,$welfareAddIdx)), 'set B836WelfareButton\[arcPid\]=null')).Count
$attrPreNull = ([regex]::Matches($openBody.Substring(0,[Math]::Max(0,$attrAddIdx)), 'set B836AttrButton\[arcPid\]=null')).Count
$welfareNullAfter = ([regex]::Matches($openBody.Substring($welfareAddIdx), 'set B836WelfareButton\[arcPid\]=null')).Count
$attrNullAfter = ([regex]::Matches($openBody.Substring($attrAddIdx), 'set B836AttrButton\[arcPid\]=null')).Count
$welfareClickBranch = ([regex]::Matches($scriptText, 'arcClicked==B836WelfareButton\[arcPid\]')).Count
$attrClickBranch = ([regex]::Matches($scriptText, 'arcClicked==B836AttrButton\[arcPid\]')).Count
$op3Call = ([regex]::Matches($scriptText, 'B836ArcTrade\(arcPid,3\)')).Count
$devDropSwitch = ([regex]::Matches($scriptText, 'constant boolean DEV_DROP_TEST=false')).Count
$devDropGate = ([regex]::Matches($scriptText, 'if DEV_DROP_TEST and DROP_TEST_USES<3')).Count
$a088UiL1 = ([regex]::Matches($abilityText, '80%概率连续施法两次')).Count
$a088UiScepter5 = ([regex]::Matches($abilityText, '10%概率连续施法五次')).Count
$a088UiL2 = ([regex]::Matches($abilityText, '50%概率连续施法三次，否则100%连续施法两次')).Count
$a088UiL3 = ([regex]::Matches($abilityText, '30%概率连续施法四次，60%概率连续施法三次，否则100%连续施法两次')).Count
$hookL4Normal = ([regex]::Matches($abilityText, '720\(神杖950\)')).Count
$hookScepter950 = ([regex]::Matches($abilityText, '950')).Count
$attrUiJackpot = ([regex]::Matches($scriptText, '10%概率全属性\+20')).Count
$attrUiNormal = ([regex]::Matches($scriptText, '1-10各9%概率全属性\+1至\+10')).Count

# ===================== v1.8.6-NOK zero-residue (hero K fully removed) =====================
$nokJassBan = @('H0K0','KA01','KA02','KA03','KA04','KK_HERO','KK_Init','KK_EnsureHeroAbilities',
    'K_POOL_ROLLED','K_POOL_HIT','K_POOL_ROLL','B891RandomAgilityNoK','QZ9HumanNoK','QC9HumanNoK',
    'R1X(''H0K0','BTNK_Hero','K_final_v2.mdx','K_final_portrait.mdx','war3mapimported\K\','v1.7.1-K-W3IFix')
$nokJass = @{}
foreach ($t in $nokJassBan) { $nokJass[$t] = ([regex]::Matches($scriptText, [regex]::Escape($t))).Count }
$nokUnitH0K0 = ([regex]::Matches($unitText, '(?m)^\[H0K0\]')).Count
$nokAbilKA = ([regex]::Matches($abilityText, '(?m)^\[KA0[1-4]\]')).Count
$nokAbilKButton = ([regex]::Matches($abilityText, '(?i)BTNKMarksmanship|BTNKCriticalStrike|BTNKBattleRoar|BTNKChemicalRage|DISBTNK_Hero|DISBTNKMarksmanship|DISBTNKCriticalStrike|DISBTNKBattleRoar|DISBTNKChemicalRage')).Count
$nokUnitKIcon = ([regex]::Matches($unitText, 'BTNK_Hero\.blp')).Count
$impText = [IO.File]::ReadAllText((Join-Path $verifyDir 'war3map.imp'), [Text.Encoding]::ASCII)
$nokImpK = ([regex]::Matches($impText, '(?i)war3mapimported\\K\\|BTNK_Hero|BTNKMarksmanship|BTNKCriticalStrike|BTNKBattleRoar|BTNKChemicalRage|DISBTNK_Hero|DISBTNKMarksmanship|DISBTNKCriticalStrike|DISBTNKBattleRoar|DISBTNKChemicalRage')).Count
# generic KK_ / English buttons retained
$nokGenericKk = ([regex]::Matches($scriptText, 'KK_GAME_DIFFICULTY')).Count
$nokGenericTips = ([regex]::Matches($scriptText, 'KKGameTips')).Count
$nokGenericKeep = ([regex]::Matches($unitText, 'BTNKeep')).Count
$nokGenericKeeper = ([regex]::Matches($unitText, 'BTNKeeperGhostBlue')).Count
$nokGenericRob = ([regex]::Matches($abilityText, 'BTNKrobWitchcraft')).Count

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
        uniqueVersionNameNok = $versionName
        versionLegacyName = $versionLegacyName
        versionOldFuwu = $versionOldFuwu
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
        welfareRoll1_1000 = $welfareRoll
        welfareClaimMark = $welfareClaimMark
        welfareRepeatHint = $welfareRepeatHint
        welfareOpenLog = $welfareOpenLog
        welfareOkLog = $welfareOkLog
        welfareRepeatLog = $welfareRepeatLog
        lotteryPoolCall = $lotteryPoolCall
        welfareTouchesFountainState = $welfareTouchesFountainState
        fountainUsesPool = $fountainUsesPool
        fountainTouchesWelfareState = $fountainTouchesWelfareState
        poolDefinitionRetained = $poolDefinitionRetained
        archiveWritesUnchanged = $archiveWrites
        attrRoll1_100 = $attrRoll
        attrJackpotCond = $attrJackpotCond
        attrJackpotGain20 = $attrJackpotGain
        attrNormalGain = $attrNormalGain
        attrCharge1000 = $attrCharge
        attrInsufficientHint = $attrInsufficient
        attrStrPermanent = $attrStr
        attrAgiPermanent = $attrAgi
        attrIntPermanent = $attrInt
        attrRollLog = $attrRollLog
        attrRejectLog = $attrRejectLog
        attrJackpotVisual = $attrJackpotVisual
        a088PrdScepter = $a088PrdScepter
        a088PrdL1NoScepter = $a088PrdL1NoScepter
        a088PrdL2NoScepter = $a088PrdL2NoScepter
        a088PrdL2Scepter3 = $a088PrdL2Scepter3
        a088PrdL3NoScepter4 = $a088PrdL3NoScepter4
        a088PrdL3Scepter4 = $a088PrdL3Scepter4
        a088PrdL3Scepter3 = $a088PrdL3Scepter3
        welfareDialogRow = $welfareDialogRow
        attrDialogRow = $attrDialogRow
        welfareDispatch = $welfareDispatch
        attrDispatch = $attrDispatch
        welfarePreNull = $welfarePreNull
        attrPreNull = $attrPreNull
        welfareNullAfter = $welfareNullAfter
        attrNullAfter = $attrNullAfter
        welfareClickBranch = $welfareClickBranch
        attrClickBranch = $attrClickBranch
        op3CallRemoved = $op3Call
        devDropSwitchOff = $devDropSwitch
        devDropGate = $devDropGate
        a088UiL1 = $a088UiL1
        a088UiScepter5 = $a088UiScepter5
        a088UiL2 = $a088UiL2
        a088UiL3 = $a088UiL3
        hookL4Normal720 = $hookL4Normal
        attrUiJackpot = $attrUiJackpot
        attrUiNormal = $attrUiNormal
        nokJass = $nokJass
        nokUnitH0K0 = $nokUnitH0K0
        nokAbilKA = $nokAbilKA
        nokAbilKButton = $nokAbilKButton
        nokUnitKIcon = $nokUnitKIcon
        nokImpK = $nokImpK
        nokGenericKk = $nokGenericKk
        nokGenericTips = $nokGenericTips
        nokGenericKeep = $nokGenericKeep
        nokGenericKeeper = $nokGenericKeeper
        nokGenericRob = $nokGenericRob
        attrDistributionJackpot = $distJackpot
        attrDistributionOk = $distOk
    }
    passed = (($results | Where-Object { -not $_.match }).Count -eq 0 -and $skinPathCount -eq 0 -and $defenseImplCount -eq 0 -and $wheelImplCount -eq 0 -and $runtimeImbaGate -eq 1 -and $lotteryFloor -eq 1 -and $versionName -eq 1 -and $versionLegacyName -eq 0 -and $versionOldFuwu -eq 0 -and $fountainUsesPool -eq 1 -and $attrCharge -eq 1 -and $attrJackpotVisual -eq 1 -and $op3Call -eq 0 -and $devDropSwitch -eq 1 -and $distOk)
}

$reportPath = Join-Path $root 'reports\verification-latest.json'
$json = $report | ConvertTo-Json -Depth 8
$json | Set-Content -LiteralPath $reportPath -Encoding UTF8
Write-Output $json
if (-not $report.passed) { exit 1 }
