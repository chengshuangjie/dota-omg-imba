from __future__ import annotations

import re
import sys
from pathlib import Path


TARGET_PREFIXES = (
    "B898Quit",
    "B901Quit",
    "B839Arc",
    "B891Arc",
    "B891Miao",
    "B896Miao",
    "B897Miao",
    "B901Arc",
    "B1031",
    "B1032",
    "B1035",
    "B1040",
    "B1042",
    "B1044",
    "B836Arc",
    "B1131Recharge",
    "B1130EntryGift",
)
TARGET_EXACT = {"B1036NormalVictory", "B1036CountSync"}
KEEP = {"B836ArcHuman", "B836ArcUInt"}

FUNCTION_RE = re.compile(
    r"(?ms)^function\s+(?P<name>[A-Za-z0-9_]+)\s+takes\s+(?P<args>.*?)\s+returns\s+(?P<ret>[A-Za-z0-9_]+)\s*\n.*?^endfunction\s*$"
)


def default_return(ret: str) -> str:
    if ret == "nothing":
        return ""
    if ret == "boolean":
        return "return false\n"
    if ret == "integer":
        return "return 0\n"
    if ret == "real":
        return "return 0.\n"
    if ret == "string":
        return 'return ""\n'
    return "return null\n"


def should_strip(name: str) -> bool:
    if name in KEEP:
        return False
    return name in TARGET_EXACT or name.startswith(TARGET_PREFIXES)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: strip_kk_persistence.py <war3map.j>")
    path = Path(sys.argv[1])
    raw = path.read_bytes()
    had_bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    newline = "\r\n" if "\r\n" in text else "\n"
    normalized = text.replace("\r\n", "\n")
    changed: list[str] = []

    def replace(match: re.Match[str]) -> str:
        name = match.group("name")
        if not should_strip(name):
            return match.group(0)
        changed.append(name)
        args = match.group("args").strip()
        ret = match.group("ret")
        body = f"function {name} takes {args} returns {ret}\n"
        body += "// v6.9 CLEAN-TEST: KK persistence implementation removed.\n"
        body += default_return(ret)
        body += "endfunction"
        return body

    updated = FUNCTION_RE.sub(replace, normalized)
    if not changed:
        raise SystemExit("no target functions found")
    if len(changed) != len(set(changed)):
        raise SystemExit("duplicate function replacement detected")
    if "function B1043Give takes" not in updated:
        raise SystemExit("B1043Give unexpectedly missing")
    if "function B1121DetectInit takes" not in updated:
        raise SystemExit("DETECT implementation unexpectedly missing")
    if "function B836ArcHuman takes" not in updated or "function B836ArcUInt takes" not in updated:
        raise SystemExit("required generic validation helper missing")

    updated = updated.replace("\n", newline)
    encoded = updated.encode("utf-8")
    if had_bom:
        encoded = b"\xef\xbb\xbf" + encoded
    path.write_bytes(encoded)
    print(f"stripped={len(changed)}")
    for name in changed:
        print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
