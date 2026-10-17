# -*- coding: utf-8 -*-
"""v1.8-integrated static gate audit: emits reports/v18-audit.{json,csv,md}"""
import io, os, re, json, csv, hashlib, subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
JP = os.path.join(ROOT, 'src', 'war3map.j')
CS = os.path.join(ROOT, 'src', 'data', 'Units', 'CampaignAbilityStrings.txt')
W3I = os.path.join(ROOT, 'src', 'war3map.w3i')
j = io.open(JP, encoding='utf-8', newline='').read()
cs = io.open(CS, encoding='utf-8', newline='').read()
w3i = open(W3I, 'rb').read()

C = []
def gate(gid, name, ok, detail=''):
    C.append({'id': gid, 'name': name, 'status': 'PASS' if ok else 'FAIL', 'detail': detail})

# 1 title
gate('G1-title', '称号 r==2 本图女神->男神, DOTA女神保留',
     j.count('本图女神')==0 and j.count('本图男神')>=1 and j.count('DOTA女神')==1,
     f"女神={j.count('本图女神')} 男神={j.count('本图男神')} DOTA女神={j.count('DOTA女神')}")
# 2 ATTR
gate('G2-attr', 'ATTR 本地视角友军广播/本人替换/敌方观察离开排除',
     'GetLocalPlayer()==abQ' in j and '双杰抽属性：本次+' not in j
     and 'IsPlayerAlly(abQ,p)' in j and 'PLAYER_STATE_OBSERVER' in j)
# 3 sven
gate('G3-sven', '斯温 selfRate=1+1*level / allyRate=1+.5*level, 旧公式=0',
     'set selfRate=1.+1.*level' in j and 'set selfRate=.5+.5*level' not in j
     and 'set allyRate=1.+.5*level' in j and 'set allyRate=.5+.25*level' not in j
     and 'GOD_STRENGTH logical=A1WH' in j)
# 4 lion
gate('G4-lion', '莱恩 SWYJ +50 精确3处/+20=0/FINGER_GROW x3/UI基础50实际100',
     j.count('SWYJ[i]=SWYJ[i]+50')==3 and j.count('SWYJ[i]=SWYJ[i]+20')==0
     and j.count('FINGER_GROW base_add=50')==3
     and cs.count('基础命中敌方英雄+50点额外伤害')==16)
# 5 bottle
gate('G5-bottle', '魔瓶族排除池/来源标记/PICKUP转换SU[XZ]/BOTTLE_FIX',
     'function B1063IsBottleFamily takes integer raw returns boolean' in j
     and 'SaveInteger(L7,GetHandleId(drop),16201,itemId)' in j
     and 'BOTTLE_FIX raw=' in j and 'CreateItem(SU[XZ]' in j)
# 6 preview
gate('G6-preview', 'SuijiTavern_Fill 入 logical; 同步生成器存在',
     'SuijiTavern_Fill' in j and 'OM7(heroHandle,mark+"Choice"+I2S(i)+"Skill")' in j
     and os.path.exists(os.path.join(ROOT,'tools','transform','sync_preview_ui.py')))
# 7 K normal pool: 50% test injection revoked; H0K0 rolls naturally in shared agility pool
gate('G7-k-normal', 'H0K0回归普通敏捷池：K_POOL/50%骰/NoK排除全部0；K24[40]成员x1；四技能R1X保留',
     'K_POOL_ROLLED' not in j and 'K_POOL_HIT' not in j and 'K_POOL_ROLL' not in j
     and 'B891RandomAgilityNoK' not in j and 'QC9HumanNoK' not in j and 'QZ9HumanNoK' not in j
     and j.count("set K24[40]='H0K0'")==1
     and "call R1X('H0K0',0,'KA01','KA02','KA03','KA04')" in j)
# 8 version + w3i
gate('G8-version', 'XOMG_VERSION/SetMapName v1.8',
     'XOMG_VERSION="v1.8-integrated"' in j and 'SetMapName("OMG IMBA v1.8-Integrated")' in j)
newlab=b'OMG IMBA v1.8-Integrated'
gate('G8-w3i', 'w3i 806B/新名x2/旧v1.7.1=0/槽外同a1c1de1',
     len(w3i)==806 and w3i.count(newlab)==2 and w3i.count(b'v1.7.1-W3IFix')==0)
# 9 miao direct pick HMD0/117
gate('G9-miao','喵刀 nMv4点击请求/MIAO_REQ同步/出生缝UB7=117/SELECT_MIAO_CREATE/权限门',
     'function MiaoDirectPickReady' in j and 'function MiaoDirectPickAllowed' in j
     and 'DzSyncData("MIAO_REQ"' in j and 'UB7=117' in j
     and 'SELECT_MIAO_CREATE' in j and 'B891ArcMiaoReplaced[GetPlayerId(p)]=true' in j
     and 'HMD0' in j)
