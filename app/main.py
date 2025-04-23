import os
import sys

# Add project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from dotenv import load_dotenv
from app.api.gemini_routes import router, health_router
from app.db.database import engine, Base
from app.db.init_db import init_db
from sqlalchemy import text
from app.core.middleware import setup_middleware
import logging
from contextlib import asynccontextmanager
import google.generativeai as genai
from app.services.gemini_service import GeminiService

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup code
    logger.info("Application started")
    
    # Print Gemini model information
    try:
        # 获取Gemini服务实例
        gemini_service = GeminiService()
        
        # 打印模型版本信息
        logger.info(f"Using Gemini model: {gemini_service.model_id}")
        logger.info(f"Embedding model: {gemini_service.embedding_model_name}")
        
        # 获取可用模型列表
        try:
            models = genai.list_models()
            gemini_models = [model.name for model in models if "gemini" in model.name.lower()]
            logger.info(f"Available Gemini models: {', '.join(gemini_models)}")
        except Exception as e:
            logger.warning(f"Could not retrieve available models list: {e}")
        
        # 打印API凭证信息（不包含敏感数据）
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "Not set")
        api_configured = "Yes" if os.getenv("GOOGLE_API_KEY") else "No"
        logger.info(f"Google Cloud Project: {project_id}")
        logger.info(f"API Key configured: {api_configured}")
        
        # 检查API配额状态
        try:
            logger.info("=== 检查Gemini API配额状态 ===")
            # 尝试发送一个简单的请求，检查配额状态
            try:
                if gemini_service.model_id:
                    test_model = genai.GenerativeModel(gemini_service.model_id)
                else:
                    test_model = genai.GenerativeModel("gemini-1.5-pro")
                    
                # 发送一个简单的请求
                response = test_model.generate_content("测试API配额")
                logger.info("API配额状态: 正常 - 成功完成测试请求")
                logger.info(f"剩余配额: Google AI API目前不直接提供查询剩余配额的接口")
                logger.info(f"配额限制: 大多数Gemini模型的默认配额是每分钟60次请求，每天大约1000-1500次请求")
            except Exception as quota_err:
                error_message = str(quota_err)
                logger.warning(f"API配额测试请求失败: {error_message}")
                
                # 检查是否是配额相关的错误
                if "429" in error_message or "quota" in error_message.lower() or "resource exhausted" in error_message.lower():
                    logger.warning("API配额状态: 配额可能已用尽或接近上限")
                    # 提取错误消息中的配额信息
                    if "limit" in error_message and "quota" in error_message:
                        parts = error_message.split("quota")
                        if len(parts) > 1:
                            logger.warning(f"配额详情: {parts[1]}")
                else:
                    logger.warning("API配额状态: 未知 - 请求失败但不是由于配额限制")
        except Exception as quota_check_err:
            logger.error(f"检查API配额状态时出错: {quota_check_err}")
        
        # 打印高级功能支持
        logger.info(f"Advanced features: Thinking Budget, Model Complexity Selection, Response Caching")
    except Exception as e:
        logger.error(f"Error printing Gemini model information: {e}")
    
    yield
    # Shutdown code
    logger.info("Application shutdown")

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
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Set up middleware
setup_middleware(app)

# Mount static files directory for API guide and benchmarks
# 挂载静态文件目录
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 获取项目根目录
static_dir = os.path.join(base_dir, "static")
api_guide_dir = os.path.join(base_dir, "static/api-guide")
logger.info(f"项目根目录: {base_dir}")
logger.info(f"静态文件目录路径: {static_dir}")
logger.info(f"API指南目录路径: {api_guide_dir}")

app.mount("/api-guide", StaticFiles(directory=api_guide_dir), name="api-guide")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

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
    favicon_path = "/api-guide/favicon.png"  # 使用挂载的静态目录
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title="Gemini Vector Search API - Interactive Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url=favicon_path,
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
        "api_guide": "/api-guide",
        "benchmark": "/api/v1/benchmark"
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

@app.get("/benchmark") 
async def benchmark_redirect():
    """
    Redirect to the benchmark page
    """
    return RedirectResponse(url="/api/v1/benchmark")

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

# If this file is run directly
if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Starting application in development mode: http://{host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=True) 