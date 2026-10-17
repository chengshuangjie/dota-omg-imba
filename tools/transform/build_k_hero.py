# -*- coding: utf-8 -*-
"""
v1.4-K reproducible SLK builder (root-cause generator, idempotent).

Responsibilities:
1. Five Unit SLKs: relocate the H0K0 block to the first contiguous row after
   the legacy last object, immediately BEFORE the standalone terminating `E`.
2. AbilityData.slk: (re)build KA01..KA04 in the first four contiguous rows
   after the legacy last ability, with native effects zeroed:
   - KA01/KA02 passive level markers (Aamk) with DataA-D = 0 (no native stat bonus).
   - KA03/KA04 pure-channel self instant (Achl), native duration/buff/movespeed
     fields zeroed; CD/levels/target preserved; mana cost 0.

Preserves per-file charset (UnitUI=GBK, rest UTF-8/ASCII), BOM-less, and the
original line ending (Unit SLKs=LF, AbilityData=CRLF).

Run from repo root:  python tools/transform/build_k_hero.py
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UNITS = os.path.join(ROOT, "src", "data", "Units")

# file -> (encoding, line_ending)
UNIT_FILES = {
    "UnitAbilities.slk": ("utf-8", "\n"),
    "UnitData.slk": ("utf-8", "\n"),
    "UnitBalance.slk": ("utf-8", "\n"),
    "UnitWeapons.slk": ("utf-8", "\n"),
    "UnitUI.slk": ("gbk", "\n"),
}
ABILITY_FILE = "AbilityData.slk"
ABILITY_ENC = "utf-8"
ABILITY_EOL = "\r\n"

ALIAS_RE = re.compile(r'^C;X1;Y\d+;K"')
# SLK dimension/boundary record: B;X<col>;Y<row>;D<type> — preserve X and D, only Y may rise.
B_RE = re.compile(r'^B;X(\d+);Y(\d+);(D\d+)$')
# Any object row carrying an explicit Y coordinate (alias rows set the row).
ROW_Y_RE = re.compile(r'C;X\d+;Y(\d+);')


def read(path, enc):
    with open(path, "rb") as f:
        raw = f.read()
    return raw.decode(enc)


def write(path, text, enc, eol):
    # normalize to target eol, drop any stray BOM
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\n", eol)
    data = text.encode(enc)
    with open(path, "wb") as f:
        f.write(data)


def split_lines(text):
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def find_e_index(lines):
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == "E":
            return i
    raise SystemExit("terminating E record not found")


def extract_block(lines, alias_code):
    """Return (block_lines, remaining_lines) for the block whose alias == alias_code."""
    start = None
    for i, ln in enumerate(lines):
        if ALIAS_RE.match(ln) and ('K"%s"' % alias_code) in ln:
            start = i
            break
    if start is None:
        return [], lines
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if ALIAS_RE.match(lines[j]) or lines[j].strip() == "E":
            end = j
            break
    block = lines[start:end]
    # trim trailing blank lines inside block
    while block and block[-1].strip() == "":
        block.pop()
    remaining = lines[:start] + lines[end:]
    # collapse a double blank left behind
    while len(remaining) >= 2 and remaining[-1].strip() == "" and remaining[-2].strip() == "":
        remaining.pop()
    return block, remaining


def relocate_unit_block(fname):
    path = os.path.join(UNITS, fname)
    if not os.path.exists(path):
        return
    enc, eol = UNIT_FILES[fname]
    lines = split_lines(read(path, enc))
    block, lines = extract_block(lines, "H0K0")
    if not block:
        return  # v1.3 / clean tree: nothing to relocate
    # Warcraft III 1.24's SLK reader is not safe with large sparse row jumps.
    # Renumber H0K0 to exactly one row after the last legacy object.
    legacy_max_y = 0
    for ln in lines:
        m = ROW_Y_RE.search(ln)
        if m:
            legacy_max_y = max(legacy_max_y, int(m.group(1)))
    hero_y = legacy_max_y + 1
    block[0] = re.sub(r';Y\d+;', ';Y%d;' % hero_y, block[0], count=1)
    e = find_e_index(lines)
    new = lines[:e] + block + [""] + lines[e:]
    write(path, "\n".join(new), enc, eol)
    print("relocated H0K0 -> contiguous Y%d before E in %s (%d block lines)" % (hero_y, fname, len(block)))


def sync_unit_boundary_b(fname):
    """Set B.Y to the actual maximum object row (including H0K0).

    The old generator placed H0K0 at sparse Y9001 and then expanded B.Y to
    9001. Warcraft III 1.24 can fail while loading such sparse custom SLKs.
    After contiguous renumbering this function intentionally allows B.Y to
    decrease back to the real used row; X and D are preserved.
    """
    path = os.path.join(UNITS, fname)
    if not os.path.exists(path):
        return
    enc, eol = UNIT_FILES[fname]
    lines = split_lines(read(path, enc))
    max_y = 0
    for ln in lines:
        m = ROW_Y_RE.search(ln)
        if m:
            max_y = max(max_y, int(m.group(1)))
    changed = False
    out = []
    for ln in lines:
        m = B_RE.match(ln)
        if m:
            x, y, d = m.group(1), int(m.group(2)), m.group(3)
            if max_y != y:
                changed = True
                ln = 'B;X%s;Y%d;%s' % (x, max_y, d)
        out.append(ln)
    if changed:
        write(path, "\n".join(out), enc, eol)
        print("synced B boundary Y->%d in %s (X/D preserved)" % (max_y, fname))


# ---- KA ability blocks (v1.7-K-VisualSkillFix: clone proven in-map hero templates) ----
# Each KA object copies a real, in-game learnable hero template's baseCode, hero
# flag (X15), button-learn fields (X7/X8/X9), levels (X72), levelSkip (X73) and
# reqLevel (X75). Native gameplay fields are zeroed; the shipped jass KK_ module
# drives all K gameplay numbers and modules unchanged.
#
# KA01 <- AHad (Devotion Aura, proven paladin hero passive, reqLevel1)
# KA02 <- AEev (Evasion, proven demon-hunter hero passive, reqLevel1)
# KA03 <- AHds (Divine Shield, proven paladin no-target self active, reqLevel1)
# KA04 <- ANdo (Doom, proven pit-lord hero ultimate, reqLevel6, levelSkip5)
def ka01_block(y):
    return [
        'C;X1;Y%d;K"KA01"' % y,
        'C;X2;K"AHad"',
        'C;X7;K"BHad"', 'C;X8;K"BHad"', 'C;X9;K"BHad"',
        'C;X15;K1',
        # native devotion armor/aura zeroed; jass drives kill-agility
        'C;X24;K0', 'C;X25;K0', 'C;X26;K0',
        'C;X61;K0', 'C;X62;K0', 'C;X69;K0', 'C;X70;K0',
        'C;X72;K4',
        'C;X75;K1',
        'C;X80;K"_"', 'C;X81;K"_"', 'C;X82;K"_"', 'C;X83;K"_"',
    ]


def ka02_block(y):
    return [
        'C;X1;Y%d;K"KA02"' % y,
        'C;X2;K"AEev"',
        'C;X15;K1',
        # native evasion dodge zeroed; jass drives 20% extra physical
        'C;X24;K0', 'C;X25;K0', 'C;X26;K0', 'C;X27;K0',
        'C;X72;K4',
        'C;X75;K1',
        'C;X80;K"_"', 'C;X81;K"_"', 'C;X82;K"_"', 'C;X83;K"_"',
    ]


def ka03_block(y):
    # AHds Divine Shield clone: no-target self active; native invulnerability
    # duration zeroed. CD 10s / cost 0 preserved from the K skill; jass KK_SK3
    # delivers the 800-radius magic AOE on spell cast by ability id.
    return [
        'C;X1;Y%d;K"KA03"' % y,
        'C;X2;K"AHds"',
        'C;X7;K"BHds"', 'C;X8;K"BHds"', 'C;X9;K"BHds"',
        'C;X15;K1',
        'C;X16;K10.0', 'C;X17;K10.0', 'C;X18;K10.0', 'C;X19;K10.0',
        'C;X20;K0', 'C;X21;K0', 'C;X22;K0', 'C;X23;K0',
        # native invulnerability duration (hero/ordinary) zeroed
        'C;X60;K0', 'C;X61;K0', 'C;X62;K0',
        'C;X68;K0', 'C;X69;K0', 'C;X70;K0',
        'C;X72;K4',
        'C;X75;K1',
        'C;X80;K"invu,vuln"', 'C;X81;K"invu,vuln"', 'C;X82;K"invu,vuln"',
        'C;X83;K"_"',
    ]


def ka04_block(y):
    # ANdo Doom clone: hero ultimate 6/11/16 (levelSkip5, reqLevel6). Native
    # doom damage/range/area/duration zeroed; jass KK_SK4 drives the temporary
    # S/2S/3S agility buff. Deliberately NOT chemicalrage: no model swap,
    # no vertex color, no blue filter, no ZCRG, no alchemist regen.
    return [
        'C;X1;Y%d;K"KA04"' % y,
        'C;X2;K"ANdo"',
        'C;X7;K"BNdo"', 'C;X8;K"BNdo"', 'C;X9;K"BNdo"',
        'C;X15;K1',
        'C;X16;K80.0', 'C;X17;K65.0', 'C;X18;K50.0',
        'C;X20;K0', 'C;X21;K0', 'C;X22;K0',
        # native doom damage / range / area / duration zeroed
        'C;X24;K0', 'C;X25;K0', 'C;X26;K0',
        'C;X32;K0', 'C;X33;K0', 'C;X34;K0',
        'C;X60;K0', 'C;X61;K0', 'C;X62;K0',
        'C;X68;K0', 'C;X69;K0', 'C;X70;K0',
        'C;X76;K0', 'C;X77;K0', 'C;X78;K0',
        'C;X72;K3',
        'C;X73;K5',
        'C;X75;K6',
        'C;X80;K"_"', 'C;X81;K"_"', 'C;X82;K"_"', 'C;X83;K"_"',
    ]


def make_ka_blocks(start_y):
    return (
        ka01_block(start_y),
        ka02_block(start_y + 1),
        ka03_block(start_y + 2),
        ka04_block(start_y + 3),
    )


def rebuild_ability_data():
    path = os.path.join(UNITS, ABILITY_FILE)
    if not os.path.exists(path):
        return  # v1.3 / clean tree has no maintained AbilityData.slk
    lines = split_lines(read(path, ABILITY_ENC))
    # drop any existing KA01..04 blocks (idempotent)
    keep = []
    skip = False
    for ln in lines:
        if ALIAS_RE.match(ln) and re.search(r'K"KA0[1-4]"', ln):
            skip = True
            continue
        if skip and (ALIAS_RE.match(ln) or ln.strip() == "E"):
            skip = False
        if skip:
            continue
        keep.append(ln)
    e = find_e_index(keep)
    legacy_max_y = 0
    for ln in keep:
        m = ROW_Y_RE.search(ln)
        if m:
            legacy_max_y = max(legacy_max_y, int(m.group(1)))
    start_y = legacy_max_y + 1
    block = []
    for b in make_ka_blocks(start_y):
        block += b
        block.append("")
    block = block[:-1]  # drop trailing blank
    new = keep[:e] + block + [""] + keep[e:]
    # AbilityData B.Y must match the real contiguous maximum row, not sparse 9004.
    out = []
    final_max_y = start_y + 3
    for ln in new:
        m = B_RE.match(ln)
        if m:
            ln = 'B;X%s;Y%d;%s' % (m.group(1), final_max_y, m.group(3))
        out.append(ln)
    write(path, "\n".join(out), ABILITY_ENC, ABILITY_EOL)
    print("rebuilt KA01..04 at contiguous Y%d..Y%d in AbilityData.slk" % (start_y, final_max_y))


def main():
    for fname in UNIT_FILES:
        relocate_unit_block(fname)
        sync_unit_boundary_b(fname)
    rebuild_ability_data()
    print("done")


if __name__ == "__main__":
    main()
