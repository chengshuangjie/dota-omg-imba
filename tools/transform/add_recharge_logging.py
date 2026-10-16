from pathlib import Path
import json

root = Path(r"D:\dota\DOTA69AI\rework-omg-imba")
src = root / "recharge-lottery-chain-build" / "war3map.j"
out = root / "recharge-logging-build"
out.mkdir(exist_ok=True)
t = src.read_text(encoding="utf-8")

def replace_once(old, new, name):
    global t
    if t.count(old) != 1:
        raise RuntimeError(f"{name}: expected 1, got {t.count(old)}")
    t = t.replace(old, new, 1)

# Shared ring-buffer globals. File output is local-only and never controls gameplay.
replace_once(
    'boolean array B1130EntryGiftGranted\nboolean array B892BoundMulticast',
    'boolean array B1130EntryGiftGranted\nstring array B1133LogRows\ninteger B1133LogCount=0\ninteger B1133LogSerial=0\nboolean array B892BoundMulticast',
    'log globals')

# Logging framework: shared ring, local file, sync bridge for KK local API results, and -rlog display.
replace_once(
'''function B836ArcBalanceText takes integer arcPid returns string
return "哦买嘎硬币："+I2S(B836ArcCoins[arcPid]-B836ArcHeld[arcPid])+"（本局暂记："+I2S(B836ArcHeld[arcPid])+"）"
endfunction
function B836ArcLocalWrite takes integer arcPid returns nothing''',
'''function B836ArcBalanceText takes integer arcPid returns string
return "哦买嘎硬币："+I2S(B836ArcCoins[arcPid]-B836ArcHeld[arcPid])+"（本局暂记："+I2S(B836ArcHeld[arcPid])+"）"
endfunction
function B1133LogWriteFile takes nothing returns nothing
local integer logOffset1133=0
local integer logIndex1133=0
if GetPlayerController(GetLocalPlayer())!=MAP_CONTROL_USER then
return
endif
call PreloadGenClear()
call PreloadStart()
call Preload("DOTA OMG IMBA recharge/archive diagnostic; local_slot="+I2S(GetPlayerId(GetLocalPlayer()))+" serial="+I2S(B1133LogSerial))
loop
exitwhen logOffset1133>=B1133LogCount
set logIndex1133=ModuloInteger(B1133LogSerial-B1133LogCount+logOffset1133,24)
call Preload(B1133LogRows[logIndex1133])
set logOffset1133=logOffset1133+1
endloop
call PreloadGenEnd("1-miao-error\\recharge-p"+I2S(GetPlayerId(GetLocalPlayer()))+".text")
call PreloadGenClear()
endfunction
function B1133LogAppend takes string logText1133 returns nothing
local integer logIndex1133=ModuloInteger(B1133LogSerial,24)
set B1133LogSerial=B1133LogSerial+1
set B1133LogRows[logIndex1133]="#"+I2S(B1133LogSerial)+" t="+R2S(TimerGetElapsed(W))+" "+logText1133
if B1133LogCount<24 then
set B1133LogCount=B1133LogCount+1
endif
call B1133LogWriteFile()
endfunction
function B1133LogSync takes nothing returns nothing
local integer logPid1133=GetPlayerId(DzGetTriggerSyncPlayer())
call B1133LogAppend("LOCAL pid="+I2S(logPid1133)+" "+DzGetTriggerSyncData())
endfunction
function B1133LogShow takes nothing returns nothing
local player logPlayer1133=GetTriggerPlayer()
local integer logOffset1133=0
local integer logIndex1133=0
if not B1132IsXiaoSheng(GetPlayerId(logPlayer1133)) then
call X37(logPlayer1133,"你没有查看充值诊断日志的权限。")
set logPlayer1133=null
return
endif
call DisplayTimedTextToPlayer(logPlayer1133,0,0,30.,"|cffffff00[充值诊断] 最近"+I2S(B1133LogCount)+"条；本地文件：1-miao-error\\recharge-p"+I2S(GetPlayerId(logPlayer1133))+".text|r")
loop
exitwhen logOffset1133>=B1133LogCount
set logIndex1133=ModuloInteger(B1133LogSerial-B1133LogCount+logOffset1133,24)
call DisplayTimedTextToPlayer(logPlayer1133,0,0,30.,B1133LogRows[logIndex1133])
set logOffset1133=logOffset1133+1
endloop
set logPlayer1133=null
endfunction
function B1133LogInit takes nothing returns nothing
local trigger logSyncTrigger1133=CreateTrigger()
call DzTriggerRegisterSyncData(logSyncTrigger1133,"B1133LG",false)
call TriggerAddAction(logSyncTrigger1133,function B1133LogSync)
set logSyncTrigger1133=null
call B1133LogAppend("INIT logger=ready")
endfunction
function B836ArcLocalWrite takes integer arcPid returns nothing''',
    'logging framework')

