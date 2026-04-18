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

### 1. 注册 GLaDOS 账号

注册地址：`https://glados.one`

### 2. 配置 GitHub Actions Secrets

进入仓库：`Settings` -> `Secrets and variables` -> `Actions`

#### 2.1 必填项

添加 `GLADOS_COOKIES`，值为 GLaDOS 账号 Cookie 的有效部分。

获取方式：

1. 打开 GLaDOS 签到页面，按 `F12`
2. 切换到 `Network`
3. 刷新页面
4. 点击第一个请求，在 `Request Headers` 中找到 `Cookie`
5. 复制完整 Cookie 值

参考格式：

```text
koa:sess=eyJ1c2xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxAwMH0=; koa:sess.sig=xJkOxxxxxxxxxxxxxxxtnM;
```

多账号时，使用 `&` 连接多个 Cookie，顺序固定，例如：

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

#### 2.3 推送配置（可选）

PushDeer：

- `PUSHDEER_SENDKEY`：PushDeer key

Telegram Bot：

- `TG_BOT_TOKEN`：BotFather 创建的 bot token
- `TG_CHAT_ID`：接收消息的 chat id
- `TG_MESSAGE_THREAD_ID`：可选，Telegram 话题线程 id

账号显示名称：

- `GLADOS_ACCOUNT_NAMES`：可选，多个账号名称使用 `&` 连接，顺序必须与 `GLADOS_COOKIES` 一致

示例：

```text
aaa@gmail.com&bbb@gmail.com
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

- **2026-04**：支持 Telegram Bot 推送、Markdown、话题线程、多账号名称显示，并调整为失败时仅发送 Telegram
- **2026-01**：重构签到脚本，增加日志输出，支持新版网址与积分兑换策略

## 问题排查

可在 GitHub Actions 的运行日志中查看详细执行结果，用于定位签到、兑换或推送问题。

## 声明

本项目不保证持续稳定运行。由于 GitHub 平台策略或 GLaDOS 接口变更，脚本可能失效，请自行备份。
