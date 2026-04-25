import requests
import json
import os
import logging
import datetime
from typing import Dict, List, Optional, Tuple
from pypushdeer import PushDeer

def beijing_time_converter(timestamp):
    utc_dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
    beijing_tz = datetime.timezone(datetime.timedelta(hours=8))
    beijing_dt = utc_dt.astimezone(beijing_tz)
    return beijing_dt.timetuple()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

root_logger = logging.getLogger()
for handler in root_logger.handlers:
    if hasattr(handler, 'formatter') and handler.formatter is not None:
        handler.formatter.converter = beijing_time_converter

logger = logging.getLogger(__name__)


# ENVIRONMENT
ENV_PUSH_KEY = "PUSHDEER_SENDKEY"
ENV_TG_BOT_TOKEN = "TG_BOT_TOKEN"
ENV_TG_CHAT_ID = "TG_CHAT_ID"
ENV_TG_MESSAGE_THREAD_ID = "TG_MESSAGE_THREAD_ID"
ENV_ACCOUNT_NAMES = "GLADOS_ACCOUNT_NAMES"
ENV_COOKIES = "GLADOS_COOKIES"
ENV_EXCHANGE_PLAN = "GLADOS_EXCHANGE_PLAN"
ENV_SITE_ORDER = "GLADOS_SITE_ORDER"

# API URLs
TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"

DEFAULT_SITE_CONFIGS = {
    "glados": {
        "name": "GLaDOS",
        "base_url": "https://glados.cloud",
        "checkin_path": "/api/user/checkin",
        "status_path": "/api/user/status",
        "points_path": "/api/user/points",
        "exchange_path": "/api/user/exchange",
        "console_checkin_path": "/console/checkin",
        "token": "glados.cloud",
    },
    "railgun": {
        "name": "Railgun",
        "base_url": "https://railgun.info",
        "checkin_path": "/api/user/checkin",
        "status_path": "/api/user/status",
        "points_path": "/api/user/points",
        "exchange_path": "/api/user/exchange",
        "console_checkin_path": "/console/checkin",
        "token": "railgun.info",
    },
}

SITE_CONFIGS: Dict[str, Dict[str, object]] = {}
SITE_DETECT_ORDER: List[str] = []

# Request Headers
HEADERS_TEMPLATE = {
    'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    'content-type': 'application/json;charset=UTF-8',
    'accept': 'application/json, text/plain, */*'
}

# Exchange Plan Points
EXCHANGE_POINTS = {"plan100": 100, "plan200": 200, "plan500": 500}


def env_site_key_prefix(site_key: str) -> str:
    # 站点环境变量前缀按站点 key 动态生成：
    # glados -> GLADOS_GLADOS_*
    # railgun -> GLADOS_RAILGUN_*
    return f"GLADOS_{site_key.upper()}"


def join_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def resolve_site_config(site_key: str, base_config: Dict[str, str]) -> Dict[str, object]:
    # 这里不逐个声明常量，而是按 prefix 规则读取环境变量。
    # 例如 glados 站读取 GLADOS_GLADOS_BASE_URL / GLADOS_GLADOS_TOKEN，
    # railgun 站读取 GLADOS_RAILGUN_BASE_URL / GLADOS_RAILGUN_TOKEN。
    prefix = env_site_key_prefix(site_key)
    base_url = os.environ.get(f"{prefix}_BASE_URL", base_config["base_url"]).strip().rstrip("/")
    checkin_path = os.environ.get(f"{prefix}_CHECKIN_PATH", base_config["checkin_path"]).strip()
    status_path = os.environ.get(f"{prefix}_STATUS_PATH", base_config["status_path"]).strip()
    points_path = os.environ.get(f"{prefix}_POINTS_PATH", base_config["points_path"]).strip()
    exchange_path = os.environ.get(f"{prefix}_EXCHANGE_PATH", base_config["exchange_path"]).strip()
    console_checkin_path = os.environ.get(
        f"{prefix}_CONSOLE_CHECKIN_PATH",
        base_config["console_checkin_path"],
    ).strip()
    token = os.environ.get(f"{prefix}_TOKEN", base_config["token"]).strip()
    site_name = os.environ.get(f"{prefix}_NAME", base_config["name"]).strip()

    return {
        "name": site_name,
        "base_url": base_url,
        "checkin_url": join_url(base_url, checkin_path),
        "status_url": join_url(base_url, status_path),
        "points_url": join_url(base_url, points_path),
        "exchange_url": join_url(base_url, exchange_path),
        "checkin_data": {"token": token},
        "headers": {
            'referer': join_url(base_url, console_checkin_path),
            'origin': base_url,
        },
    }


