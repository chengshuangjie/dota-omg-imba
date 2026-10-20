# v6.90a-1.0 发布前只读基线冻结报告

- 冻结时间：2026-10-20 16:41:37 +08:00
- 执行方：独立验收代理（只读；未修改工程、工具、稳定目录任何文件）
- 状态：**新 release v6.90a-1.0 尚未出现**；本报告只冻结发布前基线，等待 release 出现后再执行独立验收。

## 1. 稳定目录现状（`D:\游戏\Warcraft III\Maps\omg\稳定`）

| 文件 | 字节 | SHA-256 | 处置 |
|---|---:|---|---|
| Dota v6.93a OMG AI 1.0.w3x | 82,298,058 | `BC7B71D74D96898AFBAA01C3BFC9D77FE637C88E9E0D941CD53170DEC1E94890` | 另一任务保护文件，发布前后哈希必须**完全未变** |
| DOTA-OMG-IMBA-v6.9-FISSURE-T1.w3x | 56,602,080 | `1847C96BF5201072A569CEC2ECC24E79ACA163CB4C852CEF95E4AF5087842195` | 旧 FISSURE，发布后须先**备份并移出**稳定目录，目录内不得再保留 |

冻结时稳定目录仅有以上 2 个文件，无子目录、无隐藏项。

## 2. T10 权威包

| 项 | 值 |
|---|---|
| 构建包 | `maps\build\DOTA-OMG-IMBA-v6.9-ART683-T10.w3x` |
| 部署副本 | `D:\游戏\Warcraft III\Maps\omg\imba69\DOTA-OMG-IMBA-v6.9-ART683-T10.w3x` |
| 字节 | 56,712,660 |
| SHA-256 | `D5E7A02D5A9A9276434FC8643461240256A7BD997A5A5FF394AFC2A9AC0E672A` |
| 构建==部署 | 是（独立复算一致） |

## 3. 参考组件冻结（release 回读比对基准）

| 组件 | 期望 SHA-256 | 字节 | 来源 |
|---|---|---:|---|
| war3map.doo（=T2 换型） | `F6EA5428531D04AC680F9D51B318BE5B65E776B58BC342BB5004E32B2F0BF915` | 269,924 | T2 构建包内 war3map.doo，独立复算匹配 |
| war3map.w3e（=T5 64格） | `55962DAE4021A0ECA6DAD6011E9A37B00459362BC062725260D6799FB8E9F593` | 116,584 | T5 构建包内 war3map.w3e，独立复算匹配 |
| war3map.wpm（=FISSURE） | `61CCF7597378FDE26858B061AE174082543FBB25E07D0E4E3C91CB035A1F11A9` | 262,160 | 旧 FISSURE 包内 war3map.wpm，独立复算冻结 |

## 4. 版本标签 ASCII 字节与 24B 填充核算

W3I 固定 806B；两名称槽各 24B（槽A@12，槽B@234），其余字节与 noskin19 基线逐字节相等。

| 槽 | 字面量 | ASCII 字节 | 空格填充 | 合计 |
|---|---|---:|---:|---:|
| 槽A@12 XOMG_VERSION | `v6.90a-OMG-AI-1.0` | 17 | 7 | 24 |
| 槽B@234 显示名 | `Dota v6.90a OMG AI 1.0` | 22 | 2（22+2） | 24 |

## 5. 发布前观察（不作为权威冻结值）

- 冻结时 `src/war3map.j`、`src/war3map.w3i` 正被构建方编辑，标签已切到 v6.90a；属瞬态，release 出现后以 release 包回读为准。
- 现有 `README.md`、`PROJECT_MANIFEST.json` 仍描述旧版本（v1.8.9-UIFIX / v6.9-CLEAN-TEST）；验收时必须已更新为新 release 的路径/版本/哈希/大小，且 MANIFEST JSON 合法。
- 验收不执行任何 Git 操作；最终报告另附 Git 同步清单安全评审与推荐/禁止上传路径。
