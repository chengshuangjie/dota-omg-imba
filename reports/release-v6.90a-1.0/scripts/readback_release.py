# -*- coding: utf-8 -*-
"""v6.90a 1.0 release readback: MPQ readback j/w3i/doo/w3e/wpm + anchor verification."""
import mpyq, io, re, hashlib, json, sys, os

MAP = r"D:\Dota_OMG\maps\release\Dota v6.90a OMG AI 1.0.w3x"
SRC_J = r"D:\Dota_OMG\src\war3map.j"
SRC_W3I = r"D:\Dota_OMG\src\war3map.w3i"
EXP_DOO = "f6ea5428531d04ac680f9d51b318be5b65e776b58bc342bb5004e32b2f0bf915"
EXP_W3E = "55962dae4021a0eca6dad6011e9a37b00459362bc062725260d6799fb8e9f593"
TITLE = "|cffff66cc抽|r|cffffff66奖|r|cff66ffff屋|r"
POS = "call SetTextTagPos(B836LotteryTitle,GetUnitX(B836ArcHut)-128.,GetUnitY(B836ArcHut),256.)"

raw = open(MAP, "rb").read()
sig = raw.find(b"MPQ\x1a")
a = mpyq.MPQArchive.__new__(mpyq.MPQArchive); a.file = io.BytesIO(raw[sig:])
a.header = a.read_header(); a.hash_table = a.read_table("hash"); a.block_table = a.read_table("block")
j = a.read_file("war3map.j"); w3i = a.read_file("war3map.w3i")
doo = a.read_file("war3map.doo"); w3e = a.read_file("war3map.w3e"); wpm = a.read_file("war3map.wpm")
srcj = open(SRC_J, "rb").read(); srcw3i = open(SRC_W3I, "rb").read()

r = {}
r["map_sha256"] = hashlib.sha256(raw).hexdigest().upper(); r["map_bytes"] = len(raw)
r["packed_j_equals_src"] = (j == srcj); r["packed_j_bytes"] = len(j)
r["packed_w3i_equals_src"] = (w3i == srcw3i)
r["doo_match_t2"] = hashlib.sha256(doo).hexdigest() == EXP_DOO
r["w3e_match_t5"] = hashlib.sha256(w3e).hexdigest() == EXP_W3E
r["doo_sha256"] = hashlib.sha256(doo).hexdigest().upper(); r["doo_bytes"] = len(doo)
r["w3e_sha256"] = hashlib.sha256(w3e).hexdigest().upper(); r["w3e_bytes"] = len(w3e)
r["wpm_sha256"] = hashlib.sha256(wpm).hexdigest().upper(); r["wpm_bytes"] = len(wpm)
r["w3i_slotA"] = w3i[12:36].decode("ascii"); r["w3i_slotB"] = w3i[234:258].decode("ascii")
r["w3i_slotA_ok"] = w3i[12:36] == b"v6.90a-OMG-AI-1.0".ljust(24, b" ")
r["w3i_slotB_ok"] = w3i[234:258] == b"Dota v6.90a OMG AI 1.0".ljust(24, b" ")

t = j.decode("utf-8", errors="strict")
r["fffd"] = t.count("\ufffd")
r["title_x1"] = t.count(TITLE) == 1
r["create_once"] = t.count("B836LotteryTitle=CreateTextTag()") == 1
r["pos128_256_exact"] = POS in t
r["pos96_256_gone"] = "GetUnitX(B836ArcHut)-96.,GetUnitY(B836ArcHut),256.)" not in t
r["pos144_gone"] = "GetUnitY(B836ArcHut),144.)" not in t
r["pos64_gone"] = "GetUnitY(B836ArcHut),64.)" not in t
r["no_posunit"] = "SetTextTagPosUnit(B836LotteryTitle" not in t
r["permanent"] = "SetTextTagPermanent(B836LotteryTitle,true)" in t
r["lifespan0"] = "SetTextTagLifespan(B836LotteryTitle,0)" in t
r["fadepoint0"] = "SetTextTagFadepoint(B836LotteryTitle,0)" in t
r["visible"] = "SetTextTagVisibility(B836LotteryTitle,true)" in t
r["xomg_v690a"] = 'XOMG_VERSION="v6.90a-OMG-AI-1.0"' in t
r["setmapname_v690a"] = 'SetMapName("Dota v6.90a OMG AI 1.0")' in t
r["no_t10_xomg"] = 'XOMG_VERSION="v6.9-ART683-T10"' not in t
r["no_t10_setmapname"] = 'SetMapName("6.9 OMG IMBA ART683-T10")' not in t
r["nas6_frozen"] = bool(re.search(r"CreateUnit\(Player\(PLAYER_NEUTRAL_PASSIVE\),'nAS6',-5728\.,-6816\.,270\.\)", t))
i0 = t.index("// ART683-T5: runtime pure-visual"); i1 = t.index("ART683-T5] 近卫已换模")
seg = t[i0:i1]
r["t5_dzsetmodel"] = seg.count("DzSetUnitModel("); r["t5_setunitscale"] = seg.count("SetUnitScale(")
r["t4_tree"] = ("DzSetUnitModel(JW_JD," in t and "TreeofLife" in t and "SetUnitScale(JW_JD,1.8" in t)
r["buttons"] = all(b in t for b in ["幸运大抽奖（免费1次）", "1000抽属性（无限次）", "梭哈抽属性"])
r["lotopen_send"] = t.count('DzSyncData("LOTOPEN","")') == 1
r["lotopen_reg"] = t.count('DzTriggerRegisterSyncData(lotOpenTrigger,"LOTOPEN",false)') == 1
r["wpm_eq_fissure"] = hashlib.sha256(wpm).hexdigest() == "61ccf7597378fde26858b061ae174082543fbb25e07d0e4e3c91cb035a1f11a9"

ok = all([r["packed_j_equals_src"], r["packed_w3i_equals_src"], r["doo_match_t2"], r["w3e_match_t5"],
          r["pos128_256_exact"], r["pos96_256_gone"], r["pos144_gone"], r["pos64_gone"], r["no_posunit"],
          r["xomg_v690a"], r["setmapname_v690a"], r["no_t10_xomg"], r["no_t10_setmapname"],
          r["nas6_frozen"], r["t5_dzsetmodel"] == 47, r["t5_setunitscale"] == 47, r["t4_tree"],
          r["buttons"], r["lotopen_send"], r["lotopen_reg"], r["wpm_eq_fissure"],
          r["fffd"] == 0, r["w3i_slotA_ok"], r["w3i_slotB_ok"]])
r["ALL_PASS"] = ok
out = r"D:\Dota_OMG\reports\release-v6.90a-1.0\evidence\readback-release.json"
json.dump(r, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps(r, ensure_ascii=False, indent=2))
sys.exit(0 if ok else 1)
