# DOTA OMG IMBA 轻量化

基于 DOTA69AI 历史工作目录抽出的独立轻量化工程，以 OMG 随机技能 + IMBA 玩法为核心。本仓库只收录可公开的源码、构建脚本、配置模板与审计报告；地图二进制（.w3x）不入库，需在本地按下方步骤构建。

## 目录

```text
src/                    权威源码与数据
  war3map.j             功能修改入口
  war3map.w3i           内置地图名与版本信息
  war3map.imp           已删除后加皮肤资源的导入表
  data/Units/           五张 SLK、技能说明与英雄显示名文本
maps/baseline/          只读基线地图（本地保留，不入库）
maps/build/             每次构建生成的开发地图（本地生成，不入库）
assets/loading-screen/  加载图与预览图
config/tool-paths.example.json  本机构建工具路径模板
config/tool-paths.json          本地实际配置（已 gitignore，不入库）
tools/build/            可复现构建与包内回读验证
tools/transform/        轻量化形成过程的变更脚本，仅用于追溯
reports/                模式/资源/SLK/皮肤/充值链/XOMG1/IMBA 审计报告
```

## 当前功能

- 普通 OMG 随机技能、IMBA/AI 逻辑、普通守塔与基地推进。
- 熟练度、修炼境界、称号、哦买嘎硬币、知识之书、寒铁钢爪、喵刀等系统。
- 进图奖励、`-recharge` 充值命令与 `-rlog` 本地诊断日志。
- **XOMG1 存档协议**：所有 ServerValue / Stat 键统一隔离到 `XOMG1_` 前缀，记录带外层 v1 信封；空键为内存默认、不主动写服务器、不读取/迁移任何旧键；未知版本/损坏/API 错误即故障锁写并本地诊断。
- **永久 IMBA 规则层**：使用独立 `XOMG_IMBA_ENABLED=true` 与固定 `IMBA_POWER=2`，不再被旧难度或 `-neng` 关闭。统一技能伤害入口正向技能伤害 ×2（排除生命移除/直接生命操作，Fort 不重复叠乘）、统一技能治疗 ×2、已审计控制/持续时间/概率/非实体次数按规则增强；距离、范围、弹道速度、冷却、蓝耗、召唤数量和召唤寿命保持不变。
- **初始化抽奖**：按钮不再依赖旧 `XM_MODE`；有效物品池非空时有 50% 获得价格 ≥1000 的装备，否则获得 1000–1500 金币。
- **中立野怪掉落**：普通中立野怪死亡后固定10%概率掉落真实成品装备。前10分钟从价格`1–1000`的有效成品池抽取；游戏时间达到600秒后切换到无价格上限的全部有效成品池。两池都排除魔瓶族、卷轴、任务奖励、powerup和不可售内部物品。
- **野怪装备快速出售（v1.8.5-SYNCF001）**：英雄位于装备600范围内时，鼠标左键双击带野怪来源标记的地面装备，可按商店价50%快速出售。客户端本地回调只同步玩家编号和鼠标地形坐标，不创建Warcraft句柄、不枚举物品、不传本机handle ID；所有客户端在统一同步回调中选择、删除物品并加金币，临时`Rect`和`boolexpr`会显式释放。
- **掉落实机诊断**：开局把`DROP_POOL_INIT`、前若干次`DROP_ROLL`及所有`DROP_OK`写入`1-miao-error\imba-runtime.text`；游戏内输入`-droptest`可显示池状态并生成测试装备，该命令只用于测试、不写存档。
- **四英雄改名**（类型名、专有名、选择/复活/详细说明等玩家可见字段同步，rawcode/模型/技能不动）：屠夫→袁加凯、影魔→程双杰、炼金术士→土鸡、炸弹人→凯哥。
- **技能 UI 实际值**：`CampaignAbilityStrings.txt` 与运行规则同步；例如沟壑显示并结算 220/320/420/520 伤害、2/2.5/3/3.5 秒眩晕、16 秒地形，施法距离仍为 1400。
- **v1.4-K 独立新英雄 K（H0K0）**：近战敏捷原创英雄，四技能 KA01 猎手本能（击杀真实英雄永久敏捷+1/2/3/4，同次死亡去重）、KA02 捷刃（有效普攻20%额外物理=总敏捷×1/1.5/2/2.5，合成/反射不触发、防递归、不吃 IMBA×2）、KA03 加凯（800半径、当前总敏捷快照×2/3/4/5 魔法伤害、CD10、每目标一次，排友军/死亡/建筑/守卫A04R/魔免/无敌）、KA04 凯哥牛逼了（15/17/20秒、CD80/65/50、临时+S/2S/3S，重施先清旧、generation 防旧timer、死亡/到期只扣本次增量、永久成长保留）。模块直伤直减，不走 B67/XOMG 通用 IMBA 放大。
- **版本标识 v1.6-K-VisualFix**：运行标识 `XOMG_VERSION="v1.6-K-VisualFix"`，`SetMapName("OMG IMBA v1.6-K-Visible")`，W3I 内置地图名同步。保留 v1.5 的能量圈原抽奖、独立“凯哥发福利”；K（H0K0）回归普通敏捷候选池自然抽取，无权重/保底/特殊排除。同时把K从加载诊断对象恢复为完整固定四技能英雄：`H0K0` 的 `modelScale` 从1.2校正为120，英雄选择头像不再使用黄色加点占位图，新增带相机的 `K_final_portrait.mdx`，KA01–KA04采用标准英雄学习等级并在创建/复活时恢复可见；K不再进入通用OMG随机技能分配。连续SLK、`K_Hero`模型名和1.24兼容BLP修复继续保留。
- 玩家可见作者统一为“小生我怕怕”；最终胜利致谢固定为“感谢小生我怕怕、小生我看破、小生我顿悟”。
- 物理移除车轮战、30 波防守、后加皮肤资源与运行逻辑。

