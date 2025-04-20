"""
数据库初始化脚本，用于创建必要的扩展和表
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.database import engine, Base
from app.models.vector_models import Document  # 导入所有模型以确保它们被创建

def init_db():
    """初始化数据库，创建表和扩展"""
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 创建数据库会话
    with engine.connect() as conn:
        # 启用pgvector扩展
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        
        # 确保存在序列
        conn.execute(text("CREATE SEQUENCE IF NOT EXISTS document_id_seq;"))
        
        # 如果documents表已经存在，确保id列使用序列
        conn.execute(text("""
            DO $$
            BEGIN
                -- 检查是否已经存在序列关联
                IF NOT EXISTS (
                    SELECT 1 
                    FROM pg_depend d 
                    JOIN pg_class c ON c.oid = d.objid 
                    WHERE c.relname = 'documents' 
                    AND d.refobjid = (SELECT oid FROM pg_class WHERE relname = 'document_id_seq')
                ) THEN
                    -- 尝试将序列与id列关联
                    BEGIN
                        ALTER TABLE documents ALTER COLUMN id SET DEFAULT nextval('document_id_seq');
                    EXCEPTION WHEN OTHERS THEN
                        RAISE NOTICE 'Could not set default for id column: %', SQLERRM;
                    END;
                END IF;
            END;
            $$;
        """))
        
        conn.commit()
        
    print("数据库初始化完成。表、序列和pgvector扩展已创建。")

if __name__ == "__main__":
    init_db() 