def initialize_site_configs() -> None:
    global SITE_CONFIGS, SITE_DETECT_ORDER

    SITE_CONFIGS = {
        site_key: resolve_site_config(site_key, site_config)
        for site_key, site_config in DEFAULT_SITE_CONFIGS.items()
    }

    default_order = ["railgun", "glados"]
    raw_site_order = (os.environ.get(ENV_SITE_ORDER) or "").strip()
    if raw_site_order:
        requested_order = [item.strip().lower() for item in raw_site_order.split(",") if item.strip()]
        valid_order = [item for item in requested_order if item in SITE_CONFIGS]
        missing_sites = [item for item in requested_order if item not in SITE_CONFIGS]
        if missing_sites:
            logger.warning(f"忽略未知站点标识: {', '.join(missing_sites)}")
        SITE_DETECT_ORDER = valid_order or default_order
    else:
        SITE_DETECT_ORDER = default_order

    logger.info(
        "已加载站点配置: %s",
        ", ".join(
            f"{site_key}={SITE_CONFIGS[site_key]['base_url']}" for site_key in SITE_DETECT_ORDER
        ),
    )


def load_config() -> Tuple[str, str, str, str, List[str], List[str], str]:
    push_key_env = os.environ.get(ENV_PUSH_KEY)
    tg_bot_token_env = os.environ.get(ENV_TG_BOT_TOKEN)
    tg_chat_id_env = os.environ.get(ENV_TG_CHAT_ID)
    tg_message_thread_id_env = os.environ.get(ENV_TG_MESSAGE_THREAD_ID)
    account_names_env = os.environ.get(ENV_ACCOUNT_NAMES)
    raw_cookies_env = os.environ.get(ENV_COOKIES)
    exchange_plan_env = os.environ.get(ENV_EXCHANGE_PLAN)

    if not push_key_env:
        logger.warning(f"环境变量 '{ENV_PUSH_KEY}' 未设置。")
        push_key = ''
    else:
        push_key = push_key_env

    if not tg_bot_token_env or not tg_chat_id_env:
        if tg_bot_token_env or tg_chat_id_env:
            logger.warning(
                f"Telegram Bot 推送配置不完整，需要同时设置 '{ENV_TG_BOT_TOKEN}' 和 '{ENV_TG_CHAT_ID}'。"
            )
        tg_bot_token = ''
        tg_chat_id = ''
    else:
        tg_bot_token = tg_bot_token_env
        tg_chat_id = tg_chat_id_env

    tg_message_thread_id = (tg_message_thread_id_env or '').strip()

    if not raw_cookies_env:
        logger.warning(f"环境变量 '{ENV_COOKIES}' 未设置。")
        cookies_list = []
    else:
        cookies_list = [cookie.strip() for cookie in raw_cookies_env.split('&') if cookie.strip()]
        if not cookies_list:
            raise ValueError(f"环境变量 '{ENV_COOKIES}' 已设置，但未包含任何有效的 Cookie。")

    if not account_names_env:
        account_names = []
    else:
        account_names = [name.strip() for name in account_names_env.split('&') if name.strip()]

    if not exchange_plan_env:
        logger.warning(f"环境变量 '{ENV_EXCHANGE_PLAN}' 未设置，将使用默认兑换计划 'plan500'。")
        exchange_plan = "plan500"
    else:
        if exchange_plan_env in EXCHANGE_POINTS:
            exchange_plan = exchange_plan_env
            logger.info(f"使用指定的兑换计划: {exchange_plan}")
        else:
            logger.warning(f"环境变量 '{ENV_EXCHANGE_PLAN}' 的值 '{exchange_plan_env}' 无效，将使用默认兑换计划 'plan500'。")
            exchange_plan = "plan500"

    if account_names and len(account_names) != len(cookies_list):
        logger.warning(
            f"环境变量 '{ENV_ACCOUNT_NAMES}' 中的账号数量与 Cookie 数量不一致，将对缺失项回退为默认账号名。"
        )

    logger.info(f"共加载了 {len(cookies_list)} 个 Cookie 用于签到。")
    logger.info(f"当前 {ENV_PUSH_KEY} {'已设置' if push_key_env else '未设置'}。")
    logger.info(
        f"当前 Telegram Bot 推送 {'已设置' if tg_bot_token and tg_chat_id else '未设置'}。"
    )
    logger.info(
        f"当前 Telegram 话题 {'已设置' if tg_message_thread_id else '未设置'}。"
    )
    logger.info(f"当前 {ENV_EXCHANGE_PLAN}: {exchange_plan}。")

    return push_key, tg_bot_token, tg_chat_id, tg_message_thread_id, cookies_list, account_names, exchange_plan


