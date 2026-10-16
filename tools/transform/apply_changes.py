from pathlib import Path
import hashlib

root = Path(r"D:\dota\DOTA69AI\rework-omg-imba")
base = root / "baseline"
out = root / "build"
t = (base / "war3map.j").read_text(encoding="utf-8")

replacements = {
    '"我这钩子是向作者[本喵是萌新]学的，厉害吧"': '"我这钩子是向作者[小生我怕怕]学的，厉害吧"',
    '"这就是作者[本喵是萌新]制作的超强AI"': '"这就是作者[小生我怕怕]制作的超强AI"',
    '"多跟作者[本喵是萌新]学习，你也能超神"': '"多跟作者[小生我怕怕]学习，你也能超神"',
    '"本图作者"': '"小生我怕怕"',
    '"萌新求带"': '"小生我怕怕"',
    '作者：本喵是萌新': '作者：小生我怕怕',
    'call SetMapName("Dota英雄守护达拉然")': 'call SetMapName("DOTA OMG IMBA")',
    'call SetMapDescription("从115位独特的英雄中选择一位，守护达拉然。\\n按F9查看地图信息。")': 'call SetMapDescription("随机技能，强化AI，极限对抗。\\n作者：小生我怕怕\\n按F9查看地图信息。")',
    'call DialogSetMessage(KK_DIFFICULTY_DIALOG,"请选择难度或模式（仅主机选择，15秒后默认正常）")': 'call DialogSetMessage(KK_DIFFICULTY_DIALOG,"请选择难度（仅主机选择，15秒后默认正常）")',
    'call VV7(bj_FORCE_ALL_PLAYERS,15.,"|cFFFFCC00请等待主机选择本局难度、防守模式或车轮战模式。|r")': 'call VV7(bj_FORCE_ALL_PLAYERS,15.,"|cFFFFCC00请等待主机选择本局难度。|r")',
    'call DisplayTimedTextToPlayer(GetLocalPlayer(),0,0,30,"本图默认开启 |cFF00FF00-omg|r 随机OMG模式（-1 基础模式 + 随机技能）。\\n开局由主机选择新手、正常、困难或30波防守模式，15秒未选择则采用正常难度。\\n防守模式启用中路OMG，以30波三路进攻替换普通兵线；第1波与普通OMG兵线的开局出兵时点相同，进攻怪从上中下三路独立推进，不受原OMG进攻指令接管。\\n达拉然11座主防御塔初始增加2000生命、5护甲，随后在每一波进攻怪刷新时增加200生命、1护甲；黑暗方常驻AI英雄及原OMG AI逻辑保持不变。\\n|cFFFFCC00-1/-2/-3/-4/-5 快捷模式已关闭，避免重复触发默认模式。|r\\n\\n\\n")': 'call DisplayTimedTextToPlayer(GetLocalPlayer(),0,0,30,"本图默认开启 |cFF00FF00-omg|r 随机OMG模式（-1 基础模式 + 随机技能）。\\n开局由主机选择新手、正常或困难，15秒未选择则采用正常难度。\\n|cFFFFCC00车轮战和30波防守玩法已移除。|r\\n作者：|cFFFFCC00小生我怕怕|r\\n\\n")',
}

for old, new in replacements.items():
    count = t.count(old)
    if count != 1:
        raise RuntimeError(f"replacement count {count}: {old[:100]}")
    t = t.replace(old, new)

for line in (
    'set KK_DIFFICULTY_DEFENSE=DialogAddButton(KK_DIFFICULTY_DIALOG,"防守模式：中路OMG，抵御30波三路进攻",0)\n',
    'set B1004ModeButton=DialogAddButton(KK_DIFFICULTY_DIALOG,"车轮战：4倍熟练度+币奖励，cg5，随机英雄技能",0)\n',
):
    if t.count(line) != 1:
        raise RuntimeError(f"button line mismatch: {line}")
    t = t.replace(line, "")

