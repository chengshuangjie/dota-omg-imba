# -*- coding: utf-8 -*-
"""Release w3i two-slot binary edit: only bytes 12..35 and 234..258 change; rest == pre-release."""
import sys, hashlib
W3I = r"D:\Dota_OMG\src\war3map.w3i"
PRE = r"D:\Dota_OMG\backups\pre-v6.90a-1.0-20261020-163807\src__war3map.w3i"
slotA = "v6.90a-OMG-AI-1.0".encode("ascii").ljust(24, b" ")      # 17 bytes + 7 spaces = 24
slotB = "Dota v6.90a OMG AI 1.0".encode("ascii").ljust(24, b" ")  # 22 bytes + 2 spaces = 24
assert len(slotA) == 24 and len(slotB) == 24
raw = bytearray(open(W3I, "rb").read()); pre = open(PRE, "rb").read()
if len(raw) != 806: sys.exit("w3i must be 806B")
raw[12:36] = slotA
raw[234:258] = slotB
allow = set(range(12, 36)) | set(range(234, 258))
for i in range(806):
    if i in allow:
        continue
    if raw[i] != pre[i]:
        sys.exit("non-slot byte changed at %d" % i)
open(W3I, "wb").write(bytes(raw))
chk = open(W3I, "rb").read()
print("len", len(chk))
print("slotA raw", chk[12:36])
print("slotB raw", chk[234:258])
print("slotA text:", chk[12:36].decode("ascii"))
print("slotB text:", chk[234:258].decode("ascii"))
print("sha256", hashlib.sha256(chk).hexdigest().upper())
