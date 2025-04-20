"""
Database initialization script for creating necessary extensions and tables
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.database import engine, Base
from app.models.vector_models import Document  # Import all models to ensure they are created

def init_db():
    """Initialize database, create tables and extensions"""
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create database session
    with engine.connect() as conn:
        # Enable pgvector extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        
        # Ensure sequence exists
        conn.execute(text("CREATE SEQUENCE IF NOT EXISTS document_id_seq;"))
        
        # If documents table already exists, ensure id column uses sequence
        conn.execute(text("""
            DO $$
            BEGIN
                -- Check if sequence association already exists
                IF NOT EXISTS (
                    SELECT 1 
                    FROM pg_depend d 
                    JOIN pg_class c ON c.oid = d.objid 
                    WHERE c.relname = 'documents' 
                    AND d.refobjid = (SELECT oid FROM pg_class WHERE relname = 'document_id_seq')
                ) THEN
                    -- Try to associate sequence with id column
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
        
    print("Database initialization complete. Tables, sequences, and pgvector extension created.")

if __name__ == "__main__":
    init_db() 