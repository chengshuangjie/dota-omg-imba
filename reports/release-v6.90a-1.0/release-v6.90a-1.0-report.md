# v6.90a 1.0 正式发布报告（Dota v6.90a OMG AI 1.0）

状态：**FORMAL RELEASED**。构建件与稳定部署件 SHA-256 逐字节一致；verify_v17 122 项通过 / 0 失败；PJASS 仅既有 `location_m5`；T2 doo / T5 w3e 冻结哈希精确匹配；其他任务 `Dota v6.93a OMG AI 1.0.w3x` 原哈希未变。

## 1. 正式产物

| 项 | 值 |
|---|---|
| 正式地图 | `maps/release/Dota v6.90a OMG AI 1.0.w3x` |
| 字节数 | 56,712,620 |
| SHA-256 | `DFD19F9BCB7C35A2050A512C072F968FDF803F4C32A4BCEB84C9924561F68C29` |
| 稳定部署 | `D:\游戏\Warcraft III\Maps\omg\稳定\Dota v6.90a OMG AI 1.0.w3x`（哈希与构建件一致） |

## 2. 标签精确核算（24 字节固定槽）

| 槽 | 字面量 | ASCII 字节 | 填充 | 合计 |
|---|---|---|---|---|
| 版本号（槽A@12，`XOMG_VERSION`） | `v6.90a-OMG-AI-1.0` | 17 | 7 空格 | 24 |
| 显示名（槽B@234，`SetMapName`） | `Dota v6.90a OMG AI 1.0` | 22 | 2 空格 | 24 |

- JASS：`constant string XOMG_VERSION="v6.90a-OMG-AI-1.0"`（唯一 1 次）；`call SetMapName("Dota v6.90a OMG AI 1.0")`（唯一 1 次）。
- w3i 固定 806B，仅槽A@12、槽B@234 改变，其余字节与改前逐字节相等。
- 活动 ART683-T10 标识已从 JASS 两字面量、w3i 两槽、build.ps1、verify_v17.ps1、tool-paths.json 清除；verify_v17 另增 T10 两字面量零残留断言。历史 T4/T5/T6 变更注释作为保留系统说明保留，不属于活动版本标识。

## 3. 改前备份（`backups/pre-v6.90a-1.0-20261020-163807/`）

| 文件 | 字节 | SHA-256 |
|---|---|---|
| src__war3map.j | 8,581,368 | `143B492A7ECE1D2646F9C4A2A8EC0C66E627FA9E178F488A2C48DDFF22F24116` |
| src__war3map.w3i | 806 | `6841965B07F58C686659C6CD880E3CF44903DC41B5A510BA04508AB7B69C31A3` |
| tools__build__build.ps1 | 11,002 | `D49D873A8BB686608560FB05908DD05507CA5D8E88C7CC8304638518FB7270E1` |
| tools__build__verify_v17.ps1 | 17,943 | `9D3337BAB32B722C43543A64FAF3C3110B6B9F4632AB2B29911E8A27030B02D8` |
| config__tool-paths.json | 405 | `E903EEFF502E5E92654606F83D3B9842AB2C41BC610512939F841753A8331F80` |

改前已核对：当前权威 src 与已验收 T10 部署件包内 `war3map.j` 逐字节相等，w3i 两槽为 T10 标签，T2 doo / T5 w3e 哈希匹配，满足“内容须与 T10 等价”。

## 4. 构建 / 重注入 / 验证

- 权威 `tools/build/build.ps1`；PJASS 仅 `war3map.j:155341 location_m5`（基图既有，允许），新增错误 0。
- 构建后重注入：
  - T2 `war3map.doo`（269,924B）SHA `F6EA5428531D04AC680F9D51B318BE5B65E776B58BC342BB5004E32B2F0BF915`
  - T5 `war3map.w3e`（116,584B）SHA `55962DAE4021A0ECA6DAD6011E9A37B00459362BC062725260D6799FB8E9F593`
- verify_v17：重注入前 122/0、重注入后 122/0。
- 回读：包内 j（8,581,369B）== src；包内 w3i == src；doo/w3e 哈希精确匹配；wpm（262,160B）SHA `61CCF7597378FDE26858B061AE174082543FBB25E07D0E4E3C91CB035A1F11A9`。

## 5. 冻结锚点核验（回读证实）

