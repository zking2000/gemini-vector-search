import os
import subprocess
import time
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, MetaData, Table, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Set Google credential path
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if CREDENTIALS_PATH:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH
    print(f"Google credential path set: {CREDENTIALS_PATH}")
else:
    print("Warning: GOOGLE_APPLICATION_CREDENTIALS environment variable not set")

# Get database connection information from environment variables
DATABASE = os.getenv("ALLOYDB_DATABASE")
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
# Get host and port directly from environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")  # Default: localhost
DB_PORT = os.getenv("DB_PORT", "5432")  # Default PostgreSQL port

# Build database connection URL
DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@{DB_HOST}:{DB_PORT}/{DATABASE}"
print(f"Connecting to database: {DATABASE_URL.replace(PASSWORD, '****')}")

# Create SQLAlchemy engine
try:
    engine = create_engine(DATABASE_URL)
    # Test connection - using text() to wrap SQL statement
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("Database connection successful!")
except Exception as e:
    print(f"Database connection failed: {e}")
    # Create a placeholder engine, application can still start but database functions will be unavailable
    print("Creating placeholder database engine, application will start but database functions will be unavailable")
    DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@{DB_HOST}:{DB_PORT}/{DATABASE}"
    engine = create_engine(DATABASE_URL)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 
