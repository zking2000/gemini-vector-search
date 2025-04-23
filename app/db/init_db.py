"""
Database initialization script for creating necessary extensions and tables
"""
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from app.db.database import engine, Base
from app.models.vector_models import Document  # Import all models to ensure they are created

def init_db():
    """Initialize the database schema and initial data"""
    
    # Create tables
    inspector = inspect(engine)
    
    # Check if documents table exists
    if not inspector.has_table('documents'):
        print("Creating documents table...")
        Base.metadata.create_all(bind=engine)
    else:
        print("Documents table already exists.")
        
        # Check for new chunking_strategy column and add if not exists
        columns = inspector.get_columns('documents')
        column_names = [c['name'] for c in columns]
        
        if 'chunking_strategy' not in column_names:
            print("Adding chunking_strategy column to documents table...")
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE documents ADD COLUMN chunking_strategy VARCHAR(50)"
                ))
    
    # Check if pgvector extension is installed
    try:
        print("Checking pgvector extension...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
            extensions = result.fetchall()
            if not extensions:
                print("Installing pgvector extension...")
                # Try to create the extension
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
            else:
                print("pgvector extension already installed.")
    except Exception as e:
        print(f"Warning: Could not install pgvector extension. Vector operations will not work. Error: {e}")
    
    print("Database initialization complete.")

if __name__ == "__main__":
    init_db() 