# Local write telemetry. All local observations are returned via DzSyncData.
replace_once(
'''function B836ArcLocalWrite takes integer arcPid returns nothing
local string arcCurrent
local boolean arcAccepted=false
if not B836ArcHuman(arcPid) then
return
endif
// Do not mutate shared arrays, handles, RNG or gameplay under this local branch.
if GetLocalPlayer()==Player(arcPid) then
if DzAPI_Map_GetServerValueErrorCode(Player(arcPid))==0 then
set arcCurrent=DzAPI_Map_GetServerValue(Player(arcPid),"OMGARC1")
if arcCurrent==B836ArcCandidate[arcPid] then
call DzSyncData("B836AA",I2S(B836ArcSequence[arcPid]))
elseif arcCurrent==B836ArcRecord[arcPid] or (HaveSavedString(L7,StringHash("B839ArcHistory"+I2S(arcPid)),StringHash(arcCurrent)) and LoadStr(L7,StringHash("B839ArcHistory"+I2S(arcPid)),StringHash(arcCurrent))==arcCurrent) then
set arcAccepted=DzAPI_Map_SaveServerValue(Player(arcPid),"OMGARC1",B836ArcCandidate[arcPid])
if arcAccepted then
call DzSyncData("B836AA",I2S(B836ArcSequence[arcPid]))
endif
endif
endif
endif
endfunction''',
'''function B836ArcLocalWrite takes integer arcPid returns nothing
local string arcCurrent
local boolean arcAccepted=false
local integer arcError=0
if not B836ArcHuman(arcPid) then
call B1133LogAppend("WRITE_SKIP pid="+I2S(arcPid)+" reason=not_human")
return
endif
// Do not mutate shared arrays, handles, RNG or gameplay under this local branch.
if GetLocalPlayer()==Player(arcPid) then
set arcError=DzAPI_Map_GetServerValueErrorCode(Player(arcPid))
if arcError==0 then
set arcCurrent=DzAPI_Map_GetServerValue(Player(arcPid),"OMGARC1")
if arcCurrent==B836ArcCandidate[arcPid] then
call DzSyncData("B1133LG","WRITE seq="+I2S(B836ArcSequence[arcPid])+" op="+I2S(B836ArcOperation[arcPid])+" result=candidate_cached")
call DzSyncData("B836AA",I2S(B836ArcSequence[arcPid]))
elseif arcCurrent==B836ArcRecord[arcPid] or (HaveSavedString(L7,StringHash("B839ArcHistory"+I2S(arcPid)),StringHash(arcCurrent)) and LoadStr(L7,StringHash("B839ArcHistory"+I2S(arcPid)),StringHash(arcCurrent))==arcCurrent) then
set arcAccepted=DzAPI_Map_SaveServerValue(Player(arcPid),"OMGARC1",B836ArcCandidate[arcPid])
call DzSyncData("B1133LG","WRITE seq="+I2S(B836ArcSequence[arcPid])+" op="+I2S(B836ArcOperation[arcPid])+" result=save accepted="+I2S(B287_BoolToInt(arcAccepted)))
if arcAccepted then
call DzSyncData("B836AA",I2S(B836ArcSequence[arcPid]))
endif
else
call DzSyncData("B1133LG","WRITE seq="+I2S(B836ArcSequence[arcPid])+" op="+I2S(B836ArcOperation[arcPid])+" result=record_conflict current_hash="+I2S(StringHash(arcCurrent)))
endif
else
call DzSyncData("B1133LG","WRITE seq="+I2S(B836ArcSequence[arcPid])+" op="+I2S(B836ArcOperation[arcPid])+" result=api_error code="+I2S(arcError))
endif
endif
endfunction''',
    'local write telemetry')

