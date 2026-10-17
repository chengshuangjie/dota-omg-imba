# v1.8-integrated 静态门禁审计

PASS 38/38，FAIL 0

| ID | 检查 | 状态 | 说明 |
|---|---|---|---|
| G1-title | 称号 r==2 本图女神->男神, DOTA女神保留 | PASS | 女神=0 男神=1 DOTA女神=1 |
| G2-attr | ATTR 本地视角友军广播/本人替换/敌方观察离开排除 | PASS |  |
| G3-sven | 斯温 selfRate=1+1*level / allyRate=1+.5*level, 旧公式=0 | PASS |  |
| G4-lion | 莱恩 SWYJ +50 精确3处/+20=0/FINGER_GROW x3/UI基础50实际100 | PASS |  |
| G5-bottle | 魔瓶族排除池/来源标记/PICKUP转换SU[XZ]/BOTTLE_FIX | PASS |  |
| G6-preview | SuijiTavern_Fill 入 logical; 同步生成器存在 | PASS |  |
| G7-k-normal | H0K0回归普通敏捷池：K_POOL/50%骰/NoK排除全部0；K24[40]成员x1；四技能R1X保留 | PASS |  |
| G8-version | XOMG_VERSION/SetMapName v1.8 | PASS |  |
| G8-w3i | w3i 806B/新名x2/旧v1.7.1=0/槽外同a1c1de1 | PASS |  |
| G9-miao | 喵刀 nMv4点击请求/MIAO_REQ同步/出生缝UB7=117/SELECT_MIAO_CREATE/权限门 | PASS |  |
| G1-drop | DROP_SELL双击/近邻枚举/原子claimed/半价加gold/RemoveItem/失败原因 | PASS |  |
| G11-pool | 掉落EARLY(1..1000)/LATE(无cap)双池/600s切换/非pawnable排卷轴内部/各自空池保护 | PASS |  |
| G12-portrait | K主模型内嵌CAMS=1/VERS800/K_Hero/闭合/SHA e4204138 | PASS | len=54157 vers=800 modl=K_Hero cams=1 |
| G13-ai-guard | AI标记物保护：GWF选择器/GXF拾取攻击/IHG拾取/Y9F/YDF/YUF/YBE/LDF 全部marker skip，商店购买不拦 | PASS |  |
| D2-01-A0CY | A0CY长大 攻击50/100/150→100/200/300(A4T3) | PASS |  |
| D2-02-A1EJ | A1EJ战斗专注攻速0.6/1.2/1.8→1.2/2.4/3.6 | PASS |  |
| D2-03-A0FV | A0FV战意 每层15+5L→30+10L(施法/到期/恢复三处) | PASS |  |
| D2-04-A0VC | A0VC射手天赋敏捷40/60/80→80/120/160(A2NX) | PASS |  |
| D2-05-A0ER | A0ER守护天使回复25/50/75→50/100/150；神杖50/75/100不动；A0ER/Y0CI双写 | PASS |  |
| D2-06-A12P | A12P集中火力=引擎.02硬上限/攻击保留率tradeoff，不伪改(无数值插点/不改.02) | PASS |  |
| D2-07-A034 | A034伤害加深护甲10/15/20→20/30/40；A034/Y0BD双写 | PASS |  |
| D2-08-A04Q | A04Q死亡契约生命上限.3+.20K→.6+.40K；攻击SDD .03+.02K不动 | PASS |  |
| D2-09-A0E2 | A0E2淘汰之刃永久护甲+2→+4/次 | PASS |  |
| D2-10-A0NS | A0NS回光返照窗口4+BC7→8+2BC7(10/12/14s)；阈值/转治疗不动 | PASS |  |
| D2-11-A10Q | A10Q编织减CD因子.875-.125L→.75-.25L(两处)+UI .25+.25L | PASS |  |
| D2-12-A15J | A15J血肉傀儡近距15+5WZ→30+10WZ/斜坡减项15→30；神杖25+5WZ/(20+5WZ)-15不动 | PASS |  |
| D2-13-A1IN | A1IN暗影之舞脱战MS0.3/0.35/0.4→0.6/0.7/0.8(A1I8/9/IA)；HP/MP回复不动 | PASS |  |
| D2-14-A0VQ | A0VQ灵动迅捷Wex攻速.2/.3/.4/.5→.4/.6/.8/1.0(A0VJ)；火攻A109不动 | PASS |  |
| D2-15-A2CI | A2CI决斗获胜攻击8+4BC7→16+8BC7(统计+实际两处) | PASS |  |
| G14-attr-dialog | Attr分支ATTR_Core精确1次→同一DialogDisplay true keep(ATTR_DIALOG_KEEP)；关闭分支false(ATTR_DIALOG_CLOSE)；handler无destroy/重建/重复注册 | PASS |  |
| G15-attr-core | ATTR_Core 扣1000/roll1..100/10%gain20大奖/本地友军广播/YW7恭喜发财 保留 | PASS |  |
| R1-imba | 永久IMBA门控保留 | PASS |  |
| R2-lottery | 初始化抽奖下限1000-1500保留 | PASS |  |
| R3-xomg1 | XOMG1存档保留 | PASS |  |
| R4-a088 | A088保留 | PASS |  |
| R5-noskin | 无后加皮肤路径 | PASS |  |
| R6-no-wheel | 车轮战实现物理移除 | PASS |  |
| R7-no-defense | 30波防守实现物理移除 | PASS |  |

## 未实现/待联调（如实记录，未臆改）

- **portrait-live K内嵌肖像实机确认**：静态结构PASS（内嵌CAMS/PortraitCam/五序列）；游戏内取景构图仍需用户实机目测确认