# -*- coding: utf-8 -*-
"""
IMBA_POWER x2 whitelist transformer (final).
Uses global integer imbaMult (1=normal, 2=XM_MODE) to gate all inline
probability/count changes without restructuring each call site.
"""
import os, sys, csv, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src", "war3map.j")

with open(SRC, "r", encoding="utf-8") as f:
    text = f.read()

changes = []

def repl(old, new, count=1, category="", skill="", rawcode="", func="", param="", cap="", note=""):
    global text
    actual = text.count(old)
    if actual != count:
        print(f"FAIL [{category}]: expected {count} of [{old[:90]}...], found {actual}")
        sys.exit(1)
    text = text.replace(old, new)
    changes.append((category, skill, rawcode, func, param, old.strip()[:120], new.strip()[:120], cap, note))
    print(f"  OK [{category}] {func}")

# ============================================================
# 0. Global flags near IMBA_POWER
# ============================================================
print("== 0. Global flags ==")
repl(
    "constant real IMBA_POWER=2.\n",
    "constant real IMBA_POWER=2.\ninteger imbaMult=1\nboolean imbaB67DpsExclude=false\n",
    1, "global", "—", "—", "global", "imbaMult", "—",
    "imbaMult=1 normal / 2 XM_MODE; imbaB67DpsExclude for execute/econ carve"
)

# ============================================================
# 0b. Set imbaMult where XM_MODE is toggled
# ============================================================
repl(
    "if XM then\nset XM_MODE=true\nset HG=true",
    "if XM then\nset XM_MODE=true\nset imbaMult=2\nset HG=true",
    1, "global", "—", "—", "init@58266", "imbaMult", "—", "set imbaMult=2 when XM_MODE enabled"
)
repl(
    "set XM_MODE=false\n",
    "set XM_MODE=false\nset imbaMult=1\n",
    2, "global", "—", "—", "init@58308/58444", "imbaMult", "—",
    "reset imbaMult=1 when XM_MODE disabled"
)

# ============================================================
# 1. B67_DPS central damage multiplier
# ============================================================
print("== 1. B67_DPS damage x2 ==")
repl(
    "function B67_DPS takes unit p5,unit m5,integer BL7,real YM7 returns nothing\nlocal unit b67DpsKillDummyUnit=null\nif BL7==0 then\nreturn\nendif\nif BL7==2 then",
    "function B67_DPS takes unit p5,unit m5,integer BL7,real YM7 returns nothing\nlocal unit b67DpsKillDummyUnit=null\nif BL7==0 then\nreturn\nendif\n// IMBA: positive skill damage x IMBA_POWER once; BL7==6 life removal excluded; call-site exclusion for execute/econ.\nif imbaB67DpsExclude then\nset imbaB67DpsExclude=false\nelseif XM_MODE and BL7!=6 then\nset YM7=YM7*IMBA_POWER\nendif\nif BL7==2 then",
    1, "damage", "B67_DPS集中伤害", "BL7", "B67_DPS", "YM7", "BL7!=6",
    "mirrors B67 guard; BL7==6 auto-excluded"
)

# ============================================================
# 2. Carve midas/sacrifice execute (2 occurrences)
# ============================================================
repl(
    "call SetUnitLifeBJ(IH7,20)\ncall B67_DPS(ZX7,IH7,20,50)",
    "call SetUnitLifeBJ(IH7,20)\nset imbaB67DpsExclude=true\ncall B67_DPS(ZX7,IH7,20,50)",
    2, "damage-exclude", "点金/牺牲处决", "BL7==20", "B67_DPS@183639/183690", "YM7=50", "—",
    "execute/econ: target set to 20hp then 50 chaos/enhanced kill + gold/XP; excluded from multiplier"
)

# ============================================================
# 3. BA7/A0X6 control stun x2 + filters
# ============================================================
print("== 2. BA7 control ==")
repl(
    "function BA7 takes unit p5,unit m5,real Z27 returns nothing\nlocal unit BB7=CreateUnit(GetOwningPlayer(m5),'e00E',GetUnitX(m5),GetUnitY(m5),0)\nlocal integer BC7=BY7(Z27)",
    "function BA7 takes unit p5,unit m5,real Z27 returns nothing\nlocal unit BB7=null\nlocal integer BC7=0\n// IMBA: safety filters mirroring CommonUnitAddStun; duration x2 cap 5s.\nif XM_MODE then\nif MiaoStarted and GetUnitAbilityLevel(m5,'AMdI')>0 then\nreturn\nendif\nif (m5==ChaosObserverBoss and GetUnitTypeId(m5)=='NB0S') or (m5==TianxingBlackBoss and GetUnitTypeId(m5)=='NTY2') then\nreturn\nendif\nif IsMagicImmuneUnit(m5) or not UnitAlive(m5) then\nreturn\nendif\nif Z27 > 0. and Z27 < 2.5 then\nset Z27 = RMinBJ(Z27*IMBA_POWER, 5.)\nendif\nendif\nset BB7=CreateUnit(GetOwningPlayer(m5),'e00E',GetUnitX(m5),GetUnitY(m5),0)\nset BC7=BY7(Z27)",
    1, "control", "BA7/A0X6平行眩晕", "A0X6", "BA7", "Z27(秒)", "5.0s",
    "adds MiaoStarted/Boss/magic-immunity/dead filters matching CommonUnitAddStun"
)

