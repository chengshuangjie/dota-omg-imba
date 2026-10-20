# -*- coding: utf-8 -*-
"""v6.90a 1.0 release: bump XOMG_VERSION / SetMapName from ART683-T10 labels.
Strict utf-8 no BOM, LF-only, strict self-check BEFORE any write. Everything else frozen."""
import re, sys, hashlib
from collections import Counter

SRC = r"D:\Dota_OMG\src\war3map.j"
OLD_XOMG = 'constant string XOMG_VERSION="v6.9-ART683-T10"'
NEW_XOMG = 'constant string XOMG_VERSION="v6.90a-OMG-AI-1.0"'
OLD_SMN = 'call SetMapName("6.9 OMG IMBA ART683-T10")'
NEW_SMN = 'call SetMapName("Dota v6.90a OMG AI 1.0")'
TITLE = "|cffff66cc抽|r|cffffff66奖|r|cff66ffff屋|r"
POS = "call SetTextTagPos(B836LotteryTitle,GetUnitX(B836ArcHut)-128.,GetUnitY(B836ArcHut),256.)"

def fail(m):
    print("SELF-CHECK FAIL:", m); sys.exit(1)

raw = open(SRC, "rb").read()
if raw[:3] == b"\xef\xbb\xbf": fail("BOM")
text = raw.decode("utf-8", errors="strict")
if "\ufffd" in text: fail("FFFD")
if raw.count(b"\r\n") != 0: fail("CRLF")
lines = text.split("\n")

# pre-write: exactly one old literal each
xomg = [i for i, ln in enumerate(lines) if OLD_XOMG in ln]
smn = [i for i, ln in enumerate(lines) if OLD_SMN in ln]
if len(xomg) != 1: fail("old XOMG count=%d" % len(xomg))
if len(smn) != 1: fail("old SetMapName count=%d" % len(smn))
if NEW_XOMG in text: fail("new XOMG already present")
if NEW_SMN in text: fail("new SetMapName already present")

# frozen anchors must survive
if not re.search(r"CreateUnit\(Player\(PLAYER_NEUTRAL_PASSIVE\),'nAS6',-5728\.,-6816\.,270\.\)", text): fail("nAS6 frozen missing")
if POS not in text: fail("-128/256 pos missing")
if "GetUnitX(B836ArcHut)-96.,GetUnitY(B836ArcHut),256.)" in text: fail("-96/256 residue")
if "SetTextTagPosUnit(B836LotteryTitle" in text: fail("PosUnit residue")
if text.count(TITLE) != 1: fail("title text count=%d" % text.count(TITLE))
if text.count("B836LotteryTitle=CreateTextTag()") != 1: fail("create-once count")
i0 = text.index("// ART683-T5: runtime pure-visual"); i1 = text.index("ART683-T5] 近卫已换模")
seg = text[i0:i1]
if seg.count("DzSetUnitModel(") != 47: fail("T5 DzSetUnitModel=%d" % seg.count("DzSetUnitModel("))
if seg.count("SetUnitScale(") != 47: fail("T5 SetUnitScale=%d" % seg.count("SetUnitScale("))
if not ("DzSetUnitModel(JW_JD," in text and "TreeofLife" in text and "SetUnitScale(JW_JD,1.8" in text): fail("T4 tree missing")
for b in ["幸运大抽奖（免费1次）", "1000抽属性（无限次）", "梭哈抽属性"]:
    if b not in text: fail("button missing " + b)
print("STATIC SELF-CHECK PASS")

lines[xomg[0]] = lines[xomg[0]].replace(OLD_XOMG, NEW_XOMG)
lines[smn[0]] = lines[smn[0]].replace(OLD_SMN, NEW_SMN)

new_text = "\n".join(lines)
new_raw = new_text.encode("utf-8", errors="strict")
if new_raw[:3] == b"\xef\xbb\xbf": fail("BOM after")
if new_raw.count(b"\r\n") != 0: fail("CRLF after")
co, cn = Counter(text.split("\n")), Counter(lines)
print("POST DIFF added=%d removed=%d" % (len(list((cn-co).elements())), len(list((co-cn).elements()))))

final = new_raw.decode("utf-8", errors="strict")
assert len(re.findall(r'constant string XOMG_VERSION="v6\.90a-OMG-AI-1\.0"', final)) == 1
assert len(re.findall(r'SetMapName\("Dota v6\.90a OMG AI 1\.0"\)', final)) == 1
assert OLD_XOMG not in final and OLD_SMN not in final
assert POS in final and TITLE in final

open(SRC, "wb").write(new_raw)
for i, ln in enumerate(final.split("\n"), 1):
    if NEW_XOMG in ln: print("new XOMG line", i)
    if NEW_SMN in ln: print("new SetMapName line", i)
print("written bytes", len(new_raw), "sha256", hashlib.sha256(new_raw).hexdigest().upper())