old = """if b==B1004ModeButton and KK_GAME_DIFFICULTY==0 then
set B1004Wheel=true
call KKDifficulty_Apply(2)
elseif b==KK_DIFFICULTY_NEWBIE then
call KKDifficulty_Apply(1)
elseif b==KK_DIFFICULTY_DEFENSE then
if KK_GAME_DIFFICULTY==0 and KK_DEFENSE_DIFFICULTY_PENDING==false then
call KKDefenseDifficulty_Show()
endif
elseif b==KK_DIFFICULTY_HARD then"""
new = """if b==KK_DIFFICULTY_NEWBIE then
call KKDifficulty_Apply(1)
elseif b==KK_DIFFICULTY_HARD then"""
if t.count(old) != 1:
    raise RuntimeError("difficulty click branch mismatch")
t = t.replace(old, new)

old = """function B1004Start takes nothing returns nothing
local integer wheelPid=1
local trigger wheelClick=null
if B1004Started or not B1004Wheel then"""
new = """function B1004Start takes nothing returns nothing
local integer wheelPid=1
local trigger wheelClick=null
set B1004Wheel=false
return
// Removed mode: legacy implementation retained below as unreachable code for dependency safety.
if B1004Started or not B1004Wheel then"""
if t.count(old) != 1:
    raise RuntimeError("B1004Start mismatch")
t = t.replace(old, new)

old = """function KKDefense_Init takes nothing returns nothing
if KK_DEFENSE_TIMER!=null or KK_DEFENSE_WAVE>0 then"""
new = """function KKDefense_Init takes nothing returns nothing
set KK_DEFENSE_MODE=false
return
// Removed mode: legacy implementation retained below as unreachable code for dependency safety.
if KK_DEFENSE_TIMER!=null or KK_DEFENSE_WAVE>0 then"""
if t.count(old) != 1:
    raise RuntimeError("KKDefense_Init mismatch")
t = t.replace(old, new)

old = """elseif difficulty==4 then
set KK_DEFENSE_MODE=true
set PE4=true
call KKDefenseDifficulty_ApplyTechs()
call KKDefense_Init()
call VV7(bj_FORCE_ALL_PLAYERS,15.,"|cFFFFCC00已选择防守模式（"+KKDefenseDifficulty_GetName(KK_DEFENSE_DIFFICULTY)+"难度）：启用中路OMG与原AI系统；第1波随普通兵线开局时点刷新，30波怪物仍从上中下三路推进；防御塔获得初始强化并随每波成长。|r")"""
new = """elseif difficulty==4 then
set KK_DEFENSE_MODE=false
call VV7(bj_FORCE_ALL_PLAYERS,15.,"|cFFFFFF80防守玩法已移除，已切换为正常难度。|r")"""
if t.count(old) != 1:
    raise RuntimeError("difficulty 4 branch mismatch")
t = t.replace(old, new)

(out / "war3map.j").write_text(t, encoding="utf-8", newline="")

w = (base / "war3map.w3i").read_bytes()

def replace_z(data: bytes, old: str, new: str, limit: int = 1) -> bytes:
    old_bytes = old.encode("utf-8") + b"\0"
    new_bytes = new.encode("utf-8") + b"\0"
    count = data.count(old_bytes)
    if count < limit:
        raise RuntimeError(f"w3i missing {old!r}: {count}")
    return data.replace(old_bytes, new_bytes, limit)

w = replace_z(w, "Dota英雄守护达拉然", "DOTA OMG IMBA", 2)
w = replace_z(w, "本喵是萌新", "小生我怕怕", 1)
w = replace_z(w, "从115位独特的英雄中选择一位，守护达拉然。\n按F9查看地图信息。", "随机技能，强化AI，极限对抗。\n作者：小生我怕怕\n按F9查看地图信息。", 1)
(out / "war3map.w3i").write_bytes(w)

print("script", len(t.encode("utf-8")), hashlib.sha256(t.encode("utf-8")).hexdigest())
print("w3i", len(w), hashlib.sha256(w).hexdigest())
for needle in (
    "B1004Wheel=true",
    "KK_DEFENSE_MODE=true",
    'DialogAddButton(KK_DIFFICULTY_DIALOG,"防守模式',
    'DialogAddButton(KK_DIFFICULTY_DIALOG,"车轮战',
    "本喵是萌新",
    "本喵也是萌新",
    "萌新求带",
):
    print(needle, t.count(needle))