# ============================================================
# 4. Loop_Damage central DoT duration x2 cap 30s
# ============================================================
print("== 3. Duration whitelist ==")
repl(
    "function Loop_Damage takes unit ZX7,unit IH7,real d,real DUR,real YM7 returns nothing\n    local timer t=CreateTimer()\n    local integer OB7=GetHandleId(t)\n    call SaveUnitHandle(TABLE_HY,OB7,0,ZX7)",
    "function Loop_Damage takes unit ZX7,unit IH7,real d,real DUR,real YM7 returns nothing\n    local timer t=CreateTimer()\n    local integer OB7=GetHandleId(t)\n    // IMBA: DoT total duration x2 cap 30s; tick d untouched; end-time child100 syncs via same DUR.\n    if XM_MODE then\n        set DUR=RMinBJ(DUR*IMBA_POWER,30.)\n    endif\n    call SaveUnitHandle(TABLE_HY,OB7,0,ZX7)",
    1, "duration-dot", "Loop_Damage(DoT总时长)", "DUR形参", "Loop_Damage", "DUR", "30.0s",
    "central exit; BrambleMaze caller 78363 benefits automatically"
)

# ============================================================
# 5. DisarmUnitToTimed x2 cap 5s
# ============================================================
repl(
    "\t\tcall DisarmUnit(whichUnit , true , disarmId , abilityId , buffId)\n\tendif\n\tcall TimerStart(timr, time, false, null)",
    "\t\tcall DisarmUnit(whichUnit , true , disarmId , abilityId , buffId)\n\tendif\n\t// IMBA: disarm duration x2 cap 5s.\n\tif XM_MODE then\n\t\tset time=RMinBJ(time*IMBA_POWER,5.)\n\tendif\n\tcall TimerStart(timr, time, false, null)",
    1, "duration-control", "DisarmUnitToTimed(缴械)", "—", "DisarmUnitToTimed", "time", "5.0s", ""
)

# ============================================================
# 6. Miao_Lock x2 cap 5s
# ============================================================
repl(
    "function Miao_Lock takes unit mdUnit,real mdDuration,string mdAnimation,boolean mdCleanse returns nothing\nlocal timer mdTimer=CreateTimer()\ncall SaveUnitHandle(MiaoTable,GetHandleId(mdTimer),0,mdUnit)",
    "function Miao_Lock takes unit mdUnit,real mdDuration,string mdAnimation,boolean mdCleanse returns nothing\nlocal timer mdTimer=CreateTimer()\n// IMBA: pause/stun control duration x2 cap 5s.\nif XM_MODE then\nset mdDuration=RMinBJ(mdDuration*IMBA_POWER,5.)\nendif\ncall SaveUnitHandle(MiaoTable,GetHandleId(mdTimer),0,mdUnit)",
    1, "duration-control", "Miao_Lock(通用暂停)", "—", "Miao_Lock", "mdDuration", "5.0s", ""
)

# ============================================================
# 7. B1012ChainsSilence 2.0 -> x2 cap 5s
# ============================================================
repl(
    "call TimerStart(b1012SilenceTimer,2.,false,function B1012ChainsSilenceEnd)",
    "// IMBA: silence duration x2 cap 5s.\nif XM_MODE then\ncall TimerStart(b1012SilenceTimer,RMinBJ(2.*IMBA_POWER,5.),false,function B1012ChainsSilenceEnd)\nelse\ncall TimerStart(b1012SilenceTimer,2.,false,function B1012ChainsSilenceEnd)\nendif",
    1, "duration-control", "B1012ChainsSilence(锁链沉默)", "A0NS/A1DA", "B1012ChainsSilence", "2.0", "5.0s", ""
)

# ============================================================
# 8. Luna_ApplyMark 5.0 -> x2 cap 30s
# ============================================================
repl(
    "call SaveTimerHandle(L7,h,StringHash(\"LunaMarkTimer\"),t)\ncall SaveUnitHandle(L7,GetHandleId(t),0,target)\ncall TimerStart(t,5.,false,function Luna_MarkExpire)",
    "call SaveTimerHandle(L7,h,StringHash(\"LunaMarkTimer\"),t)\ncall SaveUnitHandle(L7,GetHandleId(t),0,target)\n// IMBA: mark duration x2 cap 30s.\nif XM_MODE then\ncall TimerStart(t,RMinBJ(5.*IMBA_POWER,30.),false,function Luna_MarkExpire)\nelse\ncall TimerStart(t,5.,false,function Luna_MarkExpire)\nendif",
    1, "duration-debuff", "Luna_ApplyMark(月神印记)", "FaerieFire", "Luna_ApplyMark", "5.0", "30.0s", ""
)

# ============================================================
# 9. Luna_ApplyShield 5.0 -> x2 cap 30s
# ============================================================
repl(
    "call SaveUnitHandle(L7,GetHandleId(t),0,u)\ncall SaveInteger(L7,GetHandleId(t),1,generation)\ncall TimerStart(t,5.,false,function Luna_ShieldExpire)",
    "call SaveUnitHandle(L7,GetHandleId(t),0,u)\ncall SaveInteger(L7,GetHandleId(t),1,generation)\n// IMBA: shield duration x2 cap 30s.\nif XM_MODE then\ncall TimerStart(t,RMinBJ(5.*IMBA_POWER,30.),false,function Luna_ShieldExpire)\nelse\ncall TimerStart(t,5.,false,function Luna_ShieldExpire)\nendif",
    1, "duration-buff", "Luna_ApplyShield(月神护盾)", "LunaShield", "Luna_ApplyShield", "5.0", "30.0s", ""
)

