# 红线基线 · IMBA_POWER 隔离静态验收（修改前快照）

> 生成时间：2026-10-16（只读勘察，未改工程任何文件）
> 用途：后续实施完成后做独立 diff 复验的不可变锚点。

## 0. 全文件哈希（修改前）

| 文件 | 字节数 | 行数 | SHA256 |
|---|---:|---:|---|
| `src/war3map.j` | 8,672,898 | 249,532 | `ea6d950368183556eec44c231a41541654b3bac4183ab78bac4e92dc5892d403` |

全文件哈希在实施后**允许变化**（因为会新增代码），但下列 16 个锚点区的哈希**必须逐字节不变**。

## 1. 关键词计数基线（修改前）

| 关键词 | 出现次数 | 说明 |
|---|---:|---|
| `IMBA_POWER` | 7 | 1 处常量定义 + 3 处使用 + 3 处注释 |
| `GetLocalPlayer` | 647 | 本地玩家分支（客户端同步敏感区） |
| `GetRandomInt` | 340 | 系统随机整数 |
| `GetRandomReal` | 188 | 系统随机实数 |
| `TimerStart(...,true)` 周期定时器 | 95 | tick 周期 |
| `SetPlayerState(...,PLAYER_STATE_RESOURCE_GOLD` | 132 | 经济金币写入 |

实施后这些计数只应**增加**（新增代码），不得减少；且新增项的位置必须符合下文隔离规则。

## 2. 红线锚点区（16 个，哈希逐字节不可变）

### 2.1 IMBA_POWER 常量与三处使用

| 锚点 | 行号 | 关键表达式（原文） | 区域 SHA256 |
|---|---:|---|---|
| 常量定义 | 703 | `constant real IMBA_POWER=2.` | `69121805bf2b271c044e04fb696d2a890a3fb5632b0a3c652c6576a6d503da6d` |
| 治疗倍乘 | 26785–26788 | `if XM_MODE then set healAmount=healAmount*IMBA_POWER` | `74f41c749a1379fef9e67a507d2a150658361cc2bfc09ec02b61539e063b003e` |
| 伤害倍乘 | 28398–28401 | `if XM_MODE and BL7!=6 then set YM7=YM7*IMBA_POWER` | `34b21cbae88e310844a7b6a32ed2ec428e81a425415c99a7dfbb183235cccc6c` |
| 眩晕倍乘 | 28517–28520 | `if XM_MODE and dur>0. and dur<5. then set dur=RMinBJ(dur*IMBA_POWER,5.)` | `878660db4c118d4e6c85a1d97c8699542406d50416578d71510b1033f12a1de4` |

**红线**：常量值 `2.` 不得改；三处使用的门控条件（`XM_MODE`、`BL7!=6`、`0<dur<5`、上限 `5.`）不得改。

### 2.2 抽奖概率

| 锚点 | 行号 | 关键表达式（原文） | 区域 SHA256 |
|---|---:|---|---|
| CJ1/CJ2 概率块 | 173085–173134 | `set CJ1=5+CGDIFF*2` / `set CJ2=10+CGDIFF*3` / `if GetRandomInt(1,100)<=CJ1` / `if GetRandomInt(1,100)<=CJ2` | `6b6718d746f7fd101af8816eb4c85c4727cba189c6a3d178e4f4bb8289072f54` |
| 抽奖池构建 | 39638–39661 | `if p>=1000 and B1063ItemEligible(SU[i])` / `exitwhen i>EV or B1063LotteryCount>=128` | `72461ba10daeb4b7f95940839a2a56f029201165c72b5f7e26f016b1b9650fb0` |

**红线**：`CJ1=5+CGDIFF*2`、`CJ2=10+CGDIFF*3` 公式不得改；`GetRandomInt(1,100)` 上下界不得改；价格阈值 `1000` 与池上限 `128` 不得改。

### 2.3 野怪 10% 掉落（已实现）

