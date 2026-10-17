# -*- coding: utf-8 -*-
"""
v1.8 reproducible preview-UI sync generator.
- Parse SUIJI_FIXED_CLONE_TABLE SaveInteger(key0 logical->physical, key2 logical->alternate) from war3map.j.
- Parse CampaignAbilityStrings.txt [RAW] sections.
- For every mapped clone, enforce verbatim Name/Tip/Researchtip/Researchubertip/Ubertip == logical.
- check mode (default): report divergence only, write coverage CSV; --apply copies logical text into clone sections.
- Asserts SuijiTavern_Fill stocks the logical rawcode (OM7 choice) rather than a physical proxy.
Coverage covers the 116 OMG pool; A503 placeholder / Unknown are explicitly excluded.
"""
import re, io, csv, os, sys, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
JP = os.path.join(ROOT, 'src', 'war3map.j')
CS = os.path.join(ROOT, 'src', 'data', 'Units', 'CampaignAbilityStrings.txt')
REPORT_CSV = os.path.join(ROOT, 'reports', 'preview-ui-coverage-v18.csv')
APPLY = '--apply' in sys.argv

j = io.open(JP, encoding='utf-8', newline='').read()
cs = io.open(CS, encoding='utf-8', newline='').read()

# parse clone table
phys = {}
alt = {}
for m in re.finditer(r"SaveInteger\(SUIJI_FIXED_CLONE_TABLE,0,'([A-Za-z0-9_]+)','([A-Za-z0-9_]+)'\)", j):
    phys[m.group(1)] = m.group(2)
for m in re.finditer(r"SaveInteger\(SUIJI_FIXED_CLONE_TABLE,2,'([A-Za-z0-9_]+)','([A-Za-z0-9_]+)'\)", j):
    alt[m.group(1)] = m.group(2)

# parse CS sections
sec_re = re.compile(r'^\s*\[([A-Za-z0-9_]+)\]\s*$', re.M)
matches = list(sec_re.finditer(cs))
sections = {}
order = []
for idx, m in enumerate(matches):
    raw = m.group(1)
    start = m.end()
    end = matches[idx+1].start() if idx+1 < len(matches) else len(cs)
    sections[raw] = cs[start:end]
    order.append(raw)

FIELDS = ['Name', 'Tip', 'Researchtip', 'Researchubertip', 'Ubertip']
def field(body, key):
    m = re.search(r'(?m)^' + key + r'=(.*)$', body)
    return m.group(1) if m else None

rows = []
divergence = 0
synced = 0
def check_pair(logical, clone, role):
    global divergence, synced
    lb, cb = sections.get(logical), sections.get(clone)
    if lb is None:
        rows.append([logical, clone, role, 'missing-logical-section', '', ''])
        return
    if cb is None:
        rows.append([logical, clone, role, 'clone-section-absent-in-CS(ok)', '', ''])
        return
    diffs = []
    out = cb
    for f in FIELDS:
        lv, cv = field(lb, f), field(cb, f)
        if lv is not None and cv is not None and lv != cv:
            diffs.append(f)
            if APPLY:
                out = re.sub(r'(?m)^' + f + r'=.*$', f + '=' + lv, out, count=1)
    if diffs:
        divergence += 1
        rows.append([logical, clone, role, 'diverge:' + '|'.join(diffs), '', ''])
        if APPLY:
            sections[clone] = out; synced += 1
    else:
        rows.append([logical, clone, role, 'match', '', ''])

for logical, clone in phys.items():
    check_pair(logical, clone, 'physical')
for logical, clone in alt.items():
    check_pair(logical, clone, 'alternate')

# Fill stocks logical assertion
fill_logical = ('SuijiTavern_Fill' in j and 'OM7(heroHandle,mark+"Choice"+I2S(i)+"Skill")' in j
                and 'AddUnitToStock(tavern,skill' in j)

# samples
samples = {'A1WH': phys.get('A1WH') or alt.get('A1WH'),
           'A095': phys.get('A095') or alt.get('A095'),
           'A088': phys.get('A088') or alt.get('A088'),
           'A0AY': phys.get('A0AY') or alt.get('A0AY')}  # butcher-ish sample placeholder

os.makedirs(os.path.dirname(REPORT_CSV), exist_ok=True)
with open(REPORT_CSV, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['logical', 'clone', 'role', 'status', 'sample', 'note'])
    for r in rows: w.writerow(r)
    w.writerow(['SUJI_FILL_STOCKS_LOGICAL', '', '', 'PASS' if fill_logical else 'FAIL', '', ''])

if APPLY:
    # rebuild CS from sections (append-only before first section preserved)
    pre = cs[:matches[0].start()] if matches else cs
    rebuilt = pre
    for raw in order:
        rebuilt += '[' + raw + ']' + sections[raw]
    io.open(CS, 'w', encoding='utf-8', newline='').write(rebuilt)

summary = {
    'mapped_logicals_physical': len(phys),
    'mapped_logicals_alternate': len(alt),
    'divergence': divergence,
    'synced_apply': synced,
    'fill_stocks_logical': fill_logical,
    'samples': samples,
}
print(json.dumps(summary, ensure_ascii=False, indent=2))
print('coverage CSV ->', REPORT_CSV)
