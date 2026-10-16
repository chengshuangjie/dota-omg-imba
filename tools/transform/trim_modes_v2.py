from pathlib import Path
import re

root = Path(r"D:\dota\DOTA69AI\rework-omg-imba")
src = root / "build" / "war3map.j"
out = root / "trim-build"
out.mkdir(exist_ok=True)
t = src.read_text(encoding="utf-8")


def remove_function(text: str, name: str) -> str:
    match = re.search(r"(?m)^function " + re.escape(name) + r" takes\b", text)
    if not match:
        raise RuntimeError(f"function not found: {name}")
    end = text.find("\nendfunction", match.end())
    if end < 0:
        raise RuntimeError(f"endfunction not found: {name}")
    end += len("\nendfunction")
    if end < len(text) and text[end] == "\n":
        end += 1
    return text[:match.start()] + text[end:]


# Capture definitions before mutation.
function_names = re.findall(r"(?m)^function\s+(\w+)\s+takes\b", t)

# Remove all 30-wave defense functions, except a tiny compatibility predicate used by ordinary AI filters.
defense_names = [n for n in function_names if n.startswith("KKDefense")]
for name in defense_names:
    if name != "KKDefense_IsWaveType":
        t = remove_function(t, name)
old_predicate = """function KKDefense_IsWaveType takes integer unitId returns boolean
return KK_DEFENSE_MODE and LoadBoolean(L7,StringHash("KKDefenseType"),unitId)
endfunction"""
new_predicate = """// 30-wave defense mode removed. Kept only for ordinary AI filter compatibility.
function KKDefense_IsWaveType takes integer unitId returns boolean
return false
endfunction"""
if t.count(old_predicate) != 1:
    raise RuntimeError("defense predicate mismatch")
t = t.replace(old_predicate, new_predicate)

# Remove wheel-battle functions; B1004ControlUnit is a generic wrapper still used by ordinary AI initialization.
wheel_names = [n for n in function_names if n.startswith("B1004") and n != "B1004ControlUnit"]
for name in wheel_names:
    if re.search(r"(?m)^function " + re.escape(name) + r" takes\b", t):
        t = remove_function(t, name)
# Remove defense-only helper functions that use other prefixes.
for name in [
    "B936ArcherOrder", "B936TrackDefenseSupport", "B936DisposeArcher", "B936DisposeArcherEnum",
    "B936DrainDefenseOrders", "B899DefenseApplySpawnLife", "B838ArcBossText", "B838ArcBossDeath", "B838ArcBossPump",
]:
    if re.search(r"(?m)^function " + re.escape(name) + r" takes\b", t):
        t = remove_function(t, name)
old_control = """function B1004ControlUnit takes nothing returns unit
if B1004ControlHero!=null then
return B1004ControlHero
endif
return GetTriggerUnit()
endfunction"""
new_control = """function B1004ControlUnit takes nothing returns unit
return GetTriggerUnit()
endfunction"""
if t.count(old_control) != 1:
    raise RuntimeError("control wrapper mismatch")
t = t.replace(old_control, new_control)

# Wheel-only auxiliary functions that no longer have callers.
for name in ["B1008BaseDeath", "B1008InitBaseProgress", "B1075RestoreWheelItems", "B1075RetargetWheelCourier"]:
    if re.search(r"(?m)^function " + re.escape(name) + r" takes\b", t):
        t = remove_function(t, name)

# Remove complete wheel-only blocks in shared functions.
blocks = [
"""\tif B1004Wheel then
\t\t// Engine pays half; add only the missing half, never the 10-second refund too.
\t\tif it!=null and GetUnitTypeId(GetTriggerUnit())!='N0MM' and not LoadBoolean(L7,GetHandleId(GetTriggerUnit()),StringHash("B849TempestOwned")) and not IsUnitIllusion(GetTriggerUnit()) then
\t\tset t=CreateTimer()
\t\tcall SavePlayerHandle(TABLE_HY,GetHandleId(t),0,p)
\t\tcall SaveInteger(TABLE_HY,GetHandleId(t),1,GetItemTypeId(it))
\t\tcall SaveBoolean(TABLE_HY,GetHandleId(t),2,true)
\t\tcall TimerStart(t,0.,false,function OHO)
\t\tset t=null
\t\tendif
\t\treturn
\tendif
""",
"""if B1004Wheel then
set B1004EventHero=VE8
call ExecuteFunc("B1004CountDeath")
endif
""",
"""if B1004Wheel then
return false
endif
""",
"""if B1004Wheel then
return
endif
""",
"""if B1004Wheel then
call DisplayTimedTextToPlayer(b1060GetTriggerPlayer,0,0,8.,"车轮战模式由死亡条件触发换人，不能使用 -re 重选。")
set b1060GetTriggerPlayer=null
return
endif
""",
"""if B1004Wheel then
set B979Mode=2
set B979ChoiceStarted=true
call ExecuteFunc("B979InitData")
call ExecuteFunc("B1004Start")
return
endif
""",
]
for block in blocks:
    t = t.replace(block, "")

