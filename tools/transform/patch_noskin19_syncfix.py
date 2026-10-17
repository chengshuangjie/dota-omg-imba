from pathlib import Path
import hashlib
import re

SRC_J = Path(r"D:\dota\noskin18-cumulative\work\fv4\war3map.j")
SRC_W3I = Path(r"D:\dota\noskin18-cumulative\work\pack\war3map.w3i")
OUT_DIR = Path(r"D:\dota\noskin19-syncfix\work")
OUT_J = OUT_DIR / "war3map.j"
OUT_W3I = OUT_DIR / "war3map.w3i"
NEW_NAME = b"OMG IMBA v1.8.5-SYNCF001"


def replace_function(text: str, name: str, replacement: str) -> str:
    pattern = re.compile(
        r"(?ms)^function\s+" + re.escape(name) + r"\s+takes.*?^endfunction(?=\r?$)",
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(f"{name}: expected exactly one function, got {len(matches)}")
    return text[: matches[0].start()] + replacement + text[matches[0].end() :]


with SRC_J.open("r", encoding="utf-8", errors="strict", newline="") as f:
    source = f.read()
newline = "\r\n" if "\r\n" in source else "\n"

old_global = "real B1063SellLastClick=0."
new_global = "real array B1063SellLastClick"
if source.count(old_global) != 1:
    raise RuntimeError(f"global declaration count mismatch: {source.count(old_global)}")
source = source.replace(old_global, new_global, 1)

old_version = 'constant string XOMG_VERSION="v1.7.1-K-W3IFix"'
new_version = 'constant string XOMG_VERSION="v1.8.5-SYNCF001"'
if source.count(old_version) != 1:
    raise RuntimeError(f"version declaration count mismatch: {source.count(old_version)}")
source = source.replace(old_version, new_version, 1)

mouse_down = """function B1063SellMouseDown takes nothing returns boolean
local integer key=MHEvent_GetKey()
local player p=GetLocalPlayer()
local integer pid=GetPlayerId(p)
local unit hero=null
local real now=GetGameTime()
local real cx=0.
local real cy=0.
if key!=1 then
return false
endif
if pid<0 or pid>=12 then
return false
endif
if MHUI_IsChatEditBarOn() or EditingHotKeyIndex>0 or IsSetUpUIEnable or UpdateLogIsShow or bMenuMainPanelIsEnable then
return false
endif
set hero=M7[pid]
if hero==null or not UnitAlive(hero) then
set hero=null
set p=null
return false
endif
if now-B1063SellLastClick[pid]>.35 or now<B1063SellLastClick[pid] then
set B1063SellLastClick[pid]=now
set hero=null
set p=null
return false
endif
if now-B1063SellThrottle[pid]<.5 then
set hero=null
set p=null
return false
endif
set cx=DzGetMouseTerrainX()
set cy=DzGetMouseTerrainY()
if cx<-65536. or cx>65536. or cy<-65536. or cy>65536. then
set hero=null
set p=null
return false
endif
// Local mouse code must never allocate Warcraft handles or mutate item state.
// Send only primitive click coordinates; every client selects and sells the item
// later inside the synchronized DROP_SELL callback.
set B1063SellThrottle[pid]=now
call DzSyncData("DROP_SELL",I2S(pid)+","+I2S(R2I(cx*10.))+","+I2S(R2I(cy*10.)))
set hero=null
set p=null
return false
endfunction""".replace("\n", newline)

sync = """function B1063SellSync takes nothing returns nothing
local player p=DzGetTriggerSyncPlayer()
local integer pid=GetPlayerId(p)
local string data=DzGetTriggerSyncData()
local integer length=StringLength(data)
local integer c1=-1
local integer c2=-1
local integer i=0
local real tx=0.
local real ty=0.
local unit hero=null
local item it=null
local integer h=0
local integer raw=0
local integer sale=0
local integer price=0
local rect r=null
local boolexpr filterExpr=null
if pid<0 or pid>=12 or length<1 or length>32 then
set p=null
return
endif
if GetPlayerController(p)!=MAP_CONTROL_USER or GetPlayerSlotState(p)!=PLAYER_SLOT_STATE_PLAYING then
set p=null
return
endif
loop
exitwhen i>=length
if SubString(data,i,i+1)=="," then
if c1==-1 then
set c1=i
elseif c2==-1 then
set c2=i
endif
endif
set i=i+1
endloop
if c1<=0 or c2<=c1+1 then
set p=null
return
endif
if S2I(SubString(data,0,c1))!=pid then
set p=null
return
endif
set tx=I2R(S2I(SubString(data,c1+1,c2)))/10.
set ty=I2R(S2I(SubString(data,c2+1,length)))/10.
set hero=M7[pid]
if hero==null or not UnitAlive(hero) then
call XOMG_LogEvent("DROP_SELL_FAIL pid="+I2S(pid)+" reason=no_hero")
set p=null
return
endif
if not IsUnitInRangeXY(hero,tx,ty,600.) then
call XOMG_LogEvent("DROP_SELL_FAIL pid="+I2S(pid)+" reason=far")
set hero=null
set p=null
return
endif
// This entire search runs from the synchronized callback on every client.
set B1063SellCX=tx
set B1063SellCY=ty
set B1063SellBest=null
set B1063SellBestDist=0.
set r=Rect(tx-140.,ty-140.,tx+140.,ty+140.)
set filterExpr=Condition(function B1063SellFilter)
call EnumItemsInRect(r,filterExpr,function B1063SellPickNearest)
call DestroyBoolExpr(filterExpr)
call RemoveRect(r)
set filterExpr=null
set r=null
set it=B1063SellBest
set B1063SellBest=null
if it==null then
if B1063SellFailLog[pid]<8 then
set B1063SellFailLog[pid]=B1063SellFailLog[pid]+1
call XOMG_LogEvent("DROP_SELL_FAIL pid="+I2S(pid)+" reason=not_marked")
endif
set hero=null
set p=null
return
endif
set h=GetHandleId(it)
if LoadBoolean(L7,h,16204)==true then
call XOMG_LogEvent("DROP_SELL_FAIL pid="+I2S(pid)+" reason=duplicate handle="+I2S(h))
set it=null
set hero=null
set p=null
return
endif
call SaveBoolean(L7,h,16204,true)
set raw=LoadInteger(L7,h,16201)
set price=Get_Item_Price(raw)
set sale=price/2
call B1063MarkClear(it)
call RemoveItem(it)
call SetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD,GetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD)+sale)
call DisplayTimedTextToPlayer(p,0,0,5.,"|cff00ff00[出售] 售出 "+GetObjectName(raw)+"，获得 "+I2S(sale)+" 金币|r")
call XOMG_LogEvent("DROP_SELL_DELIVER pid="+I2S(pid)+" handle="+I2S(h)+" raw="+I2S(raw)+" price="+I2S(price)+" sale="+I2S(sale))
set it=null
set hero=null
set p=null
endfunction""".replace("\n", newline)

pick_nearest = """function B1063SellPickNearest takes nothing returns nothing
local item it=GetEnumItem()
local integer h=0
local integer bestHandle=0
local real dx=0.
local real dy=0.
local real d=0.
if it==null then
return
endif
set h=GetHandleId(it)
if LoadInteger(L7,h,16201)==0 or LoadBoolean(L7,h,16204)==true or LoadBoolean(L7,h,16205)==false or B1063IsBottleFamily(LoadInteger(L7,h,16201)) then
set it=null
return
endif
set dx=GetItemX(it)-B1063SellCX
set dy=GetItemY(it)-B1063SellCY
set d=SquareRoot(dx*dx+dy*dy)
if B1063SellBest!=null then
set bestHandle=GetHandleId(B1063SellBest)
endif
if B1063SellBest==null or d<B1063SellBestDist or (d==B1063SellBestDist and h<bestHandle) then
set B1063SellBest=it
set B1063SellBestDist=d
endif
set it=null
endfunction""".replace("\n", newline)

source = replace_function(source, "B1063SellMouseDown", mouse_down)
source = replace_function(source, "B1063SellSync", sync)
source = replace_function(source, "B1063SellPickNearest", pick_nearest)

# Hard safety gates: no handle allocation, item enumeration, item lookup, or file logging in local mouse callback.
mouse_block = re.search(r"(?ms)^function B1063SellMouseDown takes.*?^endfunction", source).group(0)
for forbidden in ["Rect(", "Condition(", "EnumItemsInRect", "GetHandleId", "B1063SellBest", "XOMG_LogEvent", "CreateItem", "RemoveItem"]:
    if forbidden in mouse_block:
        raise RuntimeError(f"local mouse callback still contains forbidden operation: {forbidden}")
if mouse_block.count('DzSyncData("DROP_SELL"') != 1:
    raise RuntimeError("local mouse callback must send exactly one DROP_SELL payload")

sync_block = re.search(r"(?ms)^function B1063SellSync takes.*?^endfunction", source).group(0)
for required in ["EnumItemsInRect", "DestroyBoolExpr(filterExpr)", "RemoveRect(r)", "RemoveItem(it)", "SetPlayerState"]:
    if required not in sync_block:
        raise RuntimeError(f"synchronized callback missing: {required}")

OUT_DIR.mkdir(parents=True, exist_ok=True)
with OUT_J.open("w", encoding="utf-8", newline="") as f:
    f.write(source)

w3i = bytearray(SRC_W3I.read_bytes())
if len(w3i) != 806:
    raise RuntimeError(f"unexpected W3I size: {len(w3i)}")
if len(NEW_NAME) != 24:
    raise RuntimeError(f"new internal name must be 24 bytes, got {len(NEW_NAME)}")
old = bytes(w3i)
w3i[12:36] = NEW_NAME
w3i[234:258] = NEW_NAME
changed = [i for i, (a, b) in enumerate(zip(old, w3i)) if a != b]
outside = [i for i in changed if not (12 <= i < 36 or 234 <= i < 258)]
if outside:
    raise RuntimeError(f"W3I changed outside name slots: {outside}")
OUT_W3I.write_bytes(w3i)

print({
    "source_j_sha256": hashlib.sha256(SRC_J.read_bytes()).hexdigest(),
    "output_j_sha256": hashlib.sha256(OUT_J.read_bytes()).hexdigest(),
    "output_j_bytes": OUT_J.stat().st_size,
    "output_w3i_sha256": hashlib.sha256(OUT_W3I.read_bytes()).hexdigest(),
    "w3i_changed_bytes": len(changed),
    "w3i_outside_name_slots": outside,
    "internal_name": NEW_NAME.decode("ascii"),
})
