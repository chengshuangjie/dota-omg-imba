from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "src" / "data" / "Units" / "CampaignUnitStrings.txt"
TARGETS = {
    "U00F": ("袁加凯", ("胖子", "屠夫")),
    "Z00F": ("袁加凯", ("胖子", "屠夫")),
    "Nfir": ("程双杰", ("影魔",)),
    "Zfir": ("程双杰", ("影魔",)),
    "Zgir": ("程双杰", ("影魔",)),
    "Zhir": ("程双杰", ("影魔",)),
    "N01I": ("土鸡", ("炼金术士",)),
    "N01H": ("土鸡", ("炼金术士",)),
    "N01T": ("土鸡", ("炼金术士",)),
    "N01J": ("土鸡", ("炼金术士",)),
    "H00K": ("凯哥", ("地精工程师", "哥布林工程师", "炸弹人")),
}

text = PATH.read_text(encoding="utf-8")
for rawcode, (name, legacy_names) in TARGETS.items():
    start = text.index(f"[{rawcode}]")
    end = text.find("\n[", start + 1)
    if end < 0:
        end = len(text)
    block = text[start:end]
    for key in ("Name", "Propernames", "Tip"):
        if re.search(rf"(?m)^{key}=", block):
            block = re.sub(rf"(?m)^{key}=.*$", f"{key}={name}", block)
        else:
            block = block.rstrip("\r\n") + f"\r\n{key}={name}\r\n"
    for key in ("Awakentip", "Revivetip"):
        if re.search(rf"(?m)^{key}=", block):
            block = re.sub(rf"(?m)^{key}=.*$", f"{key}=复活 {name}", block)
    if rawcode == "H00K" and re.search(r"(?m)^Description=", block):
        block = re.sub(r"(?m)^Description=.*$", f"Description={name}", block)
    for legacy in legacy_names:
        block = block.replace(legacy, name)
    text = text[:start] + block + text[end:]

PATH.write_text(text, encoding="utf-8", newline="")

for rawcode, (name, legacy_names) in TARGETS.items():
    start = text.index(f"[{rawcode}]")
    end = text.find("\n[", start + 1)
    if end < 0:
        end = len(text)
    block = text[start:end]
    assert all(f"{key}={name}" in block for key in ("Name", "Propernames", "Tip"))
    assert all(legacy not in block for legacy in legacy_names)

print(f"updated {len(TARGETS)} hero object blocks: {PATH}")