# ============================================================
# 10. AeonDisk_Activate 2.5 -> x2 cap 10s
# ============================================================
repl(
    "call SaveInteger(L7,GetHandleId(t),1,serial)\ncall TimerStart(t,2.5,false,function AeonDisk_ActiveFinish)",
    "call SaveInteger(L7,GetHandleId(t),1,serial)\n// IMBA: aeon disk invuln window x2 cap 10s.\nif XM_MODE then\ncall TimerStart(t,RMinBJ(2.5*IMBA_POWER,10.),false,function AeonDisk_ActiveFinish)\nelse\ncall TimerStart(t,2.5,false,function AeonDisk_ActiveFinish)\nendif",
    1, "duration-buff", "AeonDisk_Activate(神盾无敌)", "A5VR", "AeonDisk_Activate", "2.5", "10.0s",
    "cooldown overlay tick separate"
)

# ============================================================
# 11. B907GiveShield 4.0 -> x2 cap 30s + end-time sync
# ============================================================
repl(
    "call SaveReal(L7,gearTargetKey,StringHash(\"B907Shield\"),gearAmount)\ncall SaveReal(L7,gearTargetKey,StringHash(\"B907ShieldUntil\"),GetGameTime()+4.)",
    "call SaveReal(L7,gearTargetKey,StringHash(\"B907Shield\"),gearAmount)\n// IMBA: gear shield duration x2 cap 30s; end-time synced.\nif XM_MODE then\ncall SaveReal(L7,gearTargetKey,StringHash(\"B907ShieldUntil\"),GetGameTime()+RMinBJ(4.*IMBA_POWER,30.))\nelse\ncall SaveReal(L7,gearTargetKey,StringHash(\"B907ShieldUntil\"),GetGameTime()+4.)\nendif",
    1, "duration-buff", "B907GiveShield(装备护盾)", "ManaShield", "B907GiveShield", "4.0", "30.0s",
    "END-TIME SYNC: B907ShieldUntil matches timer"
)
repl(
    "call SaveInteger(L7,GetHandleId(gearTimer),1,gearSerial)\ncall TimerStart(gearTimer,4.,false,function B907ShieldExpire)",
    "call SaveInteger(L7,GetHandleId(gearTimer),1,gearSerial)\nif XM_MODE then\ncall TimerStart(gearTimer,RMinBJ(4.*IMBA_POWER,30.),false,function B907ShieldExpire)\nelse\ncall TimerStart(gearTimer,4.,false,function B907ShieldExpire)\nendif",
    1, "duration-buff", "B907GiveShield timer", "ManaShield", "B907GiveShield", "4.0", "30.0s", ""
)

# ============================================================
# 12. LotusOrb_Reflect 12.0 -> x2 cap 30s
# ============================================================
repl(
    "call SaveInteger(L7,GetHandleId(cleanup),2,serial)\ncall TimerStart(cleanup,12.,false,function LotusOrb_TempFallback)",
    "call SaveInteger(L7,GetHandleId(cleanup),2,serial)\n// IMBA: lotus reflect window x2 cap 30s.\nif XM_MODE then\ncall TimerStart(cleanup,RMinBJ(12.*IMBA_POWER,30.),false,function LotusOrb_TempFallback)\nelse\ncall TimerStart(cleanup,12.,false,function LotusOrb_TempFallback)\nendif",
    1, "duration-buff", "LotusOrb_Reflect(莲花反弹)", "LotusOrb", "LotusOrb_ReflectTick", "12.0", "30.0s", ""
)

# ============================================================
# 13. NightmareAftershock 2.0 -> x2 cap 30s
# ============================================================
repl(
    "set t=CreateTimer()\ncall SaveUnitHandle(L7,GetHandleId(t),0,u)\ncall TimerStart(t,2.,false,function NightmareAftershock_SilenceEnd)",
    "set t=CreateTimer()\ncall SaveUnitHandle(L7,GetHandleId(t),0,u)\n// IMBA: nightmare aftershock debuff x2 cap 30s.\nif XM_MODE then\ncall TimerStart(t,RMinBJ(2.*IMBA_POWER,30.),false,function NightmareAftershock_SilenceEnd)\nelse\ncall TimerStart(t,2.,false,function NightmareAftershock_SilenceEnd)\nendif",
    1, "duration-debuff", "NightmareAftershock_Apply", "A4FF/BNab", "NightmareAftershock_Apply", "2.0", "30.0s", ""
)

# ============================================================
# 14. MaledictReveal 2.0 -> x2 cap 30s
# ============================================================
repl(
    "call SaveFogModifierHandle(L7,GetHandleId(t),0,f)\ncall TimerStart(t,2.,false,function MaledictReveal_End)",
    "call SaveFogModifierHandle(L7,GetHandleId(t),0,f)\n// IMBA: maledict reveal x2 cap 30s.\nif XM_MODE then\ncall TimerStart(t,RMinBJ(2.*IMBA_POWER,30.),false,function MaledictReveal_End)\nelse\ncall TimerStart(t,2.,false,function MaledictReveal_End)\nendif",
    1, "duration-debuff", "MaledictReveal_Start", "Maledict", "MaledictReveal_Start", "2.0", "30.0s", ""
)

