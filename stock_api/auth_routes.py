"""
用户认证API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
import logging

# 配置日志
logger = logging.getLogger(__name__)

# 导入认证服务和模型
try:
    from .auth_service import auth_service, get_db, get_current_user, require_auth
    from .auth_models import (
        UserCreate, UserLogin, UserResponse, TokenResponse, GoogleAuthRequest,
        PasswordResetRequest, PasswordResetConfirm, UserPreferenceUpdate,
        WatchlistCreate, WatchlistResponse, PortfolioCreate, User
    )
except ImportError as e:
    logger.error(f"导入认证模块失败: {e}")
    raise

router = APIRouter(prefix="/auth", tags=["认证"])

@router.post("/register", response_model=UserResponse)
async def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    try:
        user = auth_service.create_user(db, user_create)
        return UserResponse.from_orm(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )

@router.post("/login", response_model=TokenResponse)
async def login(user_login: UserLogin, request: Request, db: Session = Depends(get_db)):
    """用户登录"""
    user = auth_service.authenticate_user(db, user_login.email, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误"
        )
    
    # 创建会话
    session = auth_service.create_user_session(db, user, request)
    
    return TokenResponse(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        expires_in=1440 * 60,  # 24小时（秒）
        user=UserResponse.from_orm(user)
    )

@router.post("/google", response_model=TokenResponse)
async def google_login(
    google_auth: GoogleAuthRequest, 
    request: Request, 
    db: Session = Depends(get_db)
):
    """Google OAuth登录"""
    try:
        user = await auth_service.google_oauth_login(db, google_auth.code, google_auth.redirect_uri)
        session = auth_service.create_user_session(db, user, request)
        
        return TokenResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            expires_in=1440 * 60,
            user=UserResponse.from_orm(user)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google登录失败"
        )

@router.post("/refresh")
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """刷新访问token"""
    new_access_token = auth_service.refresh_access_token(db, refresh_token)
    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新token无效或已过期"
        )
    
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    """用户登出"""
    # auth_service.logout(db, credentials)
    return {"message": "登出成功"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(require_auth)):
    """获取当前用户信息"""
    return UserResponse.from_orm(current_user)

@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """验证邮箱"""
    success = auth_service.verify_email(db, token)
    if success:
        return HTMLResponse("""
        <html>
            <head><title>邮箱验证成功</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: #4CAF50;">邮箱验证成功！</h1>
                <p>您的账户已激活，可以正常使用了。</p>
                <a href="/" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">返回首页</a>
            </body>
        </html>
        """)
    else:
        return HTMLResponse("""
        <html>
            <head><title>邮箱验证失败</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: #f44336;">邮箱验证失败</h1>
                <p>验证链接无效或已过期，请重新注册或联系管理员。</p>
                <a href="/" style="background: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">返回首页</a>
            </body>
        </html>
        """)

# ==================== 用户偏好设置 API ====================

@router.get("/preferences")
async def get_user_preferences(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """获取用户偏好设置"""
    from .auth_models import UserPreference
    preference = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if not preference:
        # 创建默认偏好设置
        auth_service.create_default_preferences(db, current_user.id)
        preference = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    
    return {
        "theme": preference.theme,
        "language": preference.language,
        "currency": preference.currency,
        "email_notifications": preference.email_notifications,
        "price_alerts": preference.price_alerts,
        "news_digest": preference.news_digest,
        "risk_tolerance": preference.risk_tolerance,
        "investment_goals": preference.investment_goals
    }

@router.put("/preferences")
async def update_user_preferences(
    preference_update: UserPreferenceUpdate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """更新用户偏好设置"""
    from .auth_models import UserPreference
    preference = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    
    if not preference:
        auth_service.create_default_preferences(db, current_user.id)
        preference = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    
    # 更新字段
    update_data = preference_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preference, field, value)
    
    db.commit()
    db.refresh(preference)
    
    return {"message": "偏好设置已更新"}

# ==================== 关注列表 API ====================

@router.get("/watchlists")
async def get_user_watchlists(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """获取用户关注列表"""
    from .auth_models import UserWatchlist
    import json
    
    watchlists = db.query(UserWatchlist).filter(UserWatchlist.user_id == current_user.id).all()
    
    result = []
    for watchlist in watchlists:
        symbols = json.loads(watchlist.symbols) if watchlist.symbols else []
        result.append({
            "id": watchlist.id,
            "name": watchlist.name,
            "description": watchlist.description,
            "symbols": symbols,
            "is_default": watchlist.is_default,
            "is_public": watchlist.is_public,
            "created_at": watchlist.created_at
        })
    
    return result

@router.post("/watchlists", response_model=WatchlistResponse)
async def create_watchlist(
    watchlist_create: WatchlistCreate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """创建关注列表"""
    from .auth_models import UserWatchlist
    import json
    
    # 如果是第一个关注列表，设为默认
    existing_count = db.query(UserWatchlist).filter(UserWatchlist.user_id == current_user.id).count()
    is_default = existing_count == 0
    
    watchlist = UserWatchlist(
        user_id=current_user.id,
        name=watchlist_create.name,
        description=watchlist_create.description,
        symbols=json.dumps(watchlist_create.symbols),
        is_default=is_default,
        is_public=watchlist_create.is_public
    )
    
    db.add(watchlist)
    db.commit()
    db.refresh(watchlist)
    
    return WatchlistResponse(
        id=watchlist.id,
        name=watchlist.name,
        description=watchlist.description,
        symbols=watchlist_create.symbols,
        is_default=watchlist.is_default,
        is_public=watchlist.is_public,
        created_at=watchlist.created_at
    )

@router.put("/watchlists/{watchlist_id}")
async def update_watchlist(
    watchlist_id: int,
    watchlist_update: WatchlistCreate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """更新关注列表"""
    from .auth_models import UserWatchlist
    import json
    
    watchlist = db.query(UserWatchlist).filter(
        UserWatchlist.id == watchlist_id,
        UserWatchlist.user_id == current_user.id
    ).first()
    
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="关注列表不存在"
        )
    
    watchlist.name = watchlist_update.name
    watchlist.description = watchlist_update.description
    watchlist.symbols = json.dumps(watchlist_update.symbols)
    watchlist.is_public = watchlist_update.is_public
    
    db.commit()
    
    return {"message": "关注列表已更新"}

@router.delete("/watchlists/{watchlist_id}")
async def delete_watchlist(
    watchlist_id: int,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """删除关注列表"""
    from .auth_models import UserWatchlist
    
    watchlist = db.query(UserWatchlist).filter(
        UserWatchlist.id == watchlist_id,
        UserWatchlist.user_id == current_user.id
    ).first()
    
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="关注列表不存在"
        )
    
    db.delete(watchlist)
    db.commit()
    
    return {"message": "关注列表已删除"}

# ==================== 投资组合 API ====================

@router.get("/portfolios")
async def get_user_portfolios(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """获取用户投资组合"""
    from .auth_models import UserPortfolio
    import json
    
    portfolios = db.query(UserPortfolio).filter(UserPortfolio.user_id == current_user.id).all()
    
    result = []
    for portfolio in portfolios:
        holdings = json.loads(portfolio.holdings) if portfolio.holdings else {}
        result.append({
            "id": portfolio.id,
            "name": portfolio.name,
            "description": portfolio.description,
            "holdings": holdings,
            "total_value": portfolio.total_value,
            "cash_balance": portfolio.cash_balance,
            "is_paper_trading": portfolio.is_paper_trading,
            "is_public": portfolio.is_public,
            "created_at": portfolio.created_at
        })
    
    return result

@router.post("/portfolios")
async def create_portfolio(
    portfolio_create: PortfolioCreate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """创建投资组合"""
    from .auth_models import UserPortfolio
    import json
    
    portfolio = UserPortfolio(
        user_id=current_user.id,
        name=portfolio_create.name,
        description=portfolio_create.description,
        holdings=json.dumps({}),  # 空的持仓
        total_value=str(portfolio_create.initial_cash),
        cash_balance=str(portfolio_create.initial_cash),
        is_paper_trading=portfolio_create.is_paper_trading,
        is_public=portfolio_create.is_public
    )
    
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    
    return {
        "id": portfolio.id,
        "message": "投资组合创建成功",
        "initial_cash": portfolio_create.initial_cash
    }