## 环境准备

需要本机已安装 MPQEditor、PJASS 与 Warcraft III 1.24 的 `common.j` / `blizzard.j`。

```powershell
# 在仓库根目录
Copy-Item config/tool-paths.example.json config/tool-paths.json
# 然后编辑 config/tool-paths.json，填入本机 MPQEditor.exe / pjass-latest.exe / common.j / blizzard.j 的实际路径
```

## 构建

在仓库根目录的 PowerShell 中执行：

```powershell
./tools/build/build.ps1
```

构建脚本会：

1. 对 `src/war3map.j` 执行 PJASS 检查（仅允许基图既有的 `location_m5` 未初始化告警）。
2. 把基线地图复制到系统临时 ASCII 目录，避免 MPQEditor 对中文长路径静默失效。
3. 逐项写入源码、W3I、IMP、两张玩家可见文本、五张 SLK 与加载图资源。
4. 写入完成后复制到 `maps/build`。
5. 从成品 W3X 回读 10 个运行关键文件并核对 SHA-256。
6. 检查无后加皮肤路径、无车轮战/防守实现，以及永久 IMBA 门控、抽奖下限、抽奖入口、英雄可见名、沟壑实际结算/UI、唯一版本号和中立野怪掉落链（`ZU`成品池、固定10%、价格上限、日志、测试命令）。

## 单独验证

```powershell
./tools/build/verify.ps1 -MapPath "maps/build/DOTA-OMG-IMBA-轻量化开发版.w3x"
```

结果写入 `reports/verification-latest.json`。

## 已知告警

PJASS 仅报当前 `location_m5 没有初始化`，为基图既有项，已在 `build.ps1` 中按单条诊断白名单放行；验证器不会再因输出中含该字符串而放过其他错误。

## 发布前外部待办（KK 平台）

本地为纯静态/构建级验证，无法模拟 KK 真实服务器。发布前需在 KK 侧完成：

1. 完成个人认证，创建或认领新地图项目。
2. 为 `XOMG1_` 系列键开通 ServerValue 与 Stat 服务器存档规则 / 写入权限（新键空档，未开通前线上读写会失败）。

## 开发约定

- 功能开发从 `src/war3map.j` 开始。
- 不直接编辑 `maps/baseline` 中的地图。
- 每次构建后以包内回读结果为准，不能只看 MPQEditor 退出码。
- `tools/transform` 是历史可复现脚本，不作为日常构建入口。
- 达拉然缓存补丁、平台缓存与历史失败充值目录未带入本工程。

## 版本标识 v1.7-K-VisualSkillFix（独立构建，不覆盖旧部署）

- 运行标识 `XOMG_VERSION="v1.7-K-VisualSkillFix"`，`SetMapName("OMG IMBA v1.7-K-VisualSkillFix")`，W3I 内置地图名与 F9 全局描述同步；独立文件，不覆盖 v1.6-K-Visible/noskin5。
- 四技能改为克隆本图已实机可学的原生母本，四个 basecode 互异、四个 order 互异，禁用 Aamk×2 / ANcl×2，不使用 ANcl/AOwk/Achl：
  - KA01 猎手本能（被动）← AHad 虔诚光环母本，reqLevel1、4 级。
  - KA02 捷刃（被动）← AEev 闪避母本，reqLevel1、4 级。
  - KA03 加凯（无目标主动 AOE）← AHds 神圣护盾母本，order=divineshield，reqLevel1、4 级、CD10×4、cost0。
  - KA04 凯哥牛逼了（大招）← ANdo 末日母本，order=doom，6/11/16 学习，3 级、levelSkip5、reqLevel6，CD80/65/50；不换模型、不改顶点色、不加蓝色滤镜、不进 ZCRG、不加炼金再生。