# ============================================================
# 15. B906RazeBonus 6.0 -> x2 cap 30s + end-time sync
# ============================================================
repl(
    "call SaveInteger(L7,razeKey,3,razeStacks+1)\ncall SaveReal(L7,razeKey,4,GetGameTime()+6.)\ncall TimerStart(razeTimer,6.,false,function B906RazeExpire)",
    "call SaveInteger(L7,razeKey,3,razeStacks+1)\n// IMBA: raze bonus buff x2 cap 30s; end-time synced.\nif XM_MODE then\ncall SaveReal(L7,razeKey,4,GetGameTime()+RMinBJ(6.*IMBA_POWER,30.))\ncall TimerStart(razeTimer,RMinBJ(6.*IMBA_POWER,30.),false,function B906RazeExpire)\nelse\ncall SaveReal(L7,razeKey,4,GetGameTime()+6.)\ncall TimerStart(razeTimer,6.,false,function B906RazeExpire)\nendif",
    1, "duration-buff", "B906RazeBonus(推平奖励)", "B906", "B906RazeBonus", "6.0", "30.0s",
    "END-TIME SYNC: razeKey/4 matches timer"
)

# ============================================================
# 16. hrzycd 3.75 branch
# ============================================================
repl(
    "\tcall SaveInteger(TABLE_HY, GetHandleId(u), 'echs', 1)\n\tcall SaveUnitHandle(TABLE_HY, GetHandleId(t), 1, u)\n\tcall TimerStart(t, 3.75 , false, function hyzrcd)",
    "\tcall SaveInteger(TABLE_HY, GetHandleId(u), 'echs', 1)\n\tcall SaveUnitHandle(TABLE_HY, GetHandleId(t), 1, u)\n\t// IMBA: buff duration x2 cap 30s.\n\tif XM_MODE then\n\tcall TimerStart(t, RMinBJ(3.75*IMBA_POWER,30.) , false, function hyzrcd)\n\telse\n\tcall TimerStart(t, 3.75 , false, function hyzrcd)\n\tendif",
    1, "duration-buff", "hrzycd(3.75档)", "A2VW/A3TY", "hrzycd", "3.75", "30.0s",
    "cooldown YDWESetUnitAbilityState 3.75 untouched"
)

# ============================================================
# 17. hrzycd 5.0 branch
# ============================================================
repl(
    "\tcall SaveInteger(TABLE_HY, GetHandleId(u), 'echs', 1)\n\tcall SaveUnitHandle(TABLE_HY, GetHandleId(t), 1, u)\n\tcall TimerStart(t, 5 , false, function hyzrcd)",
    "\tcall SaveInteger(TABLE_HY, GetHandleId(u), 'echs', 1)\n\tcall SaveUnitHandle(TABLE_HY, GetHandleId(t), 1, u)\n\t// IMBA: buff duration x2 cap 30s.\n\tif XM_MODE then\n\tcall TimerStart(t, RMinBJ(5.*IMBA_POWER,30.) , false, function hyzrcd)\n\telse\n\tcall TimerStart(t, 5 , false, function hyzrcd)\n\tendif",
    1, "duration-buff", "hrzycd(5档)", "A2VW/A3TY", "hrzycd", "5.0", "30.0s", ""
)

# ============================================================
# 18. TZA 4.0 -> x2 cap 30s
# ============================================================
repl(
    "\tcall ExecuteAttackEvent(-2)\n\tendif\n\tcall TimerStart(tt, 4, false, null)",
    "\tcall ExecuteAttackEvent(-2)\n\tendif\n\t// IMBA: TZA buff x2 cap 30s.\n\tif XM_MODE then\n\tcall TimerStart(tt, RMinBJ(4.*IMBA_POWER,30.), false, null)\n\telse\n\tcall TimerStart(tt, 4, false, null)\n\tendif",
    1, "duration-buff", "TZA", "A04R/B0GS", "TZA", "4.0", "30.0s", ""
)

# ============================================================
# 19. UTA 2.0 -> x2 cap 5s (control)
# ============================================================
repl(
    "if id=='A27H' then\nif (LoadInteger(L7,(GetHandleId(targetUnit)),(705)))==0 then\ncall TimerStart(N84[GetPlayerId(GetOwningPlayer(whichUnit))],2,false,null)",
    "if id=='A27H' then\nif (LoadInteger(L7,(GetHandleId(targetUnit)),(705)))==0 then\n// IMBA: control duration x2 cap 5s.\nif XM_MODE then\ncall TimerStart(N84[GetPlayerId(GetOwningPlayer(whichUnit))],RMinBJ(2.*IMBA_POWER,5.),false,null)\nelse\ncall TimerStart(N84[GetPlayerId(GetOwningPlayer(whichUnit))],2,false,null)\nendif",
    1, "duration-control", "UTA", "A1RI/A1GU/A4L1/A28Y/A27H", "UTA", "2.0", "5.0s", ""
)

# ============================================================
# 20. XSBF 15.0 -> x2 cap 30s
# ============================================================
repl(
    "call SetUnitImitateMoveSpeed(u, 999, 800)\n\tcall TimerStart(t, 15., false, function XSBF2)",
    "call SetUnitImitateMoveSpeed(u, 999, 800)\n\t// IMBA: XSBF buff x2 cap 30s.\n\tif XM_MODE then\n\tcall TimerStart(t, RMinBJ(15.*IMBA_POWER,30.), false, function XSBF2)\n\telse\n\tcall TimerStart(t, 15., false, function XSBF2)\n\tendif",
    1, "duration-buff", "XSBF", "A4HS", "XSBF", "15.0", "30.0s", ""
)