# Simplify wheel-related conditions embedded in shared random-skill logic.
replacements = {
    "if B998TempestCreating or B1004Creating then": "if B998TempestCreating then",
    "if B1004Creating then\nreturn false\nendif\n": "",
    "if B1004ControlHero==null then\ncall BVE(O5,it,false)\nendif": "call BVE(O5,it,false)",
    "call B1004RecordKill(W78)\n": "",
    "B979Mode==2 and (B1004Wheel or GetPlayerController(GetOwningPlayer(u))==MAP_CONTROL_COMPUTER)": "B979Mode==2 and GetPlayerController(GetOwningPlayer(u))==MAP_CONTROL_COMPUTER",
    "SUIJI_TAVERN_AREA_READY or B1004Wheel": "SUIJI_TAVERN_AREA_READY",
    "SUIJI_MODE==false or B1004Wheel": "SUIJI_MODE==false",
    "ISTEST==false or SUIJI_MODE==false or p==null or B1004Wheel": "ISTEST==false or SUIJI_MODE==false or p==null",
    "set human=GetPlayerController(p)==MAP_CONTROL_USER and not B1004Wheel": "set human=GetPlayerController(p)==MAP_CONTROL_USER",
    "return not B1004Wheel and GetPlayerController(Player(suijiEventPlayerId))==MAP_CONTROL_USER": "return GetPlayerController(Player(suijiEventPlayerId))==MAP_CONTROL_USER",
    "SUIJI_MODE==false or SUIJI_AI_RE_WINDOW_STARTED or B1004Wheel": "SUIJI_MODE==false or SUIJI_AI_RE_WINDOW_STARTED",
    "if GetPlayerController(p)==MAP_CONTROL_USER and not B1004Wheel and SuijiMode_HasForcedPreset": "if GetPlayerController(p)==MAP_CONTROL_USER and SuijiMode_HasForcedPreset",
    "return not B1004Wheel and (not B836ArcStarted or TimerGetElapsed(W)-M_4<180.)": "return not B836ArcStarted or TimerGetElapsed(W)-M_4<180.",
}
for old, new in replacements.items():
    t = t.replace(old, new)

t = t.replace("call B1004RecordKill(W78)\n", "")
t = t.replace("call B838ArcBossPump()\n", "")
t = t.replace("set B838ArcBossPending[pid]=false\n", "")
t = re.sub(r'elseif arcOperation==5 then\ncall DisplayTimedTextToPlayer\(Player\(arcPid\),0,0,20\.,arcSaveStatus\+"防守通关奖励："\+B838ArcBossText\(\)\+"。奖励已发放，本局可用，无需等下一局；请重新打开 -archive 查询或领取。"\+B836ArcBalanceText\(arcPid\)\)\n', '', t, count=1)

