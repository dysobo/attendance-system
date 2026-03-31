from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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
        role=user_data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "name": user.name, "role": user.role}

@app.get("/api/users")
def list_users(current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    users = db.query(database.User).all()
    return [{"id": u.id, "name": u.name, "role": u.role} for u in users]

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
            "phone": user.phone if hasattr(user, 'phone') and user.phone else "-",  # 联系方式
            "date": str(s.date),
            "shift_type": s.shift_type,
            "note": s.note
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
        reason=request_data.reason
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    
    # 发送 webhook 通知
    webhook_config = load_webhook_config()
    if webhook_config.get("enabled") and webhook_config.get("notify_time_off"):
        send_webhook(
            webhook_config,
            "🏖️ 调休申请",
            f"{current_user.name} 申请调休\n日期：{request_data.date}\n时长：{request_data.hours}小时\n事由：{request_data.reason}",
            "http://x.dysobo.cn:8888/kq/"
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
    request.reason = update_data.reason
    request.updated_at = datetime.now()
    db.commit()
    db.refresh(request)
    return {"message": "申请已更新", "id": request.id}

@app.delete("/api/time-off/{request_id}")
def delete_time_off(request_id: int, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    request = db.query(database.TimeOffRequest).filter(database.TimeOffRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="申请不存在")
    
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
    """发送 webhook 通知"""
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
            print(f"✅ Webhook 通知发送成功：{title}")
            return True
        else:
            print(f"❌ Webhook 通知发送失败：{response.status_code}")
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
        send_webhook(
            webhook_config,
            "⏰ 加班记录",
            f"{current_user.name} 登记加班\n日期：{record_data.date}\n时长：{record_data.hours}小时\n事由：{record_data.reason}",
            "http://x.dysobo.cn:8888/kq/"
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
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    record = db.query(database.OvertimeRecord).filter(database.OvertimeRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