# ============================================================
# 21. Z9F 5.1 -> x2 cap 30s
# ============================================================
repl(
    "endif\ncall TimerStart(tt,5.1,false,function Z4F_Timer)",
    "endif\n// IMBA: Z9F buff x2 cap 30s.\nif XM_MODE then\ncall TimerStart(tt,RMinBJ(5.1*IMBA_POWER,30.),false,function Z4F_Timer)\nelse\ncall TimerStart(tt,5.1,false,function Z4F_Timer)\nendif",
    1, "duration-buff", "Z9F", "A33H", "Z9F", "5.1", "30.0s", ""
)

# ============================================================
# 22. ATD mirror lifetime - EXCLUDED per hard constraint (2026-10-16):
#     summon/illusion lifetime not doubled (AI/pathfinding/timer load).
#     Damage/healing from clones still flows through B67/B907 entry x2.
# ============================================================
print("  SKIP [duration-summon] ATD mirror lifetime (excluded per hard constraint)")

# ============================================================
# 23. EUD multicast: use imbaMult global
# ============================================================
print("== 4. Count/probability ==")
repl(
    "function EUD takes unit ZX7 returns integer\nlocal integer V77=B287_GetUnitAbilityLevel(ZX7,'A088')\nlocal boolean HaveA=false\nlocal integer r=0",
    "function EUD takes unit ZX7 returns integer\nlocal integer V77=B287_GetUnitAbilityLevel(ZX7,'A088')\nlocal boolean HaveA=false\nlocal integer r=0\n// IMBA: multicast prob x2 cap100, casts r x2 cap6 (imbaMult gates).",
    1, "multicast", "EUD多重施法", "A088", "EUD", "C/r", "100/6",
    "uses global imbaMult"
)

# V77==1 HaveA
repl("if GetPrdRandom(ZX7,'A088'+5,5) then\n            set r=5\n            set N4[id]=N4[id]+1\n        elseif GetPrdRandom(ZX7,'A088'+2,50) then\n            set r=2\n            set TF4[id]=TF4[id]+1",
     "if GetPrdRandom(ZX7,'A088'+5,IMinBJ(5*imbaMult,100)) then\n            set r=IMinBJ(5*imbaMult,6)\n            set N4[id]=N4[id]+1\n        elseif GetPrdRandom(ZX7,'A088'+2,IMinBJ(50*imbaMult,100)) then\n            set r=IMinBJ(2*imbaMult,6)\n            set TF4[id]=TF4[id]+1",
     1, "multicast", "EUD L1神杖5/2路", "A088", "EUD", "5/r5,50/r2", "100/6", "")
# V77==1 non-HaveA
repl("if GetPrdRandom(ZX7,'A088'+2,40) then\n            set r=2\n            set TF4[id]=TF4[id]+1",
     "if GetPrdRandom(ZX7,'A088'+2,IMinBJ(40*imbaMult,100)) then\n            set r=IMinBJ(2*imbaMult,6)\n            set TF4[id]=TF4[id]+1",
     1, "multicast", "EUD L1非神杖2路", "A088", "EUD", "40/r2", "100/6", "")
# V77==2 HaveA
repl("if GetPrdRandom(ZX7,'A088'+5,5) then\n            set r=5\n            set N4[id]=N4[id]+1\n        elseif GetPrdRandom(ZX7,'A088'+3,30) then\n            set r=3\n            set TG4[id]=TG4[id]+1\n        elseif GetPrdRandom(ZX7,'A088'+2,60) then\n            set r=2\n            set TF4[id]=TF4[id]+1",
     "if GetPrdRandom(ZX7,'A088'+5,IMinBJ(5*imbaMult,100)) then\n            set r=IMinBJ(5*imbaMult,6)\n            set N4[id]=N4[id]+1\n        elseif GetPrdRandom(ZX7,'A088'+3,IMinBJ(30*imbaMult,100)) then\n            set r=IMinBJ(3*imbaMult,6)\n            set TG4[id]=TG4[id]+1\n        elseif GetPrdRandom(ZX7,'A088'+2,IMinBJ(60*imbaMult,100)) then\n            set r=IMinBJ(2*imbaMult,6)\n            set TF4[id]=TF4[id]+1",
     1, "multicast", "EUD L2神杖5/3/2路", "A088", "EUD", "5/r5,30/r3,60/r2", "100/6", "")
# V77==2 non-HaveA
repl("if GetPrdRandom(ZX7,'A088'+3,25) then\n            set r=3\n            set TG4[id]=TG4[id]+1\n        elseif GetPrdRandom(ZX7,'A088'+2,50) then\n            set r=2\n            set TF4[id]=TF4[id]+1",
     "if GetPrdRandom(ZX7,'A088'+3,IMinBJ(25*imbaMult,100)) then\n            set r=IMinBJ(3*imbaMult,6)\n            set TG4[id]=TG4[id]+1\n        elseif GetPrdRandom(ZX7,'A088'+2,IMinBJ(50*imbaMult,100)) then\n            set r=IMinBJ(2*imbaMult,6)\n            set TF4[id]=TF4[id]+1",
     1, "multicast", "EUD L2非神杖3/2路", "A088", "EUD", "25/r3,50/r2", "100/6", "")