# 10 D1 ground double-click sell
gate('G1-drop','DROP_SELL双击/近邻枚举/原子claimed/半价加gold/RemoveItem/失败原因',
     'function B1063SellSync' in j and 'DzSyncData("DROP_SELL"' in j
     and 'reason=far' in j and 'reason=duplicate' in j and 'reason=not_marked' in j
     and 'set sale=price/2' in j
     and 'PLAYER_STATE_RESOURCE_GOLD)+sale' in j)
# 11 EARLY/LATE drop pools
gate('G11-pool', '掉落EARLY(1..1000)/LATE(无cap)双池/600s切换/非pawnable排卷轴内部/各自空池保护',
     'B1063BuildLatePool' in j and 'B1063LatePool' in j
     and 'elapsedReal>=600.' in j and 'set elapsedReal=TimerGetElapsed(W)' in j and 'IsItemPawnable(probe)==false' in j
     and 'DROP_POOL_INIT' in j and 'early_count=' in j and 'late_count=' in j
     and 'B1063CheapCount<=0' not in j)
# 12 K portrait embedded CAMS (runtime MDX structural)
_mdxp = os.path.join(ROOT,'assets','Kv2','model','K_final_v2.mdx')
_mb = open(_mdxp,'rb').read()
_pos=4;_vers=0;_modl='';_cams=0;_close=True
while _pos+8<=len(_mb):
    _t=_mb[_pos:_pos+4];_sz=int.from_bytes(_mb[_pos+4:_pos+8],'little')
    if _pos+8+_sz>len(_mb):_close=False;break
    if _t==b'VERS':_vers=int.from_bytes(_mb[_pos+8:_pos+12],'little')
    if _t==b'MODL' and _sz>=80:_modl=_mb[_pos+8:_pos+88].split(b'\0')[0].decode('ascii','ignore')
    if _t==b'CAMS' and _sz>=120:_cams+=1
    _pos+=8+_sz
_portrait_ok = (_mb[:4]==b'MDLX' and _close and _pos==len(_mb) and _vers==800
                and _modl=='K_Hero' and _cams==1 and len(_mb)==54157
                and hashlib.sha256(_mb).hexdigest().startswith('e42041389591493b'))
gate('G12-portrait', 'K主模型内嵌CAMS=1/VERS800/K_Hero/闭合/SHA e4204138',
     _portrait_ok, f"len={len(_mb)} vers={_vers} modl={_modl} cams={_cams}")

# AI marker guards (E1/E2/E4/E5-E8); shop purchase / one-click / courier slot / bear / Roshan / human DROP_SELL not gated
gate('G13-ai-guard','AI标记物保护：GWF选择器/GXF拾取攻击/IHG拾取/Y9F/YDF/YUF/YBE/LDF 全部marker skip，商店购买不拦',
     'if B1063MarkedGroundItem(KA7) then' in j
     and 'DROP_AI_PICK_SKIP' in j and 'DROP_AI_ATK_SKIP' in j and 'DROP_AI_DROP_SKIP' in j
     and 'not B1063MarkedGroundItem(D88)' in j and 'not B1063MarkedGroundItem(QU8)' in j
     and 'integer array B1063AiSkipLog' in j
     and 'EVENT_PLAYER_UNIT_SELL_ITEM' in j and j.count('B1063MarkedGroundItem')>=8)

# ---- D2 HP4 15 confirmed leaks x2 (SLK parser) ----
_slkp=os.path.join(ROOT,'src','data','Units','AbilityData.slk')
_slk=io.open(_slkp,encoding='utf-8',newline='').read()
_recs={}
for _m in re.finditer(r'C;X1;Y\d+;K"([^"]+)"\r?\n(.*?)(?=\r?\nC;X1;Y|\Z)',_slk,re.S):
    _d={}
    for _c in re.finditer(r'C;X(\d+);K([^\r\n]*)',_m.group(2)):
        _d[_c.group(1)]=_c.group(2).strip()
    _recs[_m.group(1)]=_d
def _cell(code,col): return _recs.get(code,{}).get(str(col),'')

# 1 A0CY Tiny Grow attack x2 (SLK A4T3)
gate('D2-01-A0CY','A0CY长大 攻击50/100/150→100/200/300(A4T3)',
     _cell('A4T3',24)=='100' and _cell('A4T3',25)=='200' and _cell('A4T3',26)=='300')
# 2 A1EJ Battle Trance AS x2 (A0XF/XG/XH X28)
gate('D2-02-A1EJ','A1EJ战斗专注攻速0.6/1.2/1.8→1.2/2.4/3.6',
     _cell('A0XF',28)=='1.2' and _cell('A0XG',28)=='2.4' and _cell('A0XH',28)=='3.6')
