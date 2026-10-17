# v1.8.1-loadfix1 加载诊断候选（待实机，不承诺可用）

## 唯一变量二分
相对主线 2fccbba，**仅**将 K 主模型 `assets/Kv2/model/K_final_v2.mdx` 回退为 af21e75 原始无 CAMS 字节（54029B / sha256 `f68e6d9d…ed48773` / CAMS=0 / 结构闭合）。其余 v1.8 功能逐字节保持，无功能源码回退。

## 保留（未改动）
- `B1063SellInit()` 保留且 main call=1；MHMsgMouseDown 与 DROP_SELL DzSync 注册保持，**双击直售未禁用**。
- 男神称号 / ATTR 友军广播+对话 keep-open / 斯温 selfRate 1.+1.*level、allyRate 1.+.5*level / 莱恩 SWYJ+50×3、实际+100 / 喵刀 HMD0 / K 普通敏捷池+四技能 / HP4 15项 / 魔瓶族 / 早晚双池 / AI 标记 skip 全部不变。

## 校验
- PJASS：仅白名单 `location_m5`，0 非预期。
- verify_v17：**112 pass / 0 fail**。
- 包内回提主模型：54029B / sha256 `f68e6d9d…ed48773` / CAMS=0 / 闭合（独立复核一致）。
- w3i：806B，24B 名 x2，槽外与 a1c1de1 基线 0 差。

## 产物
- 构建/部署 SHA256：`1CA2D509D5B8AE1A994DC19FE00D9E09FE2B2AF049BB9FF1FA26E9760DB1F9A0`（47,529,199B）。
- 部署目录：`D:\游戏\Warcraft III\Maps\omg\noskin9`，仅一张 `OMG-IMBA-v1.8.1-loadfix1-无肖像相机-只测试加载.w3x`；旧 noskin8 未改动。

## 待实机确认（静态已过）
- 本候选**仅用于加载验证**；独立 portrait 回退待解决，游戏内 K 头像/肖像取景需实机目测。
- 本轮不 commit/push，避免诊断混入主线，待用户实机决定。