def build_headers(site_key: str) -> Dict[str, str]:
    site_headers = SITE_CONFIGS[site_key].get("headers", {})
    return {**HEADERS_TEMPLATE, **site_headers}


def make_request(url: str, method: str, headers: Dict[str, str], data: Optional[Dict] = None, cookies: str = "") -> Optional[requests.Response]:

    session_headers = headers.copy()
    session_headers['cookie'] = cookies

    try:
        if method.upper() == 'POST':
            response = requests.post(url, headers=session_headers, data=json.dumps(data), timeout=20)
        elif method.upper() == 'GET':
            response = requests.get(url, headers=session_headers, timeout=20)
        else:
            logger.error(f"不支持的 HTTP 方法: {method}")
            return None

        if not response.ok:
            logger.warning(f"向 {url} 发起的请求失败，状态码 {response.status_code}。响应内容: {response.text}")
            return None
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"向 {url} 发起请求时发生网络错误: {e}")
        return None


def detect_site(cookie: str) -> Optional[str]:
    for site_key in SITE_DETECT_ORDER:
        site = SITE_CONFIGS[site_key]
        status_response = make_request(site["status_url"], 'GET', build_headers(site_key), cookies=cookie)
        if not status_response:
            continue

        try:
            status_data = status_response.json()
        except json.JSONDecodeError:
            logger.warning(f"站点 {site['name']} 状态接口返回非 JSON，跳过探测。")
            continue

        if isinstance(status_data, dict):
            if 'data' in status_data or 'leftDays' in status_data or status_data.get('code') == 0:
                logger.info(f"Cookie 已识别为 {site['name']} 站点。")
                return site_key

    return None


