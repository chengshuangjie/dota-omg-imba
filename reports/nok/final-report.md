# v1.8.6-NOK 最终候选验收报告

- 基线提交：`a2c66730b818978810203d73e77394d2c1b87428`（HEAD 未变）
- 分支：`nok-v186`（隔离 worktree：`D:\dota\DOTA-OMG-IMBA-NOK-worktree`，未污染主 repo）
- 版本：`v1.8.6-NOK`（`XOMG_VERSION` 与 `SetMapName("OMG IMBA v1.8.6-NOK")`，无 K-W3IFix 残留）

## 最终候选包
- 绝对路径：`D:\dota\DOTA-OMG-IMBA-NOK-worktree\maps\build\DOTA-OMG-IMBA-v1.8.6-NOK.w3x`
- 大小：47,438,761 B
- SHA256：`5be8dc5b4b20a75c209a76f5ef391aaa05e99c071bb37129e386c51332fba701`
- w3i：806 B；NOK 24B 标签 `OMG IMBA v1.8.6-NOK`+5 空格 精确出现 2 次；槽外/players/forces 与基线逐字节一致。

## 门结果
| 门 | 结果 |
| --- | --- |
| PJASS | 仅余基线既有 location_m5，无其它诊断 |
| verify_v17 回读语义 | 80 pass / 0 fail |
| 梭哈确定性边界（999拒/1000 1..2/4999 1..8/5000 10..250/10000 20..500） | PASS；失败 0 随机 0 扣款；成功单随机1次→清0金币→base 永久三属性同增 |
| -alt 常驻 16 态真值表 | PASS；P1/b0 营地0.70塔.01，P0 完全等旧；零新建句柄/timer/frame/effect/lightning |
| 池模拟 | PASS；K54=117(HMD0 保留)、K_4=39、稳定117、AI 41/37/39、roll bad=0 |
| MPQ 包完整性 | IMP 1880 条全部在包内；禁止 K 资源 0；无孤儿 K；基线未打包 K 英雄资源（无需显式删除） |
| 回提哈希 | 11/11 OK（j/w3i/imp/5 SLK/AbilityData/2 Campaign） |
| 包内内容标记 | ALLIN/LOTTERY/三按钮/JALTPIN/掉落提示/抽奖屋在场；包内 j 无 H0K0/KA01-04/K 目录/BTNK_Hero/K_final_v2 |

## 新增四项功能
1. **抽奖屋**：选中 nAS6 小屋直达 LOTTERY_DIALOG（不经存档页）；恰 3 业务钮固定顺序：幸运大抽奖（每局1次1..1000，规则不动）、1000抽属性（无限次）（原双杰，1000/次原 prob 三属性队友可见）、梭哈抽属性；关闭为唯一非业务控制；成功/失败均重显，仅关闭隐藏。
2. **梭哈 ALLIN_Core**：同步单结算；真人/在局/本人 M7 主英雄存活/本人所有/非幻象/金币≥1000，任一失败 0 随机 0 扣款 0 增益；G<1000 提示不足；1000≤G<5000 n=⌊G/1000⌋ gain=rand(1,2n)；G≥5000 b=⌊G/100⌋ gain=rand(max(1,b/5),5b)；单随机→清0→base 永久 STR/AGI/INT（不走 B67/IMBA×2）。队友广播逐人显式排观察/离开。
3. **野怪掉落提示**：真实每次掉落给真人的提示末尾加「，可鼠标双击直接出售」；对象/频率/双击机制/early-late/AI 不变。
4. **-alt 常驻营地线**：本地 scalar `AltRefreshPinned`（不持久化）；JALTPIN 本地 flip→AHC(当前Alt)→开/关提示；营地 `AltRefreshPinned or (b and AltShowRefreshRange)`，塔圈仍 `b and AltShowAttackRange`；cUpdateCallback 边沿原样；复用既有 56 营地 lightning/22 塔 effect。

## 三英雄精准改名（仅 CampaignUnitStrings 精确段，未全局替换）
- 屠夫[U00F]/[Z00F]：Name→屠夫，Propernames/Tip 恢复「胖子」，Awaken/Revive→复活屠夫，Ubertip 英雄名→屠夫；j 皮肤面板【27】仅改名屠夫（不启用皮肤）。
- 影魔[Nfir]/[Zfir]/[Zgir]/[Zhir]：Name/Tip→影魔，Awaken/Revive→复活影魔，Propernames 恢复完整选手池，Ubertip 3 处英雄名→影魔。
- 炼金[N01I]：Name/Tip→炼金术士，Propernames→拉泽尔．黑酿，Awaken/Revive→复活炼金术士，Ubertip 句首→炼金术士；[N01H]/[N01J]/[N01T] Name→炼金术士、Propernames 同上，删除误注入 Tip 行。
- [nAS6] 静态 Name/Tip→抽奖屋；Ubertip 定点改为准确说明（抽奖屋含幸运大抽奖/1000抽属性（无限次）/梭哈抽属性，操作完重显、主动关闭才隐藏；个人存档另输 -archive）；未改 -archive 存档弹窗 title，存档系统/权限/接口全保留。

## 红线保持
H00K 凯哥、HMD0 喵刀、作者小生我怕怕、YW7「我才是袁加凯」(E02X/Z02X)、调试串 A29J/A1MP/A1MU、UpdateLog 历史、非指引「双杰抽属性」历史引用均未动。历史审计报告保留为证据，不纳入活动零残留扫描。

## 编码/字节
- 6 张 SLK + CampaignAbilityStrings 相对 HEAD PLUS=0（仅删 K 行/单元格）；UnitUI 维持仅删 H0K0 块、GBK 原字节，未改 X2 内部名。
