"""
用户认证相关的数据模型
"""
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List
from enum import Enum

Base = declarative_base()

class AuthProvider(str, Enum):
    """认证提供商枚举"""
    EMAIL = "email"
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"

class UserStatus(str, Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"

# SQLAlchemy数据库模型
class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=True)
    full_name = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=True)  # 仅用于邮箱注册用户
    avatar_url = Column(String(500), nullable=True)
    
    # 认证相关
    auth_provider = Column(String(20), default=AuthProvider.EMAIL)
    provider_id = Column(String(100), nullable=True)  # OAuth提供商的用户ID
    is_verified = Column(Boolean, default=False)
    status = Column(String(20), default=UserStatus.PENDING_VERIFICATION)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # 用户偏好设置
    preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    watchlists = relationship("UserWatchlist", back_populates="user", cascade="all, delete-orphan")
    portfolios = relationship("UserPortfolio", back_populates="user", cascade="all, delete-orphan")

class UserPreference(Base):
    """用户偏好设置表"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 界面设置
    theme = Column(String(20), default="light")  # light, dark
    language = Column(String(10), default="zh-CN")  # zh-CN, en-US
    currency = Column(String(3), default="USD")  # USD, CNY, HKD
    
    # 通知设置
    email_notifications = Column(Boolean, default=True)
    price_alerts = Column(Boolean, default=True)
    news_digest = Column(Boolean, default=False)
    
    # 投资偏好
    risk_tolerance = Column(String(20), default="medium")  # low, medium, high
    investment_goals = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="preferences")

class UserWatchlist(Base):
    """用户关注列表表"""
    __tablename__ = "user_watchlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # 股票列表 (JSON格式存储)
    symbols = Column(Text, nullable=False)  # JSON数组：["AAPL", "GOOGL", "TSLA"]
    
    # 设置
    is_default = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="watchlists")

class UserPortfolio(Base):
    """用户投资组合表"""
    __tablename__ = "user_portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # 组合数据 (JSON格式存储)
    holdings = Column(Text, nullable=False)  # JSON格式的持仓数据
    total_value = Column(String(20), nullable=True)
    cash_balance = Column(String(20), default="0")
    
    # 设置
    is_paper_trading = Column(Boolean, default=True)  # 模拟交易
    is_public = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="portfolios")

class UserSession(Base):
    """用户会话表"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    
    # 会话信息
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_info = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # 状态
    is_active = Column(Boolean, default=True)

# Pydantic模型用于API
class UserBase(BaseModel):
    """用户基础模型"""
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None

class UserCreate(UserBase):
    """用户创建模型"""
    password: Optional[str] = None
    auth_provider: AuthProvider = AuthProvider.EMAIL

class UserLogin(BaseModel):
    """用户登录模型"""
    email: EmailStr
    password: str

class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    avatar_url: Optional[str] = None
    auth_provider: AuthProvider
    is_verified: bool
    status: UserStatus
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserPreferenceUpdate(BaseModel):
    """用户偏好更新模型"""
    theme: Optional[str] = None
    language: Optional[str] = None
    currency: Optional[str] = None
    email_notifications: Optional[bool] = None
    price_alerts: Optional[bool] = None
    news_digest: Optional[bool] = None
    risk_tolerance: Optional[str] = None
    investment_goals: Optional[str] = None

class WatchlistCreate(BaseModel):
    """关注列表创建模型"""
    name: str
    description: Optional[str] = None
    symbols: List[str]
    is_public: bool = False

class WatchlistResponse(BaseModel):
    """关注列表响应模型"""
    id: int
    name: str
    description: Optional[str] = None
    symbols: List[str]
    is_default: bool
    is_public: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class PortfolioCreate(BaseModel):
    """投资组合创建模型"""
    name: str
    description: Optional[str] = None
    initial_cash: float = 100000.0
    is_paper_trading: bool = True
    is_public: bool = False

class TokenResponse(BaseModel):
    """Token响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class GoogleAuthRequest(BaseModel):
    """Google认证请求模型"""
    code: str
    redirect_uri: str

class PasswordResetRequest(BaseModel):
    """密码重置请求模型"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """密码重置确认模型"""
    token: str
    new_password: str