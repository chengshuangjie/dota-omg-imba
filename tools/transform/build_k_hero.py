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


# ---- KA ability blocks (native effects zeroed) ----
def ka_passive(code, y):
    return [
        'C;X1;Y%d;K"%s"' % (y, code),
        'C;X2;K"Aamk"',
        'C;X15;K1',
        'C;X24;K0', 'C;X25;K0', 'C;X26;K0', 'C;X27;K0',
        'C;X28;K0', 'C;X29;K0', 'C;X30;K0', 'C;X31;K0',
        'C;X32;K0', 'C;X33;K0', 'C;X34;K0', 'C;X35;K0',
        'C;X72;K4',
        'C;X73;K2',
        'C;X75;K1',
        'C;X80;K"_"', 'C;X81;K"_"', 'C;X82;K"_"', 'C;X83;K"_"',
    ]


def ka_channel(code, y, cd, levels):
    # Clone the proven in-map no-target instant stub A0OT (base ANcl, target "_",
    # dispatched on spell event by GetSpellAbilityId in shipped jass; no native
    # damage/buff/duration). Use unique channel base orders so both active skills
    # coexist on the same hero command card.
    base_order = "roar" if code == "KA03" else "chemicalrage"
    rows = [
        'C;X1;Y%d;K"%s"' % (y, code),
        'C;X2;K"ANcl"',
        'C;X15;K1',
        # A0OT structural channel fields (cosmetic, no gameplay effect)
        'C;X32;K1',
        'C;X36;K0.98',
        'C;X44;K"%s"' % base_order,
        'C;X73;K2' if levels == 4 else 'C;X73;K5',
        'C;X74;K5',
        'C;X75;K1' if levels == 4 else 'C;X75;K6',
    ]
    # CD per level
    for k, v in enumerate(cd):
        rows.append('C;X%d;K%s' % (16 + k, v))
    # mana cost 0 for every level
    for k in range(4):
        rows.append('C;X%d;K0' % (20 + k))
    # native DataA/DataB/duration/buff explicitly zeroed (A0OT carries none)
    rows += ['C;X24;K0', 'C;X28;K0', 'C;X60;K0', 'C;X68;K0']
    rows += ['C;X72;K%d' % levels]
    # no-target (click-cast); script operates on caster
    rows += ['C;X80;K"_"', 'C;X81;K"_"', 'C;X82;K"_"', 'C;X83;K"_"']
    return rows


def make_ka_blocks(start_y):
    return (
        ka_passive("KA01", start_y),
        ka_passive("KA02", start_y + 1),
        ka_channel("KA03", start_y + 2, ["10.0", "10.0", "10.0", "10.0"], 4),
        ka_channel("KA04", start_y + 3, ["80.0", "65.0", "50.0"], 3),
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
