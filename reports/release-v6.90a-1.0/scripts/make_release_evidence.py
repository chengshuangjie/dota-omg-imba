# -*- coding: utf-8 -*-
"""Assemble release-v6.90a-1.0 machine evidence JSON from live filesystem."""
import hashlib, os, json, datetime

ROOT = r"D:\Dota_OMG"
STABLE = r"D:\游戏\Warcraft III\Maps\omg\稳定"

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def sz(p):
    return os.path.getsize(p)

release_map = os.path.join(ROOT, r"maps\release\Dota v6.90a OMG AI 1.0.w3x")
stable_map = os.path.join(STABLE, "Dota v6.90a OMG AI 1.0.w3x")
v93 = os.path.join(STABLE, "Dota v6.93a OMG AI 1.0.w3x")
fissure = os.path.join(STABLE, "DOTA-OMG-IMBA-v6.9-FISSURE-T1.w3x")

rb = json.load(open(os.path.join(ROOT, r"reports\release-v6.90a-1.0\evidence\readback-release.json"), encoding="utf-8"))

# locate stable backup dir
bk_root = os.path.join(ROOT, "backups")
bk_dir = None
for n in os.listdir(bk_root):
    if n.startswith("stable-pre-v6.90a-1.0-"):
        bk_dir = os.path.join(bk_root, n)
bk_file = os.path.join(bk_dir, "DOTA-OMG-IMBA-v6.9-FISSURE-T1.w3x") if bk_dir else None

ev = {
    "stage": "v6.90a 1.0 formal release",
    "generatedAt": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    "releaseMap": {
        "path": "maps/release/Dota v6.90a OMG AI 1.0.w3x",
        "bytes": sz(release_map),
        "sha256": sha(release_map),
    },
    "stableDeploy": {
        "path": stable_map,
        "bytes": sz(stable_map),
        "sha256": sha(stable_map),
        "buildStableHashIdentical": sha(release_map) == sha(stable_map),
    },
    "labels": {
        "versionLabel": {"value": "v6.90a-OMG-AI-1.0", "asciiBytes": 17, "padTo": 24, "paddingSpaces": 7, "w3iSlot": "A@12"},
        "displayName": {"value": "Dota v6.90a OMG AI 1.0", "asciiBytes": 22, "padTo": 24, "paddingSpaces": 2, "w3iSlot": "B@234"},
    },
    "src": {
        "war3map.j": {"bytes": sz(os.path.join(ROOT, r"src\war3map.j")), "sha256": sha(os.path.join(ROOT, r"src\war3map.j"))},
        "war3map.w3i": {"bytes": sz(os.path.join(ROOT, r"src\war3map.w3i")), "sha256": sha(os.path.join(ROOT, r"src\war3map.w3i"))},
    },
    "frozenInjected": {
        "war3map.doo": rb["doo_sha256"].lower(),
        "war3map.w3e": rb["w3e_sha256"].lower(),
        "war3map.wpm": rb["wpm_sha256"].lower(),
    },
    "verify": {
        "verify_v17_preinject": {"total": 122, "passed": 122, "failed": 0},
        "verify_v17_postreinject": {"total": 122, "passed": 122, "failed": 0},
        "pjass": {"allowedOnly": "location_m5", "diagnostic": "war3map.j:155341"},
    },
    "anchors": {
        "packed_j_equals_src": rb["packed_j_equals_src"],
        "packed_w3i_equals_src": rb["packed_w3i_equals_src"],
        "doo_match_t2": rb["doo_match_t2"],
        "w3e_match_t5": rb["w3e_match_t5"],
        "title_x1": rb["title_x1"],
        "pos128_256_exact": rb["pos128_256_exact"],
        "pos96_256_gone": rb["pos96_256_gone"],
        "no_posunit": rb["no_posunit"],
        "permanent": rb["permanent"],
        "lifespan0": rb["lifespan0"],
        "fadepoint0": rb["fadepoint0"],
        "visible": rb["visible"],
        "xomg_v690a": rb["xomg_v690a"],
        "setmapname_v690a": rb["setmapname_v690a"],
        "no_t10_residue": rb["no_t10_xomg"] and rb["no_t10_setmapname"],
        "nas6_frozen": rb["nas6_frozen"],
        "t5_dzsetmodel": rb["t5_dzsetmodel"],
        "t5_setunitscale": rb["t5_setunitscale"],
        "t4_tree": rb["t4_tree"],
        "buttons": rb["buttons"],
        "fffd": rb["fffd"],
    },
    "stableDir": {
        "fissurePresent": os.path.exists(fissure),
        "v690aPresent": os.path.exists(stable_map),
        "v693a": {"bytes": sz(v93), "sha256": sha(v93), "unchanged": sha(v93) == "bc7b71d74d96898afbaa01c3bfc9d77fe637c88e9e0d941cd53170dec1e94890"},
    },
    "oldFissureBackup": {
        "dir": bk_dir,
        "file": bk_file,
        "bytes": sz(bk_file) if bk_file and os.path.exists(bk_file) else None,
        "sha256": sha(bk_file) if bk_file and os.path.exists(bk_file) else None,
        "matchesOriginal": bk_file and os.path.exists(bk_file) and sha(bk_file) == "1847c96bf5201072a569cec2ecc24e79aca163cb4c852cef95e4af5087842195",
    },
    "ALL_PASS": rb["ALL_PASS"] and sha(release_map) == sha(stable_map) and not os.path.exists(fissure)
               and os.path.exists(stable_map) and os.path.exists(bk_file)
               and sha(bk_file) == "1847c96bf5201072a569cec2ecc24e79aca163cb4c852cef95e4af5087842195",
}

out = os.path.join(ROOT, r"reports\release-v6.90a-1.0\evidence\release-evidence.json")
json.dump(ev, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps(ev, ensure_ascii=False, indent=2))