# Receipt telemetry from owner-local readback.
replace_once(
'''function B839ArcCheckReceipt takes integer arcPid returns nothing
if B839ArcReadPending[arcPid] and B836ArcOperation[arcPid]==0 and GetLocalPlayer()==Player(arcPid) then
if DzAPI_Map_GetServerValueErrorCode(Player(arcPid))==0 and DzAPI_Map_GetServerValue(Player(arcPid),"OMGARC1")==B836ArcRecord[arcPid] then
call DzSyncData("B836AA",I2S(B836ArcSequence[arcPid]))
endif
endif
endfunction''',
'''function B839ArcCheckReceipt takes integer arcPid returns nothing
local integer receiptError1133=0
local boolean receiptMatch1133=false
if B839ArcReadPending[arcPid] and B836ArcOperation[arcPid]==0 and GetLocalPlayer()==Player(arcPid) then
set receiptError1133=DzAPI_Map_GetServerValueErrorCode(Player(arcPid))
if receiptError1133==0 then
set receiptMatch1133=DzAPI_Map_GetServerValue(Player(arcPid),"OMGARC1")==B836ArcRecord[arcPid]
endif
call DzSyncData("B1133LG","READBACK seq="+I2S(B836ArcSequence[arcPid])+" err="+I2S(receiptError1133)+" match="+I2S(B287_BoolToInt(receiptMatch1133)))
if receiptMatch1133 then
call DzSyncData("B836AA",I2S(B836ArcSequence[arcPid]))
endif
endif
endfunction''',
    'receipt telemetry')

# Retry and begin logs.
replace_once(
'''local integer arcPid=LoadInteger(L7,GetHandleId(arcRetryTimer),0)
if B836ArcOperation[arcPid]==0 and B839ArcReadPending[arcPid]''',
'''local integer arcPid=LoadInteger(L7,GetHandleId(arcRetryTimer),0)
call B1133LogAppend("RETRY pid="+I2S(arcPid)+" seq="+I2S(B836ArcSequence[arcPid])+" op="+I2S(B836ArcOperation[arcPid])+" attempt="+I2S(B836ArcAttempts[arcPid])+" pending="+I2S(B287_BoolToInt(B839ArcReadPending[arcPid])))
if B836ArcOperation[arcPid]==0 and B839ArcReadPending[arcPid]''',
    'retry log')
replace_once(
'''local integer skPurchase=B1032Journal[arcPid]
if not B836ArcHuman(arcPid) or not B836ArcLoaded[arcPid] or B836ArcOperation[arcPid]!=0 or B836ArcFault[arcPid] or ((not B1042Loaded[arcPid] or B1042Role[arcPid]!=0) and arcOperation!=14 and arcOperation!=15 and arcOperation!=17 and arcOperation!=18) then
return
endif''',
'''local integer skPurchase=B1032Journal[arcPid]
call B1133LogAppend("BEGIN_REQUEST pid="+I2S(arcPid)+" op="+I2S(arcOperation)+" loaded="+I2S(B287_BoolToInt(B836ArcLoaded[arcPid]))+" aux="+I2S(B287_BoolToInt(B1042Loaded[arcPid]))+" role="+I2S(B1042Role[arcPid])+" current_op="+I2S(B836ArcOperation[arcPid])+" fault="+I2S(B287_BoolToInt(B836ArcFault[arcPid])))
if not B836ArcHuman(arcPid) or not B836ArcLoaded[arcPid] or B836ArcOperation[arcPid]!=0 or B836ArcFault[arcPid] or ((not B1042Loaded[arcPid] or B1042Role[arcPid]!=0) and arcOperation!=14 and arcOperation!=15 and arcOperation!=17 and arcOperation!=18) then
call B1133LogAppend("BEGIN_REJECT pid="+I2S(arcPid)+" op="+I2S(arcOperation))
return
endif''',
    'begin request log')
replace_once(
'''set B836ArcAttempts[arcPid]=1
set arcRetryTimer=CreateTimer()''',
'''set B836ArcAttempts[arcPid]=1
call B1133LogAppend("BEGIN_OK pid="+I2S(arcPid)+" seq="+I2S(B836ArcSequence[arcPid])+" op="+I2S(arcOperation)+" coins="+I2S(arcCoins)+" book="+I2S(arcBook)+" claw="+I2S(arcClaw)+" miao="+I2S(arcMiao))
set arcRetryTimer=CreateTimer()''',
    'begin ok log')