| 锚点 | 行号 | 关键表达式（原文） | 区域 SHA256 |
|---|---:|---|---|
| 廉价池构建 | 39618–39637 | `if p>0 and p<=1000 and B1063ItemEligible(SU[i])` / `B1063CheapCount>=64` | `1a433da25de60fda9ebb536fd27a847f1d7cea613e7740ba4be1a926234a49c6` |
| 掉落动作（10%） | 39662–39688 | `if GetRandomInt(1,10)!=1 then return` / `CreateItem(B1063CheapPool[pick],GetUnitX(victim),GetUnitY(victim))` / 去重 `LoadBoolean(L7,h,16100)` | `2a7540e5424b87591af4fb2451719276927bf1679b864cee85d289228ca6dd82` |
| 事件注册 | 39689–39694 | `TriggerRegisterPlayerUnitEvent(t,Player(12),EVENT_PLAYER_UNIT_DEATH,null)` | `081c8c5f37cdb839773bef3fa30a2158d7b2baaa51a274e9d24590223da0126d` |
| 野怪分类白名单 | 39402–39419 | 36 野怪 rawcode + 12 线上兵 rawcode；排除 HERO/STRUCTURE/SUMMONED/ILLUSION | `6c5b0d838c4800ac524b45c55431900091865a34580d91c8b7f30d424a1d7d04` |

**红线**：`GetRandomInt(1,10)!=1`（即 10%）不得改；价格上限 `1000`、池上限 `64` 不得改；去重位 `L7/h/16100` 不得改；仅注册 `Player(12)` 不得新增其他玩家；36+12 rawcode 名单不得增删（Roshan `n00L` 天然排除）。

### 2.4 冷却

| 锚点 | 行号 | 关键表达式（原文） | 区域 SHA256 |
|---|---:|---|---|
| 冷却读取 | 10755–10767 | `set cooldown=EXGetAbilityState(a,1)` / `return cooldown` | `10d5495891ddd055d3952183713ad13caf124d71d28901a08c7400e86dc5b9c0` |
| JAPI 冷却桩 | 4786–4801 | `MHAbility_GetAbilityCooldown` / `MHAbility_SetAbilityCooldown` / `MHAbility_SetAbilityCooldownEx` 返回 `0.` | `f7e5b987f6e6ada09954b459296d969928f23ee5f57985392a33282a30dfea08` |

**红线**：`EXGetAbilityState(a,1)` 冷却读取底层不得改；桩函数返回值不得改。

### 2.5 蓝耗

| 锚点 | 行号 | 关键表达式（原文） | 区域 SHA256 |
|---|---:|---|---|
| 蓝耗注册写入 | 35955–35977 | `MHAbility_SetCustomLevelDataInt(...,ABILITY_LEVEL_DEF_DATA_MANA_COST,...)` | `b1c5faada3b51c5294dc154b03cba65a7d013203642b3b94ae65c954e9e9b791` |
| AI 蓝耗检查 | 125409–125435 | `set manaCost=B945DefinitionMana(physicalSkill,level)` / `if manaCost>0 and GetUnitState(u,UNIT_STATE_MANA)+.01<I2R(manaCost) then return false` | `69acc32f8421791cbd416beb3f52ecdd83119c84c8217bbf13d0225045cb902e` |

**红线**：`ABILITY_LEVEL_DEF_DATA_MANA_COST` 常量不得改；`B945DefinitionMana` 调用与 `mana+0.01<I2R(manaCost)` 判断不得改。

### 2.6 经济

| 锚点 | 行号 | 关键表达式（原文） | 区域 SHA256 |
|---|---:|---|---|
| 金币反作弊 | 39296–39316 | `SetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD,EV0[id])` 回写 | `a0c06a29dc645c9e12c49ef767efc630b654f6d0ee6bd78d4d88cbc0f93eb040` |
| 离位金币平分 | 32745–32780 | `SetPlayerState(DE8,GOLD,0)` 清零 + `+hY/Jg` 平分队友 | `2688ff1efe0b0f1df3b00973891da5d18eb0b1c4178c3afc89ae5e21740db490` |

