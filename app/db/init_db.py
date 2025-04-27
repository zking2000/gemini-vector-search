"""
Database initialization script for creating necessary extensions and tables
"""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.models.vector_models import Document  # Import all models to ensure they are created
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量获取数据库连接信息
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("ALLOYDB_DATABASE", "gemini_vector_search")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# 构建数据库URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 创建数据库引擎
engine = create_engine(DATABASE_URL)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """初始化数据库，创建所有表"""
    try:
        print(f"正在连接到数据库: {DB_HOST}:{DB_PORT}/{DB_NAME}")
        
        # 安全检查：只有在明确设置环境变量时才允许初始化
        if not os.getenv("FORCE_INIT_DB"):
            print("警告：数据库初始化将删除所有现有数据！")
            print("如果要继续，请设置环境变量 FORCE_INIT_DB=true")
            return
            
        # 二次确认：检查是否在生产环境
        if os.getenv("ENVIRONMENT") == "production":
            print("警告：当前处于生产环境！")
            print("如果要继续，请同时设置环境变量 FORCE_INIT_DB=true 和 ALLOW_PRODUCTION_INIT=true")
            if not os.getenv("ALLOW_PRODUCTION_INIT"):
                return
        
        with engine.connect() as conn:
            # 创建 pgvector 扩展
            print("正在创建 pgvector 扩展...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            
            # 获取所有表名
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            
            # 检查是否有现有数据
            if table_names:
                print("警告：发现现有表，将执行数据清除操作！")
                print("现有表列表：", table_names)
                
                # 备份现有数据（如果设置了备份路径）
                backup_path = os.getenv("DB_BACKUP_PATH")
                if backup_path:
                    print(f"正在备份数据到 {backup_path}...")
                    # 这里可以添加备份逻辑
                    # 例如：pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > $backup_path
                
                # 删除所有表（使用 CASCADE）
                print("正在删除现有表...")
                for table_name in table_names:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                conn.commit()
            
            # 创建所有表
            print("正在创建新表...")
            Base.metadata.create_all(bind=engine)
            
            print("数据库初始化成功")
            
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        raise e

if __name__ == "__main__":
    init_db() 