# DOTA OMG IMBA 轻量化

基于 DOTA69AI 历史工作目录抽出的独立轻量化工程，以 OMG 随机技能 + IMBA 玩法为核心。本仓库只收录可公开的源码、构建脚本、配置模板与审计报告；地图二进制（.w3x）不入库，需在本地按下方步骤构建。

## 目录

```text
src/                    权威源码与数据
  war3map.j             功能修改入口
  war3map.imp           已删除后加皮肤资源的导入表
  data/Units/           五张 SLK（UnitAbilities/Balance/Data/UI/Weapons）
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
- **IMBA 规则层**（跟随现有 XM_MODE，共享 `IMBA_POWER=2`）：统一技能伤害入口正向技能伤害 ×2（排除生命移除/直接生命操作，Fort 不叠乘）、统一技能治疗 ×2、CommonUnitAddStun 正向眩晕时长 ×2（5 秒上限）。
- **初始化抽奖**：物品表初始化后构建独立候选池（登记成品、价格 ≥1000、可购买可掉落、排除任务/存档奖励/powerup 等），CHOUJIANG 每人每局一次同步随机，池空走金币兜底。
- **中立野怪掉落**：普通中立野怪死亡 10% 掉一件低价池物品（0<价≤1000），独立 trigger + handle 去重，共享同步随机。
- **四英雄改名**（UnitUI 显示名，rawcode/模型/技能不动）：屠夫→袁加凯、影魔→程双杰、炼金术士→土鸡、炸弹人→凯哥。
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
3. 逐项写入源码、IMP、五张 SLK 与加载图资源。
4. 写入完成后复制到 `maps/build`。
5. 从成品 W3X 逐项回读并核对 SHA-256。
6. 检查脚本中无后加皮肤路径、无车轮战/防守实现，且充值命令与诊断日志仍存在。

## 单独验证

```powershell
./tools/build/verify.ps1 -MapPath "maps/build/DOTA-OMG-IMBA-轻量化开发版.w3x"
```

结果写入 `reports/verification-latest.json`。

## 已知告警

PJASS 仅报第 155276 行 `location_m5 没有初始化`，为基图既有项，已在 build.ps1 白名单放行；除此之外无错误。

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