# V77==3 HaveA
repl("if GetPrdRandom(ZX7,'A088'+5,5) then\n            set r=5\n            set N4[id]=N4[id]+1\n        elseif GetPrdRandom(ZX7,'A088'+4,20) then\n            set r=4\n            set TH4[id]=TH4[id]+1\n        elseif GetPrdRandom(ZX7,'A088'+3,40) then\n            set r=3\n            set TG4[id]=TG4[id]+1\n        elseif GetPrdRandom(ZX7,'A088'+2,80) then\n            set r=2\n            set TF4[id]=TF4[id]+1",
     "if GetPrdRandom(ZX7,'A088'+5,IMinBJ(5*imbaMult,100)) then\n            set r=IMinBJ(5*imbaMult,6)\n            set N4[id]=N4[id]+1\n        elseif GetPrdRandom(ZX7,'A088'+4,IMinBJ(20*imbaMult,100)) then\n            set r=IMinBJ(4*imbaMult,6)\n            set TH4[id]=TH4[id]+1\n        elseif GetPrdRandom(ZX7,'A088'+3,IMinBJ(40*imbaMult,100)) then\n            set r=IMinBJ(3*imbaMult,6)\n            set TG4[id]=TG4[id]+1\n        elseif GetPrdRandom(ZX7,'A088'+2,IMinBJ(80*imbaMult,100)) then\n            set r=IMinBJ(2*imbaMult,6)\n            set TF4[id]=TF4[id]+1",
     1, "multicast", "EUD L3神杖5/4/3/2路", "A088", "EUD", "5/r5,20/r4,40/r3,80/r2", "100/6", "")
# V77==3 non-HaveA
repl("if GetPrdRandom(ZX7,'A088'+4,15) then\n            set r=4\n            set TH4[id]=TH4[id]+1\n        elseif GetPrdRandom(ZX7,'A088'+3,30) then\n            set r=3\n            set TG4[id]=TG4[id]+1\n        elseif GetPrdRandom(ZX7,'A088'+2,60) then\n            set r=2\n            set TF4[id]=TF4[id]+1",
     "if GetPrdRandom(ZX7,'A088'+4,IMinBJ(15*imbaMult,100)) then\n            set r=IMinBJ(4*imbaMult,6)\n            set TH4[id]=TH4[id]+1\n        elseif GetPrdRandom(ZX7,'A088'+3,IMinBJ(30*imbaMult,100)) then\n            set r=IMinBJ(3*imbaMult,6)\n            set TG4[id]=TG4[id]+1\n        elseif GetPrdRandom(ZX7,'A088'+2,IMinBJ(60*imbaMult,100)) then\n            set r=IMinBJ(2*imbaMult,6)\n            set TF4[id]=TF4[id]+1",
     1, "multicast", "EUD L3非神杖4/3/2路", "A088", "EUD", "15/r4,30/r3,60/r2", "100/6", "")

# ============================================================
# 24. TPA probabilities (use imbaMult via existing probability local)
# ============================================================
repl(
    "\t\tif isMeleeAttacker then\n\t\t\tset probability = 25\n\t\telse\n\t\t\tset probability = 10\n\t\tendif\n\t\tif LoadInteger(TABLE_HY, GetHandleId(WXX),'bash')!= 1 and GetPrdRandom(WXX,'A4C7', probability) then",
    "\t\tif isMeleeAttacker then\n\t\t\tset probability = 25\n\t\telse\n\t\t\tset probability = 10\n\t\tendif\n\t\tset probability=IMinBJ(probability*imbaMult,100)\n\t\tif LoadInteger(TABLE_HY, GetHandleId(WXX),'bash')!= 1 and GetPrdRandom(WXX,'A4C7', probability) then",
    1, "probability", "碎颅锤/深渊之刃", "A4C7", "TPA", "25/10", "100", "melee 25->50, ranged 10->20"
)
repl(
    "\telseif B287_GetUnitAbilityLevel(WXX,'A0JJ')> 0 then\t//重击\n\t\tif GetPrdRandom(WXX,'A0JJ', 5 + 5 * B287_GetUnitAbilityLevel(WXX,'A0JJ')) then",
    "\telseif B287_GetUnitAbilityLevel(WXX,'A0JJ')> 0 then\t//重击\n\t\tset probability=IMinBJ((5 + 5 * B287_GetUnitAbilityLevel(WXX,'A0JJ'))*imbaMult,100)\n\t\tif GetPrdRandom(WXX,'A0JJ', probability) then",
    1, "probability", "Spirit Breaker重击", "A0JJ", "TPA", "5+5*lvl", "100", ""
)
repl(
    "\telseif B287_GetUnitAbilityLevel(WXX,'A081')> 0 then\t//时间锁定\n\t\t\tif (SUIJI_MODE==false or SuijiMode_HasRandomSkill(WXX,'A081')==false or GetUnitAbilityLevel(YXX,'B0C2')==0) and GetPrdRandom(WXX,'A081', 5 + 5 * B287_GetUnitAbilityLevel(WXX,'A081')) then",
    "\telseif B287_GetUnitAbilityLevel(WXX,'A081')> 0 then\t//时间锁定\n\t\t\tset probability=IMinBJ((5 + 5 * B287_GetUnitAbilityLevel(WXX,'A081'))*imbaMult,100)\n\t\t\tif (SUIJI_MODE==false or SuijiMode_HasRandomSkill(WXX,'A081')==false or GetUnitAbilityLevel(YXX,'B0C2')==0) and GetPrdRandom(WXX,'A081', probability) then",
    1, "probability", "Faceless Void时间锁定", "A081", "TPA", "5+5*lvl", "100", ""
)
repl(
    "        if GetUnitAbilityLevel(WXX,'B00B')>0 and SuijiMode_HasAghanimState(WXX) then\n            set probability = 15\n        else\n            set probability = 10\n        endif\n\t\tif GetPrdRandom(WXX,'A09E', probability) then",
    "        if GetUnitAbilityLevel(WXX,'B00B')>0 and SuijiMode_HasAghanimState(WXX) then\n            set probability = 15\n        else\n            set probability = 10\n        endif\n\t\tset probability=IMinBJ(probability*imbaMult,100)\n\t\tif GetPrdRandom(WXX,'A09E', probability) then",
    1, "probability", "Troll狂战士之怒", "A09E", "TPA", "15/10", "100", ""
)
repl(
    "\telseif GetUnitAbilityLevel(WXX,'A0WR')> 0 then\t//极度饥渴\n\t\tif GetPrdRandom(WXX,'A0WR', 15) then",
    "\telseif GetUnitAbilityLevel(WXX,'A0WR')> 0 then\t//极度饥渴\n\t\tset probability=IMinBJ(15*imbaMult,100)\n\t\tif GetPrdRandom(WXX,'A0WR', probability) then",
    1, "probability", "Lifestealer极度饥渴", "A0WR", "TPA", "15", "100", ""
)
repl(
    "\tif GetUnitAbilityLevel(WXX,'A061')==1 then\t//金箍棒\n\t\tif GetPrdRandom(WXX,'A061', 35) then",
    "\tif GetUnitAbilityLevel(WXX,'A061')==1 then\t//金箍棒\n\t\tset probability=IMinBJ(35*imbaMult,100)\n\t\tif GetPrdRandom(WXX,'A061', probability) then",
    1, "probability", "金箍棒暴击", "A061", "TPA", "35", "100", ""
)

