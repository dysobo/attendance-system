import json
import os
from typing import Optional

import requests

DEFAULT_WEBHOOK_CONFIG = {
    "enabled": False,
    "url": "",
    "route_id": "",
    "notify_time_off": True,      # 调休申请通知
    "notify_overtime": True,      # 加班记录通知
    "notify_time_off_approved": False,  # 调休审批通知
    "notify_overtime_approved": False,  # 加班确认通知
}

WEBHOOK_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "webhook_config.json")

def default_webhook_config() -> dict:
    return DEFAULT_WEBHOOK_CONFIG.copy()

def load_webhook_config() -> dict:
    try:
        if os.path.exists(WEBHOOK_CONFIG_FILE):
            with open(WEBHOOK_CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                config = default_webhook_config()
                config.update(loaded)
                return config
    except Exception as e:
        print(f"加载 webhook 配置失败：{e}")
    return default_webhook_config()

def save_webhook_config(config: dict) -> bool:
    try:
        os.makedirs(os.path.dirname(WEBHOOK_CONFIG_FILE), exist_ok=True)
        merged = default_webhook_config()
        merged.update(config)
        with open(WEBHOOK_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)
        print(f"✅ webhook 配置已保存到：{WEBHOOK_CONFIG_FILE}")
        return True
    except Exception as e:
        print(f"保存 webhook 配置失败：{e}")
        return False

def send_webhook_notification(
    webhook_url: str,
    route_id: str,
    title: str,
    content: str,
    push_img_url: Optional[str] = None,
    push_link_url: Optional[str] = None
) -> bool:
    """发送 webhook 通知"""
    try:
        payload = {
            "route_id": route_id,
            "title": title,
            "content": content
        }
        
        if push_img_url:
            payload["push_img_url"] = push_img_url
        
        if push_link_url:
            payload["push_link_url"] = push_link_url
        
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
            except ValueError:
                result = None

            if result is None or result.get("success", True):
                print(f"✅ Webhook 通知发送成功：{title}")
                return True

            print(f"❌ Webhook 通知发送失败：{result.get('message', '未知错误')}")
            return False

        print(f"❌ Webhook 通知发送失败：{response.status_code} - {response.text}")
        return False
            
    except Exception as e:
        print(f"❌ Webhook 通知发送异常：{e}")
        return False

def send_webhook(config: dict, title: str, content: str, link_url: str = "") -> bool:
    if not config.get("enabled") or not config.get("url") or not config.get("route_id"):
        return False

    return send_webhook_notification(
        webhook_url=config.get("url", ""),
        route_id=config.get("route_id", ""),
        title=title,
        content=content,
        push_link_url=link_url or None
    )

def notify_time_off_request(user_name: str, date: str, hours: float, reason: str, webhook_config: dict) -> bool:
    """调休申请通知"""
    if not webhook_config.get("enabled") or not webhook_config.get("notify_time_off"):
        return False
    
    title = "🏖️ 调休申请"
    content = f"{user_name} 申请调休\n日期：{date}\n时长：{hours}小时\n事由：{reason}"
    
    return send_webhook(webhook_config, title, content)

def notify_overtime_request(user_name: str, date: str, hours: float, reason: str, webhook_config: dict) -> bool:
    """加班记录通知"""
    if not webhook_config.get("enabled") or not webhook_config.get("notify_overtime"):
        return False
    
    title = "⏰ 加班记录"
    content = f"{user_name} 登记加班\n日期：{date}\n时长：{hours}小时\n事由：{reason}"
    
    return send_webhook(webhook_config, title, content)

def notify_time_off_approved(user_name: str, date: str, hours: float, approved: bool, webhook_config: dict, admin_comment: Optional[str] = None) -> bool:
    """调休审批通知"""
    if not webhook_config.get("enabled") or not webhook_config.get("notify_time_off_approved"):
        return False
    
    status = "✅ 已批准" if approved else "❌ 已拒绝"
    title = "🏖️ 调休审批"
    comment_line = f"\n留言：{admin_comment}" if admin_comment else ""
    content = f"{user_name} 的调休申请 {status}\n日期：{date}\n时长：{hours}小时{comment_line}"
    
    return send_webhook(webhook_config, title, content)

def notify_overtime_approved(user_name: str, date: str, hours: float, approved: bool, webhook_config: dict, admin_comment: Optional[str] = None) -> bool:
    """加班确认通知"""
    if not webhook_config.get("enabled") or not webhook_config.get("notify_overtime_approved"):
        return False
    
    status = "✅ 已确认" if approved else "❌ 已拒绝"
    title = "⏰ 加班确认"
    comment_line = f"\n留言：{admin_comment}" if admin_comment else ""
    content = f"{user_name} 的加班记录 {status}\n日期：{date}\n时长：{hours}小时{comment_line}"
    
    return send_webhook(webhook_config, title, content)
