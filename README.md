# DOTA OMG IMBA 独立维护工程

此目录以 `noskin19 / v1.8.5-noskin19-live-tested` 为实机稳定构建底包，当前正式版为 **v6.90a 1.0（Dota v6.90a OMG AI 1.0）**。后续只在 `D:\Dota_OMG` 中维护，不依赖旧项目源码或旧工具目录。

## 当前正式产物

- 正式地图：`maps/release/Dota v6.90a OMG AI 1.0.w3x`
- 正式版 SHA-256：`DFD19F9BCB7C35A2050A512C072F968FDF803F4C32A4BCEB84C9924561F68C29`
- 正式版大小：56,712,620 字节
- 稳定部署：`D:\游戏\Warcraft III\Maps\omg\稳定\Dota v6.90a OMG AI 1.0.w3x`，部署件 SHA 与构建件逐字节一致
- 版本标签（w3i 两槽均精确 24 字节）：
  - 版本号 `v6.90a-OMG-AI-1.0`：17 ASCII 字节 + 7 空格 = 24B（槽A@12，对应 `XOMG_VERSION`）
  - 显示名 `Dota v6.90a OMG AI 1.0`：22 ASCII 字节 + 2 空格 = 24B（槽B@234，对应 `SetMapName`）
- 继承自已验收 ART683-T10 的冻结内容：T2 建筑换模 `war3map.doo`（SHA `F6EA5428…F915`）、T5 64 格 Felwood 地形 `war3map.w3e`（SHA `55962DAE…9f593`）、T4 世界树 JW_JD TreeofLife 1.8、抽奖屋 nAS6 坐标 `-5728,-6816,270`、彩字标题 `SetTextTagPos(…,-128.,…,256.)` 与三按钮。

## 历史说明（保留）

- 前一正式版 `maps/release/DOTA-OMG-IMBA-v1.8.9-UIFIX.w3x`（SHA `DEE6D1F5…EBA1C`）已被 v6.90a 1.0 取代，文件保留在 release 目录仅作历史。
- ART683-T10 为已验收测试基线（抽奖屋标题水平 -128/256、T2 换模、T5 地形、T4 世界树），其内容由 v6.90a 1.0 逐字节继承；活动版本门中的 ART683-T10 测试标识已清除，仅历史报告保留。
- 稳定目录中 `Dota v6.93a OMG AI 1.0.w3x` 属于另一任务，本工程绝不修改、删除或覆盖。

## 目录说明

- `src/`：当前权威 JASS、W3I、IMP 及 8 个对象数据/文本文件。
- `assets/loading-screen/`：当前加载图、四分块 BLP 和地图预览图。
- `maps/baseline/`：实机正常的 noskin19 稳定构建底包；构建脚本会校验其 SHA-256。
- `maps/release/`：当前正式 W3X。
- `maps/build/`：历史本地重建输出（本版正式件直接落 release）。
- `tools/build/`：构建和两套回提验证脚本。
- `toolchain/`：随项目保存的 MPQEditor、PJASS、common.j 和 blizzard.j（不入库同步）。
- `reports/`：当前版本验证结果、历史阶段报告和本次发布证据。
- `PROJECT_MANIFEST.json`：全文件哈希清单与正式版指针。

## 构建

在 PowerShell 5.1 中执行：

```powershell
& "D:\Dota_OMG\tools\build\build.ps1"
```

默认输出（由 `config/tool-paths.json` 的 `outputMap` 指定）：

```text
D:\Dota_OMG\maps\release\Dota v6.90a OMG AI 1.0.w3x
```

构建流程会执行：

1. 检查稳定底包 SHA-256；
2. 运行 PJASS，只允许历史既有的 `location_m5` 诊断；
3. 将权威条目先删除再按小写 `units\` 路径写入；
4. 删除英雄 K 的 14 个专属物理资源；
5. 构建后手动重注入 T2 `war3map.doo` 与 T5 `war3map.w3e`（冻结 SHA 见上）；
6. 回提并校验脚本、对象数据、UI 文本、SLK 维度和功能锚点。

## 验证

```powershell
& "D:\Dota_OMG\tools\build\verify_v17.ps1" -MapPath "D:\Dota_OMG\maps\release\Dota v6.90a OMG AI 1.0.w3x"
```

当前预期为 122 项通过、0 失败。PJASS 只允许基图已有的 `location_m5` 未初始化诊断（war3map.j:155341）。发布证据见 `reports/release-v6.90a-1.0/`。

## 当前功能边界

- 无后加持久化皮肤商店、无防守模式、无车轮战。
- KK 持久化商店、哦买嘎币、熟练度、修炼境界、打赏、逃跑次数和减次卡已移除；纯当局抽奖屋独立保留。
- 英雄 K 及 KA01～KA04 已删除，喵刀战斗内容保留，但不再通过持久化权限发放。
- `-give 楼层 数量` 仅由名字以“小生”开头的玩家使用，只发放当局游戏金币。
- 完整调试命令和 `-setskill` 同样使用“小生”开头权限门。
- IMBA 核心倍率与旧 XM 模式解耦。
- 野怪 10% 掉装备；10 分钟后切换全部有效成品池。
- 地面装备可鼠标左键双击出售，使用联机同步安全实现。
- 抽奖屋含“幸运大抽奖（免费1次）”“1000抽属性（无限次）”“梭哈抽属性”。
- `-alt` 切换野怪营地范围线常驻显示。
- 屠夫、影魔、炼金术士为原名；“达拉然势力”已统一改为“近卫军团”。

## 维护注意

- 禁止重新运行历史 K 生成器或从旧项目覆盖当前 SLK。
- 删除 SLK 尾部对象时，必须同步更新 `B;Y` 声明，并保持唯一末尾 `E`。
- 修改地图内条目时沿用“先 delete、后 add”，路径统一使用小写 `units\...`。
- 新版本必须同步修改 `XOMG_VERSION`、`SetMapName` 及 W3I 两个固定 24 字节名称槽，并同步 `build.ps1`、`verify_v17.ps1`、`config/tool-paths.json`。
- 正式版先经构建与回提验证通过后，再部署到稳定目录；稳定目录旧件先备份核验哈希再移除。
