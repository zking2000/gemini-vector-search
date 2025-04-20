import os
import subprocess
import time
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, MetaData, Table, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# 设置Google凭证路径
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if CREDENTIALS_PATH:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH
    print(f"已设置Google凭证路径: {CREDENTIALS_PATH}")
else:
    print("警告: 未设置GOOGLE_APPLICATION_CREDENTIALS环境变量")

# 从环境变量获取数据库连接信息
DATABASE = os.getenv("ALLOYDB_DATABASE")
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
# 直接从环境变量获取主机和端口
DB_HOST = os.getenv("DB_HOST", "localhost")  # 默认localhost
DB_PORT = os.getenv("DB_PORT", "5432")  # 默认PostgreSQL端口

# 构建数据库连接URL
DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@{DB_HOST}:{DB_PORT}/{DATABASE}"
print(f"正在连接到数据库: {DATABASE_URL.replace(PASSWORD, '****')}")

# 创建SQLAlchemy引擎
try:
    engine = create_engine(DATABASE_URL)
    # 测试连接 - 使用text()包装SQL语句
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("数据库连接成功!")
except Exception as e:
    print(f"数据库连接失败: {e}")
    # 创建一个占位引擎，应用仍可启动但数据库功能将不可用
    print("创建占位数据库引擎，应用将启动但数据库功能不可用")
    DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@{DB_HOST}:{DB_PORT}/{DATABASE}"
    engine = create_engine(DATABASE_URL)

# 创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base类
Base = declarative_base()

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 
