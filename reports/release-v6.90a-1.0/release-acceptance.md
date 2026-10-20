# v6.90a-1.0 最终独立验收报告

- 验收时间：2026-10-20 17:04:49 +08:00
- 执行方：独立验收代理（只读复核；**未执行任何 Git 操作**）
- 结论：**PASS（25/25 门禁；verify_v17 122 pass / 0 fail；PJASS 仅余既有 location_m5）**

## 1. 发布包与稳定副本一致性

| 项 | 值 |
|---|---|
| 正式件 | `maps/release/Dota v6.90a OMG AI 1.0.w3x` |
| 字节 / SHA-256 | 56,712,620 / `DFD19F9BCB7C35A2050A512C072F968FDF803F4C32A4BCEB84C9924561F68C29` |
| 稳定副本 | `D:\游戏\Warcraft III\Maps\omg\稳定\Dota v6.90a OMG AI 1.0.w3x` |
| 构建==稳定 | 逐字节一致（同 SHA-256） |

## 2. 稳定目录快照核对（发布前 → 发布后）

| 文件 | 发布前 | 发布后 | 结果 |
|---|---|---|---|
| Dota v6.90a OMG AI 1.0.w3x | 无 | 56,712,620B / `DFD19F9B…68C29`（唯一） | PASS |
| Dota v6.93a OMG AI 1.0.w3x | 82,298,058B / `BC7B71D7…E94890` | 同左，哈希完全未变 | PASS |
| 旧 FISSURE | 在目录内 | 已移除；备份于 `backups/stable-pre-v6.90a-1.0-20261020-165433/`（`1847C96B…42195` 与原件一致） | PASS |

稳定目录现仅 2 项：新 v6.90a + 他任务 v6.93a；本项目新 v6.90a 唯一。

## 3. W3I 两槽原始 24B（806B 固定，槽外与 noskin19 基线相等）

| 槽 | 字面量 | ASCII | 空格 | 合计 | 结果 |
|---|---|---:|---:|---:|---|
| A@12 XOMG_VERSION | `v6.90a-OMG-AI-1.0` | 17 | 7 | 24 | PASS |
| B@234 显示名 | `Dota v6.90a OMG AI 1.0` | 22（22+2） | 2 | 24 | PASS |

## 4. JASS 正式标识

- `XOMG_VERSION="v6.90a-OMG-AI-1.0"` 恰好 1 次；`SetMapName("Dota v6.90a OMG AI 1.0")` 恰好 1 次。
- 无 ART683-T10 活动标识（旧 XOMG_VERSION / SetMapName 均为 0）；严格 UTF-8，U+FFFD=0。

## 5. 组件完整 SHA

| 组件 | SHA-256 | 等于 | 结果 |
|---|---|---|---|
| war3map.doo | `F6EA5428…F0BF915`（269,924B） | T2 | PASS |
| war3map.w3e | `55962DAE…FB8E9F593`（116,584B） | T5 | PASS |
| war3map.wpm | `61CCF759…5A1F11A9`（262,160B） | FISSURE | PASS |

## 6. T10 全部内容保持

- T5 段 47 `DzSetUnitModel(` + 47 `SetUnitScale(...,1.0)`（运行时换模 47 处；变量集口径 48 行）。
- T4 世界树：JW_JD + TreeofLife + `SetUnitScale(JW_JD,1.8)`。
- 标题 `SetTextTagPos(B836LotteryTitle,GetUnitX(B836ArcHut)-128.,…,256.)` 精确；旧 -96/144/64 与 PosUnit 无残留；永久/生命周期0/淡入点0/全玩家可见；创建唯一。
- nAS6 唯一 `CreateUnit(…,'nAS6',-5728.,-6816.,270.)`；LOTOPEN 同步对俱在；三按钮与点击/选择 handler 俱在；玩法保护（小生权限门、无持久化/防守/车轮战）保持。

## 7. 编译与回归（本次独立重跑）

- PJASS：仅既有 `location_m5`（war3map.j:155341），新增错误 0。
- verify_v17.ps1：122 pass / 0 fail，exit 0。

## 8. 文档与清单

- `PROJECT_MANIFEST.json` JSON 合法；release 路径/版本/字节/哈希与实测一致；files[] 全部条目独立复算一致。
- `README.md` 路径/版本/哈希/大小一致。

## 9. Git 同步安全评审（独立验收未执行 Git）

发布方 `git-sync-checklist.md/.json` 已逐条独立比对：**verdict: SAFE —— 未误含 toolchain 二进制、backups、游戏目录、参考素材、个人日志或他任务 v6.93a**；A1 src 哈希独立复算一致；`maps/baseline/`（52.8MB 底包二进制）已明确列入禁止上传。

### 推荐上传
- `README.md`、`PROJECT_MANIFEST.json`、`.gitignore`
- `src/`（权威 j/w3i/imp + 8 数据文件）、`tools/build/`、`config/tool-paths.json`
- `assets/loading-screen/`、`reports/release-v6.90a-1.0/`

### 禁止上传
- `toolchain/`（MPQEditor.exe、pjass、common.j/blizzard.j）、`backups/` 整树。
- `maps/build/`、`maps/baseline/`、`maps/release/*.w3x`（二进制，按政策另定）。
- `assets/reference-authorized/`、`assets/art683-t5/`、`assets/environment/`、`reports/art683/`、`reports/reference-art-migration/`。
- 游戏目录 `D:\游戏\…`（含他任务 v6.93a）；个人日志、`__pycache__/`、`*.tmp`、`*.log`。

> 独立验收未执行任何 Git；若主代理同步时清单有变更，应再次与“禁止上传”比对，命中任一即退回，不代为提交。
