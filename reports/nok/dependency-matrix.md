# NOK 依赖矩阵（草稿，待父代理只读审计）

基线 a2c66730 · worktree D:\dota\DOTA-OMG-IMBA-NOK-worktree · 分支 nok-v186

## 待审计决策点（英雄池策略）

1. **尾部收缩（推荐）**：K 稳定索引 118 == K54 上界尾部；删除 118 行并 K54=117，所有 KL4..K54 / K04..K54 循环与边界自动排除 118，无需重编号，无空槽。
2. 备选（若审计判定存在硬编码 118 依赖）：保留索引编号但从候选/选择/ban/AI/手选映射全部排除，且 118 不得为 0 被遍历。
3. 敏捷池：删 K24[40]、K_4=39；NoK 包装（B891RandomAgilityNoK/QZ9HumanNoK/QC9HumanNoK）复用面广，重构并入普通 QZ9/QC9，不盲删；现有英雄概率仅随删 K 自然重归一化（当前 NoK 本就不向真人/AI 投放 K）。

## 删除/编辑清单

| 层 | 目标 | 动作 | 证据 |
|---|---|---|---|
| jass-globals | lines 3-37 v1.4-K hero K module globals banner + KK_HERO/KK_SK1..4/AGI/MULT/RADIUS/DUR constants, KK_TAB, KK_SuppressHit, KK_CastTrigger, KK_DeathTrigger, KK_SK3_GROUP/CASTER/DAMAGE, KK_KEY_* | delete | src/war3map.j:3-37 |
| jass-globals | K_POOL_ROLLED / K_POOL_HIT boolean arrays (decl 410-411, resets 61184/85, 61261/62, 172381/82) | delete | src/war3map.j:409-411 + 6 reset lines |
| jass-globals | XOMG_VERSION constant string v1.8.5-SYNCF001 (line 754) | edit | src/war3map.j:754 |
| jass-module | KK_EnsureHeroAbilities (38186-38209) + call sites ADD_CONTENT(38214), ApplyUnit(207710) | delete | src/war3map.j:38186-38209,38214,207710 |
| jass-module | KK_IsKHero/KK_Lvl/KK_SnapAgi/KK_SK1Gain/KK_SK2Mult/KK_SK3Mult/KK_SK4Dur/KK_UltRemove/KK_UltExpire/KK_UltCast/KK_SK3_Filter/KK_SK3_Apply/KK_JiaKaiCast/KK_HitPhys/KK_DeathAction/KK_CastAction/KK_Init (241810-242163) | delete | src/war3map.j:241787 banner .. 242163 endfunction |
| jass-module | main call call KK_Init() (250762) | delete | src/war3map.j:250762 |
| jass-guard | SuijiMode_SetVisualForm K/KA04 early-return guard (89424-89427) | simplify | src/war3map.j:89424-89427 |
| jass-guard | SuijiMode_ChemicalRageCompatApply K/KA04 guard (208563-208567) | simplify | src/war3map.j:208563-208567 |
| jass-guard | SuijiMode_IsRandomPoolExcludedSkill KA01..KA04 literals (198506) | edit | src/war3map.j:198506 |
| jass-guard | SuijiMode_ApplyUnit K bypass block (207704-207715) | delete | src/war3map.j:207704-207715 |
| jass-register | R1W: call R1X(H0K0,0,KA01,KA02,KA03,KA04) (17019) | delete | src/war3map.j:17019 |
| jass-table | LX7 stable hero row 118: K34[118]/MI4[118]/K64[118]/MH4[118]=BTNK_Hero/XY7/XU7 + MJ4..MO4 clears (31426-31436) | delete | src/war3map.j:31426-31436 |
| jass-table | V5 skill row 118: HM4[118]=KA01/HN4[118]=KA02/HO4[118]=KA03/HP4[118]=KA04 (18789-18792) | delete | src/war3map.j:18789-18792 |
| jass-table | SUIJI_POOL_SOURCE[118]=18 (31456) | delete | src/war3map.j:31456 |
| jass-table | K54=118 bound (31437) | edit | src/war3map.j:31437 |
| jass-pool | K24[40]=H0K0 (31529), K_4=40 (31530) | edit | src/war3map.j:31529-31530 |
| jass-pool | B891RandomAgilityNoK (25022-25024) | refactor/delete | src/war3map.j:25020-25024 |
| jass-pool | QZ9HumanNoK (61079-61089), QC9HumanNoK (61090-61101) | refactor/delete | src/war3map.j:61079-61101 |
| jass-pool | QC9ForPlayer human/AI split (61102-61107) | refactor | src/war3map.j:61102-61107 |
| jass-pool | QC9HumanFirstAgility (61108-61116) | refactor | src/war3map.j:61108-61116 |
| slk | UnitData.slk Y3339 H0K0 hero block (model K_Hero, art=BTNK_Hero, scale120) | delete | src/data/Units/UnitData.slk |
| slk | UnitUI.slk H0K0 block (BTNK_Hero/DISBTNK_Hero, Name=凯哥) | delete | src/data/Units/UnitUI.slk |
| slk | UnitBalance.slk H0K0 block (agi primary, agi+3) | delete | src/data/Units/UnitBalance.slk |
| slk | UnitAbilities.slk H0K0 block (KA01..KA04) | delete | src/data/Units/UnitAbilities.slk |
| slk | UnitWeapons.slk H0K0 block (normal attack, no missile, range128) | delete | src/data/Units/UnitWeapons.slk |
| slk | AbilityData.slk Y6659-6662 KA01..KA04 blocks | delete | src/data/Units/AbilityData.slk |
| campaign | CampaignUnitStrings.txt [H0K0] block (name/tooltip/displayname/model K_Hero) | delete | src/data/Units/CampaignUnitStrings.txt |
| campaign | CampaignAbilityStrings.txt [KA01]猎手本能/[KA02]捷刃/[KA03]加凯/[KA04]凯哥牛逼了 blocks | delete | src/data/Units/CampaignAbilityStrings.txt |
| campaign | exact K-family buttons BTNK_Hero/Marksmanship/CriticalStrike/BattleRoar/ChemicalRage + DIS* in both txt | delete | src/data/Units/Campaign*.txt |
| imp | war3mapimported\K\K_final.mdx | delete | src/war3map.imp |
| imp | war3mapimported\K\K_final_portrait.mdx | delete | src/war3map.imp |
| imp | war3mapimported\K\K_final_v2.mdx | delete | src/war3map.imp |
| imp | war3mapimported\K\K_body.blp | delete | src/war3map.imp |
| imp | ReplaceableTextures\CommandButtons\BTNK_Hero.blp / Marksmanship / CriticalStrike / BattleRoar / ChemicalRage | delete | src/war3map.imp |
| imp | ReplaceableTextures\CommandButtonsDisabled\DISBTNK_Hero.blp + 4 DIS variants | delete | src/war3map.imp |
| assets | assets/K/K_body.blp, K_final.mdx, K_final_portrait.mdx | delete | assets/K/ |
| assets | assets/Kv2/model/K_final_v2.mdx, K_final_portrait.mdx; textures/K_body.blp; buttons/ BTNK* + DISBTNK* (13 files) | delete | assets/Kv2/ |
| tools | build.ps1 K asset copy/validate gates + sourceEntries K entries | edit | tools/build/build.ps1 |
| tools | verify_v17.ps1 K-existence gates (KA01..04 templates, KK chain, K assets, K test pool) -> replace with zero-residue + pool-completeness gates | edit | tools/build/verify_v17.ps1 |
| tools | verify.ps1 legacy v1.6 gate K assertions in final $passed expression | edit | tools/build/verify.ps1 |
| tools | tools/transform/build_k_hero.py K SLK generator | delete | tools/transform/build_k_hero.py |
| tools | tools/transform/audit_v18.py G7-k-normal K gate | edit | tools/transform/audit_v18.py |
| tools | tools/transform/sync_preview_ui.py samples H0K0: None line 88 | edit | tools/transform/sync_preview_ui.py |
| tools | config/tool-paths-v14k.json (v1.4-K legacy output path) | delete | config/tool-paths-v14k.json |
| docs | README.md K sections: line 36 v1.4-K hero, line 37 v1.6-K VisualFix, 95-106 v1.7-K historical block, 111 K真人50% retention mention, 126 K回归普通敏捷池, 133-134 K内嵌肖像 | edit | README.md |
| reports | reports/audit-v17-K-VisualSkillFix.html, reports/k-portrait-merge.json, reports/verification-v1.6-K-CompleteHero.json | delete(strip) | reports/ |
| reports | reports/noskin19-unchanged-assets.json K asset rows | edit | reports/noskin19-unchanged-assets.json |
| w3i | two 24-byte ASCII slots @0x0C and @0xEA -> exact 24B "OMG IMBA v1.8.6-NOK" + 5 spaces padding; assert len==24; all other Force/player bytes identical to noskin19 | edit | src/war3map.w3i |

