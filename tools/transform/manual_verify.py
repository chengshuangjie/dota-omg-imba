# -*- coding: utf-8 -*-
"""Manual 7-file verify + regression checks."""
import subprocess, os, tempfile, hashlib, json, time, glob

ROOT = r"D:\dota\DOTA-OMG-IMBA-轻量化"
MPQ = r"D:\dota\DOTAOMGAY\compiler\mpqeditorhhb\MPQEditor.exe"
MAP = os.path.join(ROOT, "maps", "build", "DOTA-OMG-IMBA-轻量化开发版.w3x")

checks = [
    ("war3map.j", os.path.join(ROOT, "src", "war3map.j")),
    ("war3map.imp", os.path.join(ROOT, "src", "war3map.imp")),
    ("Units\\UnitAbilities.slk", os.path.join(ROOT, "src", "data", "Units", "UnitAbilities.slk")),
    ("Units\\UnitBalance.slk", os.path.join(ROOT, "src", "data", "Units", "UnitBalance.slk")),
    ("Units\\UnitData.slk", os.path.join(ROOT, "src", "data", "Units", "UnitData.slk")),
    ("Units\\UnitUI.slk", os.path.join(ROOT, "src", "data", "Units", "UnitUI.slk")),
    ("Units\\UnitWeapons.slk", os.path.join(ROOT, "src", "data", "Units", "UnitWeapons.slk")),
]

def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

vdir = tempfile.mkdtemp(prefix="dota_verify_")
results = []
for archive, expected in checks:
    # extract
    subprocess.run([MPQ, "extract", MAP, archive, vdir, "/fp"],
                   capture_output=True, timeout=30)
    time.sleep(1.5)
    local = os.path.join(vdir, archive.lower())
    # Also try original case
    if not os.path.exists(local):
        local = os.path.join(vdir, archive)
    if not os.path.exists(local):
        # search recursively
        found = glob.glob(os.path.join(vdir, "**", os.path.basename(archive)), recursive=True)
        if found:
            local = found[0]
    if not os.path.exists(local):
        results.append((archive, "MISSING", "MISSING", False))
        continue
    actual = sha256(local)
    exp = sha256(expected)
    match = actual == exp
    results.append((archive, exp[:16], actual[:16], match))
    print(f"  {'OK' if match else 'FAIL'} {archive}: exp={exp[:16]} act={actual[:16]}")

# Regression checks on war3map.j
script_text = open(os.path.join(vdir, "war3map.j"), encoding="utf-8").read()
skinPaths = script_text.lower().count("skins\\")
defenseImpl = len([l for l in script_text.splitlines() if l.startswith("function KKDefense_") and not l.startswith("function KKDefense_IsWaveType")])
wheelImpl = len([l for l in script_text.splitlines() if l.startswith("function B1004") and not l.startswith("function B1004ControlUnit")])
recharge = len([l for l in script_text.splitlines() if l.startswith("function B1131Recharge takes")])
logger = len([l for l in script_text.splitlines() if l.startswith("function B1133LogAppend takes")])

# XOMG1 / brand / lottery / hero rename checks
xomg1 = "XOMG1" in script_text or "xomg1" in script_text.lower()
# IMBA_POWER count
imba_count = script_text.count("IMBA_POWER")
imba_mult_count = script_text.count("imbaMult")

print(f"\n--- Regression ---")
print(f"skinPaths (should be 0): {skinPaths}")
print(f"KKDefense impl (should be 0): {defenseImpl}")
print(f"B1004 wheel impl (should be 0): {wheelImpl}")
print(f"B1131Recharge (should be 1): {recharge}")
print(f"B1133LogAppend (should be 1): {logger}")
print(f"IMBA_POWER references: {imba_count}")
print(f"imbaMult references: {imba_mult_count}")

all_match = all(r[3] for r in results)
passed = all_match and skinPaths == 0 and defenseImpl == 0 and wheelImpl == 0 and recharge == 1 and logger == 1
print(f"\nOVERALL: {'PASS' if passed else 'FAIL'}")