**红线**：反作弊回写 `EV0[id]` 不得改；离位清零与 `hY/Jg` 平分公式不得改。

### 2.7 召唤实体/分身/守卫/陷阱数量与存活时间（新增硬红线）

| 计数项 | 基线值 | 红线规则 |
|---|---:|---|
| `UnitApplyTimedLife(` native 调用 | 263 | 存活时间调用数不得增加；各调用的寿命参数（如 `1.`/`2.`/`5.`/`80`/`Roundtime` 等）原值不得改 |
| `UnitApplyTimedLifeBJ(` 调用 | 6 | 同上 |
| `CreateUnit(` 调用 | 963 | 召唤实体/分身/守卫/陷阱的 `CreateUnit` 循环/数量不得引入 `IMBA_POWER`；实体生成数量不得 ×2 |
| `CreateUnitNamed(` | 0 | 基线为 0；新增需逐项核对是否为实体生成 |
| `CreateBlightedGoldmine(` | 0 | 基线为 0 |

**硬红线**：
- **允许 ×2 的仅是非实体次数**：弹射（bounce）、弹道（projectile/missile dummy）、多重施法（multi-cast）等无实体单位寿命的效果，才可 ×IMBA_POWER。
- **禁止 ×2 的**：召唤物（summon）、幻象（illusion）、守卫（ward）、陷阱（trap）、单位持续时间（`UnitApplyTimedLife` 的秒数）——这些数量与寿命必须相对基线不变。
- 复验时对每个新增 `IMBA_POWER` 引用，必须判定其作用对象是"非实体次数"还是"实体数量/寿命"；后者一律判违规。

## 3. 静态 diff 验收规则（实施后逐项核对）

### 规则 A：IMBA_POWER 隔离

1. **新增 `IMBA_POWER` 引用不得进入 `GetLocalPlayer()` 分支**。实施后 grep 所有 `IMBA_POWER` 出现行，逐行向上找最近的 `if ... GetLocalPlayer()` / `if GetLocalPlayer()==` 块；若该行位于该块的 `then...endif` 内，判违规。
2. **新增 `IMBA_POWER` 不得出现在以下红线锚点区附近（±30 行）**：
   - 距离类：`IsUnitInRange`、`DistanceBetweenPoints`、`IssuePointRange`、`GetUnitRange`
   - 冷却类：`EXGetAbilityState(a,1)`、`B582_GetAbilityCooldown`、`MHAbility_SetCooldown`、`YDWESetUnitAbilityState(u,...,1,cooldown)`
   - 蓝耗类：`ABILITY_LEVEL_DEF_DATA_MANA_COST`、`B945DefinitionMana`、`UNIT_STATE_MANA`
   - 周期类：`TimerStart(...,true,...)` 的周期参数位置
   - 系统概率类：`GetRandomInt(1,100)`、`GetRandomInt(1,10)`、`GetRandomReal`
   - 经济类：`PLAYER_STATE_RESOURCE_GOLD`、`EV0[id]`、`AdjustPlayerStateBJ(...,PLAYER_STATE_RESOURCE_GOLD)`
3. 新增 `IMBA_POWER` 只允许出现在**纯伤害/治疗/眩晕数值倍乘**的共享动作内，且必须保留 `XM_MODE` 门控（与现有三处一致）。

### 规则 B：红线锚点区哈希不变

实施后重新提取 §2 的 16 个行范围（注意：新增代码会导致行号偏移，**必须按函数名/特征表达式定位**而非固定行号），逐区比对 SHA256。任一变化即判违规，除非该变化本身就是本任务允许的新增代码（新增代码不得插入红线区内，只能追加在函数末尾或新函数）。

### 规则 C：关键词/函数逐项核对清单

实施后必须逐项 grep 并确认：