# Simplify the high-difficulty pair announcement.
old = """if chosen979==0 then
set chosen979=-1
if not B1004Wheel then
call VV7(bj_FORCE_ALL_PLAYERS,10.,"|cffffcc00AI高难技能组合："+GetUnitName(hero979)+" 暂无兼容的预设组合，本英雄使用普通组合。|r")
endif
else
if B1004Wheel then
call VV7(bj_FORCE_ALL_PLAYERS,10.,"|cffffcc00车轮战组合："+GetUnitName(hero979)+" 第"+I2S(chosen979-index979*5)+"套，额外技能为 "+GetAbilityName(B979SmallPool[chosen979])+" + "+GetAbilityName(B979UltPool[chosen979])+"。|r")
else
call VV7(bj_FORCE_ALL_PLAYERS,10.,"|cffffcc00AI高难技能组合："+GetUnitName(hero979)+" 选用第"+I2S(chosen979-index979*5)+"套，额外技能为 "+GetAbilityName(B979SmallPool[chosen979])+" + "+GetAbilityName(B979UltPool[chosen979])+"。|r")
endif
endif"""
new = """if chosen979==0 then
set chosen979=-1
call VV7(bj_FORCE_ALL_PLAYERS,10.,"|cffffcc00AI高难技能组合："+GetUnitName(hero979)+" 暂无兼容的预设组合，本英雄使用普通组合。|r")
else
call VV7(bj_FORCE_ALL_PLAYERS,10.,"|cffffcc00AI高难技能组合："+GetUnitName(hero979)+" 选用第"+I2S(chosen979-index979*5)+"套，额外技能为 "+GetAbilityName(B979SmallPool[chosen979])+" + "+GetAbilityName(B979UltPool[chosen979])+"。|r")
endif"""
if t.count(old) != 1:
    raise RuntimeError("pair announcement mismatch")
t = t.replace(old, new)

# Remove defense test command branch.
t, count = re.subn(
    r'elseif\(SubString\(VH,0,8\)=="-defend "\)then.*?elseif\(VH=="-rechoose"\)then',
    'elseif(VH=="-rechoose")then',
    t,
    count=1,
    flags=re.S,
)
if count != 1:
    raise RuntimeError("defense test command branch mismatch")

# Keep normal creep spawning by reducing former defense guards to constants rather than deleting block boundaries.
t = t.replace("if KK_DEFENSE_MODE then\nreturn false\nendif\n", "", 1)
t = t.replace("if KK_DEFENSE_MODE==false then\n", "if true then\n", 1)
t = t.replace("if KK_DEFENSE_MODE then\ncall ExecuteFunc(\"KKDefense_StartFirstWave\")\nendif\n", "", 1)

# Remove obsolete difficulty=4 and wheel branches, retaining new/normal/hard only.
old = """elseif difficulty==4 then
set KK_DEFENSE_MODE=false
call VV7(bj_FORCE_ALL_PLAYERS,15.,"|cFFFFFF80防守玩法已移除，已切换为正常难度。|r")
elif B1004Wheel then
set XM_EXP=5
set XM_GOLD=5
set XM_CG=true
set B1069RewardMultiplier=4
call VV7(bj_FORCE_ALL_PLAYERS,15.,"|cFFFFCC00已选择车轮战：4倍熟练度和胜利哦买嘎币奖励，默认启用 -cg 5，随机英雄技能。|r")
elif difficulty==3 then""".replace("elif", "elseif")
if t.count(old) != 1:
    raise RuntimeError("legacy difficulty branches mismatch")
t = t.replace(old, "elseif difficulty==3 then")

# Remove defense globals from reward/log conditions.
t = t.replace("if KK_GAME_DIFFICULTY==0 and KK_DEFENSE_DIFFICULTY_PENDING==false then", "if KK_GAME_DIFFICULTY==0 then")
t = t.replace("if KK_DEFENSE_MODE or not B836ArcStarted or B1031TestMatch then", "if not B836ArcStarted or B1031TestMatch then")
t = t.replace('"非防守胜利奖励："', '"胜利奖励："')
t = t.replace('+" defense="+I2S(B287_BoolToInt(KK_DEFENSE_MODE))', '')

# Remove obsolete defense release-note entry.
t = re.sub(r'set n=n\+1\nset UpdateLog\[n\]="\\n\|c00FF0000KK B708\|r.*?"\n', '', t, count=1)

t = t.replace('call X37(Player(arcPid),"防守第30波阿克蒙德奖励（每局一次）：普通3硬币、中等15硬币；困难两种成品各7天，地狱两种成品各15天并额外获得7天喵刀使用权限。喵刀权限按自然日计时、重复获得顺延，无需领入背包。击杀时在场真人自动获得，保存请求受理后本局可查；跨局保存以读回确认为准。小屋说明物品展示奖励摘要，完整规则以本商店规则说明为准。")\n', '')
t = t.replace('本图默认开启 |cFF00FF00-omg|r 随机OMG模式（-1 基础模式 + 随机技能）。\\n开局由主机选择新手、正常或困难，15秒未选择则采用正常难度。\\n|cFFFFCC00车轮战和30波防守玩法已移除。|r\\n作者：|cFFFFCC00小生我怕怕|r', '本图默认开启 |cFF00FF00-omg|r 随机OMG模式（-1 基础模式 + 随机技能）。\\n开局由主机选择新手、正常或困难，15秒未选择则采用正常难度。\\n作者：|cFFFFCC00小生我怕怕|r')

