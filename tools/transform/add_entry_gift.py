from pathlib import Path
import re, json

root = Path(r"D:\dota\DOTA69AI\rework-omg-imba")
src = root / "no-skins-key-verify" / "war3map.j"
out = root / "entry-gift-build"
out.mkdir(exist_ok=True)
t = src.read_text(encoding="utf-8")

# Per-match guard: fresh every game, shared/synchronized, never stored across games.
anchor = "boolean array B892MiaoPermanent\n"
if t.count(anchor) != 1:
    raise RuntimeError("global insertion anchor mismatch")
t = t.replace(anchor, anchor + "boolean array B1130EntryGiftGranted\n", 1)

# Dedicated persistent reward transaction for exact platform identity row 27.
anchor = "function B836ArcLoadSync takes nothing returns nothing\n"
if t.count(anchor) != 1:
    raise RuntimeError("function insertion anchor mismatch")
gift_function = """// Per-entry gift for exact platform identity 小生不怕#1701 (whitelist row 27).
// Runs once per match after archive load; the existing archive transaction owns retries.
function B1130EntryGift takes integer giftPid1130 returns nothing
local integer giftNow1130=0
local integer giftCoins1130=0
local integer giftBook1130=0
local integer giftClaw1130=0
if giftPid1130<0 or giftPid1130>=12 or B1130EntryGiftGranted[giftPid1130] or B894PlayerIdentityRow[giftPid1130]!=27 or B894PlayerIdentity[giftPid1130]!="小生不怕#1701" or not B836ArcLoaded[giftPid1130] then
return
endif
set giftNow1130=B836ArcNow(giftPid1130)
set giftCoins1130=IMinBJ(999999,B836ArcCoins[giftPid1130]+15)
set giftBook1130=IMaxBJ(B836ArcBook[giftPid1130],giftNow1130)+15*86400
set giftClaw1130=IMaxBJ(B836ArcClaw[giftPid1130],giftNow1130)+15*86400
set B1130EntryGiftGranted[giftPid1130]=true
call B836ArcBegin(giftPid1130,18,giftCoins1130,giftBook1130,giftClaw1130,B836ArcStamp[giftPid1130],B891ArcMiao[giftPid1130],0)
endfunction
"""
t = t.replace(anchor, gift_function + anchor, 1)

# Operation 18 may start immediately after archive load, before the auxiliary tip archive is ready.
old = "and arcOperation!=14 and arcOperation!=15 and arcOperation!=17) then"
new = "and arcOperation!=14 and arcOperation!=15 and arcOperation!=17 and arcOperation!=18) then"
if t.count(old) != 1:
    raise RuntimeError("B836ArcBegin exemption mismatch")
t = t.replace(old, new, 1)

# Trigger the grant only after all current archive fields have been loaded.
anchor = """set B1031RentalEpoch[arcPid]=B1031ArcField(arcRecord,9)
set B1031RewardEpoch[arcPid]=B1031ArcField(arcRecord,10)
set B1031NotifyPid=arcPid"""
replacement = """set B1031RentalEpoch[arcPid]=B1031ArcField(arcRecord,9)
set B1031RewardEpoch[arcPid]=B1031ArcField(arcRecord,10)
call B1130EntryGift(arcPid)
set B1031NotifyPid=arcPid"""
if t.count(anchor) != 1:
    raise RuntimeError("load-sync gift hook mismatch")
t = t.replace(anchor, replacement, 1)

# User-visible confirmation after the durable candidate is accepted/applied.
anchor = """elseif arcOperation==7 then
set B901QuitNotice[arcPid]=true
call X37(Player(arcPid),arcSaveStatus+"已扣除3个哦买嘎币，逃跑减次正在确认，请勿重复购买。"+B836ArcBalanceText(arcPid))"""
replacement = """elseif arcOperation==7 then
set B901QuitNotice[arcPid]=true
call X37(Player(arcPid),arcSaveStatus+"已扣除3个哦买嘎币，逃跑减次正在确认，请勿重复购买。"+B836ArcBalanceText(arcPid))
elseif arcOperation==18 then
call DisplayTimedTextToPlayer(Player(arcPid),0,0,20.,arcSaveStatus+"专属进图奖励：15个哦买嘎硬币、15天知识之书、15天寒铁钢爪。重复进图继续顺延。"+B836ArcBalanceText(arcPid))"""
if t.count(anchor) != 1:
    raise RuntimeError("ack gift branch mismatch")
t = t.replace(anchor, replacement, 1)

# Deterministic audit gates.
checks = {
    "exact_identity_count": t.count('B894PlayerIdentity[giftPid1130]!="小生不怕#1701"'),
    "row27_count": t.count("B894PlayerIdentityRow[giftPid1130]!=27"),
    "operation18_begin": t.count("call B836ArcBegin(giftPid1130,18,"),
    "operation18_ack": t.count("elseif arcOperation==18 then"),
    "load_hook": t.count("call B1130EntryGift(arcPid)"),
    "global_guard": t.count("boolean array B1130EntryGiftGranted"),
}
if any(v != 1 for v in checks.values()):
    raise RuntimeError(checks)

(out / "war3map.j").write_text(t, encoding="utf-8", newline="")
report = {
    "account": "小生不怕#1701",
    "frequency": "every_match_once",
    "coins": 15,
    "book_days": 15,
    "claw_days": 15,
    "operation": 18,
    "checks": checks,
    "script_bytes": len(t.encode("utf-8")),
}
(out / "entry-gift-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
