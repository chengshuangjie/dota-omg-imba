from pathlib import Path
import json

root = Path(r"D:\dota\DOTA69AI\rework-omg-imba")
src = root / "entry-gift-verify-final" / "war3map.j"
out = root / "entry-gift-fix-build"
out.mkdir(exist_ok=True)
t = src.read_text(encoding="utf-8")

old = "function InitName takes nothing returns nothing\nlocal integer b894Pid=1"
new = "function InitName takes nothing returns nothing\nlocal integer b894Pid=0"
if t.count(old) != 1:
    raise RuntimeError("InitName slot-zero fix anchor mismatch")
t = t.replace(old, new, 1)

# Immediate diagnostic confirmation for the exact owner account.
anchor = """set B894PlayerIdentityRow[b894Pid]=b894Row
if b894Row>0 then"""
replacement = """set B894PlayerIdentityRow[b894Pid]=b894Row
if b894Row==27 and B894PlayerIdentity[b894Pid]=="小生不怕#1701" then
call DisplayTimedTextToPlayer(b894Player,0,0,20.,"已识别专属账号：小生不怕#1701。存档读取成功后将发放15币、15天知识之书和15天寒铁钢爪。")
endif
if b894Row>0 then"""
if t.count(anchor) != 1:
    raise RuntimeError("identity diagnostic anchor mismatch")
t = t.replace(anchor, replacement, 1)

checks = {
    "pid_starts_zero": t.count("local integer b894Pid=0"),
    "pid_starts_one": t.count("function InitName takes nothing returns nothing\nlocal integer b894Pid=1"),
    "identity_notice": t.count("已识别专属账号：小生不怕#1701"),
    "gift_call": t.count("call B1130EntryGift(arcPid)"),
    "exact_account": t.count('B894PlayerIdentity[giftPid1130]!="小生不怕#1701"'),
}
if checks != {"pid_starts_zero": 1, "pid_starts_one": 0, "identity_notice": 1, "gift_call": 1, "exact_account": 1}:
    raise RuntimeError(checks)
(out / "war3map.j").write_text(t, encoding="utf-8", newline="")
(out / "slot0-fix-report.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(checks, ensure_ascii=False, indent=2))
