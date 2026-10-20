# v6.90a-1.0 独立验收预案（release 出现后执行；本阶段不执行）

> 本预案在发布前冻结阶段编写，供 release 出现后逐项执行。独立验收**不执行任何 Git 操作**，不修改工程/稳定目录。

## 0. 触发条件
- 新 release 包出现（预期落在稳定目录 `D:\游戏\Warcraft III\Maps\omg\稳定\`，文件名含 `v6.90a`）。
- 出现前保持等待，不改动任何文件。

## 1. 包一致性
- [ ] release 包与稳定副本 SHA-256 完全一致（逐字节；记录双方字节数与哈希）。
- [ ] 记录 release 字节数、SHA-256，与 README/PROJECT_MANIFEST 登记值逐项比对。

## 2. W3I 两槽原始 24B（806B 固定）
- [ ] 槽A@12 原始 24B = `v6.90a-OMG-AI-1.0`（17 ASCII）+ 7 空格。
- [ ] 槽B@234 原始 24B = `Dota v6.90a OMG AI 1.0`（22 ASCII，22+2）+ 2 空格。
- [ ] 两槽之外的其余字节与 noskin19 基线逐字节相等（仅两槽允许差异）。
- [ ] 历史标签（SYNCF001/W3IFix/v1.6-K/K-W3IFix/ART683-T10 等）在 w3i 中出现次数为 0。

## 3. JASS 版本门
- [ ] 无 ART683-T10 活动标识：`XOMG_VERSION="v6.9-ART683-T10"` 与 `SetMapName("6.9 OMG IMBA ART683-T10")` 均不存在。
- [ ] 正式 `XOMG_VERSION="v6.90a-OMG-AI-1.0"` 恰好 1 次；`SetMapName("Dota v6.90a OMG AI 1.0")` 恰好 1 次。
- [ ] j 严格 UTF-8（无 BOM、纯 LF、U+FFFD=0）。

## 4. 组件完整 SHA 比对
- [ ] war3map.doo SHA-256 = `F6EA5428531D04AC680F9D51B318BE5B65E776B58BC342BB5004E32B2F0BF915`（=T2，269,924B）。
- [ ] war3map.w3e SHA-256 = `55962DAE4021A0ECA6DAD6011E9A37B00459362BC062725260D6799FB8E9F593`（=T5，116,584B）。
- [ ] war3map.wpm SHA-256 = `61CCF7597378FDE26858B061AE174082543FBB25E07D0E4E3C91CB035A1F11A9`（=FISSURE，262,160B）。

## 5. T10 冻结项保持
- [ ] T5 段 47 个 `DzSetUnitModel(` + 47 个 `SetUnitScale(...,1.0)`（任务口径“48 建筑换模”；变量集 48 行、运行时换模 47 处，两者分别记录）。
- [ ] T4 世界树保留：`DzSetUnitModel(JW_JD,...)` + `TreeofLife` + `SetUnitScale(JW_JD,1.8`。
- [ ] 标题 TextTag：`call SetTextTagPos(B836LotteryTitle,GetUnitX(B836ArcHut)-128.,GetUnitY(B836ArcHut),256.)` 精确存在；旧 -96 定位、144/64 高度、`SetTextTagPosUnit` 均无残留。
- [ ] 标题永久/生命周期0/淡入点0/全玩家可见；唯一 `B836LotteryTitle=CreateTextTag()`；无 GetLocalPlayer 门控。
- [ ] nAS6：`CreateUnit(Player(PLAYER_NEUTRAL_PASSIVE),'nAS6',-5728.,-6816.,270.)` 唯一；模型/坐标/朝向/碰撞/交互零改动。
- [ ] LOTOPEN 同步对：`DzSyncData("LOTOPEN","")` 与 `DzTriggerRegisterSyncData(lotOpenTrigger,"LOTOPEN",false)` 俱在。
- [ ] 三按钮：`幸运大抽奖（免费1次）`、`1000抽属性（无限次）`、`梭哈抽属性` 俱在；点击/选择 handler 俱在。
- [ ] 玩法保护保持：“小生”开头权限门（-give/-setskill/调试命令）、KK 持久化/皮肤店/防守模式/车轮战仍为 0。

## 6. 编译与回归
- [ ] PJASS：仅既有 `location_m5` 诊断（L155341），新增错误 0。
- [ ] verify_v17.ps1 实跑 0 fail（pass 总数以实跑为准，不锁死 T10 的 118）。

## 7. 稳定目录卫生
- [ ] 稳定目录内本项目仅新 v6.90a 文件一个。
- [ ] 旧 FISSURE（`1847C96B…42195`）已备份且不在稳定目录。
- [ ] v6.93a 保护文件哈希 `BC7B71D7…E94890` 完全未变。

## 8. 文档与清单
- [ ] README.md 路径/版本/哈希/大小与 release 一致。
- [ ] PROJECT_MANIFEST.json 路径/版本/哈希/大小一致，JSON 合法可解析。

## 9. Git 同步清单安全评审（最终报告章节；本阶段不执行 Git）
- [ ] 评审发布代理提供的同步清单，确认**未**误含：
  - toolchain 二进制（MPQEditor.exe、pjass 可执行、common.j/blizzard.j 随包副本）；
  - `backups/` 全部历史备份；
  - 游戏目录（`D:\游戏\…` 整树，含部署包与他任务地图）；
  - 参考素材（`assets/reference-authorized`、`assets/art683-t5` 等库存/图集/参考包）；
  - 个人日志、临时输出、`.bak`；
  - 其他任务的 v6.93a 保护文件；
  - 本地构建大地图（maps/build、maps/release 历史包）。
- [ ] 输出「推荐上传路径」与「禁止上传路径」两份清单，供主代理从干净 origin/main 同步；独立验收不代为提交。

## 验收产物
- `release-acceptance.json`（机器可读逐项结果）
- `release-acceptance.md`（独立结论：PASS/FAIL + 证据 + Git 清单评审）
- 写入本目录 `D:\Dota_OMG\reports\release-v6.90a-1.0\`，并经 verifier-hub 格式/内容校验。