| # | 关键词/函数 | 核对要点 |
|---:|---|---|
| 1 | `IMBA_POWER` | 总出现数 = 7 + 新增数；新增数逐行过规则 A |
| 2 | `GetLocalPlayer` | 总出现数 = 647 + 新增数；新增分支内不得有 IMBA_POWER / GetRandomInt / SetPlayerState GOLD |
| 3 | `GetRandomInt(1,10)` | 野怪10%掉落概率，必须仍在 `B1063NeutralDropAction` 共享动作内 |
| 4 | `GetRandomInt(1,100)<=CJ1` / `<=CJ2` | 抽奖概率公式不变 |
| 5 | `CJ1=5+CGDIFF*2` / `CJ2=10+CGDIFF*3` | 公式行不得改动 |
| 6 | `EXGetAbilityState(a,1)` | 冷却读取底层不变 |
| 7 | `B582_GetAbilityCooldown` | 函数体不变 |
| 8 | `ABILITY_LEVEL_DEF_DATA_MANA_COST` | 蓝耗写入常量不变 |
| 9 | `B945DefinitionMana` | AI 蓝耗检查调用不变 |
| 10 | `TimerStart(...,true,` | 95 个周期定时器周期值不变；新增 timer 不得复用既有 timer handle |
| 11 | `PLAYER_STATE_RESOURCE_GOLD` | 132 处金币写入不得绕过 EV0 反作弊 |
| 12 | `B832WardCreep` | 36+12 rawcode 白名单不变 |
| 13 | `B1063BuildCheapPool` | 价格 `p<=1000`、上限 `64` 不变 |
| 14 | `B1063BuildLotteryPool` | 价格 `p>=1000`、上限 `128` 不变 |
| 15 | `LoadBoolean(L7,h,16100)` | 野怪掉落去重位不变 |
| 16 | `TriggerRegisterPlayerUnitEvent(t,Player(12),EVENT_PLAYER_UNIT_DEATH` | 野怪事件注册仅 Player(12) |
| 17 | `RMinBJ(dur*IMBA_POWER,5.)` | 眩晕硬上限 5.0 秒不变 |
| 18 | `BL7!=6` | 生命移除(6)不倍乘的排除条件不变 |
| 19 | `UnitApplyTimedLife(` native | 基线 263 处；寿命参数值原值；不得新增召唤实体寿命调用 |
| 20 | `UnitApplyTimedLifeBJ(` | 基线 6 处；寿命参数原值 |
| 21 | `CreateUnit(` | 基线 963 处；循环内 CreateUnit 不得引入 IMBA_POWER；召唤实体/分身/守卫/陷阱数量不得 ×2 |
| 22 | 新增 IMBA_POWER 作用对象分类 | 仅弹射/弹道/多重等非实体次数可 ×2；召唤/幻象/守卫/陷阱/寿命秒数一律禁止 ×2 |
| 23 | PJASS 语法 | 修改后 JASS 无语法错误 |
| 24 | 包内 7/7 | war3map.j + war3map.imp + 5 SLK 哈希与 verification-latest.json expected 匹配 |

### 规则 D：距离类原值

距离相关表达式（`IsUnitInRange` 的半径参数、`DistanceBetweenPoints` 的比较阈值、`IssuePointRange` 的距离参数）在实施后不得被新增代码修改。既有距离常量（如 `800.`/`750.`/`700.`/`650.`/`600.` 分段、`1400.`/`1600.`/`1000.` 等）必须原值保留。

## 4. 复验方法

实施完成后：
1. 重新计算 `war3map.j` 全文件 SHA256（记录变化量）。
2. 按特征表达式定位 16 个红线区（函数名锚定），逐区提取文本并算 SHA256，与 §2 比对。
3. grep `IMBA_POWER` 全部出现行，逐行向上追溯是否在 `GetLocalPlayer` 分支内；逐行判定作用对象是"非实体次数"还是"实体数量/寿命"。
4. grep §3 规则 C 的 24 项关键词，逐项确认计数与位置。
5. 核对 §2.7 实体计数：UnitApplyTimedLife=263、UnitApplyTimedLifeBJ=6、CreateUnit=963 不得异常增加；寿命参数值不变。
6. PJASS 语法检查通过；包内 7/7 文件哈希匹配。
7. 任一红线区哈希变化或任一规则违规 → 复验不通过，退回实施方修正。