# ACK receive/commit logs.
replace_once(
'''local integer arcOperation
local string arcSaveStatus="|cff00ff00存档已提交，本局已生效，下局读取更新。|r"
if not B836ArcHuman(arcPid) then''',
'''local integer arcOperation
local string arcSaveStatus="|cff00ff00存档已提交，本局已生效，下局读取更新。|r"
call B1133LogAppend("ACK_RX pid="+I2S(arcPid)+" data="+arcData+" expected="+I2S(B836ArcSequence[arcPid])+" op="+I2S(B836ArcOperation[arcPid]))
if not B836ArcHuman(arcPid) then''',
    'ack receive log')
replace_once(
'''set B836ArcOperation[arcPid]=0
set B836ArcFault[arcPid]=false
if B836ArcHuman(arcPid) then''',
'''set B836ArcOperation[arcPid]=0
set B836ArcFault[arcPid]=false
call B1133LogAppend("ACK_COMMIT pid="+I2S(arcPid)+" op="+I2S(arcOperation)+" pending="+I2S(B287_BoolToInt(B839ArcReadPending[arcPid]))+" coins="+I2S(B836ArcCoins[arcPid])+" book="+I2S(B836ArcBook[arcPid])+" claw="+I2S(B836ArcClaw[arcPid])+" miao="+I2S(B891ArcMiao[arcPid]))
if B836ArcHuman(arcPid) then''',
    'ack commit log')

# Entry gift and archive-load logs.
replace_once(
'''local integer giftBook1130=0
local integer giftClaw1130=0
if giftPid1130<0 or giftPid1130>=12 or B1130EntryGiftGranted[giftPid1130] or not B1132IsXiaoSheng(giftPid1130) or not B836ArcLoaded[giftPid1130] then
return
endif''',
'''local integer giftBook1130=0
local integer giftClaw1130=0
call B1133LogAppend("GIFT_CHECK pid="+I2S(giftPid1130)+" granted="+I2S(B287_BoolToInt(B1130EntryGiftGranted[giftPid1130]))+" fuzzy="+I2S(B287_BoolToInt(B1132IsXiaoSheng(giftPid1130)))+" loaded="+I2S(B287_BoolToInt(B836ArcLoaded[giftPid1130])))
if giftPid1130<0 or giftPid1130>=12 or B1130EntryGiftGranted[giftPid1130] or not B1132IsXiaoSheng(giftPid1130) or not B836ArcLoaded[giftPid1130] then
call B1133LogAppend("GIFT_SKIP pid="+I2S(giftPid1130))
return
endif''',
    'gift check log')
replace_once(
'''set B1130EntryGiftGranted[giftPid1130]=true
call B836ArcBegin(giftPid1130,18,giftCoins1130,giftBook1130,giftClaw1130,B836ArcStamp[giftPid1130],B891ArcMiao[giftPid1130],0)''',
'''set B1130EntryGiftGranted[giftPid1130]=true
call B1133LogAppend("GIFT_CANDIDATE pid="+I2S(giftPid1130)+" coins="+I2S(giftCoins1130)+" book="+I2S(giftBook1130)+" claw="+I2S(giftClaw1130))
call B836ArcBegin(giftPid1130,18,giftCoins1130,giftBook1130,giftClaw1130,B836ArcStamp[giftPid1130],B891ArcMiao[giftPid1130],0)''',
    'gift candidate log')
replace_once(
'''local string arcRecord
local integer arcEpoch=S2I(arcEpochText)
if not B836ArcHuman(arcPid) or B836ArcLoaded[arcPid] then''',
'''local string arcRecord
local integer arcEpoch=S2I(arcEpochText)
call B1133LogAppend("LOAD_RX pid="+I2S(arcPid)+" epoch="+arcEpochText+" identity_empty="+I2S(B287_BoolToInt(B894PlayerIdentity[arcPid]==null or B894PlayerIdentity[arcPid]==\"\"))+" row="+I2S(B894PlayerIdentityRow[arcPid])+" fuzzy="+I2S(B287_BoolToInt(B1132IsXiaoSheng(arcPid))))
if not B836ArcHuman(arcPid) or B836ArcLoaded[arcPid] then''',
    'load receive log')
replace_once(
'''set B1031RewardEpoch[arcPid]=B1031ArcField(arcRecord,10)
call B1130EntryGift(arcPid)''',
'''set B1031RewardEpoch[arcPid]=B1031ArcField(arcRecord,10)
call B1133LogAppend("LOAD_OK pid="+I2S(arcPid)+" coins="+I2S(B836ArcCoins[arcPid])+" book="+I2S(B836ArcBook[arcPid])+" claw="+I2S(B836ArcClaw[arcPid])+" miao="+I2S(B891ArcMiao[arcPid]))
call B1130EntryGift(arcPid)''',
    'load ok log')

