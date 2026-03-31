from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from jose import JWTError, jwt
import database
import os
import hashlib
import requests
import json
import json
import io
import csv
import re
import time
import xml.etree.ElementTree as ET
from hashlib import sha1

# ==================== 配置 ====================

SECRET_KEY = os.getenv("JWT_SECRET", "attendance-system-secret-key-2026")
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 30

def get_password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password, hashed_password):
    return get_password_hash(plain_password) == hashed_password

security = HTTPBearer()

app = FastAPI(title="考勤管理系统", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Pydantic 模型 ====================

class UserLogin(BaseModel):
    name: str
    password: str

class UserCreate(BaseModel):
    name: str
    password: str
    role: str = "member"
    phone: Optional[str] = None

class ShiftCreate(BaseModel):
    user_id: int
    date: date
    shift_type: str
    note: Optional[str] = None

class ShiftUpdate(BaseModel):
    shift_type: Optional[str] = None
    note: Optional[str] = None

class TimeOffRequestCreate(BaseModel):
    date: date
    hours: float = 8.0
    type: str = "U"  # U 调休/B 病假/S 事假/H 婚假/C 产假/L 护理假/J 经期假/Y 孕期假/R 哺乳假/N 年休假/T 探亲假/Z 丧假
    reason: Optional[str] = None

class WebhookConfig(BaseModel):
    enabled: bool = False
    url: str = ""
    route_id: str = ""
    notify_time_off: bool = True
    notify_overtime: bool = True
    notify_time_off_approved: bool = False
    notify_overtime_approved: bool = False

class TimeOffRequestApprove(BaseModel):
    approved: bool

class OvertimeRecordCreate(BaseModel):
    date: date
    hours: float
    reason: Optional[str] = None

class OvertimeRecordApprove(BaseModel):
    approved: bool

# ==================== 工具函数 ====================
# (已在上方定义)

def create_access_token(data: dict):
    to_encode = data.copy()
    # sub 必须是字符串
    if 'sub' in to_encode:
        to_encode['sub'] = str(to_encode['sub'])
    to_encode.update({"exp": datetime.now().timestamp() + TOKEN_EXPIRE_DAYS * 86400})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(database.get_db)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        # sub 是字符串，转成整数
        user_id = int(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(database.User).filter(database.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# ==================== 初始化 ====================

@app.on_event("startup")
def startup():
    database.init_db()
    # 创建默认管理员
    db = database.SessionLocal()
    try:
        admin = db.query(database.User).filter(database.User.name == "admin").first()
        if not admin:
            admin = database.User(name="admin", password=get_password_hash("admin123"), role="admin")
            db.add(admin)
            db.commit()
            print("✅ 默认管理员已创建：admin / admin123")
    finally:
        db.close()

# ==================== API 路由 ====================

@app.get("/")
def root():
    return {"message": "考勤管理系统 API", "version": "1.0.0"}

# --- 用户认证 ---

@app.post("/api/login")
def login(user_data: UserLogin, db: Session = Depends(database.get_db)):
    user = db.query(database.User).filter(database.User.name == user_data.name).first()
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    token = create_access_token({"sub": user.id, "role": user.role})
    return {
        "token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "role": user.role
        }
    }

@app.post("/api/users")
def create_user(user_data: UserCreate, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    existing = db.query(database.User).filter(database.User.name == user_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    user = database.User(
        name=user_data.name,
        password=get_password_hash(user_data.password),
        role=user_data.role,
        phone=user_data.phone if hasattr(user_data, 'phone') else None
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "name": user.name, "role": user.role, "phone": user.phone}

@app.get("/api/users")
def list_users(current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    users = db.query(database.User).all()
    return [{"id": u.id, "name": u.name, "role": u.role, "phone": u.phone} for u in users]

@app.post("/api/users/{user_id}/reset-password")
def reset_password(user_id: int, password_data: dict, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    user = db.query(database.User).filter(database.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.password = get_password_hash(password_data.get("password", "123456"))
    db.commit()
    return {"message": "密码已重置"}

@app.post("/api/auth/change-password")
def change_password(password_data: dict, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    old_password = password_data.get("oldPassword")
    new_password = password_data.get("newPassword")
    
    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="请填写所有密码字段")
    
    if not verify_password(old_password, current_user.password):
        raise HTTPException(status_code=400, detail="当前密码错误")
    
    current_user.password = get_password_hash(new_password)
    db.commit()
    return {"message": "密码修改成功"}

@app.delete("/api/users/{user_id}")
def delete_user(user_id: int, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    
    user = db.query(database.User).filter(database.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    db.delete(user)
    db.commit()
    return {"message": "用户已删除"}

@app.put("/api/users/{user_id}/role")
def update_user_role(user_id: int, role_data: dict, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    user = db.query(database.User).filter(database.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    new_role = role_data.get("role")
    if new_role not in ["admin", "member"]:
        raise HTTPException(status_code=400, detail="无效的角色")
    
    user.role = new_role
    db.commit()
    db.refresh(user)
    return {"message": "角色已更新", "role": user.role}

@app.put("/api/users/{user_id}")
def update_user(user_id: int, user_data: dict, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    user = db.query(database.User).filter(database.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新用户信息
    if "name" in user_data:
        user.name = user_data["name"]
    if "role" in user_data:
        user.role = user_data["role"]
    if "phone" in user_data:
        user.phone = user_data["phone"]
    if "wechat_user_id" in user_data:
        user.wechat_user_id = user_data["wechat_user_id"]
    if "enable_push" in user_data:
        user.enable_push = user_data["enable_push"]
    # 密码只在创建时设置，编辑时不更新
    
    db.commit()
    db.refresh(user)
    return {"message": "用户信息已更新", "user": {"id": user.id, "name": user.name, "role": user.role, "phone": user.phone, "wechat_user_id": user.wechat_user_id, "enable_push": user.enable_push}}

# ==================== 企业微信绑定 ====================

@app.get("/api/wechat/bind")
def get_wechat_bind(current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """获取当前用户的企业微信绑定信息"""
    return {
        "wechat_user_id": current_user.wechat_user_id,
        "enable_push": current_user.enable_push
    }

@app.post("/api/wechat/bind")
def bind_wechat(data: dict, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """绑定企业微信用户 ID"""
    current_user.wechat_user_id = data.get("wechat_user_id", "")
    current_user.enable_push = data.get("enable_push", True)
    db.commit()
    return {"message": "绑定成功", "wechat_user_id": current_user.wechat_user_id}

# ==================== 企业微信配置 ====================

@app.get("/api/wechat/config")
def get_wechat_config(current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """获取企业微信配置（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    config = db.query(database.WechatConfig).first()
    if not config:
        return {
            "api_url": "https://qyapi.weixin.qq.com",
            "corp_id": "",
            "secret": "",
            "agent_id": 0,
            "token": "",
            "encoding_aes_key": "",
            "enabled": False
        }
    
    return {
        "api_url": config.api_url,
        "corp_id": config.corp_id,
        "secret": config.secret,
        "agent_id": config.agent_id,
        "token": config.token,
        "encoding_aes_key": config.encoding_aes_key,
        "enabled": config.enabled
    }

@app.post("/api/wechat/config")
def save_wechat_config(config_data: dict, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """保存企业微信配置（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    config = db.query(database.WechatConfig).first()
    if not config:
        config = database.WechatConfig()
        db.add(config)
    
    config.api_url = config_data.get("api_url", "https://qyapi.weixin.qq.com")
    config.corp_id = config_data.get("corp_id", "")
    config.secret = config_data.get("secret", "")
    config.agent_id = config_data.get("agent_id", 0)
    config.token = config_data.get("token", "")
    config.encoding_aes_key = config_data.get("encoding_aes_key", "")
    config.enabled = config_data.get("enabled", False)
    config.updated_at = datetime.now()
    
    db.commit()
    return {"message": "配置已保存"}

@app.post("/api/wechat/test-push")
def test_wechat_push(data: dict, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """测试企业微信推送（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # 发送给管理员自己
    title = data.get("title", "测试推送")
    content = data.get("content", "这是一条测试消息")
    link_url = data.get("link", "http://x.dysobo.cn:8888/kq/")
    
    success = send_wechat_message(current_user.id, title, content, link_url, db)
    
    if success:
        return {"message": "测试推送已发送"}
    else:
        raise HTTPException(status_code=500, detail="推送失败，请检查配置")

# ==================== 企业微信回调接口 ====================

def verify_wechat_signature(token: str, signature: str, timestamp: str, nonce: str) -> bool:
    """验证企业微信签名"""
    try:
        sorted_list = sorted([token, timestamp, nonce])
        hash_str = ''.join(sorted_list).encode('utf-8')
        hash_str = sha1(hash_str).hexdigest()
        return hash_str == signature
    except Exception as e:
        print(f"❌ 签名验证失败：{e}")
        return False

def decrypt_wechat_message(encoding_aes_key: str, encrypt: str) -> str:
    """解密企业微信消息"""
    # TODO: 实现 AES 解密
    # 这里简化处理，实际需要使用 Crypto.Cipher.AES
    return encrypt

@app.get("/api/wechat/callback")
def wechat_callback_get(
    msg_signature: str = "",
    timestamp: str = "",
    nonce: str = "",
    echostr: str = "",
    db: Session = Depends(database.get_db)
):
    """企业微信 URL 验证（GET 请求）"""
    config = db.query(database.WechatConfig).filter(database.WechatConfig.enabled == True).first()
    
    if not config or not config.token:
        return echostr
    
    # 验证签名
    if verify_wechat_signature(config.token, msg_signature, timestamp, nonce):
        return echostr
    else:
        raise HTTPException(status_code=403, detail="签名验证失败")

@app.post("/api/wechat/callback")
async def wechat_callback_post(
    request: Request,
    msg_signature: str = "",
    timestamp: str = "",
    nonce: str = "",
    db: Session = Depends(database.get_db)
):
    """接收企业微信消息（POST 请求）"""
    config = db.query(database.WechatConfig).filter(database.WechatConfig.enabled == True).first()
    
    # 验证签名
    if config and config.token:
        if not verify_wechat_signature(config.token, msg_signature, timestamp, nonce):
            raise HTTPException(status_code=403, detail="签名验证失败")
    
    # 读取请求体
    body = await request.body()
    body_str = body.decode('utf-8')
    
    # 解析 XML
    try:
        xml_root = ET.fromstring(body_str)
        
        # 获取消息类型
        msg_type = xml_root.find('MsgType').text if xml_root.find('MsgType') is not None else ''
        
        # 只处理文本消息
        if msg_type != 'text':
            return "success"
        
        # 获取发送者
        from_user = xml_root.find('FromUserName').text if xml_root.find('FromUserName') is not None else ''
        
        # 获取消息内容
        content = xml_root.find('Content').text if xml_root.find('Content') is not None else ''
        
        # 处理指令
        response = process_wechat_command(from_user, content, db)
        
        # 返回响应（简化处理，实际需要加密）
        # TODO: 实现响应加密
        print(f"✅ 处理指令：{from_user} - {content} → {response}")
        
        return "success"
        
    except Exception as e:
        print(f"❌ 解析消息失败：{e}")
        return "success"  # 返回 success 避免企业微信重试

def process_wechat_command(user_wechat_id: str, command: str, db: Session):
    """处理企业微信指令"""
    # 根据企业微信 ID 查找用户
    user = db.query(database.User).filter(database.User.wechat_user_id == user_wechat_id).first()
    if not user:
        return "❌ 未找到绑定用户，请先在考勤系统中绑定企业微信 ID"
    
    command = command.strip().lower()
    
    # 指令：记加班 Xh
    match = re.match(r'记加班\s*(\d+(?:\.\d+)?)\s*h?', command)
    if match:
        hours = float(match.group(1))
        return create_overtime_command(user, hours, db)
    
    # 指令：查加班
    if command in ['查加班', '加班', 'query overtime']:
        return query_overtime_command(user, db)
    
    # 指令：查调休
    if command in ['查调休', '调休', 'query leave']:
        return query_leave_command(user, db)
    
    # 指令：帮助
    if command in ['帮助', 'help', '指令']:
        return get_help_command()
    
    return "❌ 未知指令，发送【帮助】查看可用指令"

def create_overtime_command(user: database.User, hours: float, db: Session) -> str:
    """记加班指令"""
    from datetime import date
    
    # 创建加班记录
    record = database.OvertimeRecord(
        user_id=user.id,
        date=date.today(),
        hours=hours,
        reason="企业微信指令",
        status="pending"
    )
    db.add(record)
    db.commit()
    
    # 发送通知给管理员
    admins = db.query(database.User).filter(database.User.role == "admin").all()
    for admin in admins:
        send_wechat_message(
            admin.id,
            f"加班申请 - {user.name}",
            f"{user.name} 申请加班\n日期：{date.today()}\n时长：{hours}小时\n\n请点击审批",
            "http://x.dysobo.cn:8888/kq/?page=overtime",
            db
        )
    
    return f"✅ 已提交加班申请：今日加班 {hours} 小时\n请等待管理员确认"

def query_overtime_command(user: database.User, db: Session) -> str:
    """查询加班指令"""
    from datetime import date, timedelta
    
    # 本月起止日期
    today = date.today()
    month_start = date(today.year, today.month, 1)
    month_end = date(today.year, today.month + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)
    
    # 查询本月加班
    records = db.query(database.OvertimeRecord).filter(
        database.OvertimeRecord.user_id == user.id,
        database.OvertimeRecord.date >= month_start,
        database.OvertimeRecord.date < month_end,
        database.OvertimeRecord.status == "approved"
    ).all()
    
    total_hours = sum(r.hours for r in records)
    
    return f"📊 本月加班统计\n累计：{total_hours} 小时\n笔数：{len(records)} 笔"

def query_leave_command(user: database.User, db: Session) -> str:
    """查询调休指令"""
    from datetime import date
    
    # 本月起止日期
    today = date.today()
    month_start = date(today.year, today.month, 1)
    month_end = date(today.year, today.month + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)
    
    # 查询本月调休
    records = db.query(database.TimeOffRequest).filter(
        database.TimeOffRequest.user_id == user.id,
        database.TimeOffRequest.date >= month_start,
        database.TimeOffRequest.date < month_end,
        database.TimeOffRequest.status == "approved"
    ).all()
    
    total_hours = sum(r.hours for r in records)
    
    return f"📊 本月调休统计\n累计：{total_hours} 小时\n笔数：{len(records)} 笔"

def get_help_command() -> str:
    """帮助指令"""
    return """📖 可用指令：

🕐 加班相关：
  记加班 Xh - 记录当日加班 X 小时
  查加班 - 查询本月加班统计

🏖️ 调休相关：
  查调休 - 查询本月调休统计

❓ 其他：
  帮助 - 显示此帮助信息

示例：
  记加班 3h
  查加班"""

# ==================== 企业微信推送函数 ====================

def get_wechat_access_token(db: Session) -> str:
    """获取企业微信 access_token"""
    config = db.query(database.WechatConfig).filter(database.WechatConfig.enabled == True).first()
    if not config or not config.corp_id or not config.secret:
        return ""
    
    try:
        url = f"{config.api_url}/cgi-bin/gettoken"
        params = {
            "corpid": config.corp_id,
            "corpsecret": config.secret
        }
        response = requests.get(url, params=params, timeout=10)
        result = response.json()
        
        if result.get("errcode") == 0:
            return result.get("access_token", "")
        else:
            print(f"❌ 获取 access_token 失败：{result}")
            return ""
    except Exception as e:
        print(f"❌ 获取 access_token 异常：{e}")
        return ""

def send_wechat_message(user_id: int, title: str, content: str, link_url: str = "", db: Session = None):
    """发送企业微信消息"""
    if not db:
        return False
    
    # 检查企业微信配置
    config = db.query(database.WechatConfig).filter(database.WechatConfig.enabled == True).first()
    if not config:
        return False
    
    # 获取用户的企业微信 ID
    user = db.query(database.User).filter(database.User.id == user_id).first()
    if not user or not user.enable_push or not user.wechat_user_id:
        return False
    
    # 获取 access_token
    access_token = get_wechat_access_token(db)
    if not access_token:
        return False
    
    # 发送文本卡片消息
    try:
        url = f"{config.api_url}/cgi-bin/message/send?access_token={access_token}"
        payload = {
            "touser": user.wechat_user_id,
            "msgtype": "textcard",
            "agentid": config.agent_id,
            "textcard": {
                "title": title,
                "description": content,
                "url": link_url if link_url else "http://x.dysobo.cn:8888/kq/",
                "btntxt": "查看详情"
            }
        }
        
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
        result = response.json()
        
        if result.get("errcode") == 0:
            print(f"✅ 企业微信消息发送成功：{user.name} - {title}")
            return True
        else:
            print(f"❌ 企业微信消息发送失败：{result}")
            return False
    except Exception as e:
        print(f"❌ 企业微信消息发送异常：{e}")
        return False

# --- 排班管理 ---

@app.get("/api/shifts/team")
def get_team_shifts(db: Session = Depends(database.get_db)):
    """获取班组排班 - 今日往后 30 天（含今日）"""
    from datetime import timedelta
    today = date.today()
    end_date = today + timedelta(days=29)  # 含今日共 30 天
    
    shifts = db.query(database.Shift).filter(
        database.Shift.date >= today,
        database.Shift.date <= end_date
    ).order_by(database.Shift.date, database.Shift.user_id).all()
    
    result = []
    for s in shifts:
        user = db.query(database.User).filter(database.User.id == s.user_id).first()
        result.append({
            "id": s.id,
            "user_id": s.user_id,
            "user_name": user.name if user else "未知",
            "phone": user.phone if user and user.phone else "-",  # 联系方式
            "date": str(s.date),
            "shift_type": s.shift_type,
            "note": s.note if s.note else "-"  # 备注
        })
    return result

@app.get("/api/shifts")
def list_shifts(start_date: Optional[date] = None, end_date: Optional[date] = None, user_id: Optional[int] = None, db: Session = Depends(database.get_db)):
    query = db.query(database.Shift)
    if start_date:
        query = query.filter(database.Shift.date >= start_date)
    if end_date:
        query = query.filter(database.Shift.date <= end_date)
    if user_id:
        query = query.filter(database.Shift.user_id == user_id)
    
    shifts = query.order_by(database.Shift.date).all()
    result = []
    for s in shifts:
        user = db.query(database.User).filter(database.User.id == s.user_id).first()
        result.append({
            "id": s.id,
            "user_id": s.user_id,
            "user_name": user.name if user else "未知",
            "phone": user.phone if user and user.phone else "-",
            "date": str(s.date),
            "shift_type": s.shift_type,
            "note": s.note
        })
    return result

@app.post("/api/shifts")
def create_shift(shift_data: ShiftCreate, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # 确保 user_id 是整数
    user_id = int(shift_data.user_id) if isinstance(shift_data.user_id, str) else shift_data.user_id
    
    # 检查是否已存在该用户该日期的排班
    existing = db.query(database.Shift).filter(
        database.Shift.user_id == user_id,
        database.Shift.date == shift_data.date
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该日期已存在排班")
    
    shift = database.Shift(user_id=user_id, date=shift_data.date, shift_type=shift_data.shift_type, note=shift_data.note)
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return {"id": shift.id, "message": "排班创建成功"}

@app.put("/api/shifts/{shift_id}")
def update_shift(shift_id: int, shift_data: ShiftUpdate, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    shift = db.query(database.Shift).filter(database.Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="排班不存在")
    
    if shift_data.shift_type is not None:
        shift.shift_type = shift_data.shift_type
    if shift_data.note is not None:
        shift.note = shift_data.note
    
    db.commit()
    db.refresh(shift)
    return {"id": shift.id, "message": "排班更新成功"}

@app.delete("/api/shifts/{shift_id}")
def delete_shift(shift_id: int, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    shift = db.query(database.Shift).filter(database.Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="排班不存在")
    
    db.delete(shift)
    db.commit()
    return {"message": "排班删除成功"}

# --- 调休申请 ---

@app.get("/api/time-off")
def list_time_off(user_id: Optional[int] = None, status: Optional[str] = None, db: Session = Depends(database.get_db)):
    query = db.query(database.TimeOffRequest)
    if user_id:
        query = query.filter(database.TimeOffRequest.user_id == user_id)
    if status:
        query = query.filter(database.TimeOffRequest.status == status)
    
    requests = query.order_by(database.TimeOffRequest.created_at.desc()).all()
    result = []
    for r in requests:
        user = db.query(database.User).filter(database.User.id == r.user_id).first()
        result.append({
            "id": r.id,
            "user_id": r.user_id,
            "user_name": user.name if user else "未知",
            "date": str(r.date),
            "hours": r.hours,
            "type": r.type,
            "reason": r.reason,
            "status": r.status,
            "created_at": str(r.created_at)
        })
    return result

@app.post("/api/time-off")
def create_time_off(request_data: TimeOffRequestCreate, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    request = database.TimeOffRequest(
        user_id=current_user.id,
        date=request_data.date,
        hours=request_data.hours,
        type=request_data.type,
        reason=request_data.reason
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    
    # 发送 webhook 通知
    webhook_config = load_webhook_config()
    if webhook_config.get("enabled") and webhook_config.get("notify_time_off"):
        link_url = f"http://x.dysobo.cn:8888/kq/?page=timeoff&id={request.id}"
        type_names = {"U":"调休","B":"病假","S":"事假","H":"婚假","C":"产假","L":"护理假","J":"经期假","Y":"孕期假","R":"哺乳假","N":"年休假","T":"探亲假","Z":"丧假"}
        type_name = type_names.get(request_data.type, "调休")
        content = f"申请人：{current_user.name}\n类型：{type_name}\n日期：{request_data.date}\n时长：{request_data.hours}小时\n事由：{request_data.reason}\n\n👉 点击审批：{link_url}"
        send_webhook(
            webhook_config,
            f"🏖️ {type_name}申请 - 待审批",
            content,
            link_url
        )
    
    return {"id": request.id, "message": "调休申请已提交"}

@app.post("/api/time-off/{request_id}/approve")
def approve_time_off(request_id: int, approve_data: TimeOffRequestApprove, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    request = db.query(database.TimeOffRequest).filter(database.TimeOffRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="申请不存在")
    
    request.status = "approved" if approve_data.approved else "rejected"
    request.approved_by = current_user.id
    request.updated_at = datetime.now()
    db.commit()
    
    # 发送企业微信推送通知给申请人
    type_names = {"U":"调休","B":"病假","S":"事假","H":"婚假","C":"产假","L":"护理假","J":"经期假","Y":"孕期假","R":"哺乳假","N":"年休假","T":"探亲假","Z":"丧假"}
    type_name = type_names.get(request.type, "调休")
    status_text = "已批准" if approve_data.approved else "已拒绝"
    title = f"{type_name}申请{status_text}"
    content = f"您的{type_name}申请{status_text}\n日期：{request.date}\n时长：{request.hours}小时"
    link_url = f"http://x.dysobo.cn:8888/kq/?page=timeoff"
    send_wechat_message(request.user_id, title, content, link_url, db)
    
    return {"message": "申请已" + ("批准" if approve_data.approved else "拒绝")}

@app.put("/api/time-off/{request_id}")
def update_time_off(request_id: int, update_data: TimeOffRequestCreate, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    request = db.query(database.TimeOffRequest).filter(database.TimeOffRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="申请不存在")
    
    request.date = update_data.date
    request.hours = update_data.hours
    request.type = update_data.type
    request.reason = update_data.reason
    request.updated_at = datetime.now()
    db.commit()
    db.refresh(request)
    return {"message": "申请已更新", "id": request.id}

@app.delete("/api/time-off/{request_id}")
def delete_time_off(request_id: int, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    request = db.query(database.TimeOffRequest).filter(database.TimeOffRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="申请不存在")
    
    # 权限检查：管理员可删除任何记录，本人只能删除 pending/rejected
    if current_user.role != "admin":
        if request.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限删除")
        # 本人只能删除 pending 或 rejected 状态
        if request.status not in ["pending", "rejected"]:
            raise HTTPException(status_code=400, detail="已批准，不可删除")
    
    db.delete(request)
    db.commit()
    return {"message": "申请已删除"}

# --- 加班记录 ---

@app.get("/api/overtime")
def list_overtime(user_id: Optional[int] = None, status: Optional[str] = None, db: Session = Depends(database.get_db)):
    query = db.query(database.OvertimeRecord)
    if user_id:
        query = query.filter(database.OvertimeRecord.user_id == user_id)
    if status:
        query = query.filter(database.OvertimeRecord.status == status)
    
    records = query.order_by(database.OvertimeRecord.date.desc()).all()
    result = []
    for r in records:
        user = db.query(database.User).filter(database.User.id == r.user_id).first()
        result.append({
            "id": r.id,
            "user_id": r.user_id,
            "user_name": user.name if user else "未知",
            "date": str(r.date),
            "hours": r.hours,
            "reason": r.reason,
            "status": r.status,
            "created_at": str(r.created_at)
        })
    return result

# Webhook 配置文件路径（使用相对路径，与 main.py 同目录）
import os
WEBHOOK_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "webhook_config.json")

def load_webhook_config():
    """加载 webhook 配置"""
    try:
        if os.path.exists(WEBHOOK_CONFIG_FILE):
            with open(WEBHOOK_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"加载 webhook 配置失败：{e}")
    return {"enabled": False, "url": "", "route_id": "", "notify_time_off": True, "notify_overtime": True, "notify_time_off_approved": False, "notify_overtime_approved": False}

def save_webhook_config(config: dict):
    """保存 webhook 配置"""
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(WEBHOOK_CONFIG_FILE), exist_ok=True)
        with open(WEBHOOK_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✅ webhook 配置已保存到：{WEBHOOK_CONFIG_FILE}")
        return True
    except Exception as e:
        print(f"保存 webhook 配置失败：{e}")
        return False

def send_webhook(config: dict, title: str, content: str, link_url: str = ""):
    """发送 webhook 通知
    Args:
        config: webhook 配置
        title: 标题
        content: 内容
        link_url: 跳转链接
    """
    if not config.get("enabled") or not config.get("url") or not config.get("route_id"):
        return False
    try:
        payload = {
            "route_id": config.get("route_id", ""),
            "title": title,
            "content": content
        }
        if link_url:
            payload["push_link_url"] = link_url
        
        response = requests.post(config.get("url", ""), json=payload, headers={"Content-Type": "application/json"}, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✅ Webhook 通知发送成功：{title}")
                return True
            else:
                print(f"❌ Webhook 通知发送失败：{result.get('message')}")
                return False
        else:
            print(f"❌ Webhook 通知发送失败：{response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Webhook 通知发送异常：{e}")
        return False

@app.get("/api/webhook/config")
def get_webhook_config(current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """获取 webhook 配置（仅管理员）"""
    if current_user.role != "admin":
        return {"enabled": False, "url": "", "route_id": "", "notify_time_off": True, "notify_overtime": True, "notify_time_off_approved": False, "notify_overtime_approved": False}
    return load_webhook_config()

@app.post("/api/webhook/config")
def update_webhook_config(webhook_config: WebhookConfig, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """更新 webhook 配置（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    config = webhook_config.dict()
    save_webhook_config(config)
    return {"message": "配置已保存", "config": config}

@app.post("/api/webhook/test")
def test_webhook(webhook_test: dict, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """测试 webhook 推送（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    config = load_webhook_config()
    title = webhook_test.get("title", "测试推送")
    content = webhook_test.get("content", "这是一条测试消息")
    success = send_webhook(config, title, content)
    if success:
        return {"message": "测试推送已发送"}
    else:
        raise HTTPException(status_code=500, detail="推送失败，请检查配置")

@app.post("/api/overtime")
def create_overtime(record_data: OvertimeRecordCreate, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    record = database.OvertimeRecord(
        user_id=current_user.id,
        date=record_data.date,
        hours=record_data.hours,
        reason=record_data.reason
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    # 发送 webhook 通知
    webhook_config = load_webhook_config()
    if webhook_config.get("enabled") and webhook_config.get("notify_overtime"):
        link_url = f"http://x.dysobo.cn:8888/kq/?page=overtime&id={record.id}"
        content = f"申请人：{current_user.name}\n日期：{record_data.date}\n时长：{record_data.hours}小时\n事由：{record_data.reason}\n\n👉 点击确认：{link_url}"
        send_webhook(
            webhook_config,
            "⏰ 加班记录 - 待确认",
            content,
            link_url
        )
    
    return {"id": record.id, "message": "加班记录已提交"}

@app.post("/api/overtime/{record_id}/approve")
def approve_overtime(record_id: int, approve_data: OvertimeRecordApprove, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    record = db.query(database.OvertimeRecord).filter(database.OvertimeRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    record.status = "approved" if approve_data.approved else "rejected"
    record.approved_by = current_user.id
    db.commit()
    
    # 发送企业微信推送通知给申请人
    status_text = "已确认" if approve_data.approved else "已拒绝"
    title = f"加班记录{status_text}"
    content = f"您的加班记录{status_text}\n日期：{record.date}\n时长：{record.hours}小时"
    link_url = f"http://x.dysobo.cn:8888/kq/?page=overtime"
    send_wechat_message(record.user_id, title, content, link_url, db)
    
    return {"message": "加班记录已" + ("批准" if approve_data.approved else "拒绝")}

@app.put("/api/overtime/{record_id}")
def update_overtime(record_id: int, update_data: OvertimeRecordCreate, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    record = db.query(database.OvertimeRecord).filter(database.OvertimeRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    record.date = update_data.date
    record.hours = update_data.hours
    record.reason = update_data.reason
    db.commit()
    db.refresh(record)
    return {"message": "记录已更新", "id": record.id}

@app.delete("/api/overtime/{record_id}")
def delete_overtime(record_id: int, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    record = db.query(database.OvertimeRecord).filter(database.OvertimeRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    # 权限检查：管理员可删除任何记录，本人只能删除 pending/rejected
    if current_user.role != "admin":
        if record.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限删除")
        # 本人只能删除 pending 或 rejected 状态
        if record.status not in ["pending", "rejected"]:
            raise HTTPException(status_code=400, detail="已确认，不可删除")
    
    db.delete(record)
    db.commit()
    return {"message": "记录已删除"}

# --- 统计汇总 ---

@app.get("/api/stats/summary")
def get_summary(current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """获取统计汇总
    - 管理员：统计所有组员的总和（本年度）
    - 组员：仅统计自己的
    """
    from datetime import datetime
    current_year = datetime.now().year
    year_start = date(current_year, 1, 1)
    
    # 如果是管理员，统计所有组员；如果是组员，只统计自己
    if current_user.role == "admin":
        users = db.query(database.User).filter(database.User.role == "member").all()
    else:
        users = [current_user]
    
    # 初始化总和
    total_approved_time_off = 0
    total_pending_time_off = 0
    total_overtime_hours = 0.0
    total_pending_overtime = 0
    
    for user in users:
        # 调休统计 - 本年度（按小时计算）
        approved_time_off_records = db.query(database.TimeOffRequest).filter(
            database.TimeOffRequest.user_id == user.id,
            database.TimeOffRequest.status == "approved",
            database.TimeOffRequest.date >= year_start
        ).all()
        approved_time_off = sum(r.hours for r in approved_time_off_records)
        
        pending_time_off_records = db.query(database.TimeOffRequest).filter(
            database.TimeOffRequest.user_id == user.id,
            database.TimeOffRequest.status == "pending",
            database.TimeOffRequest.date >= year_start
        ).all()
        pending_time_off = sum(r.hours for r in pending_time_off_records)
        
        # 加班统计 - 本年度
        approved_overtime = db.query(database.OvertimeRecord).filter(
            database.OvertimeRecord.user_id == user.id,
            database.OvertimeRecord.status == "approved",
            database.OvertimeRecord.date >= year_start
        ).all()
        total_overtime_hours += sum(r.hours for r in approved_overtime)
        
        # 待确认加班 - 所有（不限年度）
        pending_overtime = db.query(database.OvertimeRecord).filter(
            database.OvertimeRecord.user_id == user.id,
            database.OvertimeRecord.status == "pending"
        ).count()
        
        # 累加
        total_approved_time_off += approved_time_off
        total_pending_time_off += pending_time_off
        total_pending_overtime += pending_overtime
    
    # 返回总和
    return {
        "is_admin": current_user.role == "admin",
        "total_users": len(users),
        "time_off_approved": total_approved_time_off,
        "time_off_pending": total_pending_time_off,
        "overtime_hours": total_overtime_hours,
        "overtime_pending": total_pending_overtime
    }

@app.get("/api/stats/my-summary")
def get_my_summary(current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """获取当前用户的统计"""
    approved_time_off = db.query(database.TimeOffRequest).filter(
        database.TimeOffRequest.user_id == current_user.id,
        database.TimeOffRequest.status == "approved"
    ).count()
    pending_time_off = db.query(database.TimeOffRequest).filter(
        database.TimeOffRequest.user_id == current_user.id,
        database.TimeOffRequest.status == "pending"
    ).count()
    
    approved_overtime = db.query(database.OvertimeRecord).filter(
        database.OvertimeRecord.user_id == current_user.id,
        database.OvertimeRecord.status == "approved"
    ).all()
    total_overtime_hours = sum(r.hours for r in approved_overtime)
    pending_overtime = db.query(database.OvertimeRecord).filter(
        database.OvertimeRecord.user_id == current_user.id,
        database.OvertimeRecord.status == "pending"
    ).count()
    
    return {
        "user_name": current_user.name,
        "time_off_approved": approved_time_off,
        "time_off_pending": pending_time_off,
        "overtime_hours": total_overtime_hours,
        "overtime_pending": pending_overtime
    }

# ==================== 数据导出与备份 ====================

@app.get("/api/export/monthly")
def export_monthly_stats(month: Optional[int] = None, year: Optional[int] = None, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """导出当月统计数据（CSV 格式）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    from datetime import timedelta
    import calendar
    # 默认当前月份
    if not month or not year:
        today = date.today()
        month = today.month
        year = today.year
    
    # 计算月份起止日期
    month_start = date(year, month, 1)
    _, days_in_month = calendar.monthrange(year, month)
    
    # 获取所有用户
    users = db.query(database.User).filter(database.User.role == "member").all()
    
    # 准备 CSV 数据
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入表头 - 第一行：标题
    header = ['姓名'] + [f'{d}日' for d in range(1, days_in_month + 1)]
    writer.writerow(header)
    
    # 写入每个用户的数据
    for user in users:
        row = [user.name]
        
        # 查询该用户当月的所有调休和加班记录
        time_off_records = db.query(database.TimeOffRequest).filter(
            database.TimeOffRequest.user_id == user.id,
            database.TimeOffRequest.date >= month_start,
            database.TimeOffRequest.date < date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)
        ).all()
        
        overtime_records = db.query(database.OvertimeRecord).filter(
            database.OvertimeRecord.user_id == user.id,
            database.OvertimeRecord.date >= month_start,
            database.OvertimeRecord.date < date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)
        ).all()
        
        # 按日期组织数据
        daily_data = {}
        
        # 处理假期记录（12 种类型）
        for t in time_off_records:
            day = t.date.day
            if day not in daily_data:
                daily_data[day] = []
            type_symbol = t.type if t.type else 'U'  # 默认为 U
            daily_data[day].append(f"{type_symbol}{t.hours}")  # U/B/S/H/C/L/J/Y/R/N/T/Z = 各种假期
        
        # 处理加班记录
        for o in overtime_records:
            day = o.date.day
            if day not in daily_data:
                daily_data[day] = []
            daily_data[day].append(f"▲{o.hours}")  # ▲ = 加班
        
        # 填充每天的记录
        for day in range(1, days_in_month + 1):
            if day in daily_data:
                row.append(' '.join(daily_data[day]))
            else:
                row.append('')
        
        writer.writerow(row)
    
    csv_content = output.getvalue()
    
    return {
        "filename": f"考勤统计_{year}年{month}月.csv",
        "data": csv_content
    }

@app.get("/api/backup/export")
def export_backup(current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """导出所有数据备份（JSON 格式）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # 导出所有表数据
    users = db.query(database.User).all()
    shifts = db.query(database.Shift).all()
    time_off = db.query(database.TimeOffRequest).all()
    overtime = db.query(database.OvertimeRecord).all()
    
    backup_data = {
        "export_time": datetime.now().isoformat(),
        "version": "1.0",
        "users": [
            {
                "id": u.id, "name": u.name, "role": u.role, 
                "phone": u.phone, "created_at": str(u.created_at)
            } for u in users
        ],
        "shifts": [
            {
                "id": s.id, "user_id": s.user_id, "date": str(s.date),
                "shift_type": s.shift_type, "note": s.note, "created_at": str(s.created_at)
            } for s in shifts
        ],
        "time_off_requests": [
            {
                "id": t.id, "user_id": t.user_id, "date": str(t.date),
                "hours": t.hours, "reason": t.reason, "status": t.status,
                "approved_by": t.approved_by, "created_at": str(t.created_at)
            } for t in time_off
        ],
        "overtime_records": [
            {
                "id": o.id, "user_id": o.user_id, "date": str(o.date),
                "hours": o.hours, "reason": o.reason, "status": o.status,
                "approved_by": o.approved_by, "created_at": str(o.created_at)
            } for o in overtime
        ]
    }
    
    return {"filename": f"考勤备份_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "data": backup_data}

@app.post("/api/backup/import")
def import_backup(backup_data: dict, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """从备份文件恢复数据"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    try:
        # 验证备份数据格式
        if "users" not in backup_data:
            raise HTTPException(status_code=400, detail="无效的备份文件格式")
        
        # 清空现有数据（谨慎操作）
        db.query(database.OvertimeRecord).delete()
        db.query(database.TimeOffRequest).delete()
        db.query(database.Shift).delete()
        db.query(database.User).delete()
        db.commit()
        
        # 恢复用户数据（排除 admin 用户）
        admin_user = db.query(database.User).filter(database.User.role == "admin").first()
        
        for u in backup_data.get("users", []):
            if u["role"] == "admin" and admin_user:
                continue  # 跳过 admin 用户
            user = database.User(
                id=u["id"], name=u["name"], role=u["role"],
                phone=u.get("phone"), password=admin_user.password if admin_user else get_password_hash("123456")
            )
            db.add(user)
        
        # 恢复排班数据
        for s in backup_data.get("shifts", []):
            shift = database.Shift(
                id=s["id"], user_id=s["user_id"], date=s["date"],
                shift_type=s["shift_type"], note=s.get("note")
            )
            db.add(shift)
        
        # 恢复调休数据
        for t in backup_data.get("time_off_requests", []):
            time_off = database.TimeOffRequest(
                id=t["id"], user_id=t["user_id"], date=t["date"],
                hours=t["hours"], reason=t.get("reason"), status=t["status"],
                approved_by=t.get("approved_by")
            )
            db.add(time_off)
        
        # 恢复加班数据
        for o in backup_data.get("overtime_records", []):
            overtime = database.OvertimeRecord(
                id=o["id"], user_id=o["user_id"], date=o["date"],
                hours=o["hours"], reason=o.get("reason"), status=o["status"],
                approved_by=o.get("approved_by")
            )
            db.add(overtime)
        
        db.commit()
        
        return {"message": "数据恢复成功", "count": {
            "users": len(backup_data.get("users", [])),
            "shifts": len(backup_data.get("shifts", [])),
            "time_off": len(backup_data.get("time_off_requests", [])),
            "overtime": len(backup_data.get("overtime_records", []))
        }}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"恢复失败：{str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
