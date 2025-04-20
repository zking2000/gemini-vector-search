"""
中间件模块 - 提供API请求日志记录与错误处理功能
"""
import time
import uuid
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/api.log")
    ]
)

logger = logging.getLogger("api")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件 - 记录每个请求的处理时间和结果
    """
    
    async def dispatch(self, request: Request, call_next):
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 记录请求开始
        start_time = time.time()
        path = request.url.path
        method = request.method
        client = request.client.host if request.client else "unknown"
        logger.info(f"请求开始 [{request_id}] {method} {path} 来自 {client}")
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            logger.info(
                f"请求完成 [{request_id}] {method} {path} "
                f"状态码: {response.status_code} "
                f"耗时: {process_time:.4f}秒"
            )
            
            # 添加请求ID和处理时间到响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # 记录异常
            process_time = time.time() - start_time
            logger.error(
                f"请求异常 [{request_id}] {method} {path} "
                f"错误: {str(e)} "
                f"耗时: {process_time:.4f}秒"
            )
            
            # 重新抛出异常，让FastAPI的异常处理器处理
            raise

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中间件 - 限制API请求频率
    """
    def __init__(self, app, rate_limit_per_minute=60):
        super().__init__(app)
        self.rate_limit = rate_limit_per_minute
        self.requests = {}  # {ip: [timestamp1, timestamp2, ...]}
        self.window = 60  # 时间窗口（秒）
    
    async def dispatch(self, request: Request, call_next):
        # 获取客户端IP
        client_ip = request.client.host if request.client else "unknown"
        
        # 跳过健康检查端点
        if request.url.path in ["/health", "/vector-status"]:
            return await call_next(request)
        
        # 当前时间
        now = time.time()
        
        # 初始化客户端记录
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # 清理过期的请求记录
        self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < self.window]
        
        # 检查是否超过速率限制
        if len(self.requests[client_ip]) >= self.rate_limit:
            logger.warning(f"速率限制 {client_ip} 超过每分钟 {self.rate_limit} 请求的限制")
            return Response(
                content={"detail": "请求过于频繁，请稍后再试"},
                status_code=429,
                media_type="application/json"
            )
        
        # 记录请求时间
        self.requests[client_ip].append(now)
        
        # 处理请求
        return await call_next(request)

def setup_middleware(app):
    """
    配置所有中间件
    """
    # 请求日志中间件
    app.add_middleware(RequestLoggingMiddleware)
    
    # 速率限制中间件
    app.add_middleware(RateLimitMiddleware, rate_limit_per_minute=120)
    
    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 在生产环境中应指定允许的域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ) 