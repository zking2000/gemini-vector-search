import os
import sys

# Add project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from dotenv import load_dotenv
from app.api.gemini_routes import router, health_router
from app.db.database import engine, Base
from app.db.init_db import init_db
from sqlalchemy import text
from app.core.middleware import setup_middleware
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/app.log")
    ]
)
logger = logging.getLogger("app")

# Load environment variables
load_dotenv()

# Initialize database
try:
    init_db()
    logger.info("Database initialization successful")
except Exception as e:
    logger.error(f"Error initializing database: {e}")

# Create FastAPI application
app = FastAPI(
    title="Gemini Vector Search API",
    description="""
    # Gemini Vector Search API

    API system based on Google Gemini 2.0 Flash model, providing the following features:
    
    ## Main Features
    
    * **Vector Retrieval**: Convert documents to vectors and perform similarity searches
    * **Document Management**: Upload, retrieve, and manage documents
    * **Smart Q&A**: Answer questions based on document content
    """,
    version="1.0.0",
    docs_url=None,  # Disable default docs path, we'll create a custom one
    redoc_url="/redoc",
    openapi_url="/api/openapi.json"
)

# Set up middleware
setup_middleware(app)

# Include API routes
app.include_router(router, tags=["API"])

# Include health check routes
app.include_router(health_router, tags=["System"])

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(f"Global exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Custom OpenAPI documentation path, enhancing Swagger UI experience
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title="Gemini Vector Search API - Interactive Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url="/static/favicon.png",
        oauth2_redirect_url=None,
        init_oauth=None,
    )

# Custom OpenAPI information
@app.get("/api/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    openapi_schema = get_openapi(
        title="Gemini Vector Search API",
        version="1.0.0",
        description="""
        # Gemini Vector Search API Documentation
        
        This is an API system based on Google Gemini 2.0 Flash model, providing document management, vector retrieval, and AI generation capabilities.
        
        ## Access Information
        
        All API endpoints are freely accessible without authentication.
        
        ## Main Features
        
        * Document Management: Upload PDFs, add documents, get document listings
        * Vector Retrieval: Generate embedding vectors, search similar documents
        * Text Generation: Generate completion text based on Gemini model
        * Integrated Functions: Combined vector retrieval and text generation in a unified query
        
        Please refer to the project documentation for detailed usage instructions.
        """,
        routes=app.routes,
    )
    
    # Modify tag order and descriptions
    openapi_schema["tags"] = [
        {
            "name": "System",
            "description": "System health check and status related endpoints"
        },
        {
            "name": "API",
            "description": "Core functionality API endpoints"
        }
    ]
    
    return openapi_schema

# Home page
@app.get("/")
async def root():
    """
    Return API home page information, including documentation links
    """
    return {
        "message": "Welcome to the Gemini Vector Search API",
        "swagger_docs": "/docs",
        "redoc": "/redoc",
        "api_guide": "/api-guide"
    }

# Health check endpoint
@app.get("/health", tags=["health"])
def health_check():
    """
    Health check endpoint for monitoring system operational status
    
    Returns:
        dict: Dictionary containing status information
    """
    return {"status": "healthy"}

# pgvector status check endpoint
@app.get("/vector-status", tags=["health"])
async def vector_status():
    """
    Check if the pgvector extension is correctly installed
    
    Returns:
        dict: Dictionary containing pgvector installation status
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
            has_vector = result.scalar() is not None
            return {"pgvector_installed": has_vector}
    except Exception as e:
        logger.error(f"Error checking pgvector status: {e}")
        return {"pgvector_installed": False, "error": str(e)}

# Provide static files for API guide
try:
    app.mount("/api-guide", StaticFiles(directory="static", html=True), name="api_guide")
except Exception as e:
    logger.error(f"Unable to mount static files directory: {e}")
    # Create a temporary route as an alternative
    @app.get("/api-guide")
    async def api_guide_redirect():
        """Redirect to API documentation"""
        return {"message": "API usage guide is currently unavailable, please check the Swagger documentation", "docs_url": "/docs"}

# Add document browser page route
# This feature has been removed

# Startup event
@app.on_event("startup")
async def startup_event():
    """Code executed at application startup"""
    logger.info("Application started")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Code executed at application shutdown"""
    logger.info("Application shutdown")

# If this file is run directly
if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Starting application in development mode: http://{host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=True) 