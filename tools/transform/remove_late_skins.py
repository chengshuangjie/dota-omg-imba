from pathlib import Path
import re, struct, json

root = Path(r"D:\dota\DOTA69AI\rework-omg-imba")
src_j = root / "final-key-verify" / "war3map.j"
src_imp = root / "final-key-verify" / "war3map.imp"
out = root / "no-late-skins-build"
out.mkdir(exist_ok=True)
t = src_j.read_text(encoding="utf-8")


def replace_function_body(text: str, name: str, body: str) -> str:
    m = re.search(r"(?m)^function " + re.escape(name) + r" takes[^\n]*returns[^\n]*\n", text)
    if not m:
        raise RuntimeError(f"function not found: {name}")
    end = text.find("\nendfunction", m.end())
    if end < 0:
        raise RuntimeError(f"endfunction not found: {name}")
    return text[:m.end()] + body.rstrip("\n") + text[end:]


# Remove the large late-added skin catalog and disable its initialization/sync pipeline.
for name in [
    "B1032CatalogInit",
    "B1032Init",
    "B1032Apply",
    "B1032ApplyNotify",
    "B1032Restore",
    "B1032Reconcile",
    "B1039ApplyLegacy",
    "B1039Request",
    "B1039Notify",
    "B1039Check",
    "B1039Pulse",
]:
    t = replace_function_body(t, name, "// Late-added skin system removed.\nreturn")

# Route both former skin entry points to the retained hero mastery/realm screen.
old = 'set B1031ArchiveButton[arcPid]=DialogAddButton(B836ArcDialog[arcPid],"当前英雄皮肤 / 熟练度",0)'
new = 'set B1031ArchiveButton[arcPid]=DialogAddButton(B836ArcDialog[arcPid],"当前英雄熟练度 / 修炼境界",0)'
if t.count(old) != 1:
    raise RuntimeError("archive button mismatch")
t = t.replace(old, new)

old = """if arcClicked==B1031ArchiveButton[arcPid] then
set B1032Detail[arcPid]=0
call B1032Open(arcPid)"""
new = """if arcClicked==B1031ArchiveButton[arcPid] then
set B1035Page[arcPid]=0
call B1035Open(arcPid)"""
if t.count(old) != 1:
    raise RuntimeError("archive click branch mismatch")
t = t.replace(old, new)

old = """function B1031Chat takes nothing returns nothing
local integer realmPid=GetPlayerId(GetTriggerPlayer())
if GetEventPlayerChatString()==\"-skin\" then
call B1032Open(realmPid)
else
set B1035Page[realmPid]=0
call B1035Open(realmPid)
endif
endfunction"""
new = """function B1031Chat takes nothing returns nothing
local integer realmPid=GetPlayerId(GetTriggerPlayer())
set B1035Page[realmPid]=0
call B1035Open(realmPid)
endfunction"""
if t.count(old) != 1:
    raise RuntimeError("mastery chat function mismatch")
t = t.replace(old, new)

# Remove obsolete visible wording while retaining mastery and title behavior.
t = t.replace("各英雄分别累计，皮肤不改变英雄归属。", "各英雄分别累计。")
t = t.replace("修炼境界 / 骷髅王皮肤", "修炼境界")

# No runtime model path under skins may remain in the deliverable script.
skin_paths = sorted(set(re.findall(r'(?i)skins(?:\\\\|\\)[^"\r\n]+', t)))
if skin_paths:
    raise RuntimeError(f"residual skins paths: {skin_paths[:10]}")

(out / "war3map.j").write_text(t, encoding="utf-8", newline="")

# Remove the complete late-added skins directory from the import manifest.
data = src_imp.read_bytes()
version, count = struct.unpack_from("<II", data, 0)
pos = 8
entries = []
for _ in range(count):
    flag = data[pos]
    pos += 1
    end = data.index(0, pos)
    name = data[pos:end].decode("utf-8")
    pos = end + 1
    entries.append((flag, name))
removed = [name for _, name in entries if name.lower().startswith("skins\\")]
kept = [(flag, name) for flag, name in entries if not name.lower().startswith("skins\\")]
if len(removed) != 1416:
    raise RuntimeError(f"expected 1416 skins entries, got {len(removed)}")
buf = bytearray(struct.pack("<II", version, len(kept)))
for flag, name in kept:
    buf.append(flag)
    buf.extend(name.encode("utf-8"))
    buf.append(0)
(out / "war3map.imp").write_bytes(buf)

report = {
    "original_script_bytes": len(src_j.read_bytes()),
    "new_script_bytes": len((out / "war3map.j").read_bytes()),
    "script_bytes_removed": len(src_j.read_bytes()) - len((out / "war3map.j").read_bytes()),
    "original_imp_count": count,
    "new_imp_count": len(kept),
    "removed_skin_entries": len(removed),
    "removed_first": removed[:5],
    "removed_last": removed[-5:],
}
(out / "remove-late-skins-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
