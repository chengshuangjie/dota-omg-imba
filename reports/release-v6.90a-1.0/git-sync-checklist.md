# Git 同步清单（v6.90a 1.0）

本清单供主代理从干净 `origin/main` 筛选同步。本次发布**未执行任何 git clone/add/commit/push，未修改 `.git`**。

## A. 推荐上传（权威源码 / 脚本 / 配置 / 报告）

### A1. 权威源码
- `src/war3map.j`（8,581,369B，SHA `7248DB967B02863B000CB671A126A036C401FC78C541C07F943B18E25B712DDA`）
- `src/war3map.w3i`（806B，SHA `2D29ECAF9C819D9C5EB14F6AD081C2974A9EB09524C94DABB611901FFFD43EA0`）
- `src/war3map.imp`（89,654B，SHA `1FB5C0B5389AE83C39BACB99AAD48AF86C253AFB74357F47F65A8D651AA9846D`）
- `src/data/Units/`：`AbilityData.slk`、`CampaignAbilityStrings.txt`、`CampaignUnitStrings.txt`、`UnitAbilities.slk`、`UnitBalance.slk`、`UnitData.slk`、`UnitUI.slk`、`UnitWeapons.slk`

### A2. 构建/验证脚本与配置
- `tools/build/build.ps1`
- `tools/build/verify_v17.ps1`
- `tools/build/strip_kk_persistence.py`
- `config/tool-paths.json`（本机绝对工具路径按需本地化；不要同步 `config/environment/` 本机覆盖）
- `README.md`、`PROJECT_MANIFEST.json`（合法 JSON、UTF-8 无 BOM）

### A3. 发布报告与证据（本目录）
- `reports/release-v6.90a-1.0/release-v6.90a-1.0-report.md`
- `reports/release-v6.90a-1.0/git-sync-checklist.md` / `.json`（本清单）
- `reports/release-v6.90a-1.0/evidence/`（readback、release-evidence、v17 快照、PJASS、verifier-results）
- `reports/release-v6.90a-1.0/scripts/`（可复现脚本）

### A4. 可选地图产物（按仓库策略决定是否入库）
- `maps/release/Dota v6.90a OMG AI 1.0.w3x`（56,712,620B，SHA `DFD19F9BCB7C35A2050A512C072F968FDF803F4C32A4BCEB84C9924561F68C29`）
- 历史正式件 `maps/release/DOTA-OMG-IMBA-v1.8.9-UIFIX.w3x` 仅历史保留，是否入库由策略定。

## B. 禁止上传 / 禁止同步

- `toolchain/` 全部二进制与随包副本：MPQEditor.exe、pjass、`jass/24/common.j`、`jass/24/blizzard.j`。
- `backups/` 全部目录：改前备份 `pre-v6.90a-1.0-20261020-163807/`、稳定旧件备份 `stable-pre-v6.90a-1.0-20261020-165433/`、历史阶段备份。
- 系统临时 scratch / 缓存（TEMP、构建临时 stage）。
- 游戏安装目录 `D:\游戏\Warcraft III\` 整树：稳定目录部署件、`imba69/` 测试部署、其他 imba 目录均不上传。
- 第三方参考素材：`assets/reference-authorized/`、历史迁移/审计大文件、库存图集。
- **其他任务保护文件 `Dota v6.93a OMG AI 1.0.w3x`（含其所在目录）绝不同步、不覆盖。**
- `maps/baseline/`：52.8MB（52,800,385B）noskin19 稳定底包二进制大文件，与 `maps/build/` 同类，禁止上传。
- 本机 `maps/build/` 历史本地重建大地图、个人路径、本机日志、`config/environment/`。
- 历史 `reports/art683/` 阶段大证据按需本地保留，不强制同步。
