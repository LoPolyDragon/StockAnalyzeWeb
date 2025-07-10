#!/usr/bin/env python3
"""
测试认证API
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8080"

def test_register():
    """测试注册API"""
    print("测试注册API...")
    url = f"{BASE_URL}/auth/register"
    data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "password123",
        "auth_provider": "email"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            print("注册成功!")
        else:
            print("注册失败!")
    except Exception as e:
        print(f"请求错误: {e}")

def test_login():
    """测试登录API"""
    print("\n测试登录API...")
    url = f"{BASE_URL}/auth/login"
    data = {
        "email": "test@example.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            print("登录成功!")
            data = response.json()
            print(f"访问令牌: {data.get('access_token')}")
        else:
            print("登录失败!")
    except Exception as e:
        print(f"请求错误: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        test_login()
    else:
        test_register() 