- 视觉接入 K-v2：主模型 `K_final_v2.mdx`、`K_body.blp`、专属英雄按钮 `BTNK_Hero`/`DISBTNK_Hero`，四技能 Art/ResearchArt 全部改用包内专属 `BTNK*` 按钮并配各自 DIS；禁用 PASBTN，主模型 modelScale 校正为 1.0 附近。
- 兼容链双保险：`SuijiMode_ChemicalRageCompatApply` 与 `SuijiMode_SetVisualForm` 两个入口均对 `H0K0`/`KA04` 直接 return，阻断炼金化学狂暴换模/换色/滤镜/再生链。
- 完整保留 IMBA、初始化抽奖、中立野怪掉落、凯哥发福利/属性、A088、XOMG1、无皮肤、防守（已物理移除）、车轮（已物理移除）；K 原技能数值与模块（SK3 加凯等）不变。
- 静态/构建级通过，未冒充实机；自定义 portrait 模型因 UnitUI/UnitData 无 portrait 字段、`MHUnit_SetPortrait` 为空 stub 暂未接线，作为动态缺口如实记录。

## 版本标识 v1.8.5-SYNCF001（noskin19实机通过基线）

- 权威来源为`noskin19`成品地图的包内回提内容；运行标识`XOMG_VERSION="v1.8.5-SYNCF001"`，W3I两个固定24字节名称槽均为`OMG IMBA v1.8.5-SYNCF001`。脚本`SetMapName`保持已验证可加载基线字符串，不为统一显示而修改已通过实机的脚本。
- 累计保留v1.8的男神称号、双杰抽属性队友可见和弹窗保持、斯温/莱恩数值、魔瓶修复、K测试期真人50%候选逻辑、喵刀直选、HP4增强、无皮肤/无防守/无车轮边界。
- 野怪掉落前10分钟使用价格1–1000池，600秒后使用全部有效成品池，固定10%掉率不变。
- 地面装备左键双击出售按半价结算；本地鼠标回调只发送玩家编号与点击坐标，物品枚举、认领、移除和金币写入均在同步回调中执行，避免各客户端用本机handle ID造成装备状态分叉。
- 用户已完成单局实机验证：地图可正常完成对局、装备双击出售正常、10分钟后掉落规则未出现异常。长期双人同步仍建议持续观察。
- `.w3x`二进制不上传Git；仓库保存可复现的源码、对象数据、资源、构建器、同步修复脚本和验证报告。

## 版本标识 v1.8-integrated（历史说明）

