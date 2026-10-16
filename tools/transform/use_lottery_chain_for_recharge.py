from pathlib import Path
import json

root = Path(r"D:\dota\DOTA69AI\rework-omg-imba")
src = root / "recharge-verify" / "war3map.j"
out = root / "recharge-lottery-chain-build"
out.mkdir(exist_ok=True)
t = src.read_text(encoding="utf-8")

# One fuzzy entitlement rule shared by entry gift and admin recharge.
# Prefer platform identity; when it is empty, fall back to the current player name.
old = """return 0
endfunction
function B894IdentityInfo takes nothing returns nothing"""
new = """return 0
endfunction
function B1132ContainsXiaoSheng takes string fuzzyText1132 returns boolean
local integer fuzzyPos1132=0
local integer fuzzyNeedleLength1132=StringLength(\"小生\")
local integer fuzzyTextLength1132=StringLength(fuzzyText1132)
if fuzzyText1132==null or fuzzyText1132==\"\" then
return false
endif
loop
exitwhen fuzzyPos1132+fuzzyNeedleLength1132>fuzzyTextLength1132
if SubString(fuzzyText1132,fuzzyPos1132,fuzzyPos1132+fuzzyNeedleLength1132)==\"小生\" then
return true
endif
set fuzzyPos1132=fuzzyPos1132+1
endloop
return false
endfunction
function B1132IsXiaoSheng takes integer fuzzyPid1132 returns boolean
if fuzzyPid1132<0 or fuzzyPid1132>=12 then
return false
endif
if B1132ContainsXiaoSheng(B894PlayerIdentity[fuzzyPid1132]) then
return true
endif
return B1132ContainsXiaoSheng(GetPlayerName(Player(fuzzyPid1132)))
endfunction
function B894IdentityInfo takes nothing returns nothing"""
if t.count(old) != 1:
    raise RuntimeError("fuzzy identity helper insertion point mismatch")
t = t.replace(old, new, 1)

old = "call DisplayTextToPlayer(b1060GetTriggerPlayer,0,0,\"平台完整身份未读取，专属福利未启用；不会退回昵称判断。\")"
new = "call DisplayTextToPlayer(b1060GetTriggerPlayer,0,0,\"平台完整身份未读取；当前玩家名：\"+GetPlayerName(b1060GetTriggerPlayer)+\"。包含‘小生’仍可启用专属福利。\")"
if t.count(old) != 1:
    raise RuntimeError("whoami empty identity text mismatch")
t = t.replace(old, new, 1)

old = """if b894Row==27 and B894PlayerIdentity[b894Pid]==\"小生不怕#1701\" then
call DisplayTimedTextToPlayer(b894Player,0,0,20.,\"已识别专属账号：小生不怕#1701。存档读取成功后将发放15币、15天知识之书和15天寒铁钢爪。\")
endif"""
new = """if B1132IsXiaoSheng(b894Pid) then
call DisplayTimedTextToPlayer(b894Player,0,0,20.,\"已模糊识别‘小生’账号。KK存档读取成功后将发放15币、15天知识之书和15天寒铁钢爪，并开放 -recharge。\")
endif"""
if t.count(old) != 1:
    raise RuntimeError("exact recognition announcement mismatch")
t = t.replace(old, new, 1)

old = "// Per-entry gift for exact platform identity 小生不怕#1701 (whitelist row 27)."
new = "// Per-entry gift for platform identities or player names containing 小生."
if t.count(old) != 1:
    raise RuntimeError("entry gift comment mismatch")
t = t.replace(old, new, 1)
old = "if giftPid1130<0 or giftPid1130>=12 or B1130EntryGiftGranted[giftPid1130] or B894PlayerIdentityRow[giftPid1130]!=27 or B894PlayerIdentity[giftPid1130]!=\"小生不怕#1701\" or not B836ArcLoaded[giftPid1130] then"
new = "if giftPid1130<0 or giftPid1130>=12 or B1130EntryGiftGranted[giftPid1130] or not B1132IsXiaoSheng(giftPid1130) or not B836ArcLoaded[giftPid1130] then"
if t.count(old) != 1:
    raise RuntimeError("entry gift exact identity condition mismatch")
t = t.replace(old, new, 1)

# Remove the custom operation-19 exemption. Recharge will use Dalaran's proven lottery operation 3.
old = "and arcOperation!=14 and arcOperation!=15 and arcOperation!=17 and arcOperation!=18 and arcOperation!=19) then"
new = "and arcOperation!=14 and arcOperation!=15 and arcOperation!=17 and arcOperation!=18) then"
if t.count(old) != 1:
    raise RuntimeError("operation19 exemption mismatch")
