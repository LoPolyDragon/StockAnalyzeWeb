#!/usr/bin/env python3
"""
简单的认证API服务器
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import uvicorn
import uuid
from typing import Optional

# 创建FastAPI应用
app = FastAPI(title="Simple Auth API")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# 模型定义
class UserLogin(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    email: str
    full_name: Optional[str] = None
    password: str
    auth_provider: str = "email"

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    is_verified: bool = False

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 86400
    user: UserResponse

# 内存中的用户数据库
users_db = {}
next_user_id = 1

# 路由
@app.post("/auth/register")
async def register(user: UserCreate):
    """用户注册"""
    global next_user_id
    
    if user.email in users_db:
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    # 创建用户
    user_id = next_user_id
    next_user_id += 1
    
    users_db[user.email] = {
        "id": user_id,
        "email": user.email,
        "full_name": user.full_name,
        "password": user.password,  # 实际应用中应该哈希密码
        "auth_provider": user.auth_provider,
        "is_verified": True  # 简化起见，自动验证
    }
    
    print(f"用户注册成功: {user.email}")
    
    return UserResponse(
        id=user_id,
        email=user.email,
        full_name=user.full_name,
        is_verified=True
    )

@app.post("/auth/login")
async def login(user: UserLogin):
    """用户登录"""
    if user.email not in users_db:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    
    stored_user = users_db[user.email]
    
    if stored_user["password"] != user.password:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    
    print(f"用户登录成功: {user.email}")
    
    # 生成令牌
    access_token = str(uuid.uuid4())
    refresh_token = str(uuid.uuid4())
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=stored_user["id"],
            email=stored_user["email"],
            full_name=stored_user["full_name"],
            is_verified=stored_user["is_verified"]
        )
    )

@app.get("/test_auth.html")
async def test_auth_html():
    """测试登录页面"""
    if os.path.exists("static/test_auth.html"):
        return FileResponse("static/test_auth.html")
    else:
        raise HTTPException(status_code=404, detail="测试页面不存在")

@app.get("/")
async def root():
    """根路径"""
    return {"message": "Simple Auth API Server"}

if __name__ == "__main__":
    print("启动简单认证API服务器...")
    uvicorn.run(app, host="0.0.0.0", port=8080) 