## 保留清单（不得删除）

| 类别 | 目标 | 说明 |
|---|---|---|
| KEEP | HMD0 喵刀 hero (K24[39], stable index 117, SUIJI_POOL_SOURCE[117]=17, B891RandomHeroRange 117-skip) | tail-shrink K54=117 leaves 117 intact |
| KEEP | H00K 凯哥/炸弹人 (general renamed hero; sync_hero_visible_names_v11.py) | different rawcode; explicitly protected |
| KEEP | KK_GAME_DIFFICULTY/KK_DIFFICULTY_*/KKGameTips_*/KK_AIMAXZB_EQUIPPED/AIMAXZB_* | general difficulty/tips/AI-item systems, prefix collision only |
| KEEP | KK_RELEASE_VERSION="KK_B1122" general match/sync/order log tag | used by B1037/B1111/B1120 logging, not hero K |
| KEEP | YY7("我才是袁加凯！") and UpdateLog 袁加凯 mentions | 屠夫 rename, general hero |
| KEEP | 凯哥发福利 welfare button, ATTR双杰抽属性, 斯神威神, 莱恩, 魔瓶族, 野怪掉落, 双击直售, 喵刀直选, syncfix chain, XOMG1, IMBA layer | all non-K systems; semantic/hash preserved |
| KEEP | generic BTNKeep/BTNKeeperGhostBlue/BTNKelThuzad/BTNKiljaedin/BTNKnight/BTNKobold*/BTNKotoBeast/BTNKrobWitchcraft buttons | unrelated native UI |
| KEEP | unrelated arrays indexed 118: HW4/HX4/HY4/HZ4 acidbomb-thunderbolt-bloodlust-auravamp; HR4..HU4 A6B7..A6CD; T64 title; h7/UK7 terrain remap | different indexing schemes, not K row |
| KEEP | SetMapName("OMG IMBA v1.7.1-K-W3IFix") proven load script label | deliberately retained per noskin19 policy; not K-hero player text |