- 运行标识 `XOMG_VERSION="v1.8-integrated"`，`SetMapName("OMG IMBA v1.8-Integrated")`，W3I 两个 24 字节名槽（0x0C/0xEA）精确写入 `OMG IMBA v1.8-Integrated`，槽外与 a1c1de1 806B 基线 100% 一致；独立输出 `maps/build/DOTA-OMG-IMBA-v1.8-Integrated.w3x`。
- **称号**：仅 r==2 显示由“本图女神”改为“本图男神”；DOTA女神/权限/身份/颜色/key 不动。
- **ATTR 双杰抽属性广播**：成功结算后按本地视角仅向本人 + IsPlayerAlly 且 B836ArcHuman/playing/未离开/非观察显示一次，含玩家名/gain/累计，大奖带标识；本人旧消息 ClearTextMessages 替换；YW7 恭喜发财保留；日志仅本地不广播；费用/概率/加成不改。
- **斯神威神 A1WH/Y0EP/YE1A/X1WH**：selfRate=1.+1.*level（额外基础攻击 200/300/400%），allyRate=1.+.5*level（友军 150/200/250%）；持续 25s/神杖 35s 保持，不参与通用时长增强；UI 四形态同步；GOD_STRENGTH 限流本地日志。
- **莱恩死亡一指 A095/A09W/Y0BZ/Y0C1**：SXI 两处 + SWYJ_DT 一处成长 +20→+50（精确 3 处），SWYJPD 去重保持，base+SWYJ 每目标仅一次进 B67；UI 明确基础+50/本图实际+100；浮字/-st 显示基础累计 X/实际 2X；FINGER_GROW 日志。
- **魔瓶族**：12 索引 XZ/AZ/BZ/CZ/IA/YA/HJ0/HJ1/WA/QA/NA/JA 的 SU/ZU/BU 全族在 B1063 池构建与名称判据中排除（低价池候选=0）；野怪 CreateItem 后按 handleId 写来源标记(raw/price/time/claimed/sellable)；真人主英雄 PICKUP 标记+内部瓶态+缺 BottleTarget 时安全替换为满瓶 SU[XZ]=I00L，复制 charges/SetItemPlayer/SetItemDroppable/SetItemPawnable，BOTTLE_FIX 限流日志；商店瓶/空瓶装符不转换；D78 保持未启用。
- **选人预览 UI**：`SuijiTavern_Fill` 以 logical rawcode 入 stock；`tools/transform/sync_preview_ui.py` 为可复现映射/逐字同步/覆盖生成器（check-only，116 池内文案一致；池外 32 处历史克隆差异不在本轮改动）。
- **K 回归普通敏捷池**：撤销历史真人 50% 测试注入（删除 K_POOL_ROLLED/K_POOL_HIT、50% 骰、首敏捷槽强插、hit/miss 分支、NoK 排除与 K_POOL_ROLL 日志）；H0K0=K24[40] 以与同类相同的权重进入共享敏捷候选池，由池大小+J 不重复自然决定，无权重/保底/特殊排除；K 本体/四技能/模型/按钮/w3i 全部保留。
- 完整保留 IMBA、初始化抽奖、泉水/A4DK/B836 福利、中立野怪 10%、XOMG1、A088、无皮肤/防守/车轮。
- **喵刀直选 HMD0（117）**：nMv4 选中记录 SELECT_MIAO_DISPLAY/CLICK；有权限（B891ArcMiaoActive+Human+未Replaced+未Busy）且 M7 空 → DzSyncData("MIAO_REQ") 并提示，无权限 X37 获取文案 + SELECT_MIAO_DENY；线上出生缝 Q19/通用循环在正常决出后、CreateUnitAtLoc 前，request+Allowed → UB7=117、J[117]=true、Replaced=true、SELECT_MIAO_CREATE；AI 不覆写；B891MiaoReplace 开局3分钟路径独立不动。HMD0 仍被普通/AI 池排除。
- **野怪地面双击直售 DROP_SELL**：本地左键 0.35s 同玩家双击 → DzGetMouseTerrainX/Y → Rect 近邻枚举最近带标记/未认领/可售/非瓶族地面物 → DzSyncData；接收方确定性复核真人/M7活/IsUnitInRangeXY<=600/标记/地面/未认领，首达原子 claimed，sale=Get_Item_Price(raw)/2 下取整，清标 RemoveItem，SetPlayerState 加 gold（卖出不扣金），提示一次；失败限流 far/not-ground/not-marked/duplicate。PICKUP 已先清直售资格，DROP 清标不恢复。
- **掉落 EARLY/LATE 双池**：EARLY=price 1..1000 有效成品，LATE=全部有效成品无 1000 上限，共用同一 B1063ItemEligible 探针（排魔瓶族/卷轴/任务奖励/powerup/不可售内部）；TimerGetElapsed(W)>=600 同步切 LATE，各自空池保护，GetRandomInt 同步；10% roll=GetRandomInt(1,10) roll==1 原样不动；日志 DROP_POOL_INIT early_count/late_count、DROP_ROLL、DROP_OK。
- **AI 标记物保护**：GWF 公共选择器排带来源标记地面物（同时关拾取+攻击）；GXF 拾取 $D0003/攻击 $D000F 分支各自 marked skip；IHG 拾取事件在任何 MarkClear 前拒/不换件；Y9F/YDF/YUF/YBE/LDF 信使投递/售物回收/背包/靴落收集在 owned 判定后加 marked skip；限流 DROP_AI_*_SKIP/pid≤12；不影响 AI 商店购买/一键购/信使槽位/熊灵/Roshan/XVO/人类 DROP_SELL。
- **HP4 15 个确认漏增强核心维度×2**：A0CY攻100/200/300、A1EJ攻速1.2/2.4/3.6、A0FV每层30+10L、A0VC敏捷80/120/160、A0ER回复50/100/150(神杖50/75/100不动)、A034护甲20/30/40(双写)、A04Q生命上限.6+.40L、A0E2永久护甲+4、A0NS窗口8+2BC7、A10Q减CD.75-.25L、A15J近距30+10WZ、A1IN脱战MS.6/.7/.8、A0VQ Wex攻速.4/.6/.8/1.0、A2CI获胜攻击16+8BC7；A12P 为引擎.02攻速硬上限/攻击保留率 tradeoff，无数值可翻，不伪改。范围/距离/召唤/自身CD/蓝耗一律不动。
- **K 内嵌肖像**：count1 候选（内嵌 PortraitCam CAMS=1，前54029B 与原 v2 逐字节相同，VERS800/五序列/MTLS/TEXS/GEOS/BONE/PIVT 不变，11 处 K_body）合入运行时 K_final_v2.mdx；UnitUI 主模型路径不变，经典默认肖像读内嵌 CAMS；独立 K_final_portrait.mdx 保留。
- **待实机确认（静态已 PASS）**：K 内嵌肖像游戏内取景构图需用户实机目测；2 冲突项/8 Unknown 禁猜、89 排除未动。