# Recharge parsing and candidate logs.
replace_once(
'''call X37(Player(rechargeAuthor1131),"|cff00ff00[充值] 命令已接收，正在校验‘小生’模糊身份和KK存档。|r")
if not B836ArcHuman(rechargeAuthor1131) or not B1132IsXiaoSheng(rechargeAuthor1131) then''',
'''call X37(Player(rechargeAuthor1131),"|cff00ff00[充值] 命令已接收，正在校验‘小生’模糊身份和KK存档。|r")
call B1133LogAppend("CMD_RX author="+I2S(rechargeAuthor1131)+" raw="+rechargeText1131+" fuzzy="+I2S(B287_BoolToInt(B1132IsXiaoSheng(rechargeAuthor1131)))+" identity_empty="+I2S(B287_BoolToInt(B894PlayerIdentity[rechargeAuthor1131]==null or B894PlayerIdentity[rechargeAuthor1131]==\"\")))
if not B836ArcHuman(rechargeAuthor1131) or not B1132IsXiaoSheng(rechargeAuthor1131) then''',
    'command receive log')
replace_once(
'''set B1131RechargeAmount[rechargeTarget1131]=rechargeAmount1131
call B836ArcBegin(rechargeTarget1131,3,rechargeCoins1131,rechargeBook1131,rechargeClaw1131,B836ArcStamp[rechargeTarget1131],rechargeMiao1131,0)''',
'''set B1131RechargeAmount[rechargeTarget1131]=rechargeAmount1131
call B1133LogAppend("CMD_CANDIDATE author="+I2S(rechargeAuthor1131)+" target="+I2S(rechargeTarget1131)+" type="+rechargeType1131+" amount="+I2S(rechargeAmount1131)+" coins="+I2S(rechargeCoins1131)+" book="+I2S(rechargeBook1131)+" claw="+I2S(rechargeClaw1131)+" miao="+I2S(rechargeMiao1131))
call B836ArcBegin(rechargeTarget1131,3,rechargeCoins1131,rechargeBook1131,rechargeClaw1131,B836ArcStamp[rechargeTarget1131],rechargeMiao1131,0)''',
    'command candidate log')

# Native H99 command routing for -rlog.
replace_once(
'''if SubString(HD9,0,9)=="-recharge" then
call ExecuteFunc("B1131Recharge")
return
endif''',
'''if HD9=="-rlog" then
call ExecuteFunc("B1133LogShow")
return
endif
if SubString(HD9,0,9)=="-recharge" then
call ExecuteFunc("B1131Recharge")
return
endif''',
    'rlog H99 route')

# Initialize the logger before archive traffic begins.
replace_once(
'''local integer arcPid=0
call B838WawjInit()''',
'''local integer arcPid=0
call B1133LogInit()
call B838WawjInit()''',
    'logger init')

# Identity acquisition log after KK platform identity is read.
replace_once(
'''set b894Row=B894MatchIdentity(B894PlayerIdentity[b894Pid])
set B894PlayerIdentityRow[b894Pid]=b894Row
if B1132IsXiaoSheng(b894Pid) then''',
'''set b894Row=B894MatchIdentity(B894PlayerIdentity[b894Pid])
set B894PlayerIdentityRow[b894Pid]=b894Row
call B1133LogAppend("IDENTITY pid="+I2S(b894Pid)+" empty="+I2S(B287_BoolToInt(B894PlayerIdentity[b894Pid]==null or B894PlayerIdentity[b894Pid]==\"\"))+" row="+I2S(b894Row)+" fuzzy="+I2S(B287_BoolToInt(B1132IsXiaoSheng(b894Pid)))+" name_hash="+I2S(StringHash(GetPlayerName(b894Player))))
if B1132IsXiaoSheng(b894Pid) then''',
    'identity acquisition log')

# KK main archive local-read telemetry before B836AL reaches shared state.
replace_once(
'''local integer arcEpoch
local string arcRecord
set B836ArcLoadAttempts=B836ArcLoadAttempts+1''',
'''local integer arcEpoch
local string arcRecord
local integer arcLoadError1133=0
set B836ArcLoadAttempts=B836ArcLoadAttempts+1''',
    'load tick error local')
