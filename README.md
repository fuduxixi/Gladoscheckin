# Glados 自动签到

用于 GLaDOS 自动签到与积分兑换，支持多账号、按站点分账号 Cookie、Telegram Bot 推送（含话题线程）、账号自定义显示名，以及失败时仅发送 Telegram 通知。

- 站点：老站 `https://glados.cloud`（镜像 `glados.one` / `glados.network` 等）、新站 `https://railgun.info`
- 运行：GitHub Actions 定时执行（每天 2 次），也可手动触发

---

## 目录

- [1. 快速开始](#1-快速开始)
- [2. 配置 Cookie（两种方式）](#2-配置-cookie两种方式)
- [3. 怎么取 Cookie](#3-怎么取-cookie)
- [4. Secrets / 环境变量总表](#4-secrets--环境变量总表)
- [5. 推送行为](#5-推送行为)
- [6. 积分兑换](#6-积分兑换)
- [7. 排查手册](#7-排查手册)
- [8. 文件结构](#8-文件结构)
- [9. 更新日志](#9-更新日志)

---

## 1. 快速开始

1. 在对应站点注册并登录账号：老站 `https://glados.cloud`，新站 `https://railgun.info`
2. 进入仓库 `Settings` → `Secrets and variables` → `Actions`，按下面的方式添加 Cookie
3. 到 `Actions` → `auto check` → `Run workflow` 手动跑一次，确认推送结果
4. 之后每天自动运行，无需干预

> 建议先看 [2. 配置 Cookie](#2-配置-cookie两种方式)：**推荐用「按站点分账号」，以后哪个账号失效只改那一个 secret。**

---

## 2. 配置 Cookie（两种方式）

### 方式一（推荐）：按站点分账号，哪个失效改哪个

每个账号单独一个 Secret，互相独立。**某个 Cookie 失效时，只需更新它对应的那一个**，不用动另一个，也不会误删。

| Secret | 必填 | 说明 |
|---|---|---|
| `GLADOS_COOKIE_RAILGUN` | 二选一 | 新站 `railgun.info` 账号的 Cookie |
| `GLADOS_COOKIE_GLADOS` | 二选一 | 老站 `glados.cloud` 账号的 Cookie |
| `GLADOS_NAME_RAILGUN` | 可选 | 新站账号显示名，例如 `account1@example.com` |
| `GLADOS_NAME_GLADOS` | 可选 | 老站账号显示名，例如 `account2@example.com` |

行为说明：

- 只要设置了**任意一个** `GLADOS_COOKIE_*`，脚本就进入「按站点模式」：
  - 该账号的站点**强制绑定**，不再自动探测，也就不会再出现「站点识别失败」
  - 此时**整条 `GLADOS_COOKIES` 会被忽略**（日志会提示），避免同一账号重复签到
- 两个站点各只支持一个账号；同一站点多账号请用方式二
- 没配 `GLADOS_NAME_*` 时，按顺序回退到 `GLADOS_ACCOUNT_NAMES` 的位置取值，取不到就显示 `账号 N`

日志特征：

```text
已启用按站点 Cookie: railgun(account1@example.com), glados(account2@example.com)
第 1 个账户已指定站点: railgun
第 2 个账户已指定站点: glados
```

### 方式二（兼容）：合并成一条 `GLADOS_COOKIES`

多账号用 `&` 连接成一条，顺序与 `GLADOS_ACCOUNT_NAMES` / `GLADOS_ACCOUNT_SITES` 一一对应。

```text
cookie_railgun&cookie_glados
```

- 未设置任何 `GLADOS_COOKIE_*` 时生效
- 顺序固定：第 1 段对应 `GLADOS_ACCOUNT_NAMES` 第 1 个名字、`GLADOS_ACCOUNT_SITES` 第 1 个站点，以此类推
- 支持一个站点挂多个账号（此时必须用 `GLADOS_ACCOUNT_SITES` 指明站点，否则靠自动探测）
- **注意**：GitHub Secret 只写不读，点 `Update` 时输入框是空的（不会回显旧值）。**只填一段会让其他账号立刻失效**，必须把整条重新粘贴一遍

### 两种方式怎么选

| 场景 | 建议 |
|---|---|
| 每个站点各一个账号（最常见） | **方式一**，独立 secret，哪个失效改哪个 |
| 同一站点多个账号 | 方式二 + `GLADOS_ACCOUNT_SITES` |
| 从旧配置迁移 | 先建好 `GLADOS_COOKIE_*`，跑一次确认正常后，可删掉 `GLADOS_COOKIES` |

---

## 3. 怎么取 Cookie

1. 打开对应站点的签到页：
   - 老 GLaDOS：`https://glados.cloud/console/checkin`
   - 新 Railgun：`https://railgun.info/console/checkin`
2. 确认页面处于**已登录**状态（没登录就先登录）
3. 按 `F12` → 切到 `Network` → 刷新页面
4. 点任意一个 `/api/user/...` 请求，在 `Request Headers` 里找到 `Cookie`
5. 复制**完整值**（右键 → Copy value），格式如下：

```text
koa:sess=eyJ1c2...wMH0=; koa:sess.sig=xJkOxxxxxxxxxxxxxxxtnM;
```

> 会话有效期大约 1 个月。仓库长期不运行 / 长时间没重新登录后，Cookie 必然失效，重新登录再取一次即可。

---

## 4. Secrets / 环境变量总表

### 4.1 Cookie 与账号

| 名称 | 必填 | 说明 |
|---|---|---|
| `GLADOS_COOKIE_RAILGUN` | 见上 | 新站 Cookie（推荐） |
| `GLADOS_COOKIE_GLADOS` | 见上 | 老站 Cookie（推荐） |
| `GLADOS_NAME_RAILGUN` / `GLADOS_NAME_GLADOS` | 可选 | 按站点账号显示名 |
| `GLADOS_COOKIES` | 兼容 | 多账号合并 Cookie，`&` 连接 |
| `GLADOS_ACCOUNT_NAMES` | 可选 | 多账号显示名，`&` 连接，与 `GLADOS_COOKIES` 顺序一致 |
| `GLADOS_ACCOUNT_SITES` | 可选 | 多账号站点绑定，`&` 连接，取值 `railgun` / `glados` |
| `GLADOS_SITE_ORDER` | 可选 | 自动探测顺序，逗号分隔，默认 `railgun,glados` |

### 4.2 推送

| 名称 | 说明 |
|---|---|
| `TG_BOT_TOKEN` | Telegram Bot token（BotFather 创建） |
| `TG_CHAT_ID` | 接收消息的 chat id |
| `TG_MESSAGE_THREAD_ID` | 可选，话题线程 id |
| `PUSHDEER_SENDKEY` | 可选，PushDeer key |

### 4.3 兑换

| 名称 | 说明 |
|---|---|
| `GLADOS_EXCHANGE_PLAN` | `plan100` / `plan200` / `plan500`，默认 `plan500` |

### 4.4 站点参数覆盖（接口变更时用，无需改代码）

默认内置站点：

- `glados` → `https://glados.cloud`
- `railgun` → `https://railgun.info`

对每个站点 `<SITE>`（`GLADOS` / `RAILGUN`）都可覆盖：

```text
GLADOS_<SITE>_BASE_URL
GLADOS_<SITE>_CHECKIN_PATH
GLADOS_<SITE>_STATUS_PATH
GLADOS_<SITE>_POINTS_PATH
GLADOS_<SITE>_EXCHANGE_PATH
GLADOS_<SITE>_CONSOLE_CHECKIN_PATH
GLADOS_<SITE>_TOKEN
GLADOS_<SITE>_NAME
```

示例：`railgun.info` 换域名时，只需改 Secret/Variable：

```text
GLADOS_RAILGUN_BASE_URL=https://example.com
GLADOS_RAILGUN_TOKEN=example.com
GLADOS_RAILGUN_CONSOLE_CHECKIN_PATH=/console/checkin
```

> 注意：新增的 `GLADOS_COOKIE_*` / `GLADOS_NAME_*` 需要在 workflow 的 `env:` 中转发才会传给脚本，仓库已内置。

---

## 5. 推送行为

- Telegram 消息使用 Markdown 格式
- 配置了 `TG_MESSAGE_THREAD_ID` 时发送到指定话题
- **本次存在失败 → 只发 Telegram**，不发 PushDeer（避免干扰）
- 本次无失败且配置了 `PUSHDEER_SENDKEY` → 额外发 PushDeer
- 未配置账号显示名 → 显示为 `账号 1`、`账号 2`
- 推送正文**不会**打进 Actions 日志（防止脱敏影响可读性），要核对每个账号的明细请看 Telegram 消息

Telegram 消息示例：

```text
*GLaDOS 签到结果*

- 成功: 1
- 失败: 0
- 重复: 1

*account1@example.com*
- 站点: `Railgun`
- 本次积分: `2`
- 剩余天数: `358 天`
- 总积分: `45 积分`
- 签到状态: 签到成功，获得 2 积分
- 兑换状态: 积分不足，未兑换: plan500
```

---

## 6. 积分兑换

| 值 | 需要积分 | 兑换天数 |
|---|---:|---:|
| `plan100` | 100 | 10 天 |
| `plan200` | 200 | 30 天 |
| `plan500` | 500 | 100 天 |

- 不配置 `GLADOS_EXCHANGE_PLAN` 时默认按 `plan500` 判断
- 积分不足时只提示「积分不足，未兑换」，不算失败

---

## 7. 排查手册

### 7.1 先看哪里

`Actions` → `auto check` → 最近一次运行 → `glados checkin` → `running checkin` 步骤日志。关键行：

```text
已启用按站点 Cookie: railgun(xxx), glados(xxx)     ← 确认用的是哪种 Cookie 模式
共加载了 N 个 Cookie 用于签到
正在处理第 N 个账户...
第 N 个账户已指定站点: xxx                          ← 站点绑定情况
[GLaDOS] 签到失败: code=-2, message=没有权限, reason=None
推送标题: GLaDOS 签到, 成功0, 失败1, 重复1
```

> 定时任务由 GitHub 调度，**经常延迟几十分钟到几小时**，属正常现象。
> `delete-workflow-runs` 只保留最近 7 天日志，更早的会 410 过期，要判断「从哪天开始坏」请尽早看。

### 7.2 错误码含义（判根因靠这个）

| 日志特征 | 含义 | 处理 |
|---|---|---|
| `code=-2, message=没有权限` | **Cookie / 会话失效**（最常见） | 重新登录该站点，按 [第 3 节](#3-怎么取-cookie) 取新 Cookie，只更新对应账号那一个 secret |
| `code=4, reason=device-mismatch` | GLaDOS 防自动化**设备校验**：请求 UA 平台与登录设备不一致 | 脚本已内置自适应：按服务端返回的 `loginDevice` 切换 UA 重试一次，一般无需处理；若持续失败，重新登录后在浏览器手动签到一次并刷新 Cookie |
| 推送里「站点识别失败 / 未知站点」 | 自动探测阶段，两个站的 `/api/user/status` 都没返回 `data` / `leftDays` / `code==0` | 基本等同 Cookie 失效；日志会打印每个站的 `HTTP / code / message`。改用「按站点模式」可彻底避免此问题 |
| 「重复签到，明天再来」 | 当天已经签过 | 正常，不是错误 |
| 「积分不足，未兑换」 | 积分没到兑换门槛 | 正常，不是错误 |
| 请求失败 / 状态码 5xx | 网络抖动 | 脚本已内置重试（3 次，退避 1/2/4 秒，429/5xx 自动重试） |

### 7.3 常见问题

**Q：改了 `GLADOS_COOKIES` 后另一个账号也失效了？**
GitHub Secret 不回显旧值，点 `Update` 后必须把**整条**重新粘贴。改用「按站点模式」就不会再有这个问题。

**Q：为什么今天显示「重复」而不是「成功」？**
当天已经签过一次（手动触发或定时任务先跑过）。第二天首次运行会显示签到成功。

**Q：日志里 `GLADOS_ACCOUNT_SITES 未设置`？**
这句反映的是 **workflow 有没有把这个 secret 转发给脚本**，不是 secret 存不存在。用「按站点模式」时不需要它。

**Q：怎么只测一个账号？**
暂时把另一个 `GLADOS_COOKIE_*` 删除，跑完再补回来；或本地 `python checkin.py` 并只设一个环境变量。

**Q：本地怎么跑？**

```bash
pip install requests pypushdeer
GLADOS_COOKIE_RAILGUN='koa:sess=...; koa:sess.sig=...' python checkin.py
```

---

## 8. 文件结构

```text
checkin.py                          # 签到主脚本
.github/workflows/gladosCheck.yml   # Actions 定时任务
README.md
```

---

## 9. 更新日志

- **2026-10**：
  - 新增**按站点分账号 Cookie**：`GLADOS_COOKIE_RAILGUN` / `GLADOS_COOKIE_GLADOS`（+ 可选 `GLADOS_NAME_*`），单个账号失效只改一个 secret，站点强制绑定
  - workflow 补上 `GLADOS_ACCOUNT_SITES` 转发（此前 secret 已建但从未传给脚本）
  - 站点识别失败时打印每个站的 `HTTP / code / message`，签到失败时打印 `code / reason`，便于定位
  - 新增 `code:4 device-mismatch` 设备平台自适应（按 `loginDevice` 切换 UA 重试一次）
  - 新增网络层重试/退避：`Session + HTTPAdapter + urllib3.Retry`（3 次，1/2/4 秒，429/5xx）
- **2026-04**：支持老 GLaDOS 与新 `railgun.info` 双站点自动识别；支持 Telegram Bot 推送、Markdown、话题线程、多账号名称显示；失败时仅发送 Telegram
- **2026-01**：重构脚本，增加日志输出，支持新版网址与积分兑换策略

---

## 声明

本项目不保证持续稳定运行。由于 GitHub 平台策略或 GLaDOS 接口变更，脚本可能失效，请自行备份。
