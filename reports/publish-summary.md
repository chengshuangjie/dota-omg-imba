# Git 发布记录（publish-summary）

## 目标仓库

- 远端：https://github.com/chengshuangjie/dota-omg-imba
- 默认分支：main
- 提交信息：`feat: ship XOMG1 IMBA gameplay and stability hardening`

## 本地提交状态（已完成，待网络推送）

- 本地 HEAD commit SHA：`5e3a63fadcacc5ee28cb59b5e2609323cc8d0de4`
- 分支：main（root-commit，36 files changed, 536227 insertions）
- 暂存白名单：`src/`、`tools/`、`config/tool-paths.example.json`、`README.md`、`.gitignore`、公开 `reports/`（不含 backup-*）、`assets/loading-screen/`。
- 已排除（.gitignore 生效，未入暂存）：
  - `maps/**/*.w3x` 地图二进制（远端空仓无 LFS）
  - `reports/backup-*/` 本地备份（含约 46MB .w3x.bak）
  - `config/tool-paths.json` 本机绝对路径配置
  - `*.bak` / 日志 / 缓存 / 浏览器与凭证材料

## 推送阻塞（需用户在本机网络/代理就绪后执行）

- 现象：`git push -u origin main` 报 `fatal: unable to access 'https://github.com/chengshuangjie/dota-omg-imba.git/': Failed to connect to github.com:443 after 21079 ms: Could not connect to server`。
- 排查：git 全局无 http(s).proxy；环境变量无 HTTP(S)_PROXY；本机监听端口无常见代理（7890/7897/1080/10809/8888 均未监听）。
- 结论：本机当前网络无法直连 github.com:443，属网络连通性阻塞（非凭证/登录页问题）。未操作浏览器认证页、未 force。
- 网络/代理就绪后，在仓库根目录执行一次即可完成推送：
  ```powershell
  git push -u origin main
  ```
  推送后用 `git ls-remote origin main` 或网页确认远端 main HEAD 等于 `5e3a63fadcacc5ee28cb59b5e2609323cc8d0de4`。

## 敏感扫描结果

递归扫描待提交文本文件（.ps1/.py/.json/.md/.html/.j/.slk/.txt，排除 maps 与 reports/backup-*）：

- 无 KK 缓存 / DotaDalaran 实验材料 / 浏览器数据 / cookie / token / password / 私钥（-----BEGIN）。
- 命中项均为良性：`tool-paths.example.json` 的 `C:/PATH/TO/...` 占位；`war3map.j` 的游戏音效 `SecretFound.wav`；`trim_modes_v2.py` 的代码变量 `token`；报告中“KK 认证”为发布待办文字。
- 本机绝对路径已清洗：`verification-latest.json` 的 map 字段改为相对路径 `maps/build/...`；`SLK精简报告.json` 的旧 `D:\dota\DOTA69AI\...` 前缀改为 `Units/...`；哈希与验证结论未改动。
- 真实 `config/tool-paths.json`（含 `D:\dota\DOTAOMGAY\...`）已被 .gitignore 排除，未提交。

## 未入库本地 W3X（保留在本地，不入 Git 历史）

| 文件 | 大小(字节) | SHA-256 |
| --- | --- | --- |
| maps/baseline/DOTA-OMG-IMBA-轻量化基线.w3x | 43,601,181 | `55dbca6debd44ae60284e819061d5136b2670120f7e80e0d2331dbc31b29a546` |
| maps/build/DOTA-OMG-IMBA-轻量化开发版.w3x | 46,161,255 | `b8b2ef336372a6854c0523cecb937fe1545d6beab65102eaaae3ecb62bc528ee` |

包内 war3map.j SHA-256：`ea6d950368183556eec44c231a41541654b3bac4183ab78bac4e92dc5892d403`。

## 外部 KK 发布待办（不阻塞本地交付）

1. 完成个人 KK 认证，创建或认领新地图项目。
2. 在 KK 后台为 `XOMG1_` 系列键开通 ServerValue 与 Stat 服务器存档规则 / 写入权限。
3. 本地为纯静态/构建级验证，无法模拟 KK 真实服务器；CAS 读回、故障锁、空键默认与线上 Stat 展示需在 KK 环境回归。