- 抽奖屋彩字 `|cffff66cc抽|r|cffffff66奖|r|cff66ffff屋|r` 唯一；`CreateTextTag()` 唯一；定位精确为 `call SetTextTagPos(B836LotteryTitle,GetUnitX(B836ArcHut)-128.,GetUnitY(B836ArcHut),256.)`；-96/144/64 历史位置全清；无 PosUnit；permanent=true / lifespan=0 / fadepoint=0 / 全员可见；空守卫无 local-player 分支。
- nAS6：`CreateUnit(Player(PLAYER_NEUTRAL_PASSIVE),'nAS6',-5728.,-6816.,270.)` 唯一，模型/坐标/朝向/碰撞/交互零改动。
- T5 段 47 `DzSetUnitModel` + 47 `SetUnitScale(1.0)`；T4 世界树 `DzSetUnitModel(JW_JD, … TreeofLife …)` + `SetUnitScale(JW_JD,1.8`。
- 三按钮：`幸运大抽奖（免费1次）`、`1000抽属性（无限次）`、`梭哈抽属性` 齐备；LOTTERY_Click / LOTTERY_Selected handler 保留。
- LOTOPEN 同步对：`DzSyncData("LOTOPEN","")` 与 `DzTriggerRegisterSyncData(lotOpenTrigger,"LOTOPEN",false)` 各 1 次。
- `war3map.wpm`（262,160B）SHA `61CCF7597378FDE26858B061AE174082543FBB25E07D0E4E3C91CB035A1F11A9`，与 FISSURE 冻结值一致。
- 严格 UTF-8：无 BOM、纯 LF、U+FFFD=0。

## 6. 稳定目录发布与哈希核验

- 盘点稳定目录仅两件：本项目旧 `DOTA-OMG-IMBA-v6.9-FISSURE-T1.w3x`（56,602,080B，SHA `1847C96BF5201072A569CEC2ECC24E79ACA163CB4C852CEF95E4AF5087842195`）与另一任务 `Dota v6.93a OMG AI 1.0.w3x`。
- 旧 FISSURE-T1 已备份至 `backups/stable-pre-v6.90a-1.0-20261020-165433/`，备份哈希与原件一致后从稳定目录移除（`fissurePresent=false`）。
- 新正式图以精确文件名 `Dota v6.90a OMG AI 1.0.w3x` 复制入稳定目录；构建==稳定（`buildStableHashIdentical=true`）。
- `Dota v6.93a OMG AI 1.0.w3x`（82,298,058B）SHA `BC7B71D74D96898AFBAA01C3BFC9D77FE637C88E9E0D941CD53170DEC1E94890` 保持不变（`unchanged=true`），未触碰。

## 7. Git 同步清单

主代理将从干净 `origin/main` 筛选同步；本地产物不上传。机器可读清单见 `git-sync-checklist.json`，可读版见 `git-sync-checklist.md`。

### 7.1 应同步（权威源码 / 脚本 / 配置 / 报告）

- `src/war3map.j`、`src/war3map.w3i`、`src/war3map.imp`
- `src/data/Units/` 下 8 个 SLK / 文本（AbilityData、CampaignAbilityStrings、CampaignUnitStrings、UnitAbilities、UnitBalance、UnitData、UnitUI、UnitWeapons）
- `tools/build/build.ps1`、`tools/build/verify_v17.ps1`、`tools/build/strip_kk_persistence.py`
- `config/tool-paths.json`（注意：本机绝对工具路径按需本地化；不入库 `config/environment/` 本机覆盖）
- `README.md`、`PROJECT_MANIFEST.json`（合法 JSON、UTF-8 无 BOM）
- 本报告目录 `reports/release-v6.90a-1.0/` 内的脚本与文本证据（md/json/csv/log）
- 可选地图产物：`maps/release/Dota v6.90a OMG AI 1.0.w3x`（是否入库由仓库策略决定；哈希见第 1 节）

### 7.2 本机不得上传 / 禁止同步

- `toolchain/` 二进制（MPQEditor、pjass、common.j、blizzard.j）——第三方/随存工具，不入库。
- `backups/` 全部目录（改前备份、稳定旧件备份、历史阶段备份）。
- 临时 scratch / 缓存（系统 TEMP、构建临时 stage、`reports/art683/` 历史阶段大证据按需保留但不强制同步）。
- 游戏安装目录 `D:\游戏\Warcraft III\`（含稳定目录、各 imba 测试部署、其他任务地图）。
- 第三方参考素材 `assets/reference-authorized/`、历史迁移/审计大文件。
- 其他任务产物 `Dota v6.93a OMG AI 1.0.w3x` 及其目录，绝不同步/覆盖。
- 用户个人路径、本机日志、环境覆盖 `config/environment/`。
- 本次未执行任何 git clone/add/commit/push，未修改 `.git`。

## 8. 证据索引

- `evidence/readback-release.json`：包内 j/w3i/doo/w3e/wpm 回读与锚点全量结果。
- `evidence/release-evidence.json`：发布汇总（产物/稳定/备份/锚点/稳定目录），`ALL_PASS=true`。
- `evidence/verify-preinject.log`、`evidence/verify-postreinject.log`：verify_v17 全量输出。
- `evidence/verification-v17-postreinject.json/.csv`：122 项结果快照。
- `evidence/pjass-release.txt` / `.err.txt`：PJASS 输出。
- `scripts/`：jass/w3i 改写、回读、证据汇编脚本（可复现）。