# ============================================================
# 25. Scattered PRD probabilities (inline, gated via imbaMult)
# ============================================================
# A0C6 (two sites)
repl("GetPrdRandom(YXX, 'A0C6', 20)", "GetPrdRandom(YXX, 'A0C6', IMinBJ(20*imbaMult,100))",
     1, "probability", "Axe反击螺旋(YXX侧)", "A0C6", "FJLX@92735", "20", "100", "")
repl("GetPrdRandom(WXX, 'A0C6', 20)", "GetPrdRandom(WXX, 'A0C6', IMinBJ(20*imbaMult,100))",
     1, "probability", "Axe反击螺旋(WXX侧)", "A0C6", "FJLX@92741", "20", "100", "")
# A2KU
repl("GetPrdRandom(ZX7,'A2KU',15)", "GetPrdRandom(ZX7,'A2KU',IMinBJ(15*imbaMult,100))",
     1, "probability", "Naga激流(神杖)", "A2KU", "@81291", "15", "100", "")
# A263
repl("GetPrdRandom(ZX7, 'A263', 30)", "GetPrdRandom(ZX7, 'A263', IMinBJ(30*imbaMult,100))",
     2, "probability", "被动A(双路径)", "A263", "@46804+dup", "30", "100", "both code paths doubled")
# A264
repl("GetPrdRandom(ZX7, 'A264', 20)", "GetPrdRandom(ZX7, 'A264', IMinBJ(20*imbaMult,100))",
     2, "probability", "被动B(双路径)", "A264", "@46860+dup", "20", "100", "both code paths doubled")
# A2QG
repl("GetPrdRandom(ZX7, 'A2QG', 15)", "GetPrdRandom(ZX7, 'A2QG', IMinBJ(15*imbaMult,100))",
     2, "probability", "被动C(双路径)", "A2QG", "@46894+dup", "15", "100", "both code paths doubled")
# A03Y
repl("GetPrdRandom(p5,'A03Y',30)", "GetPrdRandom(p5,'A03Y',IMinBJ(30*imbaMult,100))",
     1, "probability", "被动D", "A03Y", "@90355", "30", "100", "")
# A4L7 (two sites)
repl("GetPrdRandom(WXX, 'A4L7', 20)", "GetPrdRandom(WXX, 'A4L7', IMinBJ(20*imbaMult,100))",
     1, "probability", "被动E", "A4L7", "@112445", "20", "100", "")
repl("GetPrdRandom(u, 'A4L7', 20)", "GetPrdRandom(u, 'A4L7', IMinBJ(20*imbaMult,100))",
     1, "probability", "被动E(2)", "A4L7", "@216350", "20", "100", "")
# A2RA
repl("GetPrdRandom(ZX7,'A2RA',40)", "GetPrdRandom(ZX7,'A2RA',IMinBJ(40*imbaMult,100))",
     1, "probability", "被动F", "A2RA", "@147269", "40", "100", "")
# A2PX
repl("GetPrdRandom(ZX7 , 'A2PX' , 40.)", "GetPrdRandom(ZX7 , 'A2PX' , IMinBJ(40*imbaMult,100))",
     1, "probability", "狼人重击", "A2PX", "@223487", "40", "100", "")
# A00K
repl("GetPrdRandom(ZX7 , 'A00K' , 15. + level * 5.)", "GetPrdRandom(ZX7 , 'A00K' , IMinBJ((15 + level * 5)*imbaMult,100))",
     1, "probability", "剑舞", "A00K", "@223498", "15+5*lvl", "100", "")
