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
    @{ Archive = 'Units\UnitWeapons.slk'; Expected = (Join-Path $root 'src\data\Units\UnitWeapons.slk') },
    @{ Archive = 'Units\AbilityData.slk'; Expected = (Join-Path $root 'src\data\Units\AbilityData.slk') }
)

$results = @()
foreach ($check in $checks) {
    $relativeLocal = $check.Archive.ToLowerInvariant()
    $local = Join-Path $verifyDir $relativeLocal
    $localParent = Split-Path -Parent $local
    [IO.Directory]::CreateDirectory($localParent) | Out-Null
    $extractExit = 0
    $extracted = $false
    for ($try = 1; $try -le 5 -and -not $extracted; $try++) {
        & $config.mpqEditor extract $MapPath $check.Archive $verifyDir /fp
        $extractExit = $LASTEXITCODE
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
    if (-not $extracted) {
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
$versionName = ([regex]::Matches($scriptText, 'constant string XOMG_VERSION="v1\.6-K-VisualFix"')).Count
$versionLegacyName = ([regex]::Matches($scriptText, 'constant string XOMG_VERSION="v1\.2-dropfix"')).Count
$versionOldFuwu = ([regex]::Matches($scriptText, 'constant string XOMG_VERSION="v1\.3-fuwu"')).Count
$lotteryRuntimeGate = ([regex]::Matches($scriptText, 'CHOUJIANGSTATE\[rJ\]==1 and XOMG_IMBA_ENABLED')).Count
$legacyLotteryGate = ([regex]::Matches($scriptText, 'CHOUJIANGSTATE\[rJ\]==1 and XM_MODE')).Count
# K human candidate pools: one 50% roll per pool, human fallback excludes K, AI generic path retained.
$kHumanRoll50 = ([regex]::Matches($scriptText, 'set K_POOL_HIT\[id\]=GetRandomInt\(1,100\)<=50')).Count
$kHumanFallbackNoK = ([regex]::Matches($scriptText, 'return GetUnitPointValueByType\(K24\[GetRandomInt\(1,K_4-2\)\]\)')).Count
$kHumanPoolResets = ([regex]::Matches($scriptText, 'set K_POOL_ROLLED\[')).Count
$kHumanAgilityDispatch = ([regex]::Matches($scriptText, 'set Q39=QC9HumanFirstAgility\(p,Q39,Q69\)')).Count
$kPoolLog = ([regex]::Matches($scriptText, 'K_POOL_ROLL pid=')).Count
# v1.3 welfare button (凯哥发福利)
$welfareRoll = ([regex]::Matches($scriptText, 'set roll=GetRandomInt\(1,1000\)')).Count
$welfareClaimMark = ([regex]::Matches($scriptText, 'set LOTTERY_CLAIMED\[id\]=true')).Count
$welfareRepeatHint = ([regex]::Matches($scriptText, '本局福利已领取')).Count
$welfareOpenLog = ([regex]::Matches($scriptText, 'LOTTERY_OPEN pid=')).Count
$welfareOkLog = ([regex]::Matches($scriptText, 'LOTTERY_OK pid=')).Count
$welfareRepeatLog = ([regex]::Matches($scriptText, 'LOTTERY_REPEAT pid=')).Count
# independent fountain lottery and archive-only welfare
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
# exhaustive distribution over roll=1..100 (deterministic, no RNG): jackpot=10, gain 1..10 each=9
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
# A4DK remains the original fountain lottery UI; archive-dialog row owns the welfare name
$welfareName = ([regex]::Matches($abilityText, '(?m)^Name=凯哥发福利$')).Count
$oldLotteryName = ([regex]::Matches($abilityText, '(?m)^Name=抽奖$')).Count
# dialog rows (archive shop nAS6), unconditional, not archive/ticket gated
$welfareDialogRow = ([regex]::Matches($scriptText, 'DialogAddButton\(B836ArcDialog\[arcPid\],"凯哥发福利：每局一次领1-1000金币（无存档）"')).Count
$attrDialogRow = ([regex]::Matches($scriptText, 'DialogAddButton\(B836ArcDialog\[arcPid\],"双杰抽属性：1000金币抽全属性')).Count
$welfareDispatch = ([regex]::Matches($scriptText, 'call WELFARE_Claim\(arcPid\)')).Count
$attrDispatch = ([regex]::Matches($scriptText, 'call ATTR_Core\(arcPid\)')).Count
# v1.3 blocker fix: B836ArcOpen handle lifecycle. Last assignment before return must be DialogAddButton;
# no set-null AFTER creation; exactly one stale clear BEFORE add; click has a unique equality branch.
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
# old archive op3 draw must no longer be invoked from a button
$op3Call = ([regex]::Matches($scriptText, 'B836ArcTrade\(arcPid,3\)')).Count
# dev-only -droptest default OFF + cap
$devDropSwitch = ([regex]::Matches($scriptText, 'constant boolean DEV_DROP_TEST=false')).Count
$devDropGate = ([regex]::Matches($scriptText, 'if DEV_DROP_TEST and DROP_TEST_USES<3')).Count
# v1.3 A088 UI tree phrases (raw casts, no inflated four/six)
$a088UiL1 = ([regex]::Matches($abilityText, '80%概率连续施法两次')).Count
$a088UiScepter5 = ([regex]::Matches($abilityText, '10%概率连续施法五次')).Count
$a088UiL2 = ([regex]::Matches($abilityText, '50%概率连续施法三次，否则100%连续施法两次')).Count
$a088UiL3 = ([regex]::Matches($abilityText, '30%概率连续施法四次，60%概率连续施法三次，否则100%连续施法两次')).Count
# v1.3 hook actual B67 x2
$hookL4Normal = ([regex]::Matches($abilityText, '720\(神杖950\)')).Count
$hookScepter950 = ([regex]::Matches($abilityText, '950')).Count
# v1.3 attribute distribution text (F9/chat/dialog, scriptText)
$attrUiJackpot = ([regex]::Matches($scriptText, '10%概率全属性\+20')).Count
$attrUiNormal = ([regex]::Matches($scriptText, '1-10各9%概率全属性\+1至\+10')).Count

# ===================== v1.4-K hero K (H0K0 / KA01..KA04) checks =====================
# isolate KK module block (from first KK_ function to function main) for no-IMBA gating
$kkBlockMatch = [regex]::Match($scriptText, '(?s)(function KK_IsKHero.*?)(?=function main takes)')
$kkBlock = $kkBlockMatch.Groups[1].Value
$kRegHero = ([regex]::Matches($scriptText, "call R1X\('H0K0',0,'KA01','KA02','KA03','KA04'\)")).Count
# B2 fix: fake int/MD wiring must be ABSENT; H0K0 lives in agility K24 at index 40 and K34[118]
$kPoolM84 = ([regex]::Matches($scriptText, "set M84\[42\]='H0K0'")).Count
$kPoolMD4 = ([regex]::Matches($scriptText, "set MD4\[60\]='H0K0'")).Count
$kBoundM94 = ([regex]::Matches($scriptText, 'set M94=42')).Count
$kBoundME4 = ([regex]::Matches($scriptText, 'set ME4=60')).Count
$kK34118 = ([regex]::Matches($scriptText, "set K34\[118\]='H0K0'")).Count
$kIndexSkills = ([regex]::Matches($scriptText, "set HM4\[118\]='KA01'")).Count + ([regex]::Matches($scriptText, "set HN4\[118\]='KA02'")).Count + ([regex]::Matches($scriptText, "set HO4\[118\]='KA03'")).Count + ([regex]::Matches($scriptText, "set HP4\[118\]='KA04'")).Count
$kPreviewIcon = ([regex]::Matches($scriptText, 'set MH4\[118\]="ReplaceableTextures\\\\CommandButtons\\\\BTNHeroBladeMaster\.blp"')).Count
$kPreviewStand = ([regex]::Matches($scriptText, 'call XY7\(K34\[118\],"stand"\)')).Count
$kPreviewScale = ([regex]::Matches($scriptText, 'call XU7\(K34\[118\],1\.0,MI4\[118\]\)')).Count
$kK54 = ([regex]::Matches($scriptText, 'set K54=118')).Count
$kK2440 = ([regex]::Matches($scriptText, "set K24\[40\]='H0K0'")).Count
$kKAgiBound = ([regex]::Matches($scriptText, 'set K_4=40')).Count
$kExclusion = ([regex]::Matches($scriptText, "or skill=='KA0[1-4]'")).Count
# constants live in top globals (unique KK_ names -> count over whole scriptText)
# SK1 permanent kill agility 1/2/3/4
$kSk1Gain = ([regex]::Matches($scriptText, 'KK_SK1_AGI_L[1-4] = [1-4]')).Count
# SK2 20% extra physical = total agi x 1/1.5/2/2.5
$kSk2Chance = ([regex]::Matches($scriptText, 'KK_SK2_CHANCE = 20')).Count
$kSk2Mult = ([regex]::Matches($scriptText, 'KK_SK2_MULT_L[1-4] = [0-9.]+')).Count
# SK3 800 radius, agi snapshot x2/3/4/5
$kSk3Radius = ([regex]::Matches($scriptText, 'KK_SK3_RADIUS = 800\.0')).Count
$kSk3Mult = ([regex]::Matches($scriptText, 'KK_SK3_MULT_L[1-4] = [2-5]')).Count
# SK4 durations 15/17/20
$kSk4Dur = ([regex]::Matches($scriptText, 'KK_SK4_DUR_L[1-3] = (15|17|20)\.0')).Count
# ---- function-body checks inside kkBlock ----
# SK1 permanent SetHeroAgi on killer; victim dedup token
$kSk1SetAgi = ([regex]::Matches($kkBlock, 'SetHeroAgi\(killer, GetHeroAgi\(killer, false\) \+ KK_SK1Gain')).Count
$kSk1VictimDedup = ([regex]::Matches($kkBlock, 'KK_KEY_VICTIM_DONE')).Count
# SK2 synthetic/suppression guard; physical normal damage; no IMBA x2
$kSk2SynGuard = ([regex]::Matches($kkBlock, 'if B964Synthetic then')).Count
$kSk2Suppress = ([regex]::Matches($kkBlock, 'KK_SuppressHit')).Count
$kSk2Normal = ([regex]::Matches($kkBlock, 'DAMAGE_TYPE_NORMAL')).Count
# SK3 magic damage; filters ally/magicimmune/structure/A04R ward/invuln (Filter + Apply =2 each)
$kSk3Magic = ([regex]::Matches($kkBlock, 'DAMAGE_TYPE_MAGIC')).Count
$kSk3FilterAlly = ([regex]::Matches($kkBlock, 'IsUnitAlly\(t, GetOwningPlayer\(KK_SK3_CASTER\)\)')).Count
$kSk3FilterMagic = ([regex]::Matches($kkBlock, 'UNIT_TYPE_MAGIC_IMMUNE')).Count
$kSk3FilterStruct = ([regex]::Matches($kkBlock, 'UNIT_TYPE_STRUCTURE')).Count
$kSk3FilterWard = ([regex]::Matches($kkBlock, "GetUnitAbilityLevel\(t, 'A04R'\) > 0")).Count
$kSk3FilterInvuln = ([regex]::Matches($kkBlock, 'IsUnitInvulncerable\(t\)')).Count
# SK4 bonus S*level, generation token, re-cast clear old, death cleanup
$kSk4Bonus = ([regex]::Matches($kkBlock, 'set inc = S \* level')).Count
$kSk4Gen = ([regex]::Matches($kkBlock, 'KK_KEY_ULT_GEN')).Count
$kSk4Recast = ([regex]::Matches($kkBlock, 'call KK_UltRemove\(h, oldGen\)')).Count
$kSk4DeathClean = ([regex]::Matches($kkBlock, 'if KK_IsKHero\(dying\)')).Count
# global single death trigger registered once for all players; killer=real K gate
$kDeathReg = ([regex]::Matches($kkBlock, 'EVENT_PLAYER_UNIT_DEATH')).Count
$kDeathKillerGate = ([regex]::Matches($kkBlock, 'if killer == null or not KK_IsKHero\(killer\)')).Count
# module must never route through B67 / IMBA_POWER / XOMG amplification
$kNoImbaPower = ([regex]::Matches($kkBlock, 'IMBA_POWER')).Count
$kNoB67 = ([regex]::Matches($kkBlock, 'call B67\(')).Count
# SLK rows (extracted)
$slkAbil = [IO.File]::ReadAllText((Join-Path $verifyDir 'units\unitabilities.slk'), [Text.Encoding]::UTF8)
$slkUI = [IO.File]::ReadAllText((Join-Path $verifyDir 'units\unitui.slk'), [Text.Encoding]::UTF8)
$slkBal = [IO.File]::ReadAllText((Join-Path $verifyDir 'units\unitbalance.slk'), [Text.Encoding]::UTF8)
$slkWep = [IO.File]::ReadAllText((Join-Path $verifyDir 'units\unitweapons.slk'), [Text.Encoding]::UTF8)
$slkData = [IO.File]::ReadAllText((Join-Path $verifyDir 'units\unitdata.slk'), [Text.Encoding]::UTF8)
$slkAbilData = [IO.File]::ReadAllText((Join-Path $verifyDir 'units\abilitydata.slk'), [Text.Encoding]::UTF8)
$kSlkGrant = ([regex]::Matches($slkAbil, 'KA01,KA02,KA03,KA04')).Count
$kSlkModel = ([regex]::Matches($slkUI, 'war3mapimported\\K\\K_final\.mdx')).Count
# isolate H0K0 block in each SLK (alias line -> next alias line)
function Get-HeroBlock($text, $id) {
    $m = [regex]::Match($text, ('(?s)C;X1;Y\d+;K"' + [regex]::Escape($id) + '".*?(?=C;X1;Y\d+;K"|\z)'))
    return $m.Value
}
$balBlock = Get-HeroBlock $slkBal 'H0K0'
$wepBlock = Get-HeroBlock $slkWep 'H0K0'
$dataBlock = Get-HeroBlock $slkData 'H0K0'
$uiBlock = Get-HeroBlock $slkUI 'H0K0'
$kUiModelScale = ([regex]::Matches($uiBlock, 'C;X20;K120\.0')).Count
$kBalAgiPrimary = ([regex]::Matches($balBlock, 'C;X33;K"AGI"')).Count
$kBalStr = ([regex]::Matches($balBlock, 'C;X48;K18')).Count
$kBalStrPlus = ([regex]::Matches($balBlock, 'C;X49;K2\.0')).Count
$kBalAgi = ([regex]::Matches($balBlock, 'C;X2;K22')).Count
$kBalAgiPlus = ([regex]::Matches($balBlock, 'C;X3;K2\.2')).Count
$kBalInt = ([regex]::Matches($balBlock, 'C;X17;K16')).Count
$kBalIntPlus = ([regex]::Matches($balBlock, 'C;X18;K1\.5')).Count
$kWepNormal = ([regex]::Matches($wepBlock, 'C;X57;K"normal"')).Count
$kWepNormal2 = ([regex]::Matches($wepBlock, 'C;X58;K"normal"')).Count
$kWepNoMissile = ([regex]::Matches($wepBlock, 'missile')).Count
$kWepRange = ([regex]::Matches($wepBlock, 'C;X38;K128')).Count
$kDataPoints = ([regex]::Matches($dataBlock, 'C;X19;K118')).Count
# B1: real ability objects in AbilityData.slk
$kAbJdKA01 = ([regex]::Matches($slkAbilData, 'K"KA01"')).Count
$kAbJdKA02 = ([regex]::Matches($slkAbilData, 'K"KA02"')).Count
$kAbJdKA03 = ([regex]::Matches($slkAbilData, 'K"KA03"')).Count
$kAbJdKA04 = ([regex]::Matches($slkAbilData, 'K"KA04"')).Count
$ka03Block = Get-HeroBlock $slkAbilData 'KA03'
$ka04Block = Get-HeroBlock $slkAbilData 'KA04'
$ka01Block = Get-HeroBlock $slkAbilData 'KA01'
$ka02Block = Get-HeroBlock $slkAbilData 'KA02'
$kAbJdLvl = ([regex]::Matches($ka01Block, 'C;X72;K4')).Count + ([regex]::Matches($ka02Block, 'C;X72;K4')).Count + ([regex]::Matches($ka03Block, 'C;X72;K4')).Count
$kAbJdSK4Lvl = ([regex]::Matches($ka04Block, 'C;X72;K3')).Count
$kAbJdSK3CD = ([regex]::Matches($ka03Block, 'C;X1[6-9];K10\.0')).Count
$kAbJdSK4CD = ([regex]::Matches($ka04Block, 'C;X16;K80\.0')).Count + ([regex]::Matches($ka04Block, 'C;X17;K65\.0')).Count + ([regex]::Matches($ka04Block, 'C;X18;K50\.0')).Count
$kAbJdNoTarget = ([regex]::Matches($ka03Block, 'C;X8[012];K"_"')).Count + ([regex]::Matches($ka04Block, 'C;X8[012];K"_"')).Count
# B3: every target rawcode appears strictly before the terminating E; E is last non-empty line
function Test-BeforeE($text, $code) {
    $lines = $text -split "`r?`n"
    $e = -1
    for ($i = 0; $i -lt $lines.Count; $i++) { if ($lines[$i].Trim() -eq 'E') { $e = $i } }
    if ($e -lt 0) { return $false }
    for ($i = $e + 1; $i -lt $lines.Count; $i++) { if ($lines[$i].Trim() -ne '') { return $false } }
    for ($i = $e; $i -lt $lines.Count; $i++) { if ($lines[$i] -match ('K"' + [regex]::Escape($code) + '"')) { return $false } }
    return $true
}
$b3Pos = (Test-BeforeE $slkAbil 'H0K0') -and (Test-BeforeE $slkData 'H0K0') -and (Test-BeforeE $slkBal 'H0K0') -and (Test-BeforeE $slkWep 'H0K0') -and (Test-BeforeE $slkUI 'H0K0') -and (Test-BeforeE $slkAbilData 'KA01') -and (Test-BeforeE $slkAbilData 'KA02') -and (Test-BeforeE $slkAbilData 'KA03') -and (Test-BeforeE $slkAbilData 'KA04')
# C2: B boundary Y must be >= hero alias Y, every object row Y <= B.Y, and E stays last non-empty line.
function Test-SlkBoundary($text, $heroId) {
    $lines = $text -split "`r?`n"
    $bY = -1
    foreach ($ln in $lines) {
        $m = [regex]::Match($ln, '^B;X\d+;Y(\d+);D\d+$')
        if ($m.Success) { $bY = [int]$m.Groups[1].Value }
    }
    if ($bY -lt 0) { return $false }
    $heroY = -1
    foreach ($ln in $lines) {
        $m = [regex]::Match($ln, ('C;X1;Y(\d+);K"' + [regex]::Escape($heroId) + '"'))
        if ($m.Success) { $heroY = [int]$m.Groups[1].Value }
    }
    if ($heroY -lt 0 -or $bY -lt $heroY) { return $false }
    foreach ($ln in $lines) {
        $m = [regex]::Match($ln, 'C;X\d+;Y(\d+);')
        if ($m.Success -and [int]$m.Groups[1].Value -gt $bY) { return $false }
    }
    $eSeen = $false
    foreach ($ln in $lines) {
        $t = $ln.Trim()
        if ($eSeen -and $t -ne '') { return $false }
        if ($t -eq 'E') { $eSeen = $true }
    }
    return $eSeen
}
$kBoundaryAbil = Test-SlkBoundary $slkAbil 'H0K0'
$kBoundaryData = Test-SlkBoundary $slkData 'H0K0'
$kBoundaryBal = Test-SlkBoundary $slkBal 'H0K0'
$kBoundaryWep = Test-SlkBoundary $slkWep 'H0K0'
$kBoundaryUI = Test-SlkBoundary $slkUI 'H0K0'
$kBoundaryOk = $kBoundaryAbil -and $kBoundaryData -and $kBoundaryBal -and $kBoundaryWep -and $kBoundaryUI
# loadfix4: Warcraft III 1.24 requires contiguous custom SLK rows; sparse Y9001/Y9004 crashed before script init.
$kContiguousUnitRows = (([regex]::Matches($slkAbil, 'C;X1;Y3339;K"H0K0"')).Count -eq 1) -and (([regex]::Matches($slkData, 'C;X1;Y3339;K"H0K0"')).Count -eq 1) -and (([regex]::Matches($slkBal, 'C;X1;Y3339;K"H0K0"')).Count -eq 1) -and (([regex]::Matches($slkWep, 'C;X1;Y3339;K"H0K0"')).Count -eq 1) -and (([regex]::Matches($slkUI, 'C;X1;Y3339;K"H0K0"')).Count -eq 1) -and (([regex]::Matches($slkAbil, '(?m)^B;X4;Y3339;D0\r?$')).Count -eq 1) -and (([regex]::Matches($slkData, '(?m)^B;X25;Y3339;D0\r?$')).Count -eq 1) -and (([regex]::Matches($slkBal, '(?m)^B;X52;Y3339;D0\r?$')).Count -eq 1) -and (([regex]::Matches($slkWep, '(?m)^B;X60;Y3339;D0\r?$')).Count -eq 1) -and (([regex]::Matches($slkUI, '(?m)^B;X39;Y3339;D0\r?$')).Count -eq 1)
$kContiguousAbilityRows = (([regex]::Matches($slkAbilData, 'C;X1;Y6659;K"KA01"')).Count -eq 1) -and (([regex]::Matches($slkAbilData, 'C;X1;Y6660;K"KA02"')).Count -eq 1) -and (([regex]::Matches($slkAbilData, 'C;X1;Y6661;K"KA03"')).Count -eq 1) -and (([regex]::Matches($slkAbilData, 'C;X1;Y6662;K"KA04"')).Count -eq 1) -and (([regex]::Matches($slkAbilData, '(?m)^B;X87;Y6662;D0\r?$')).Count -eq 1)
# B1: KA01/02 passive DataA-D all zero (no native stat); KA03/04 clone proven in-map
# no-target instant stub A0OT (base ANcl, dispatched by GetSpellAbilityId on spell event),
# no AOwk/Achl, native Data/DataB/duration/buff zeroed; no-target click-cast.
$kAbJdPassiveZero = ([regex]::Matches($ka01Block, 'C;X(2[4-9]|3[0-5]);K0')).Count + ([regex]::Matches($ka02Block, 'C;X(2[4-9]|3[0-5]);K0')).Count
$kAbJdAncl = ([regex]::Matches($ka03Block, 'C;X2;K"ANcl"')).Count + ([regex]::Matches($ka04Block, 'C;X2;K"ANcl"')).Count
$kAbJdNoOwk = ([regex]::Matches($ka03Block, 'AOwk')).Count + ([regex]::Matches($ka04Block, 'AOwk')).Count
$kAbJdNoAchl = ([regex]::Matches($ka03Block, 'Achl')).Count + ([regex]::Matches($ka04Block, 'Achl')).Count
$kAbJdChanZero = ([regex]::Matches($ka03Block, 'C;X(24|28|60|68);K0')).Count + ([regex]::Matches($ka04Block, 'C;X(24|28|60|68);K0')).Count
$kAbJdSmallLevelSkip = ([regex]::Matches($ka01Block, 'C;X73;K2')).Count + ([regex]::Matches($ka02Block, 'C;X73;K2')).Count + ([regex]::Matches($ka03Block, 'C;X73;K2')).Count
$kAbJdUltLevelSkip = ([regex]::Matches($ka04Block, 'C;X73;K5')).Count
$kAbJdUltReqLevel = ([regex]::Matches($ka04Block, 'C;X75;K6')).Count
$kAbJdActiveOrders = ([regex]::Matches($ka03Block, 'C;X44;K"roar"')).Count + ([regex]::Matches($ka04Block, 'C;X44;K"chemicalrage"')).Count
# proven template evidence: A0OT object row present and referenced by shipped jass spell dispatch
$kTplA0OTRow = ([regex]::Matches($slkAbilData, 'K"A0OT"')).Count
$kTplA0OTJass = ([regex]::Matches($scriptText, "GetSpellAbilityId\(\)=='A0OT'")).Count
$kUnitStr = ([regex]::Matches($unitText, '(?m)^\[H0K0\]')).Count
$kUnitStringMatch = [regex]::Match($unitText, '(?ms)^\[H0K0\].*?(?=^\[|\z)')
$kUnitStringBlock = $kUnitStringMatch.Value
$kHeroIcon = ([regex]::Matches($kUnitStringBlock, '(?m)^(Art|ScoreScreenIcon)=ReplaceableTextures\\CommandButtons\\BTNHeroBladeMaster\.blp$')).Count
$kNoDiagnosticIcon = ([regex]::Matches($kUnitStringBlock, 'BTNStatUp\.blp')).Count
$kAbilStr = ([regex]::Matches($abilityText, '(?m)^\[KA0[1-4]\]')).Count
$kSkillIcons = ([regex]::Matches($abilityText, '(?m)^\[KA0[1-4]\]')).Count
$kEnsureAbilities = ([regex]::Matches($scriptText, 'function KK_EnsureHeroAbilities takes unit u returns nothing')).Count
$kApplyBypass = ([regex]::Matches($scriptText, 'if GetUnitTypeId\(u\)==KK_HERO then')).Count
$kEnsureCalls = ([regex]::Matches($scriptText, 'call KK_EnsureHeroAbilities\(u\)')).Count
# IMP paths present
$impText = [IO.File]::ReadAllText((Join-Path $verifyDir 'war3map.imp'), [Text.Encoding]::UTF8)
$kImpMdx = ([regex]::Matches($impText, 'war3mapimported\\K\\K_final\.mdx')).Count
$kImpPortrait = ([regex]::Matches($impText, 'war3mapimported\\K\\K_final_portrait\.mdx')).Count
$kImpBlp = ([regex]::Matches($impText, 'war3mapimported\\K\\K_body\.blp')).Count
# packaged world model, portrait model and texture readback hash compare against staged assets
$kMdxStage = Join-Path $root 'assets\K\K_final.mdx'
$kPortraitStage = Join-Path $root 'assets\K\K_final_portrait.mdx'
$kBlpStage = Join-Path $root 'assets\K\K_body.blp'
$kMdxMatch = 0; $kPortraitMatch = 0; $kBlpMatch = 0
foreach ($pair in @(@{kind='world'; arc='war3mapimported\K\K_final.mdx'; stage=$kMdxStage}, @{kind='portrait'; arc='war3mapimported\K\K_final_portrait.mdx'; stage=$kPortraitStage}, @{kind='texture'; arc='war3mapimported\K\K_body.blp'; stage=$kBlpStage})) {
    $dst = Join-Path $verifyDir ($pair.arc -replace '\\','/')
    [IO.Directory]::CreateDirectory((Split-Path -Parent $dst)) | Out-Null
    for ($try=1; $try -le 5; $try++) {
        & $config.mpqEditor extract $MapPath $pair.arc $verifyDir /fp | Out-Null
        Start-Sleep -Milliseconds 400
        if (Test-Path -LiteralPath $dst -PathType Leaf) { break }
    }
    if ((Test-Path -LiteralPath $dst) -and (Test-Path -LiteralPath $pair.stage)) {
        $h1=(Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash.ToLowerInvariant()
        $h2=(Get-FileHash -LiteralPath $pair.stage -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($pair.kind -eq 'world') { $kMdxMatch = ($h1 -eq $h2) } elseif ($pair.kind -eq 'portrait') { $kPortraitMatch = ($h1 -eq $h2) } else { $kBlpMatch = ($h1 -eq $h2) }
    }
}
# Packaged K model must contain a non-empty classic MODL name and exact chunk bounds.
$kMdxModelNameOk = $false
$kMdxModelName = ''
$kMdxPacked = Join-Path $verifyDir 'war3mapimported/K/K_final.mdx'
if (Test-Path -LiteralPath $kMdxPacked -PathType Leaf) {
    $mdx = [IO.File]::ReadAllBytes($kMdxPacked)
    if ($mdx.Length -ge 16 -and [Text.Encoding]::ASCII.GetString($mdx,0,4) -eq 'MDLX') {
        $mdxPos = 4
        $mdxBoundsOk = $true
        while ($mdxPos + 8 -le $mdx.Length) {
            $mdxTag = [Text.Encoding]::ASCII.GetString($mdx,$mdxPos,4)
            $mdxSize = [BitConverter]::ToUInt32($mdx,$mdxPos + 4)
            if ([uint64]$mdxPos + 8 + [uint64]$mdxSize -gt [uint64]$mdx.Length) { $mdxBoundsOk = $false; break }
            if ($mdxTag -eq 'MODL' -and $mdxSize -ge 80) {
                $kMdxModelName = [Text.Encoding]::ASCII.GetString($mdx,$mdxPos + 8,80).Trim([char]0)
            }
            $mdxPos += 8 + $mdxSize
        }
        $kMdxModelNameOk = ($mdxBoundsOk -and $mdxPos -eq $mdx.Length -and $kMdxModelName -eq 'K_Hero')
    }
}
# Packaged portrait must contain a valid CAMS camera chunk.
$kPortraitCameraOk = $false
$kPortraitPacked = Join-Path $verifyDir 'war3mapimported/K/K_final_portrait.mdx'
if (Test-Path -LiteralPath $kPortraitPacked -PathType Leaf) {
    $portraitBytes = [IO.File]::ReadAllBytes($kPortraitPacked)
    if ($portraitBytes.Length -ge 16 -and [Text.Encoding]::ASCII.GetString($portraitBytes,0,4) -eq 'MDLX') {
        $portraitPos = 4
        $portraitCams = 0
        $portraitBoundsOk = $true
        while ($portraitPos + 8 -le $portraitBytes.Length) {
            $portraitTag = [Text.Encoding]::ASCII.GetString($portraitBytes,$portraitPos,4)
            $portraitSize = [BitConverter]::ToUInt32($portraitBytes,$portraitPos + 4)
            if ([uint64]$portraitPos + 8 + [uint64]$portraitSize -gt [uint64]$portraitBytes.Length) { $portraitBoundsOk = $false; break }
            if ($portraitTag -eq 'CAMS' -and $portraitSize -ge 120) { $portraitCams++ }
            $portraitPos += 8 + $portraitSize
        }
        $kPortraitCameraOk = ($portraitBoundsOk -and $portraitPos -eq $portraitBytes.Length -and $portraitCams -eq 1)
    }
}
# Packaged K texture must use a Warcraft III 1.24-compatible palette BLP1 header.
$kBlpCompatible = $false
$kBlpPacked = Join-Path $verifyDir 'war3mapimported/K/K_body.blp'
if (Test-Path -LiteralPath $kBlpPacked -PathType Leaf) {
    $blp = [IO.File]::ReadAllBytes($kBlpPacked)
    if ($blp.Length -ge 156 -and [Text.Encoding]::ASCII.GetString($blp,0,4) -eq 'BLP1') {
        $blpCompression = [BitConverter]::ToUInt32($blp,4)
        $blpWidth = [BitConverter]::ToUInt32($blp,12)
        $blpHeight = [BitConverter]::ToUInt32($blp,16)
        $blpPictureType = [BitConverter]::ToUInt32($blp,20)
        $blpOffset0 = [BitConverter]::ToUInt32($blp,28)
        $blpSize0 = [BitConverter]::ToUInt32($blp,92)
        $kBlpCompatible = ($blpCompression -eq 1 -and ($blpPictureType -eq 4 -or $blpPictureType -eq 5) -and $blpWidth -gt 0 -and $blpHeight -gt 0 -and ([uint64]$blpOffset0 + [uint64]$blpSize0) -le [uint64]$blp.Length)
    }
}

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
        kHumanRoll50 = $kHumanRoll50
        kHumanFallbackNoK = $kHumanFallbackNoK
        kHumanPoolResets = $kHumanPoolResets
        kHumanAgilityDispatch = $kHumanAgilityDispatch
        kPoolLog = $kPoolLog
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
        versionLegacyName = $versionLegacyName
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
        a088ForbiddenCountMul = $a088ForbiddenCountMul
        a088SetSix = $a088SetSix
        a088PrdScepter = $a088PrdScepter
        a088PrdL1NoScepter = $a088PrdL1NoScepter
        a088PrdL2NoScepter = $a088PrdL2NoScepter
        a088PrdL2Scepter3 = $a088PrdL2Scepter3
        a088PrdL3NoScepter4 = $a088PrdL3NoScepter4
        a088PrdL3Scepter4 = $a088PrdL3Scepter4
        a088PrdL3Scepter3 = $a088PrdL3Scepter3
        a088R5 = $a088R5
        a088R4 = $a088R4
        a088R3 = $a088R3
        a088R2 = $a088R2
        welfareName = $welfareName
        oldLotteryName = $oldLotteryName
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
        hookScepter950 = $hookScepter950
        attrUiJackpot = $attrUiJackpot
        attrUiNormal = $attrUiNormal
        versionOldFuwu = $versionOldFuwu
        kRegHero = $kRegHero
        kPoolM84 = $kPoolM84
        kPoolMD4 = $kPoolMD4
        kBoundM94 = $kBoundM94
        kBoundME4 = $kBoundME4
        kK34118 = $kK34118
        kIndexSkills = $kIndexSkills
        kPreviewIcon = $kPreviewIcon
        kPreviewStand = $kPreviewStand
        kPreviewScale = $kPreviewScale
        kK54 = $kK54
        kK2440 = $kK2440
        kKAgiBound = $kKAgiBound
        kExclusion = $kExclusion
        kSk1Gain = $kSk1Gain
        kSk1SetAgi = $kSk1SetAgi
        kSk1VictimDedup = $kSk1VictimDedup
        kSk2Chance = $kSk2Chance
        kSk2Mult = $kSk2Mult
        kSk2SynGuard = $kSk2SynGuard
        kSk2Suppress = $kSk2Suppress
        kSk2Normal = $kSk2Normal
        kSk3Radius = $kSk3Radius
        kSk3Mult = $kSk3Mult
        kSk3Magic = $kSk3Magic
        kSk3FilterAlly = $kSk3FilterAlly
        kSk3FilterMagic = $kSk3FilterMagic
        kSk3FilterStruct = $kSk3FilterStruct
        kSk3FilterWard = $kSk3FilterWard
        kSk3FilterInvuln = $kSk3FilterInvuln
        kSk4Dur = $kSk4Dur
        kSk4Bonus = $kSk4Bonus
        kSk4Gen = $kSk4Gen
        kSk4Recast = $kSk4Recast
        kSk4DeathClean = $kSk4DeathClean
        kDeathReg = $kDeathReg
        kDeathKillerGate = $kDeathKillerGate
        kNoImbaPower = $kNoImbaPower
        kNoB67 = $kNoB67
        kSlkGrant = $kSlkGrant
        kSlkModel = $kSlkModel
        kUiModelScale120 = $kUiModelScale
        kBalAgiPrimary = $kBalAgiPrimary
        kBalStr = $kBalStr
        kBalStrPlus = $kBalStrPlus
        kBalAgi = $kBalAgi
        kBalAgiPlus = $kBalAgiPlus
        kBalInt = $kBalInt
        kBalIntPlus = $kBalIntPlus
        kWepNormal = $kWepNormal
        kWepNormal2 = $kWepNormal2
        kWepNoMissile = $kWepNoMissile
        kWepRange = $kWepRange
        kDataPoints = $kDataPoints
        kBoundaryAbil = $kBoundaryAbil
        kBoundaryData = $kBoundaryData
        kBoundaryBal = $kBoundaryBal
        kBoundaryWep = $kBoundaryWep
        kBoundaryUI = $kBoundaryUI
        kBoundaryOk = $kBoundaryOk
        kContiguousUnitRows = $kContiguousUnitRows
        kContiguousAbilityRows = $kContiguousAbilityRows
        kAbJdKA01 = $kAbJdKA01
        kAbJdKA02 = $kAbJdKA02
        kAbJdKA03 = $kAbJdKA03
        kAbJdKA04 = $kAbJdKA04
        kAbJdLvl = $kAbJdLvl
        kAbJdSK4Lvl = $kAbJdSK4Lvl
        kAbJdSK3CD = $kAbJdSK3CD
        kAbJdSK4CD = $kAbJdSK4CD
        b3PosBeforeE = $b3Pos
        kAbJdPassiveZero = $kAbJdPassiveZero
        kAbJdAncl = $kAbJdAncl
        kAbJdNoOwk = $kAbJdNoOwk
        kAbJdNoAchl = $kAbJdNoAchl
        kAbJdChanZero = $kAbJdChanZero
        kAbJdSmallLevelSkip = $kAbJdSmallLevelSkip
        kAbJdUltLevelSkip = $kAbJdUltLevelSkip
        kAbJdUltReqLevel = $kAbJdUltReqLevel
        kAbJdActiveOrders = $kAbJdActiveOrders
        kAbJdNoTarget = $kAbJdNoTarget
        kTplA0OTRow = $kTplA0OTRow
        kTplA0OTJass = $kTplA0OTJass
        kUnitStr = $kUnitStr
        kHeroIcon = $kHeroIcon
        kNoDiagnosticIcon = $kNoDiagnosticIcon
        kAbilStr = $kAbilStr
        kEnsureAbilities = $kEnsureAbilities
        kApplyBypass = $kApplyBypass
        kEnsureCalls = $kEnsureCalls
        kImpMdx = $kImpMdx
        kImpPortrait = $kImpPortrait
        kImpBlp = $kImpBlp
        kMdxMatch = $kMdxMatch
        kPortraitMatch = $kPortraitMatch
        kPortraitCameraOk = $kPortraitCameraOk
        kMdxModelName = $kMdxModelName
        kMdxModelNameOk = $kMdxModelNameOk
        kBlpMatch = $kBlpMatch
        kBlpCompatible124 = $kBlpCompatible
        attrDistributionJackpot = $distJackpot
        attrDistributionNormalEach = ($distNormal.GetEnumerator() | Sort-Object Name | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join ','
        attrDistributionOk = $distOk
    }
    passed = (($results | Where-Object { -not $_.match }).Count -eq 0 -and $skinPathCount -eq 0 -and $defenseImplCount -eq 0 -and $wheelImplCount -eq 0 -and $rechargeCount -eq 1 -and $loggerCount -eq 1 -and $runtimeImbaGate -eq 1 -and $runtimeMultTwo -eq 1 -and $runtimeMultReset -eq 0 -and $lotteryFloor -eq 1 -and $oldLotteryLowGold -eq 0 -and $versionName -eq 1 -and $versionLegacyName -eq 0 -and $lotteryRuntimeGate -eq 1 -and $legacyLotteryGate -eq 0 -and $kHumanRoll50 -eq 1 -and $kHumanFallbackNoK -eq 1 -and $kHumanPoolResets -eq 4 -and $kHumanAgilityDispatch -eq 9 -and $kPoolLog -eq 2 -and $dropCheapUsesFinishedItems -eq 1 -and $dropLotteryUsesFinishedItems -eq 1 -and $dropChanceFixedTen -eq 1 -and $dropPriceCap -eq 1 -and $dropMissingCreepsCovered -eq 1 -and $dropInitLog -eq 1 -and $dropRollLog -eq 1 -and $dropSuccessLog -eq 1 -and $dropTestCommand -eq 1 -and $fissureDuration -eq 1 -and $fissureStunScale -eq 1 -and $heroTipNewCount -eq 11 -and $heroTipLegacyCount -eq 0 -and $fissureResearchActual -ge 1 -and $fissureUberActual -ge 1 -and $fissureUiDistance -ge 2 -and $fissureUiDuration -ge 2 -and $welfareRoll -eq 1 -and $welfareClaimMark -eq 1 -and $welfareRepeatHint -eq 1 -and $welfareOpenLog -eq 1 -and $welfareOkLog -eq 1 -and $welfareRepeatLog -ge 1 -and $lotteryPoolCall -eq 2 -and $welfareTouchesFountainState -eq 0 -and $fountainUsesPool -eq 1 -and $fountainTouchesWelfareState -eq 0 -and $poolDefinitionRetained -eq 1 -and $archiveWrites -eq 11 -and $attrRoll -eq 1 -and $attrJackpotCond -eq 1 -and $attrJackpotGain -eq 1 -and $attrNormalGain -eq 1 -and $attrCharge -eq 1 -and $attrInsufficient -eq 1 -and $attrStr -eq 1 -and $attrAgi -eq 1 -and $attrInt -eq 1 -and $attrRollLog -eq 1 -and $attrRejectLog -ge 1 -and $attrJackpotVisual -eq 1 -and $a088ForbiddenCountMul -eq 0 -and $a088SetSix -eq 0 -and $a088PrdScepter -eq 3 -and $a088PrdL1NoScepter -eq 1 -and $a088PrdL2NoScepter -eq 1 -and $a088PrdL2Scepter3 -eq 2 -and $a088PrdL3NoScepter4 -eq 1 -and $a088PrdL3Scepter4 -eq 1 -and $a088PrdL3Scepter3 -eq 1 -and $a088R5 -ge 3 -and $a088R4 -eq 2 -and $a088R3 -eq 4 -and $a088R2 -eq 6 -and $welfareName -eq 0 -and $oldLotteryName -eq 1 -and $welfareDialogRow -eq 1 -and $attrDialogRow -eq 1 -and $welfareDispatch -eq 1 -and $attrDispatch -eq 1 -and $welfarePreNull -eq 1 -and $attrPreNull -eq 1 -and $welfareNullAfter -eq 0 -and $attrNullAfter -eq 0 -and $welfareClickBranch -eq 1 -and $attrClickBranch -eq 1 -and $op3Call -eq 0 -and $devDropSwitch -eq 1 -and $devDropGate -eq 1 -and $a088UiL1 -ge 2 -and $a088UiScepter5 -ge 3 -and $a088UiL2 -ge 2 -and $a088UiL3 -ge 2 -and $hookL4Normal -ge 1 -and $hookScepter950 -ge 2 -and $attrUiJackpot -ge 1 -and $attrUiNormal -ge 1 -and $versionName -eq 1 -and $versionOldFuwu -eq 0 -and $versionLegacyName -eq 0 -and $kRegHero -eq 1 -and $kPoolM84 -eq 0 -and $kPoolMD4 -eq 0 -and $kBoundM94 -eq 0 -and $kBoundME4 -eq 0 -and $kK34118 -eq 1 -and $kIndexSkills -eq 4 -and $kPreviewIcon -eq 1 -and $kPreviewStand -eq 1 -and $kPreviewScale -eq 1 -and $kK54 -eq 1 -and $kK2440 -eq 1 -and $kKAgiBound -eq 1 -and $kExclusion -eq 4 -and $kSk1Gain -eq 4 -and $kSk1SetAgi -eq 1 -and $kSk1VictimDedup -ge 1 -and $kSk2Chance -eq 1 -and $kSk2Mult -eq 4 -and $kSk2SynGuard -eq 1 -and $kSk2Suppress -ge 3 -and $kSk2Normal -eq 1 -and $kSk3Radius -eq 1 -and $kSk3Mult -eq 4 -and $kSk3Magic -eq 1 -and $kSk3FilterAlly -eq 2 -and $kSk3FilterMagic -eq 2 -and $kSk3FilterStruct -eq 2 -and $kSk3FilterWard -eq 2 -and $kSk3FilterInvuln -eq 2 -and $kSk4Dur -eq 3 -and $kSk4Bonus -eq 1 -and $kSk4Gen -ge 3 -and $kSk4Recast -eq 1 -and $kSk4DeathClean -eq 1 -and $kDeathReg -eq 1 -and $kDeathKillerGate -eq 1 -and $kNoImbaPower -eq 0 -and $kNoB67 -eq 0 -and $kSlkGrant -eq 1 -and $kSlkModel -eq 1 -and $kUiModelScale -eq 1 -and $kBalAgiPrimary -eq 1 -and $kBalStr -eq 1 -and $kBalStrPlus -eq 1 -and $kBalAgi -eq 1 -and $kBalAgiPlus -eq 1 -and $kBalInt -eq 1 -and $kBalIntPlus -eq 1 -and $kWepNormal -eq 1 -and $kWepNormal2 -eq 1 -and $kWepNoMissile -eq 0 -and $kWepRange -eq 1 -and $kDataPoints -eq 1 -and $kBoundaryOk -eq $true -and $kContiguousUnitRows -eq $true -and $kContiguousAbilityRows -eq $true -and $kAbJdKA01 -eq 1 -and $kAbJdKA02 -eq 1 -and $kAbJdKA03 -eq 1 -and $kAbJdKA04 -eq 1 -and $kAbJdLvl -eq 3 -and $kAbJdSK4Lvl -eq 1 -and $kAbJdSK3CD -eq 4 -and $kAbJdSK4CD -eq 3 -and $kAbJdNoTarget -eq 6 -and $b3Pos -eq $true -and $kAbJdPassiveZero -eq 24 -and $kAbJdAncl -eq 2 -and $kAbJdNoOwk -eq 0 -and $kAbJdNoAchl -eq 0 -and $kAbJdChanZero -eq 8 -and $kAbJdSmallLevelSkip -eq 3 -and $kAbJdUltLevelSkip -eq 1 -and $kAbJdUltReqLevel -eq 1 -and $kAbJdActiveOrders -eq 2 -and $kTplA0OTRow -eq 1 -and $kTplA0OTJass -ge 1 -and $kUnitStr -eq 1 -and $kHeroIcon -eq 2 -and $kNoDiagnosticIcon -eq 0 -and $kAbilStr -eq 4 -and $kEnsureAbilities -eq 1 -and $kApplyBypass -eq 1 -and $kEnsureCalls -ge 2 -and $kImpMdx -eq 1 -and $kImpPortrait -eq 1 -and $kImpBlp -eq 1 -and $kMdxMatch -eq $true -and $kPortraitMatch -eq $true -and $kPortraitCameraOk -eq $true -and $kMdxModelNameOk -eq $true -and $kBlpMatch -eq $true -and $kBlpCompatible -eq $true -and $distOk)
}

$reportPath = Join-Path $root 'reports\verification-latest.json'
$json = $report | ConvertTo-Json -Depth 8
$json | Set-Content -LiteralPath $reportPath -Encoding UTF8
Write-Output $json
if (-not $report.passed) { exit 1 }
