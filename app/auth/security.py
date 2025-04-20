import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def get_credentials():
    """
    从环境变量获取API凭证 (仅作为参考，不再使用认证)
    """
    username = os.getenv("API_USERNAME", "admin")
    password = os.getenv("API_PASSWORD", "password")
    return {"username": username, "password": password}

# 移除了verify_credentials函数和HTTP基本认证逻辑 