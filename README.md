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
- **中立野怪掉落**：普通中立野怪死亡后固定 10% 概率掉一件价格 `1–1000` 的真实成品装备。掉落池从商店 `ZU` 成品层构建，不再误用 `SU` 卷轴/占位层；事件按死亡单位 handle 去重，共享同步随机，不受 IMBA 概率倍率影响。
- **掉落实机诊断**：开局把 `DROP_INIT`（低价池数量）、前 12 次 `DROP_ROLL`（随机点数）及所有 `DROP_OK`（物品、价格）写入 `1-miao-error\imba-runtime.text`；游戏内输入 `-droptest` 可显示池状态并在出生点生成一件测试装备，该命令只用于测试、不写存档。
- **四英雄改名**（类型名、专有名、选择/复活/详细说明等玩家可见字段同步，rawcode/模型/技能不动）：屠夫→袁加凯、影魔→程双杰、炼金术士→土鸡、炸弹人→凯哥。
- **技能 UI 实际值**：`CampaignAbilityStrings.txt` 与运行规则同步；例如沟壑显示并结算 220/320/420/520 伤害、2/2.5/3/3.5 秒眩晕、16 秒地形，施法距离仍为 1400。
- **v1.4-K 独立新英雄 K（H0K0）**：近战敏捷原创英雄，四技能 KA01 猎手本能（击杀真实英雄永久敏捷+1/2/3/4，同次死亡去重）、KA02 捷刃（有效普攻20%额外物理=总敏捷×1/1.5/2/2.5，合成/反射不触发、防递归、不吃 IMBA×2）、KA03 加凯（800半径、当前总敏捷快照×2/3/4/5 魔法伤害、CD10、每目标一次，排友军/死亡/建筑/守卫A04R/魔免/无敌）、KA04 凯哥牛逼了（15/17/20秒、CD80/65/50、临时+S/2S/3S，重施先清旧、generation 防旧timer、死亡/到期只扣本次增量、永久成长保留）。模块直伤直减，不走 B67/XOMG 通用 IMBA 放大。
- **版本标识 v1.5-LotteryFix-K50**：运行标识 `XOMG_VERSION="v1.5-LotteryFix-K50"`，`SetMapName("OMG IMBA v1.5-K50-Fix")`，W3I 内置地图名同步为 `OMG IMBA v1.5-K50-Fix`。保留 loadfix5 的连续 SLK、`K_Hero` 模型名和兼容 BLP 修复；泉水能量圈恢复原初始化装备/金币抽奖，“凯哥发福利”只保留在存档商店且两者状态隔离；每次为真人生成或刷新候选英雄池时，K 精确 50% 出现，未命中时真人回退池排除 K，AI 抽取逻辑不变。
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
