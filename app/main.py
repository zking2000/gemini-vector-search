import os
import sys

# 将项目根目录添加到Python路径
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

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/app.log")
    ]
)
logger = logging.getLogger("app")

# 加载环境变量
load_dotenv()

# 初始化数据库
try:
    init_db()
    logger.info("数据库初始化成功")
except Exception as e:
    logger.error(f"初始化数据库时出错: {e}")

# 创建FastAPI应用
app = FastAPI(
    title="Gemini 向量搜索API",
    description="""
    # Gemini 向量搜索API

    基于Google Gemini 2.0 Flash模型的API系统，提供以下功能：
    
    ## 主要功能
    
    * **向量检索**：将文档转换为向量并进行相似度搜索
    * **文档管理**：上传、检索和管理文档
    * **智能问答**：基于文档内容回答问题
    """,
    version="1.0.0",
    docs_url=None,  # 禁用默认的docs路径，我们将创建自定义的
    redoc_url="/redoc",
    openapi_url="/api/openapi.json"
)

# 设置中间件
setup_middleware(app)

# 包含API路由
app.include_router(router, tags=["API"])

# 包含健康检查路由
app.include_router(health_router, tags=["系统"])

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """处理所有未处理的异常"""
    logger.error(f"全局异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误: {str(exc)}"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """处理HTTP异常"""
    logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# 自定义的OpenAPI文档路径，增强Swagger UI体验
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title="Gemini向量搜索API - 交互式文档",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url="/static/favicon.png",
        oauth2_redirect_url=None,
        init_oauth=None,
    )

# 自定义OpenAPI信息
@app.get("/api/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    openapi_schema = get_openapi(
        title="Gemini向量搜索API",
        version="1.0.0",
        description="""
        # Gemini向量搜索API文档
        
        这是一个基于Google Gemini 2.0 Flash模型的API系统，提供文档管理、向量检索和AI生成功能。
        
        ## 访问说明
        
        所有API端点均可自由访问，无需认证。
        
        ## 主要功能
        
        * 文档管理：上传PDF、添加文档、获取文档列表
        * 向量检索：生成嵌入向量、搜索相似文档
        * 文本生成：基于Gemini模型生成补全文本
        * 集成功能：结合向量检索与文本生成的一体化查询
        
        详细使用说明请参考项目文档。
        """,
        routes=app.routes,
    )
    
    # 修改标签顺序和描述
    openapi_schema["tags"] = [
        {
            "name": "系统",
            "description": "系统健康检查和状态相关端点"
        },
        {
            "name": "API",
            "description": "核心功能API端点"
        }
    ]
    
    return openapi_schema

# 主页
@app.get("/")
async def root():
    """
    返回API主页信息，包含文档链接
    """
    return {
        "message": "欢迎使用Gemini向量搜索API",
        "swagger_docs": "/docs",
        "redoc": "/redoc",
        "api_guide": "/api-guide"
    }

# 健康检查端点
@app.get("/health", tags=["health"])
def health_check():
    """
    健康检查端点，用于监控系统是否正常运行
    
    返回:
        dict: 包含状态信息的字典
    """
    return {"status": "healthy"}

# pgvector状态检查端点
@app.get("/vector-status", tags=["health"])
async def vector_status():
    """
    检查pgvector扩展是否正确安装
    
    返回:
        dict: 包含pgvector安装状态的字典
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
            has_vector = result.scalar() is not None
            return {"pgvector_installed": has_vector}
    except Exception as e:
        logger.error(f"检查pgvector状态时出错: {e}")
        return {"pgvector_installed": False, "error": str(e)}

# 提供API指南的静态文件
try:
    app.mount("/api-guide", StaticFiles(directory="static", html=True), name="api_guide")
except Exception as e:
    logger.error(f"无法挂载静态文件目录: {e}")
    # 创建一个临时路由作为替代
    @app.get("/api-guide")
    async def api_guide_redirect():
        """重定向到API文档"""
        return {"message": "API使用指南暂不可用，请查看Swagger文档", "docs_url": "/docs"}

# 添加文档浏览器页面路由
# 该功能已移除

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行的代码"""
    logger.info("应用启动")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行的代码"""
    logger.info("应用关闭")

# 如果直接运行此文件
if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"以开发模式启动应用: http://{host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=True) 