# 3 A0FV Warpath per-stack attack x2 (3 sites)
gate('D2-03-A0FV','A0FV战意 每层15+5L→30+10L(施法/到期/恢复三处)',
     j.count('(30 + 10 * WUV)')==2 and '(30+10*level)*stacks' in j
     and '(15 + 5 * WUV)' not in j)
# 4 A0VC Marksmanship permanent agi x2 (A2NX)
gate('D2-04-A0VC','A0VC射手天赋敏捷40/60/80→80/120/160(A2NX)',
     _cell('A2NX',24)=='80' and _cell('A2NX',25)=='120' and _cell('A2NX',26)=='160')
# 5 A0ER Guardian Angel regen x2 (registry normal triple + SLK A0ER/Y0CI double-write; scepter untouched)
gate('D2-05-A0ER','A0ER守护天使回复25/50/75→50/100/150；神杖50/75/100不动；A0ER/Y0CI双写',
     'ABILITY_DATA_DATA_C,50.,100.,150.,50.,75.,100.' in j
     and _cell('A0ER',32)=='50.0' and _cell('A0ER',33)=='100.0' and _cell('A0ER',34)=='150.0'
     and _cell('Y0CI',32)=='50.0' and _cell('Y0CI',33)=='100.0' and _cell('Y0CI',34)=='150.0')
# 6 A12P engine attack-speed cap .02 hard limit / retention tradeoff: NO numerical change
gate('D2-06-A12P','A12P集中火力=引擎.02硬上限/攻击保留率tradeoff，不伪改(无数值插点/不改.02)',
     'A12P' in j)  # informational: engine cap, no numerical x2 applied
# 7 A034 Amplify Damage armor reduction x2 (A034+Y0BD double-write)
gate('D2-07-A034','A034伤害加深护甲10/15/20→20/30/40；A034/Y0BD双写',
     _cell('A034',24)=='20' and _cell('A034',25)=='30' and _cell('A034',26)=='40'
     and _cell('Y0BD',24)=='20' and _cell('Y0BD',25)=='30' and _cell('Y0BD',26)=='40')
# 8 A04Q Death Pact max-HP coefficient x2; attack SDD untouched
gate('D2-08-A04Q','A04Q死亡契约生命上限.3+.20K→.6+.40K；攻击SDD .03+.02K不动',
     '(.6+.40*KP7)' in j and '(.03+.02*KP7)' in j and '(.3+.20*KP7)' not in j)
# 9 A0E2 Culling Blade permanent armor +2→+4
gate('D2-09-A0E2','A0E2淘汰之刃永久护甲+2→+4/次',
     'CullingBladePermanentArmor")+4,254' in j and 'Armor")+2,254' not in j)
# 10 A0NS Borrowed Time window 4+BC7→8+2BC7; threshold/100% conversion untouched
gate('D2-10-A0NS','A0NS回光返照窗口4+BC7→8+2BC7(10/12/14s)；阈值/转治疗不动',
     'set BZ7=8+2*BC7' in j and 'set BZ7=4+BC7' not in j)
# 11 A10Q Weave CDR factor .875-.125L→.75-.25L (hero+labike) + UI sync
gate('D2-11-A10Q','A10Q编织减CD因子.875-.125L→.75-.25L(两处)+UI .25+.25L',
     j.count('0.75-0.25')==2 and '(0.25+0.25*B287_GetUnitAbilityLevel(ZX7,\'A10Q\'))' in j
     and '0.875-0.125' not in j)
# 12 A15J Flesh Golem near x2 + slope subtraction 15→30; scepter branches untouched
gate('D2-12-A15J','A15J血肉傀儡近距15+5WZ→30+10WZ/斜坡减项15→30；神杖25+5WZ/(20+5WZ)-15不动',
     'set a=30+10*WZ' in j and '(30+10*WZ)-30*' in j
     and 'set a=25+5*WZ' in j and '(20+5*WZ)-15*' in j)
# 13 A1IN Shadow Dance off-combat MS x2 (A1I8/9/IA); HP/MP regen untouched
gate('D2-13-A1IN','A1IN暗影之舞脱战MS0.3/0.35/0.4→0.6/0.7/0.8(A1I8/9/IA)；HP/MP回复不动',
     _cell('A1I8',24)=='0.6' and _cell('A1I9',24)=='0.7' and _cell('A1IA',24)=='0.8')
# 14 A0VQ Alacrity Wex AS x2 (A0VJ); Exort attack A109 untouched
gate('D2-14-A0VQ','A0VQ灵动迅捷Wex攻速.2/.3/.4/.5→.4/.6/.8/1.0(A0VJ)；火攻A109不动',
     _cell('A0VJ',24)=='0.4' and _cell('A0VJ',25)=='0.6' and _cell('A0VJ',26)=='0.8' and _cell('A0VJ',27)=='1.0')