t = t.replace(old, new, 1)

# Remove custom operation-19 failure branch; operation 3 uses the native lottery retry/failure path.
old = """if B836ArcOperation[arcPid]==17 then
call X37(Player(arcPid),"打赏已在本局生效，平台存档提交未成功；输入 -tipretry 可重新提交存档。")
elseif B836ArcOperation[arcPid]==19 then
call X37(Player(B1131RechargeAuthor[arcPid]),"充值尚未确认，未显示成功。平台恢复后请重新输入原 -recharge 指令。")
call X37(Player(arcPid),"管理员充值写入平台存档失败，本次未确认，请联系管理员重试。")
else"""
new = """if B836ArcOperation[arcPid]==17 then
call X37(Player(arcPid),"打赏已在本局生效，平台存档提交未成功；输入 -tipretry 可重新提交存档。")
else"""
if t.count(old) != 1:
    raise RuntimeError("operation19 retry branch mismatch")
t = t.replace(old, new, 1)

# Replace acknowledgement: transaction 3 remains the single source of truth.
old = """elseif arcOperation==3 then
call DisplayTimedTextToPlayer(Player(arcPid),0,0,20.,arcSaveStatus+"双圣抽奖："+B836ArcPrizeText[arcPid]+"。奖励已发放，本局可用，请重新打开 -archive 查询或领取。")"""
new = """elseif arcOperation==3 then
if B1131RechargeAmount[arcPid]>0 then
call DisplayTimedTextToPlayer(Player(B1131RechargeAuthor[arcPid]),0,0,20.,arcSaveStatus+"后台充值到账：玩家"+I2S(arcPid)+" "+B1131RechargeType[arcPid]+" +"+I2S(B1131RechargeAmount[arcPid])+"。")
if B1131RechargeAuthor[arcPid]!=arcPid then
call DisplayTimedTextToPlayer(Player(arcPid),0,0,20.,arcSaveStatus+"后台充值到账："+B1131RechargeType[arcPid]+" +"+I2S(B1131RechargeAmount[arcPid])+"。"+B836ArcBalanceText(arcPid))
endif
set B1131RechargeAmount[arcPid]=0
else
call DisplayTimedTextToPlayer(Player(arcPid),0,0,20.,arcSaveStatus+"双圣抽奖："+B836ArcPrizeText[arcPid]+"。奖励已发放，本局可用，请重新打开 -archive 查询或领取。")
endif"""
if t.count(old) != 1:
    raise RuntimeError("lottery ack branch mismatch")
t = t.replace(old, new, 1)

# Delete the obsolete operation-19 acknowledgement branch.
old = """elseif arcOperation==19 then
call DisplayTimedTextToPlayer(Player(B1131RechargeAuthor[arcPid]),0,0,20.,arcSaveStatus+"充值成功：玩家"+I2S(arcPid)+" "+B1131RechargeType[arcPid]+" +"+I2S(B1131RechargeAmount[arcPid])+"。")
if B1131RechargeAuthor[arcPid]!=arcPid then
call DisplayTimedTextToPlayer(Player(arcPid),0,0,20.,arcSaveStatus+"管理员充值："+B1131RechargeType[arcPid]+" +"+I2S(B1131RechargeAmount[arcPid])+"。"+B836ArcBalanceText(arcPid))
endif"""
if t.count(old) != 1:
    raise RuntimeError("old operation19 ack mismatch")
t = t.replace(old, "", 1)

# Match the lottery prerequisites: target archive and auxiliary archive must both be ready.
old = """if not B836ArcHuman(rechargeTarget1131) or not B836ArcLoaded[rechargeTarget1131] then
call X37(Player(rechargeAuthor1131),"目标玩家必须在线且KK存档已读取成功；电脑或空槽位不能充值。")"""
new = """if not B836ArcHuman(rechargeTarget1131) or not B836ArcLoaded[rechargeTarget1131] or not B1042Loaded[rechargeTarget1131] or B1042Role[rechargeTarget1131]!=0 then
call X37(Player(rechargeAuthor1131),"目标玩家必须在线，且KK主存档和辅助存档均已读取成功；请进图后稍等再充值。")"""
if t.count(old) != 1:
    raise RuntimeError("recharge readiness check mismatch")
t = t.replace(old, new, 1)

# Use the exact transaction used by Dalaran double-saint lottery.
old = "call B836ArcBegin(rechargeTarget1131,19,rechargeCoins1131,rechargeBook1131,rechargeClaw1131,B836ArcStamp[rechargeTarget1131],rechargeMiao1131,0)"
new = "call B836ArcBegin(rechargeTarget1131,3,rechargeCoins1131,rechargeBook1131,rechargeClaw1131,B836ArcStamp[rechargeTarget1131],rechargeMiao1131,0)"
if t.count(old) != 1:
    raise RuntimeError("operation19 recharge call mismatch")
