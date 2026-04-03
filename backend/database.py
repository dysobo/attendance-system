from sqlalchemy import create_engine, Column, Integer, String, Date, Float, DateTime, ForeignKey, Text, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./attendance.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==================== 数据模型 ====================

class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(100), nullable=False)
    role = Column(String(20), default="member")  # admin 或 member
    phone = Column(String(20), nullable=True)  # 联系方式
    wechat_user_id = Column(String(100), nullable=True)  # 企业微信用户 ID（用于个人推送）
    enable_push = Column(Boolean, default=True)  # 是否启用推送通知
    created_at = Column(DateTime, default=datetime.now)


class Shift(Base):
    """排班表"""
    __tablename__ = "shifts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    shift_type = Column(String(20), nullable=False)  # 早班/晚班/休息
    note = Column(String(200))
    created_at = Column(DateTime, default=datetime.now)


class TimeOffRequest(Base):
    """调休申请表"""
    __tablename__ = "time_off_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    hours = Column(Float, default=8.0)  # 调休时长（小时）
    type = Column(String(1), default="U")  # 假期类型：U 调休/B 病假/S 事假/H 婚假/C 产假/L 护理假/J 经期假/Y 孕期假/R 哺乳假/N 年休假/T 探亲假/Z 丧假
    reason = Column(Text)
    status = Column(String(20), default="pending")  # pending/approved/rejected
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class OvertimeRecord(Base):
    """加班记录表"""
    __tablename__ = "overtime_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    hours = Column(Float, nullable=False)
    reason = Column(Text)
    status = Column(String(20), default="pending")  # pending/approved/rejected
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class WechatConfig(Base):
    """企业微信配置表"""
    __tablename__ = "wechat_config"
    
    id = Column(Integer, primary_key=True, index=True)
    api_url = Column(String(200), default="https://qyapi.weixin.qq.com")  # 企业微信 API 地址
    corp_id = Column(String(100))  # CorpID
    secret = Column(String(200))  # Secret
    agent_id = Column(Integer)  # AgentID
    token = Column(String(100))  # Token
    encoding_aes_key = Column(String(200))  # EncodingAESKey
    enabled = Column(Boolean, default=False)  # 是否启用
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# ==================== 数据库操作 ====================

def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)
    index_statements = [
        ("idx_shifts_user_date_unique", "CREATE UNIQUE INDEX IF NOT EXISTS idx_shifts_user_date_unique ON shifts (user_id, date)"),
        ("idx_shifts_date_user", "CREATE INDEX IF NOT EXISTS idx_shifts_date_user ON shifts (date, user_id)"),
        ("idx_time_off_user_status_date", "CREATE INDEX IF NOT EXISTS idx_time_off_user_status_date ON time_off_requests (user_id, status, date)"),
        ("idx_overtime_user_status_date", "CREATE INDEX IF NOT EXISTS idx_overtime_user_status_date ON overtime_records (user_id, status, date)")
    ]
    with engine.begin() as conn:
        for index_name, statement in index_statements:
            try:
                conn.execute(text(statement))
            except Exception as e:
                print(f"⚠️ 创建索引失败 {index_name}: {e}")


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
