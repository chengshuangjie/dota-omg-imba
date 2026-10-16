from pathlib import Path
import re, shutil
ROOT=Path(r'D:\dota\DOTA-OMG-IMBA-轻量化')
p=ROOT/'src'/'war3map.j'
s=p.read_text(encoding='utf-8')
orig=s
# Permanent IMBA gate independent of legacy XM difficulty.
s=s.replace('constant real IMBA_POWER=2.\ninteger imbaMult=1\nboolean imbaB67DpsExclude=false',
'''constant real IMBA_POWER=2.
constant boolean XOMG_IMBA_ENABLED=true
constant string XOMG_VERSION="v1.1-runtime"
integer imbaMult=2
integer XOMG_DAMAGE_LOG_COUNT=0
boolean imbaB67DpsExclude=false''',1)
# New gameplay blocks only: switch the explicitly tagged IMBA gates, not legacy XM rules.
lines=s.splitlines()
for i,line in enumerate(lines):
    if '// IMBA:' in line:
        for j in range(i+1,min(i+8,len(lines))):
            if 'if XM_MODE and BL7!=6 then' in lines[j]:
                lines[j]=lines[j].replace('if XM_MODE and BL7!=6 then','if XOMG_IMBA_ENABLED and BL7!=6 then')
                break
            if 'elseif XM_MODE and BL7!=6 then' in lines[j]:
                lines[j]=lines[j].replace('elseif XM_MODE and BL7!=6 then','elseif XOMG_IMBA_ENABLED and BL7!=6 then')
                break
            if 'if XM_MODE and dur' in lines[j]:
                lines[j]=lines[j].replace('if XM_MODE and dur','if XOMG_IMBA_ENABLED and dur')
                break
            if 'if XM_MODE then' in lines[j]:
                lines[j]=lines[j].replace('if XM_MODE then','if XOMG_IMBA_ENABLED then')
                break
s='\n'.join(lines)+'\n'
# imbaMult is permanent for new probability/count rules; remove only injected resets/sets.
s=s.replace('set XM_MODE=true\nset imbaMult=2\n','set XM_MODE=true\n',1)
s=s.replace('set XM_MODE=false\nset imbaMult=1\n','set XM_MODE=false\n')
# Add bounded runtime damage trace in both B67 paths.
s=s.replace('''elseif XOMG_IMBA_ENABLED and BL7!=6 then
set YM7=YM7*IMBA_POWER
endif
if BL7==2 then''','''elseif XOMG_IMBA_ENABLED and BL7!=6 then
if XOMG_DAMAGE_LOG_COUNT<12 then
call B1133LogAppend("IMBA_DAMAGE path=DPS type="+I2S(BL7)+" base="+R2S(YM7)+" actual="+R2S(YM7*IMBA_POWER)+" legacyXM="+I2S(B287_BoolToInt(XM_MODE))+" mult="+I2S(imbaMult)+" ver="+XOMG_VERSION)
set XOMG_DAMAGE_LOG_COUNT=XOMG_DAMAGE_LOG_COUNT+1
endif
set YM7=YM7*IMBA_POWER
endif
if BL7==2 then''',1)
s=s.replace('''if XOMG_IMBA_ENABLED and BL7!=6 then
set YM7=YM7*IMBA_POWER
endif
set Fe=true''','''if XOMG_IMBA_ENABLED and BL7!=6 then
if XOMG_DAMAGE_LOG_COUNT<12 then
call B1133LogAppend("IMBA_DAMAGE path=B67 type="+I2S(BL7)+" base="+R2S(YM7)+" actual="+R2S(YM7*IMBA_POWER)+" legacyXM="+I2S(B287_BoolToInt(XM_MODE))+" mult="+I2S(imbaMult)+" ver="+XOMG_VERSION)
set XOMG_DAMAGE_LOG_COUNT=XOMG_DAMAGE_LOG_COUNT+1
endif
set YM7=YM7*IMBA_POWER
endif
set Fe=true''',1)
# Lottery: 50% >=1000 equipment, otherwise 1000-1500 gold. No 50-80 legacy branch.
start=s.index('function CHOUJIANG takes nothing returns nothing')
end=s.index('endfunction',start)+len('endfunction')
old=s[start:end]
new='''function CHOUJIANG takes nothing returns nothing
local unit u=M7[GetPlayerId(GetOwningPlayer(GetTriggerUnit()))]
local player p=GetOwningPlayer(u)
local integer id=GetPlayerId(p)
local item it=null
local integer zb=0
local string name=""
local integer n=0
call B1063BuildLotteryPool()
if B1063LotteryCount>0 and GetRandomInt(1,100)<=50 then
set zb=B1063LotteryPool[GetRandomInt(1,B1063LotteryCount)]
endif
if zb!=0 then
if UnitInventoryCount(u)<6 then
set it=UnitAddItemById(u,zb)
else
set it=CreateItem(zb,GetUnitX(u),GetUnitY(u))
endif
call SetItemPlayer(it,p,true)
call SetItemUserData(it,1)
set name=GetItemName(it)
set name=MHString_Sub(name,0,MHString_Find(name,"|n",0))
call DisplayTimedTextToForce(GetPlayersAll(),12.,Q[id]+KZ4[id]+"|r 抽奖获得了: |cFF00FF00"+name+"|r")
call B1133LogAppend("LOTTERY pid="+I2S(id)+" kind=item raw="+I2S(zb)+" min_price="+I2S(B1063LotteryMinPrice)+" pool="+I2S(B1063LotteryCount)+" ver="+XOMG_VERSION)
else
set n=GetRandomInt(1000,1500)
call SetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD,GetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD)+n)
call DestroyEffect(AddSpecialEffect("Abilities\\Spells\\Other\\Transmute\\PileofGold.mdl",GetUnitX(u),GetUnitY(u)))
call DisplayTimedTextToForce(GetPlayersAll(),12.,Q[id]+KZ4[id]+"|r 抽奖获得了: |cFF00FF00"+I2S(n)+"枚金币|r")
call B1133LogAppend("LOTTERY pid="+I2S(id)+" kind=gold amount="+I2S(n)+" pool="+I2S(B1063LotteryCount)+" ver="+XOMG_VERSION)
endif
set CHOUJIANGSTATE[id]=0
call UnitRemoveAbility(SuijiTavernB295_GetEnergyCircle(id),'A4DK')
set u=null
set p=null
set it=null
endfunction'''
s=s[:start]+new+s[end:]
# Init log includes permanent gate.
s=s.replace('call B1133LogAppend("INIT logger=ready")','call B1133LogAppend("INIT logger=ready ver="+XOMG_VERSION+" imba="+I2S(B287_BoolToInt(XOMG_IMBA_ENABLED))+" mult="+I2S(imbaMult)+" legacyXM="+I2S(B287_BoolToInt(XM_MODE)))',1)
assert s!=orig
p.write_text(s,encoding='utf-8',newline='\n')
print('written',p,'bytes',p.stat().st_size)
print('gates',s.count('XOMG_IMBA_ENABLED'),'legacy resets',s.count('set imbaMult=1'))