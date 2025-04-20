"""
Configuration Management Module - Handling application configuration and environment variables
"""
import os
import logging
from pydantic import BaseSettings, validator
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("app.config")

class Settings(BaseSettings):
    """Application Configuration Settings"""
    
    # API Configuration
    API_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Gemini Vector Search Platform"
    VERSION: str = "1.0.0"
    
    # Authentication Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_secret_key")
    API_KEY: str = os.getenv("API_KEY", "")
    
    # Google API Configuration
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    
    # Database Configuration
    ALLOYDB_DATABASE: str = os.getenv("ALLOYDB_DATABASE", "")
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "app.db")
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["*"]
    
    # Cache Configuration
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 默认缓存有效期1小时 # Default cache TTL 1 hour
    VECTOR_CACHE_TTL: int = int(os.getenv("VECTOR_CACHE_TTL", "86400"))  # 默认向量缓存24小时 # Default vector cache TTL 24 hours
    
    # Rate Limit Configuration
    RATE_LIMIT: int = int(os.getenv("RATE_LIMIT", "100"))  # 每分钟API调用限制 # API calls limit per minute
    
    # Database Connection String
    @validator("ALLOYDB_DATABASE", "DB_USER", "DB_PASSWORD", pre=True)
    def build_database_connection(cls, v, values):
        """Build Database Connection String"""
        return v

    DATABASE_URL: Optional[str] = None

    # AlloyDB Connection
    def __init__(self, **data):
        super().__init__(**data)
        if self.ALLOYDB_DATABASE and self.DB_USER and self.DB_PASSWORD:
            self.DATABASE_URL = f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.ALLOYDB_DATABASE}"
        else:
            # If environment variables are incomplete, use SQLite as fallback
            logger.warning("Database configuration incomplete, using SQLite database")
            self.DATABASE_URL = f"sqlite:///{self.SQLITE_DB_PATH}"

    # Validate Google API Configuration
    @validator("GOOGLE_API_KEY")
    def validate_google_api_key(cls, v):
        if not v:
            logger.warning("Google API key not set, some features may not be available")
        return v

    class Config:
        case_sensitive = True
        env_file = ".env"


# Create global settings object
settings = Settings()

def get_settings():
    """Return application settings object"""
    return settings 