# Remove obsolete globals. Keep B1069RewardMultiplier=1 because normal reward code uses it.
global_names = [
    "KK_DIFFICULTY_DEFENSE",
    "KK_DEFENSE_MODE", "KK_DEFENSE_DIFFICULTY", "KK_DEFENSE_DIFFICULTY_PENDING",
    "KK_DEFENSE_DIFFICULTY_DIALOG", "KK_DEFENSE_DIFFICULTY_NORMAL", "KK_DEFENSE_DIFFICULTY_MEDIUM",
    "KK_DEFENSE_DIFFICULTY_HARD", "KK_DEFENSE_DIFFICULTY_HELL", "KK_DEFENSE_WAVE",
    "KK_DEFENSE_NEXT_WAVE", "KK_DEFENSE_ACTIVE_UNITS", "KK_DEFENSE_MAINTENANCE_TICKS",
    "KK_DEFENSE_TOWER_LEVEL", "KK_DEFENSE_COMPLETE", "KK_DEFENSE_TIMER", "KK_DEFENSE_TIMER_DIALOG",
    "KK_DEFENSE_UNITS", "KK_DEFENSE_PERIODIC_UNITS", "KK_DEFENSE_SOULS", "KK_DEFENSE_OBJECTS",
    "KK_DEFENSE_PRUNE_GROUP", "KK_DEFENSE_PRUNE_WAVE", "KK_DEFENSE_DEATH_TRIGGER",
    "KK_DEFENSE_MAINTENANCE_TRIGGER", "KK_DEFENSE_ATTACK_TRIGGER", "KK_DEFENSE_MECHANIC_TRIGGER",
    "KK_DEFENSE_STATE", "KK_DEFENSE_MECHANIC_TICK", "KK_DEFENSE_REFLECTING",
    "KK_DEFENSE_DEATH_BURSTING", "KK_DEFENSE_CLEANUP_PENDING", "KK_DEFENSE_DEATH_FEEDERS",
    "KK_DEFENSE_TEST_WAVE", "KK_DEFENSE_TEST_PLAYER",
    "B838ArcBossRewarded", "B838ArcBossDifficulty", "B838ArcBossTime", "B838ArcBossPending",
    "B1004Wheel", "B1004Started", "B1004Creating", "B1004ModeButton", "B1004ControlHero",
    "B1004EventHero", "B1004WorkHero", "B1004WorkPlayer", "B1004Known", "B1004Deaths",
    "B1004AIKills", "B1004Pending", "B1004Dialog", "B1004Yes", "B1004No", "B1004Asked",
    "B1004Busy", "B1004Initialized", "B1004HeroIndex", "B1004RetryAt", "B1004PulseTimer",
]
lines = t.splitlines(keepends=True)
kept = []
for line in lines:
    if any(re.search(r"\b" + re.escape(name) + r"\b", line) for name in global_names):
        # Only remove declaration lines in the globals block (single-token declaration, no control syntax).
        stripped = line.strip()
        if not any(token in stripped for token in ("if ", "call ", "return ", "set ", "function ", "//")):
            continue
    kept.append(line)
t = "".join(kept)

# Remove wheel wording from shared UI.
t = t.replace('call DisplayTimedTextToPlayer(p,0,0,5,"车轮战：装备按原价出售，补回差价 "+I2S(OJO)+" 金币。")', 'call DisplayTimedTextToPlayer(p,0,0,5,"物品出售差价已返还："+I2S(OJO)+" 金币。")')
t = t.replace("// B1004 wheel battle: shared state; dialogs never mutate gameplay locally.\n", "")
t = t.replace("-jiaren, -jiajineng, -defend 1-30, -wawj", "-jiaren, -jiajineng, -wawj")
t = t.replace("Wheel mode retains the normal tower callbacks; this independent listener", "Normal mode retains the tower callbacks; this independent listener")

(out / "war3map.j").write_text(t, encoding="utf-8", newline="")
print("wrote", out / "war3map.j", len(t.encode("utf-8")), "removed_functions", len(defense_names) + len(wheel_names) + 2)