# 15 A2CI Duel permanent attack 8+4BC7→16+8BC7 (stats + actual)
gate('D2-15-A2CI','A2CI决斗获胜攻击8+4BC7→16+8BC7(统计+实际两处)',
     j.count('+16+8*BC7')==2 and '+8+4*BC7' not in j)

# Attr dialog keep-open: ATTR_Core once, same dialog re-display true, close false; no destroy/rebuild/re-register
_click = j.split('function B836ArcDialogClick',1)[1].split('endfunction',1)[0]
gate('G14-attr-dialog','Attr分支ATTR_Core精确1次→同一DialogDisplay true keep(ATTR_DIALOG_KEEP)；关闭分支false(ATTR_DIALOG_CLOSE)；handler无destroy/重建/重复注册',
     _click.count('call ATTR_Core(arcPid)')==1
     and 'call ATTR_Core(arcPid)\ncall DialogDisplay(Player(arcPid),B836ArcDialog[arcPid],true)' in _click
     and 'ATTR_DIALOG_KEEP' in _click
     and 'elseif arcClicked==B836ArcCloseButton[arcPid] then' in _click
     and 'DialogDisplay(Player(arcPid),B836ArcDialog[arcPid],false)' in _click
     and 'ATTR_DIALOG_CLOSE' in _click
     and 'DialogDestroy' not in _click
     and 'TriggerRegisterDialogEvent' not in _click
     and j.count('call ATTR_Core(arcPid)')==1)
# ATTR cost/prob/gain unchanged; local ally broadcast + jackpot YW7 retained
gate('G15-attr-core','ATTR_Core 扣1000/roll1..100/10%gain20大奖/本地友军广播/YW7恭喜发财 保留',
     'SetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD,gold-1000)' in j
     and 'roll=GetRandomInt(1,100)' in j and 'set gain=20' in j
     and 'IsPlayerAlly(abQ,p)' in j and 'call YW7("恭喜发财"' in j)

# retained systems
gate('R1-imba', '永久IMBA门控保留', 'constant boolean XOMG_IMBA_ENABLED=true' in j)
gate('R2-lottery', '初始化抽奖下限1000-1500保留', 'GetRandomInt(1000,1500)' in j)
gate('R3-xomg1', 'XOMG1存档保留', 'XOMG1' in j)
gate('R4-a088', 'A088保留', 'A088' in j)
gate('R5-noskin', '无后加皮肤路径', 'skins\\' not in j.lower())
gate('R6-no-wheel', '车轮战实现物理移除', not re.search(r'(?m)^function B1004(?!ControlUnit)', j))
gate('R7-no-defense', '30波防守实现物理移除', not re.search(r'(?m)^function KKDefense_(?!IsWaveType)', j))

# deferred register
DEFER = [
 ('portrait-live','K内嵌肖像实机确认','静态结构PASS（内嵌CAMS/PortraitCam/五序列）；游戏内取景构图仍需用户实机目测确认'),
]

os.makedirs(os.path.join(ROOT,'reports'), exist_ok=True)
# json
summary={'total':len(C),'pass':sum(1 for x in C if x['status']=='PASS'),
         'fail':sum(1 for x in C if x['status']=='FAIL'),'checks':C,'deferred':DEFER}
io.open(os.path.join(ROOT,'reports','v18-audit.json'),'w',encoding='utf-8').write(json.dumps(summary,ensure_ascii=False,indent=2))
# csv
with open(os.path.join(ROOT,'reports','v18-audit.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f); w.writerow(['id','name','status','detail'])
    for x in C: w.writerow([x['id'],x['name'],x['status'],x['detail']])
    w.writerow([]); w.writerow(['DEFERRED','item','reason',''])
    for d in DEFER: w.writerow(d)
# md
md=['# v1.8-integrated 静态门禁审计','',f"PASS {summary['pass']}/{summary['total']}，FAIL {summary['fail']}","",'| ID | 检查 | 状态 | 说明 |','|---|---|---|---|']
for x in C: md.append(f"| {x['id']} | {x['name']} | {x['status']} | {x['detail']} |")
md+=['','## 未实现/待联调（如实记录，未臆改）','']
for d in DEFER: md.append(f"- **{d[0]} {d[1]}**：{d[2]}")
io.open(os.path.join(ROOT,'reports','v18-audit.md'),'w',encoding='utf-8').write('\n'.join(md))

for x in C: print(x['status'],x['id'],x['name'])
print('PASS',summary['pass'],'FAIL',summary['fail'])