def checkin_and_process(cookie: str, exchange_plan: str) -> Tuple[str, str, str, str, str, str]:

    site_key = detect_site(cookie)
    if not site_key:
        return "站点识别失败", "0", "获取剩余天数失败", "获取剩余积分失败", "兑换跳过或失败", "未知站点"

    site = SITE_CONFIGS[site_key]
    site_name = site["name"]
    site_headers = build_headers(site_key)

    status_msg = "签到请求失败"
    points_gained = "0"
    remaining_days = "获取剩余天数失败"
    remaining_points = "获取剩余积分失败"
    exchange_msg = "兑换跳过或失败"
    points_data = {}

    checkin_response = make_request(site["checkin_url"], 'POST', site_headers, site["checkin_data"], cookies=cookie)
    if not checkin_response:
        return status_msg, points_gained, remaining_days, remaining_points, exchange_msg, site_name

    try:
        checkin_data = checkin_response.json()
        response_message = str(checkin_data.get('message', '无消息字段'))
        points_gained = str(checkin_data.get('points', 0))
        response_message_lower = response_message.lower()

        if "checkin" in response_message_lower and "got" in response_message_lower:
            status_msg = f"签到成功，获得 {points_gained} 积分"
        elif "repeat" in response_message_lower or "already" in response_message_lower:
            status_msg = "重复签到，明天再来"
            points_gained = "0"
        elif checkin_data.get('code') == 0:
            status_msg = f"签到成功，获得 {points_gained} 积分"
        else:
            status_msg = f"签到失败: {response_message}"
            points_gained = "0"
    except json.JSONDecodeError:
        logger.error(f"解析签到响应 JSON 失败: {checkin_response.text}")
        return status_msg, points_gained, remaining_days, remaining_points, exchange_msg, site_name

    status_response = make_request(site["status_url"], 'GET', site_headers, cookies=cookie)
    if status_response:
        try:
            status_data = status_response.json()
            status_payload = status_data.get('data', status_data)
            left_days_float = status_payload.get('leftDays', None)
            if left_days_float is not None:
                remaining_days = f"{int(float(left_days_float))} 天"
            else:
                remaining_days = "获取剩余天数失败 (响应结构异常)"
        except json.JSONDecodeError:
            logger.error(f"解析状态响应 JSON 失败: {status_response.text}")
            remaining_days = "获取剩余天数失败 (JSON解析错误)"
        except (ValueError, TypeError):
            logger.error(f"解析剩余天数时出错: {status_data.get('data', {}).get('leftDays', 'unknown') if 'status_data' in locals() else 'unknown'}")
            remaining_days = "获取剩余天数失败 (数值转换错误)"
    else:
        remaining_days = "获取剩余天数失败 (HTTP请求失败)"

    points_response = make_request(site["points_url"], 'GET', site_headers, cookies=cookie)
    if points_response:
        try:
            points_data = points_response.json()
            points_float = points_data.get('points', None)
            if points_float is None:
                points_float = points_data.get('data', {}).get('points', None) if isinstance(points_data.get('data'), dict) else None
            if points_float is not None:
                remaining_points = f"{int(float(points_float))} 积分"
            else:
                remaining_points = "获取剩余积分失败 (响应结构异常)"
        except json.JSONDecodeError:
            logger.error(f"解析积分响应 JSON 失败: {points_response.text}")
            remaining_points = "获取剩余积分失败 (JSON解析错误)"
        except (ValueError, TypeError):
            logger.error(f"解析剩余积分时出错: {points_data.get('points', 'unknown') if isinstance(points_data, dict) else 'unknown'}")
            remaining_points = "获取剩余积分失败 (数值转换错误)"
    else:
        remaining_points = "获取剩余积分失败 (HTTP请求失败)"

    current_points_numeric = 0
    try:
        current_points_source = points_data.get('points', 0)
        if current_points_source in (None, '') and isinstance(points_data.get('data'), dict):
            current_points_source = points_data.get('data', {}).get('points', 0)
        current_points_numeric = int(float(current_points_source))
    except (ValueError, TypeError, AttributeError):
        logger.warning(f"无法解析当前积分数值，可能影响兑换判断: {remaining_points}")

    required_points = EXCHANGE_POINTS.get(exchange_plan, 500)
    if current_points_numeric >= required_points:
        logger.info(f"[{site_name}] 开始兑换 {exchange_plan} 计划 (需要 {required_points} 积分)")
        exchange_response = make_request(site["exchange_url"], 'POST', site_headers, {"planType": exchange_plan}, cookies=cookie)
        if exchange_response:
            try:
                exchange_data = exchange_response.json()
                code = exchange_data.get('code', -1)
                if code == 0:
                    exchange_msg = f"兑换成功：{exchange_plan}"
                else:
                    detailed_msg = exchange_data.get('message', "未知错误")
                    exchange_msg = f"兑换失败: {exchange_plan}, 错误代码: {code}, 详情: {detailed_msg}"
            except json.JSONDecodeError:
                logger.error(f"解析兑换响应 JSON 失败: {exchange_response.text}")
                exchange_msg = f"兑换响应解析失败: {exchange_plan}"
        else:
            exchange_msg = f"兑换请求失败：{exchange_plan}"
    else:
        logger.info(f"[{site_name}] 积分不足以兑换 {exchange_plan}。所需: {required_points}, 当前: {current_points_numeric}")
        exchange_msg = f"积分不足，未兑换: {exchange_plan}"

    return status_msg, points_gained, remaining_days, remaining_points, exchange_msg, site_name


def has_failures(results: List[Dict[str, str]]) -> bool:
    return any("失败" in r['status'] or "失败" in r['exchange'] for r in results)


def get_account_label(account_names: List[str], index: int) -> str:
    if index < len(account_names) and account_names[index]:
        return account_names[index]
    return f"账号 {index + 1}"


def format_push_content(results: List[Dict[str, str]], account_names: List[str]) -> Tuple[str, str]:

    success_count = sum(1 for r in results if "成功" in r['status'])
    fail_count = sum(1 for r in results if "失败" in r['status'] or "失败" in r['exchange'])
    repeat_count = sum(1 for r in results if "重复" in r['status'])

    title = f'GLaDOS 签到, 成功{success_count}, 失败{fail_count}, 重复{repeat_count}'

    content_lines = []
    for i, res in enumerate(results):
        line_parts = [
            f"{get_account_label(account_names, i)}[{res['site']}]:",
            f"P:{res['points']}",
            f"剩余天数:{res['days']}",
            f"总积分:{res['points_total']}",
            f"| {res['status']}",
            f"; {res['exchange']}"
        ]
        line = " ".join(line_parts)
        content_lines.append(line)

    content = "\n".join(content_lines)
    return title, content


