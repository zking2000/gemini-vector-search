"""
配置管理模块 - 处理应用配置和环境变量
"""
import os
import logging
from pydantic_settings import BaseSettings
from pydantic import validator
from typing import Optional, Dict, Any, List

logger = logging.getLogger("config")

class Settings(BaseSettings):
    """应用配置设置"""
    
    # API 配置
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Gemini向量搜索平台"
    DEBUG: bool = False
    
    # 认证配置
    API_USERNAME: str = os.getenv("API_USERNAME", "admin")
    API_PASSWORD: str = os.getenv("API_PASSWORD", "password")
    
    # Google API配置
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", None)
    
    # 数据库配置
    ALLOYDB_PROJECT_ID: str = os.getenv("ALLOYDB_PROJECT_ID", "")
    ALLOYDB_REGION: str = os.getenv("ALLOYDB_REGION", "")
    ALLOYDB_CLUSTER_ID: str = os.getenv("ALLOYDB_CLUSTER_ID", "")
    ALLOYDB_INSTANCE_ID: str = os.getenv("ALLOYDB_INSTANCE_ID", "")
    ALLOYDB_DATABASE: str = os.getenv("ALLOYDB_DATABASE", "")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    
    # 服务器配置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS配置
    CORS_ORIGINS: List[str] = ["*"]
    
    # 缓存配置
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 默认缓存有效期1小时
    VECTOR_CACHE_TTL: int = int(os.getenv("VECTOR_CACHE_TTL", "86400"))  # 默认向量缓存24小时
    
    # 速率限制配置
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT", "120"))
    
    # 数据库连接字符串
    @property
    def DATABASE_URI(self) -> str:
        """构建数据库连接字符串"""
        if all([self.ALLOYDB_PROJECT_ID, self.ALLOYDB_REGION, 
                self.ALLOYDB_CLUSTER_ID, self.ALLOYDB_INSTANCE_ID,
                self.ALLOYDB_DATABASE, self.DB_USER, self.DB_PASSWORD]):
            # AlloyDB连接
            return (
                f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@"
                f"localhost:5432/{self.ALLOYDB_DATABASE}?sslmode=disable"
            )
        else:
            # 如果环境变量不完整，使用SQLite作为备选
            logger.warning("数据库配置不完整，使用SQLite数据库")
            return "sqlite:///./app.db"
    
    # 验证Google API配置
    @validator("GOOGLE_API_KEY")
    def validate_google_api_key(cls, v):
        if not v:
            logger.warning("Google API密钥未设置，一些功能可能不可用")
        return v
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# 创建全局设置对象
settings = Settings()

def get_settings() -> Settings:
    """返回应用设置对象"""
    return settings 