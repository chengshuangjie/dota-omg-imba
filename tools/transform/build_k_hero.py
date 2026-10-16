# -*- coding: utf-8 -*-
"""
v1.4-K reproducible SLK builder (root-cause generator, idempotent).

Responsibilities:
1. Five Unit SLKs: relocate the H0K0 Y9001 block to immediately BEFORE the
   standalone terminating `E` record; E stays the last non-empty line.
2. AbilityData.slk: (re)build KA01..KA04 rows with native effects zeroed:
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
    e = find_e_index(lines)
    # insert block right before E; keep a blank separator if present before E
    new = lines[:e] + block + [""] + lines[e:]
    write(path, "\n".join(new), enc, eol)
    print("relocated H0K0 -> before E in %s (%d block lines)" % (fname, len(block)))


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
        'C;X75;K1',
        'C;X80;K"_"', 'C;X81;K"_"', 'C;X82;K"_"', 'C;X83;K"_"',
    ]


def ka_channel(code, y, cd, levels):
    # Clone the proven in-map no-target instant stub A0OT (base ANcl, target "_",
    # dispatched on spell event by GetSpellAbilityId in shipped jass; no native
    # damage/buff/duration). Keep its structural channel fields, then clear any
    # native Data/DataB/duration/buff explicitly; mana cost 0; CD/levels per spec.
    rows = [
        'C;X1;Y%d;K"%s"' % (y, code),
        'C;X2;K"ANcl"',
        'C;X15;K1',
        # A0OT structural channel fields (cosmetic, no gameplay effect)
        'C;X32;K1',
        'C;X36;K0.98',
        'C;X73;K1',
        'C;X74;K5',
        'C;X75;K1',
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


KA_BLOCKS = (
    ka_passive("KA01", 9001),
    ka_passive("KA02", 9002),
    ka_channel("KA03", 9003, ["10.0", "10.0", "10.0", "10.0"], 4),
    ka_channel("KA04", 9004, ["80.0", "65.0", "50.0"], 3),
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
    block = []
    for b in KA_BLOCKS:
        block += b
        block.append("")
    block = block[:-1]  # drop trailing blank
    new = keep[:e] + block + [""] + keep[e:]
    write(path, "\n".join(new), ABILITY_ENC, ABILITY_EOL)
    print("rebuilt KA01..04 (passive zeroed; KA03/04 clone A0OT ANcl no-target, native zeroed) in AbilityData.slk")


def main():
    for fname in UNIT_FILES:
        relocate_unit_block(fname)
    rebuild_ability_data()
    print("done")


if __name__ == "__main__":
    main()
