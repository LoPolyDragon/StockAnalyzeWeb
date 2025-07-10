"""
用户认证服务
"""
import hashlib
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
import jwt
import bcrypt
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, Request
import httpx
import json
import os
import logging

from .auth_models import (
    User, UserSession, UserPreference, UserWatchlist, UserPortfolio,
    UserCreate, UserLogin, UserResponse, TokenResponse, AuthProvider, UserStatus,
    Base
)

logger = logging.getLogger(__name__)

# 数据库配置
try:
    DATABASE_URL = "sqlite:///./stock_advisor_users.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    logger.info("成功初始化认证数据库")
except Exception as e:
    logger.error(f"初始化认证数据库失败: {e}")
    # 创建一个空的会话工厂，避免导入错误
    SessionLocal = None

# JWT配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24小时
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Google OAuth配置
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# 邮件配置
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

security = HTTPBearer(auto_error=False)

class AuthService:
    def __init__(self):
        self.db_session = SessionLocal
    
    def get_db(self):
        """获取数据库会话"""
        if SessionLocal is None:
            logger.error("数据库会话工厂未初始化")
            raise HTTPException(status_code=500, detail="认证服务暂时不可用")
        
        db = None
        try:
            db = SessionLocal()
            yield db
        except Exception as e:
            logger.error(f"创建数据库会话失败: {e}")
            if db:
                db.close()
            raise HTTPException(status_code=500, detail="数据库连接失败")
        finally:
            if db:
                db.close()
    
    def hash_password(self, password: str) -> str:
        """密码哈希"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """创建访问token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """创建刷新token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token已过期")
            return None
        except jwt.JWTError as e:
            logger.warning(f"Token验证失败: {e}")
            return None
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return db.query(User).filter(User.id == user_id).first()
    
    def create_user(self, db: Session, user_create: UserCreate) -> User:
        """创建用户"""
        # 检查邮箱是否已存在
        existing_user = self.get_user_by_email(db, user_create.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被注册"
            )
        
        # 创建用户
        hashed_password = None
        if user_create.password and user_create.auth_provider == AuthProvider.EMAIL:
            hashed_password = self.hash_password(user_create.password)
        
        # 生成用户名
        username = user_create.username
        if not username:
            username = user_create.email.split('@')[0]
            # 确保用户名唯一
            counter = 1
            base_username = username
            while db.query(User).filter(User.username == username).first():
                username = f"{base_username}{counter}"
                counter += 1
        
        db_user = User(
            email=user_create.email,
            username=username,
            full_name=user_create.full_name,
            hashed_password=hashed_password,
            auth_provider=user_create.auth_provider,
            is_verified=True,  # 默认设置为已验证
            status=UserStatus.ACTIVE  # 默认设置为激活状态
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # 创建默认用户偏好
        self.create_default_preferences(db, db_user.id)
        
        # 发送验证邮件（仅邮箱注册用户）
        if user_create.auth_provider == AuthProvider.EMAIL:
            self.send_verification_email(db_user.email, db_user.id)
        
        return db_user
    
    def create_default_preferences(self, db: Session, user_id: int):
        """创建默认用户偏好"""
        preference = UserPreference(
            user_id=user_id,
            theme="light",
            language="zh-CN",
            currency="USD",
            email_notifications=True,
            price_alerts=True,
            news_digest=False,
            risk_tolerance="medium"
        )
        db.add(preference)
        db.commit()
    
    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """验证用户登录"""
        user = self.get_user_by_email(db, email)
        if not user:
            return None
        
        if user.auth_provider != AuthProvider.EMAIL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"该账户使用{user.auth_provider}登录，请使用相应的登录方式"
            )
        
        if not user.hashed_password:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="账户未激活或已被暂停，请联系管理员"
            )
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
    
    def create_user_session(self, db: Session, user: User, request: Request) -> UserSession:
        """创建用户会话"""
        session_id = secrets.token_urlsafe(32)
        
        # 创建tokens
        access_token = self.create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token = self.create_refresh_token({"sub": str(user.id), "email": user.email})
        
        # 获取客户端信息
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        
        session = UserSession(
            user_id=user.id,
            session_id=session_id,
            access_token=access_token,
            refresh_token=refresh_token,
            ip_address=client_ip,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return session
    
    def get_current_user(self, db: Session, credentials: Optional[HTTPAuthorizationCredentials]) -> Optional[User]:
        """获取当前用户"""
        if not credentials:
            return None
        
        payload = self.verify_token(credentials.credentials)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = self.get_user_by_id(db, int(user_id))
        if not user or user.status != UserStatus.ACTIVE:
            return None
        
        return user
    
    async def google_oauth_login(self, db: Session, auth_code: str, redirect_uri: str) -> User:
        """Google OAuth登录"""
        try:
            # 获取access token
            token_url = "https://oauth2.googleapis.com/token"
            token_data = {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": auth_code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri
            }
            
            async with httpx.AsyncClient() as client:
                token_response = await client.post(token_url, data=token_data)
                token_response.raise_for_status()
                token_info = token_response.json()
                
                # 获取用户信息
                user_info_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={token_info['access_token']}"
                user_response = await client.get(user_info_url)
                user_response.raise_for_status()
                user_data = user_response.json()
            
            email = user_data.get("email")
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无法获取Google账户邮箱信息"
                )
            
            # 检查用户是否已存在
            user = self.get_user_by_email(db, email)
            if not user:
                # 创建新用户
                user_create = UserCreate(
                    email=email,
                    full_name=user_data.get("name"),
                    auth_provider=AuthProvider.GOOGLE
                )
                user = self.create_user(db, user_create)
                user.provider_id = user_data.get("id")
                user.avatar_url = user_data.get("picture")
            else:
                # 更新现有用户信息
                if user.auth_provider != AuthProvider.GOOGLE:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="该邮箱已使用其他方式注册，请使用原始登录方式"
                    )
                user.last_login = datetime.utcnow()
                if user_data.get("picture"):
                    user.avatar_url = user_data.get("picture")
            
            db.commit()
            db.refresh(user)
            
            return user
            
        except httpx.HTTPError as e:
            logger.error(f"Google OAuth请求失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google登录失败，请重试"
            )
        except Exception as e:
            logger.error(f"Google OAuth登录失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="登录服务暂时不可用"
            )
    
    def send_verification_email(self, email: str, user_id: int):
        """发送邮箱验证邮件"""
        if not EMAIL_USER or not EMAIL_PASSWORD:
            logger.warning("邮件服务未配置，跳过发送验证邮件")
            return
        
        try:
            # 生成验证token
            verification_token = self.create_access_token(
                {"user_id": user_id, "type": "email_verification"},
                expires_delta=timedelta(hours=24)
            )
            
            # 构建验证链接
            verification_url = f"http://127.0.0.1:8000/auth/verify-email?token={verification_token}"
            
            # 邮件内容
            subject = "Stock AI Advisor - 邮箱验证"
            body = f"""
            欢迎使用 Stock AI Advisor！
            
            请点击以下链接验证您的邮箱：
            {verification_url}
            
            如果您没有注册账户，请忽略此邮件。
            
            链接将在24小时后失效。
            """
            
            # 发送邮件
            msg = MIMEMultipart()
            msg['From'] = EMAIL_USER
            msg['To'] = email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"验证邮件已发送至: {email}")
            
        except Exception as e:
            logger.error(f"发送验证邮件失败: {e}")
    
    def verify_email(self, db: Session, token: str) -> bool:
        """验证邮箱"""
        payload = self.verify_token(token)
        if not payload or payload.get("type") != "email_verification":
            return False
        
        user_id = payload.get("user_id")
        if not user_id:
            return False
        
        user = self.get_user_by_id(db, user_id)
        if not user:
            return False
        
        user.is_verified = True
        user.status = UserStatus.ACTIVE
        db.commit()
        
        return True
    
    def refresh_access_token(self, db: Session, refresh_token: str) -> Optional[str]:
        """刷新访问token"""
        payload = self.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # 验证refresh token是否在数据库中存在且有效
        session = db.query(UserSession).filter(
            and_(
                UserSession.refresh_token == refresh_token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).first()
        
        if not session:
            return None
        
        # 生成新的access token
        user = self.get_user_by_id(db, int(user_id))
        if not user or user.status != UserStatus.ACTIVE:
            return None
        
        new_access_token = self.create_access_token({
            "sub": str(user.id),
            "email": user.email
        })
        
        # 更新session中的access token
        session.access_token = new_access_token
        session.last_activity = datetime.utcnow()
        db.commit()
        
        return new_access_token
    
    def logout(self, db: Session, credentials: HTTPAuthorizationCredentials):
        """用户登出"""
        if not credentials:
            return
        
        # 将对应的session标记为非活跃
        session = db.query(UserSession).filter(
            UserSession.access_token == credentials.credentials
        ).first()
        
        if session:
            session.is_active = False
            db.commit()

# 全局认证服务实例
auth_service = AuthService()

# 依赖注入函数
def get_db():
    """获取数据库会话"""
    if SessionLocal is None:
        logger.error("数据库会话工厂未初始化")
        raise HTTPException(status_code=500, detail="认证服务暂时不可用")
    
    db = None
    try:
        db = SessionLocal()
        yield db
    except Exception as e:
        logger.error(f"创建数据库会话失败: {e}")
        if db:
            db.close()
        raise HTTPException(status_code=500, detail="数据库连接失败")
    finally:
        if db:
            db.close()

def get_current_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """获取当前用户依赖"""
    return auth_service.get_current_user(db, credentials)

def require_auth(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """需要认证的依赖"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要登录才能访问此资源",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return current_user