def format_telegram_content(results: List[Dict[str, str]], account_names: List[str]) -> str:
    success_count = sum(1 for r in results if "成功" in r['status'])
    fail_count = sum(1 for r in results if "失败" in r['status'] or "失败" in r['exchange'])
    repeat_count = sum(1 for r in results if "重复" in r['status'])

    lines = [
        "*GLaDOS 签到结果*",
        "",
        f"- 成功: {success_count}",
        f"- 失败: {fail_count}",
        f"- 重复: {repeat_count}",
        ""
    ]

    for i, res in enumerate(results):
        lines.extend([
            f"*{get_account_label(account_names, i)}*",
            f"- 站点: `{res['site']}`",
            f"- 本次积分: `{res['points']}`",
            f"- 剩余天数: `{res['days']}`",
            f"- 总积分: `{res['points_total']}`",
            f"- 签到状态: {res['status']}",
            f"- 兑换状态: {res['exchange']}",
            ""
        ])

    return "\n".join(lines).strip()


def send_pushdeer_notification(push_key: str, title: str, content: str) -> bool:
    try:
        pushdeer = PushDeer(pushkey=push_key)
        pushdeer.send_text(title, desp=content)
        logger.info("PushDeer 推送发送成功。")
        return True
    except Exception as e:
        logger.error(f"发送 PushDeer 推送失败: {e}")
        return False


def send_telegram_notification(
    bot_token: str,
    chat_id: str,
    message_thread_id: str,
    title: str,
    content: str,
    markdown_text: Optional[str] = None
) -> bool:
    payload = {
        "chat_id": chat_id,
        "text": markdown_text or f"{title}\n\n{content}",
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    if message_thread_id:
        payload["message_thread_id"] = int(message_thread_id)
    try:
        response = requests.post(TELEGRAM_API_URL.format(token=bot_token), json=payload, timeout=15)
        if not response.ok:
            logger.error(f"发送 Telegram Bot 推送失败，状态码 {response.status_code}: {response.text}")
            return False
        logger.info("Telegram Bot 推送发送成功。")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"发送 Telegram Bot 推送失败: {e}")
        return False


def main():
    initialize_site_configs()
    results: List[Dict[str, str]] = []
    failed = False
    telegram_markdown_text = None
    push_key = ''
    tg_bot_token = ''
    tg_chat_id = ''
    tg_message_thread_id = ''

    try:
        push_key, tg_bot_token, tg_chat_id, tg_message_thread_id, cookies_list, account_names, exchange_plan = load_config()

        if not cookies_list:
            logger.error("未找到有效的 Cookie，退出程序。")
            failed = True
            title, content = "# 未找到 cookies!", ""
            telegram_markdown_text = "*GLaDOS 签到执行失败*\n\n- 原因: 未找到有效 cookies"
        else:
            for idx, cookie in enumerate(cookies_list, 1):
                logger.info(f"正在处理第 {idx} 个账户...")
                status, points, days, points_total, exchange, site = checkin_and_process(cookie, exchange_plan)
                results.append({
                    'status': status,
                    'points': points,
                    'days': days,
                    'points_total': points_total,
                    'exchange': exchange,
                    'site': site
                })

            title, content = format_push_content(results, account_names)
            telegram_markdown_text = format_telegram_content(results, account_names)
            failed = has_failures(results)
            logger.info(f"推送标题: {title}")
            logger.info(
                "推送正文已生成（为避免日志脱敏影响可读性，不在 Actions 日志中输出完整正文）。"
            )

    except Exception as e:
        logger.error(f"主程序执行过程中发生未预期的错误: {e}")
        failed = True
        title, content = "# 脚本执行出错", str(e)
        telegram_markdown_text = f"*GLaDOS 签到执行失败*\n\n- 异常: `{str(e)}`"

    sent = False
    if tg_bot_token and tg_chat_id:
        sent = send_telegram_notification(
            tg_bot_token,
            tg_chat_id,
            tg_message_thread_id,
            title,
            content,
            telegram_markdown_text,
        ) or sent
    else:
        logger.info(
            f"未完整设置 '{ENV_TG_BOT_TOKEN}' 与 '{ENV_TG_CHAT_ID}'，跳过 Telegram Bot 推送。"
        )

    if failed:
        logger.info("检测到失败结果，按配置跳过 PushDeer 推送。")
    elif push_key:
        sent = send_pushdeer_notification(push_key, title, content) or sent
    else:
        logger.info(f"未设置 '{ENV_PUSH_KEY}'，跳过 PushDeer 推送。")

    if not sent:
        logger.info("未发送任何推送通知。")


if __name__ == '__main__':
    main()