t = t.replace(old, new, 1)

# Route recharge through the map's proven global '-' command bus (H99).
# The separate chat trigger was present in source but did not fire in the user's KK match.
old = """local boolean IW9=((HD9==\"-aishowde\")or(HD9==\"-aishowdg\")or(HD9==\"-aishowdedg\")or(HD9==\"-aishowdynamic\"))
if HI9 and Ve()==false then"""
new = """local boolean IW9=((HD9==\"-aishowde\")or(HD9==\"-aishowdg\")or(HD9==\"-aishowdedg\")or(HD9==\"-aishowdynamic\"))
if SubString(HD9,0,9)==\"-recharge\" then
call ExecuteFunc(\"B1131Recharge\")
return
endif
if HI9 and Ve()==false then"""
if t.count(old) != 1:
    raise RuntimeError("H99 command bus insertion point mismatch")
t = t.replace(old, new, 1)

# Add an immediate diagnostic before any permission or archive checks.
old = """local integer rechargeMiao1131=0
if not B836ArcHuman(rechargeAuthor1131) or B894PlayerIdentity[rechargeAuthor1131]!=\"小生不怕#1701\" or B894PlayerIdentityRow[rechargeAuthor1131]!=27 then"""
new = """local integer rechargeMiao1131=0
call X37(Player(rechargeAuthor1131),\"|cff00ff00[充值] 命令已接收，正在校验‘小生’模糊身份和KK存档。|r\")
if not B836ArcHuman(rechargeAuthor1131) or not B1132IsXiaoSheng(rechargeAuthor1131) then"""
if t.count(old) != 1:
    raise RuntimeError("recharge diagnostic insertion point mismatch")
t = t.replace(old, new, 1)

# Disable the non-working standalone chat trigger. H99 is the single command entry.
old = "    call B1131RechargeInit()"
if t.count(old) != 1:
    raise RuntimeError("standalone recharge init call mismatch")
t = t.replace(old, "    // B1131Recharge is routed through the native H99 '-' command bus.", 1)

checks = {
    "operation19_refs": t.count("arcOperation==19") + t.count(",19,rechargeCoins1131"),
    "lottery_operation3_call": t.count("call B836ArcBegin(rechargeTarget1131,3,"),
    "lottery_local_write": t.count('DzAPI_Map_SaveServerValue(Player(arcPid),"OMGARC1",B836ArcCandidate[arcPid])'),
    "lottery_receipt": t.count('DzAPI_Map_GetServerValue(Player(arcPid),"OMGARC1")==B836ArcRecord[arcPid]'),
    "lottery_sync_ack": t.count('DzSyncData("B836AA",I2S(B836ArcSequence[arcPid]))'),
    "recharge_ack": t.count("后台充值到账"),
    "native_h99_route": t.count('if SubString(HD9,0,9)=="-recharge" then'),
    "standalone_init_calls": t.count("call B1131RechargeInit()"),
    "received_diagnostic": t.count("[充值] 命令已接收"),
    "fuzzy_helper": t.count("function B1132IsXiaoSheng takes"),
    "fuzzy_entry_gift": t.count("or not B1132IsXiaoSheng(giftPid1130)"),
    "fuzzy_recharge": t.count("or not B1132IsXiaoSheng(rechargeAuthor1131)"),
    "fuzzy_announcement": t.count("已模糊识别‘小生’账号"),
    "exact_entry_rule": t.count('B894PlayerIdentityRow[giftPid1130]!=27') + t.count('B894PlayerIdentity[giftPid1130]!="小生不怕#1701"'),
}
if checks["operation19_refs"] != 0 or checks["lottery_operation3_call"] != 1 or checks["lottery_local_write"] != 1 or checks["lottery_receipt"] != 1 or checks["lottery_sync_ack"] < 2 or checks["recharge_ack"] < 2 or checks["native_h99_route"] != 1 or checks["standalone_init_calls"] != 0 or checks["received_diagnostic"] != 1 or checks["fuzzy_helper"] != 1 or checks["fuzzy_entry_gift"] != 1 or checks["fuzzy_recharge"] != 1 or checks["fuzzy_announcement"] != 1 or checks["exact_entry_rule"] != 0:
    raise RuntimeError(checks)
(out / "war3map.j").write_text(t, encoding="utf-8", newline="")
(out / "lottery-chain-report.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(checks, ensure_ascii=False, indent=2))