replace_once(
'''if GetLocalPlayer()==Player(arcPid) then
if DzAPI_Map_GetServerValueErrorCode(Player(arcPid))==0 then
set arcEpoch=DzAPI_Map_GetGameStartTime()
set arcRecord=DzAPI_Map_GetServerValue(Player(arcPid),"OMGARC1")
if arcEpoch>=1500000000 and StringLength(arcRecord)<=63 then
call DzSyncData("B836AL",I2S(arcEpoch)+";"+arcRecord)
endif
endif
endif''',
'''if GetLocalPlayer()==Player(arcPid) then
set arcLoadError1133=DzAPI_Map_GetServerValueErrorCode(Player(arcPid))
if arcLoadError1133==0 then
set arcEpoch=DzAPI_Map_GetGameStartTime()
set arcRecord=DzAPI_Map_GetServerValue(Player(arcPid),"OMGARC1")
call DzSyncData("B1133LG","LOAD_LOCAL attempt="+I2S(B836ArcLoadAttempts)+" err=0 epoch="+I2S(arcEpoch)+" len="+I2S(StringLength(arcRecord)))
if arcEpoch>=1500000000 and StringLength(arcRecord)<=63 then
call DzSyncData("B836AL",I2S(arcEpoch)+";"+arcRecord)
call DzSyncData("B1133LG","LOAD_SEND attempt="+I2S(B836ArcLoadAttempts)+" result=sent")
else
call DzSyncData("B1133LG","LOAD_SEND attempt="+I2S(B836ArcLoadAttempts)+" result=invalid_epoch_or_length")
endif
else
call DzSyncData("B1133LG","LOAD_LOCAL attempt="+I2S(B836ArcLoadAttempts)+" err="+I2S(arcLoadError1133))
endif
endif''',
    'load tick local telemetry')

# JASS requires functions to be defined before direct calls. Move the logging framework
# before B894IdentityInfo/InitName, while keeping B1132IsXiaoSheng available to -rlog.
log_framework_start = t.index("function B1133LogWriteFile takes nothing returns nothing")
log_framework_end = t.index("function B836ArcLocalWrite takes integer arcPid returns nothing", log_framework_start)
log_framework_block = t[log_framework_start:log_framework_end]
t = t[:log_framework_start] + t[log_framework_end:]
log_framework_anchor = t.index("function B894IdentityInfo takes nothing returns nothing")
t = t[:log_framework_anchor] + log_framework_block + t[log_framework_anchor:]

checks = {
    "log_globals": t.count("integer B1133LogSerial=0"),
    "log_append": t.count("function B1133LogAppend takes"),
    "log_file": t.count('recharge-p"+I2S(GetPlayerId(GetLocalPlayer()))+".text"'),
    "log_sync": t.count('DzTriggerRegisterSyncData(logSyncTrigger1133,"B1133LG",false)'),
    "rlog_route": t.count('if HD9=="-rlog" then'),
    "identity_log": t.count("LOAD_RX pid="),
    "gift_logs": t.count("GIFT_CHECK pid=") + t.count("GIFT_CANDIDATE pid="),
    "command_logs": t.count("CMD_RX author=") + t.count("CMD_CANDIDATE author="),
    "write_logs": t.count('DzSyncData("B1133LG","WRITE'),
    "readback_log": t.count('DzSyncData("B1133LG","READBACK'),
    "retry_log": t.count("RETRY pid="),
    "ack_logs": t.count("ACK_RX pid=") + t.count("ACK_COMMIT pid="),
    "identity_acquire_log": t.count("IDENTITY pid="),
    "load_local_logs": t.count('DzSyncData("B1133LG","LOAD_LOCAL') + t.count('DzSyncData("B1133LG","LOAD_SEND'),
}
expected = {
    "log_globals": 1, "log_append": 1, "log_file": 1, "log_sync": 1,
    "rlog_route": 1, "identity_log": 1, "gift_logs": 2,
    "command_logs": 2, "write_logs": 4, "readback_log": 1,
    "retry_log": 1, "ack_logs": 2, "identity_acquire_log": 1,
    "load_local_logs": 4,
}
if checks != expected:
    raise RuntimeError({"checks": checks, "expected": expected})
(out / "war3map.j").write_text(t, encoding="utf-8", newline="")
(out / "logging-report.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(checks, ensure_ascii=False, indent=2))