# A1OY
repl("GetPrdRandom(ZX7 , 'A1OY' , 25.)", "GetPrdRandom(ZX7 , 'A1OY' , IMinBJ(25*imbaMult,100))",
     1, "probability", "被动I", "A1OY", "@223545", "25", "100", "")
# ABcr
repl("GetPrdRandom(ZX7 , 'ABcr' , 7+level*2)", "GetPrdRandom(ZX7 , 'ABcr' , IMinBJ((7+level*2)*imbaMult,100))",
     1, "probability", "致死打击", "ABcr", "@223556", "7+2*lvl", "100", "")
# A03Q
repl("GetPrdRandom(ZX7 , 'A03Q' , 17)", "GetPrdRandom(ZX7 , 'A03Q' , IMinBJ(17*imbaMult,100))",
     1, "probability", "恩赐解脱", "A03Q", "@223570", "17", "100", "")
# A03N
repl("GetPrdRandom(ZX7 , 'A03N' , 25)", "GetPrdRandom(ZX7 , 'A03N' , IMinBJ(25*imbaMult,100))",
     1, "probability", "混沌一击", "A03N", "@223581", "25", "100", "")
# A19Q (variable d=5+BC7*5)
repl("GetPrdRandom(ZX7,'A19Q',d)", "GetPrdRandom(ZX7,'A19Q',IMinBJ(d*imbaMult,100))",
     1, "probability", "被动M", "A19Q", "@88225", "d=5+5*lvl", "100", "")
# A2EY (variable probability=25)
repl("GetPrdRandom(WLE,'A2EY', probability)", "GetPrdRandom(WLE,'A2EY', IMinBJ(probability*imbaMult,100))",
     1, "probability", "被动N", "A2EY", "@218601", "probability=25", "100", "")
# A4HE (variable i=20/10)
repl("GetPrdRandom(ZX7,'A4HE', i)", "GetPrdRandom(ZX7,'A4HE', IMinBJ(i*imbaMult,100))",
     1, "probability", "被动O", "A4HE", "@223018", "i=10/20", "100", "")
# I0TE (variable rate=XJBJ_RATE*100)
repl("GetPrdRandom(ZX7 , 'I0TE' , rate)", "GetPrdRandom(ZX7 , 'I0TE' , IMinBJ(rate*imbaMult,100))",
     1, "probability", "水晶剑/血棘", "I0TE", "@223604", "rate", "100", "")
# I0A3 (variable rate=DPBJ_RATE*100)
repl("GetPrdRandom(ZX7 , 'I0A3' , rate)", "GetPrdRandom(ZX7 , 'I0A3' , IMinBJ(rate*imbaMult,100))",
     1, "probability", "大炮", "I0A3", "@223613", "rate", "100", "")

# ============================================================
# 26. Bounce counts (times/max)
# ============================================================
# TSFB3 (A004 scepter): times=3, max=3 -> 6,6 (cap 8)
repl(
    "        call SaveInteger(TABLE_P,chainHandle,3,3)\n        call SaveInteger(TABLE_P,chainHandle,4,3)",
    "        // IMBA: bounce count x2 cap 8 (imbaMult gates).\n        call SaveInteger(TABLE_P,chainHandle,3,IMinBJ(3*imbaMult,8))\n        call SaveInteger(TABLE_P,chainHandle,4,IMinBJ(3*imbaMult,8))",
    1, "bounce", "飞镖弹射(神杖)", "A004", "TSFB3@66377", "times=3,max=3", "8",
    "400 radius at 66339 untouched; 1000 speed at 66345 untouched"
)
# FZD (A10D scepter): times=3 -> 6 (cap 8)
repl(
    "            call SaveInteger(TABLE_P,chainHandle,2,BC7)\n            call SaveInteger(TABLE_P,chainHandle,3,3)\n            call TimerStart(chainTimer,15.,false,function B582_BounceChainTimeout)",
    "            call SaveInteger(TABLE_P,chainHandle,2,BC7)\n            // IMBA: bounce count x2 cap 8.\n            call SaveInteger(TABLE_P,chainHandle,3,IMinBJ(3*imbaMult,8))\n            call TimerStart(chainTimer,15.,false,function B582_BounceChainTimeout)",
    1, "bounce", "PL灵魂之矛弹射(神杖)", "A10D", "FZD@82418", "times=3", "8",
    "400 radius at 82362 untouched; 1000 speed at 82420 untouched"
)

# ============================================================
# 27. Visage familiar count - EXCLUDED per hard constraint (2026-10-16):
#     summon entity count not doubled (unit cap, AI, pathfinding, timer load).
#     Familiar damage/healing still flows through B67/B907 entry x2.
# ============================================================
print("  SKIP [summon] Visage familiar count (excluded per hard constraint)")

# ============================================================
# Write output
# ============================================================
with open(SRC, "w", encoding="utf-8", newline="\n") as f:
    f.write(text)

# Generate changes CSV
csv_path = os.path.join(ROOT, "reports", "IMBA-POWER-x2-改动明细-20261016.csv")
with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["类别","技能名","rawcode","函数","参数","原公式","新公式","帽","排除/备注"])
    for c in changes:
        w.writerow(c)

new_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
print(f"\nDone. {len(changes)} changes applied.")
print(f"New size: {len(text)} bytes")
print(f"New SHA256: {new_hash}")
print(f"CSV: {csv_path}")
