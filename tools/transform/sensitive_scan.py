# -*- coding: utf-8 -*-
"""Sensitive scan on changed files before commit."""
import re, os

ROOT = r"D:\dota\DOTA-OMG-IMBA-轻量化"
patterns = [
    (r'(?i)(password|passwd|secret|api[_-]?key|token|bearer)\s*[=:]\s*\S+', 'credential'),
    (r'-----BEGIN [A-Z]+ PRIVATE KEY-----', 'private key'),
    (r'ghp_[A-Za-z0-9]{20,}', 'github token'),
    (r'xox[baprs]-[A-Za-z0-9-]{10,}', 'slack token'),
    (r'AKIA[0-9A-Z]{16}', 'aws key'),
]

changed = []
for root, dirs, files in os.walk(os.path.join(ROOT, "src")):
    for f in files:
        changed.append(os.path.join(root, f))
for d in ["reports", "tools", "config"]:
    for root, dirs, files in os.walk(os.path.join(ROOT, d)):
        for f in files:
            changed.append(os.path.join(root, f))

hits = 0
for path in changed:
    try:
        text = open(path, encoding='utf-8', errors='ignore').read()
    except:
        continue
    for pat, label in patterns:
        for m in re.finditer(pat, text):
            # allow common.j/blizzard.j references
            print(f"  HIT [{label}] {os.path.relpath(path, ROOT)}: {m.group()[:60]}")
            hits += 1
print(f"\nSensitive scan: {hits} hits")
