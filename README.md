# Glados 自动签到

用于 GLaDOS 自动签到与积分兑换，支持 Telegram Bot 推送、Telegram 话题线程推送、多账号显示账号名称，以及失败时仅发送 Telegram 通知。

## 功能说明

- 自动签到
- 自动兑换积分
- 支持多账号
- 支持 Telegram Bot 推送
- 支持 Telegram 话题线程推送
- 支持自定义账号显示名称
- 失败时仅发送 Telegram，避免 PushDeer 干扰

## 使用说明

### 1. 注册账号

老站注册地址：`https://glados.one`

新迁移站点：`https://railgun.info`

### 2. 配置 GitHub Actions Secrets

进入仓库：`Settings` -> `Secrets and variables` -> `Actions`

#### 2.1 必填项

添加 `GLADOS_COOKIES`，值为账号 Cookie 的有效部分。

获取方式：

1. 打开对应站点的签到页面，按 `F12`
2. 切换到 `Network`
3. 刷新页面
4. 点击签到或状态相关请求，在 `Request Headers` 中找到 `Cookie`
5. 复制完整 Cookie 值

站点参考：

- 老 GLaDOS：`https://glados.cloud/console/checkin`
- 新 Railgun：`https://railgun.info/console/checkin`

参考格式：

```text
koa:sess=eyJ1c2xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxAwMH0=; koa:sess.sig=xJkOxxxxxxxxxxxxxxxtnM;
```

多账号时，使用 `&` 连接多个 Cookie，顺序固定，例如：

```text
cookie_glados&cookie_railgun&cookie_glados_2
```

脚本默认会按 Cookie 自动识别当前账号属于老 GLaDOS 还是新 Railgun。
如果你已经明确知道每个账号对应哪个站点，建议配置 `GLADOS_ACCOUNT_SITES`，避免自动探测误判。

站点相关参数默认已内置，但也支持通过环境变量覆盖，方便站点域名、路径或页面结构变化后快速调整，无需改代码。

例如：

```text
cookie1&cookie2&cookie3
```

#### 2.2 积分兑换策略（可选）

添加 `GLADOS_EXCHANGE_PLAN`。

| 值 | 积分要求 | 兑换天数 |
|---|---:|---:|
| `plan100` | 100 | 10 天 |
| `plan200` | 200 | 30 天 |
| `plan500` | 500 | 100 天 |

默认值为 `plan500`。

#### 2.3 站点环境变量覆盖（可选）

默认内置站点：

- `glados` -> `https://glados.cloud`
- `railgun` -> `https://railgun.info`

如站点域名、接口路径、签到页路径、token 文案发生变化，可通过环境变量覆盖：

- `GLADOS_SITE_ORDER`：站点探测顺序，逗号分隔，例如 `railgun,glados`
- `GLADOS_GLADOS_BASE_URL`
- `GLADOS_GLADOS_CHECKIN_PATH`
- `GLADOS_GLADOS_STATUS_PATH`
- `GLADOS_GLADOS_POINTS_PATH`
- `GLADOS_GLADOS_EXCHANGE_PATH`
- `GLADOS_GLADOS_CONSOLE_CHECKIN_PATH`
- `GLADOS_GLADOS_TOKEN`
- `GLADOS_GLADOS_NAME`
- `GLADOS_RAILGUN_BASE_URL`
- `GLADOS_RAILGUN_CHECKIN_PATH`
- `GLADOS_RAILGUN_STATUS_PATH`
- `GLADOS_RAILGUN_POINTS_PATH`
- `GLADOS_RAILGUN_EXCHANGE_PATH`
- `GLADOS_RAILGUN_CONSOLE_CHECKIN_PATH`
- `GLADOS_RAILGUN_TOKEN`
- `GLADOS_RAILGUN_NAME`

示例：如果 `railgun.info` 后续切换域名，可只改 Secret/Variable：

```text
GLADOS_RAILGUN_BASE_URL=https://example.com
GLADOS_RAILGUN_TOKEN=example.com
GLADOS_RAILGUN_CONSOLE_CHECKIN_PATH=/console/checkin
```

接口路径若也变化，可继续覆盖，例如：

```text
GLADOS_RAILGUN_CHECKIN_PATH=/api/user/checkin
GLADOS_RAILGUN_STATUS_PATH=/api/user/status
GLADOS_RAILGUN_POINTS_PATH=/api/user/points
GLADOS_RAILGUN_EXCHANGE_PATH=/api/user/exchange
```

#### 2.4 推送配置（可选）

PushDeer：

- `PUSHDEER_SENDKEY`：PushDeer key

Telegram Bot：

- `TG_BOT_TOKEN`：BotFather 创建的 bot token
- `TG_CHAT_ID`：接收消息的 chat id
- `TG_MESSAGE_THREAD_ID`：可选，Telegram 话题线程 id

账号显示名称：

- `GLADOS_ACCOUNT_NAMES`：可选，多个账号名称使用 `&` 连接，顺序必须与 `GLADOS_COOKIES` 一致

账号固定站点：

- `GLADOS_ACCOUNT_SITES`：可选，多个站点标识使用 `&` 连接，顺序必须与 `GLADOS_COOKIES` 一致
- 支持值：`glados`、`railgun`
- 已配置的账号将直接走指定站点，不再自动探测；未配置项才回退为自动探测

示例：

```text
aaa@gmail.com&bbb@gmail.com
```

```text
railgun&glados
```

### 3. 推送行为说明

- Telegram 消息默认使用 Markdown 格式
- 如果配置了 `TG_MESSAGE_THREAD_ID`，消息会发送到指定话题
- 若本次结果中存在失败，仅发送 Telegram
- 若本次结果无失败，且同时配置了 `PUSHDEER_SENDKEY`，则会额外发送 PushDeer
- 若未配置账号显示名称，则默认显示为 `账号 1`、`账号 2`

## 文件结构

```text
checkin.py
.github/workflows/gladosCheck.yml
README.md
imgs/
```

## 更新日志

- **2026-04**：支持老 GLaDOS 与新 `railgun.info` 双站点自动识别；支持 Telegram Bot 推送、Markdown、话题线程、多账号名称显示，并调整为失败时仅发送 Telegram
- **2026-01**：重构签到脚本，增加日志输出，支持新版网址与积分兑换策略

## 问题排查

可在 GitHub Actions 的运行日志中查看详细执行结果，用于定位签到、兑换或推送问题。

## 声明

本项目不保证持续稳定运行。由于 GitHub 平台策略或 GLaDOS 接口变更，脚本可能失效，请自行备份。
