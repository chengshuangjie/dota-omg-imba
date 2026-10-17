# v1.8-Integrated 源码门禁状态（未封包 / 未构建 / 未部署）

- 日期：2026-10-17
- 范围：仅源码/SLK/脚本/报告；无 W3X 改动，未 build、未建 noskin8、未 commit/push。
- 静态门禁 `tools/transform/audit_v18.py`：**36 PASS / 0 FAIL**。
- PJASS：仅白名单 `location_m5 没有初始化` 一条（build.ps1 单条放行），其余 0。

## 本轮完成项与门禁

| 区 | 结论 | 关键证据 |
|---|---|---|
| K 撤销 50% 测试注入 | PASS | K_POOL_ROLLED/K_POOL_HIT/K_POOL_ROLL/B891RandomAgilityNoK/QC9HumanNoK/QZ9HumanNoK 计数=0；H0K0=K24[40] 成员×1；R1X('H0K0',0,'KA01'..'KA04') 保留；human 回归 QC9 共享敏捷池，无权重/保底/排除 |
| K 内嵌肖像 | PASS | 运行时 K_final_v2.mdx=54157B，sha256 e4204138…，MDLX/VERS800/MODL K_Hero/CAMS=1/闭合；前54029B 与原 v2 逐字节相同；五序列/MTLS/TEXS/GEOS/BONE/PIVT 不变；11 处 K_body；独立 portrait 保留；UnitUI 主模型路径不变 |
| 掉落 EARLY/LATE 双池 | PASS | EARLY p>0 and p<=1000；LATE p>0 无上界；共用 B1063ItemEligible；>=600 同步切 LATE；10% roll=GetRandomInt(1,10) roll==1 原样；DROP_POOL_INIT/DROP_ROLL/DROP_OK |
| AI 标记物保护 | PASS | E1 GWF 选择器；E2 GXF 拾取/攻击双分支；E4 IHG 拾取（MarkClear 前）；E5 Y9F/YDF；E6 YUF；E7 YBE；E8 LDF；DROP_AI_*_SKIP 限流；商店购买/一键购/信使槽位/熊灵/Roshan/XVO/人类 DROP_SELL 不拦 |
| HP4 15 项×2 | PASS | 14 项数值×2 落地（SLK 7 载体 + 脚本 8 公式，A0ER/A034 双写）；A12P 引擎.02 硬上限/tradeoff 不改；见 d2-hp4-15-implementation.csv |
| 称号/ATTR/斯温/莱恩/魔瓶/预览/喵刀/DROP_SELL/版本w3i | PASS | 见 v18-audit.{md,json,csv} |

## 未改动 / 边界
- 神杖载体、附属 tradeoff、范围/距离/召唤/自身 CD/蓝耗一律不动。
- 2 冲突项、8 Unknown、89 排除项未读未动。
- K 肖像游戏内取景构图需用户实机目测（静态结构已 PASS）。

## 交付物
- `reports/v18-audit.{md,json,csv}`（36 PASS/0 FAIL）
- `reports/d2-hp4-15-implementation.csv`（15 项逐项 old→new/位置/不动项）
- `reports/k-portrait-merge.json`（肖像合并结构校验/SHA）
