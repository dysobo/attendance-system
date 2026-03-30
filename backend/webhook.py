import requests
import json
from typing import Optional

# Webhook 配置（存储在数据库中）
WEBHOOK_CONFIG = {
    "enabled": False,
    "url": "",
    "route_id": "",
    "notify_time_off": True,      # 调休申请通知
    "notify_overtime": True,      # 加班记录通知
    "notify_time_off_approved": False,  # 调休审批通知
    "notify_overtime_approved": False,  # 加班确认通知
}

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
            print(f"✅ Webhook 通知发送成功：{title}")
            return True
        else:
            print(f"❌ Webhook 通知发送失败：{response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Webhook 通知发送异常：{e}")
        return False

def notify_time_off_request(user_name: str, date: str, hours: float, reason: str, webhook_config: dict) -> bool:
    """调休申请通知"""
    if not webhook_config.get("enabled") or not webhook_config.get("notify_time_off"):
        return False
    
    title = "🏖️ 调休申请"
    content = f"{user_name} 申请调休\n日期：{date}\n时长：{hours}小时\n事由：{reason}"
    
    return send_webhook_notification(
        webhook_url=webhook_config.get("url", ""),
        route_id=webhook_config.get("route_id", ""),
        title=title,
        content=content
    )

def notify_overtime_request(user_name: str, date: str, hours: float, reason: str, webhook_config: dict) -> bool:
    """加班记录通知"""
    if not webhook_config.get("enabled") or not webhook_config.get("notify_overtime"):
        return False
    
    title = "⏰ 加班记录"
    content = f"{user_name} 登记加班\n日期：{date}\n时长：{hours}小时\n事由：{reason}"
    
    return send_webhook_notification(
        webhook_url=webhook_config.get("url", ""),
        route_id=webhook_config.get("route_id", ""),
        title=title,
        content=content
    )

def notify_time_off_approved(user_name: str, date: str, hours: float, approved: bool, webhook_config: dict) -> bool:
    """调休审批通知"""
    if not webhook_config.get("enabled") or not webhook_config.get("notify_time_off_approved"):
        return False
    
    status = "✅ 已批准" if approved else "❌ 已拒绝"
    title = "🏖️ 调休审批"
    content = f"{user_name} 的调休申请 {status}\n日期：{date}\n时长：{hours}小时"
    
    return send_webhook_notification(
        webhook_url=webhook_config.get("url", ""),
        route_id=webhook_config.get("route_id", ""),
        title=title,
        content=content
    )

def notify_overtime_approved(user_name: str, date: str, hours: float, approved: bool, webhook_config: dict) -> bool:
    """加班确认通知"""
    if not webhook_config.get("enabled") or not webhook_config.get("notify_overtime_approved"):
        return False
    
    status = "✅ 已确认" if approved else "❌ 已拒绝"
    title = "⏰ 加班确认"
    content = f"{user_name} 的加班记录 {status}\n日期：{date}\n时长：{hours}小时"
    
    return send_webhook_notification(
        webhook_url=webhook_config.get("url", ""),
        route_id=webhook_config.get("route_id", ""),
        title=title,
        content=content
    )
