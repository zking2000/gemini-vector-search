"""
Middleware Module - Provides API request logging and error handling functionality
"""
import time
import uuid
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

# Configure logging
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
    Request Logging Middleware - Records processing time and results for each request
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request start
        start_time = time.time()
        path = request.url.path
        method = request.method
        client = request.client.host if request.client else "unknown"
        logger.info(f"Request started [{request_id}] {method} {path} from {client}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            logger.info(
                f"Request completed [{request_id}] {method} {path} "
                f"Status code: {response.status_code} "
                f"Processing time: {process_time:.4f}s"
            )
            
            # Add request ID and processing time to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Log exception
            process_time = time.time() - start_time
            logger.error(
                f"Request exception [{request_id}] {method} {path} "
                f"Error: {str(e)} "
                f"Processing time: {process_time:.4f}s"
            )
            
            # Re-raise exception for FastAPI's exception handler to handle
            raise

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate Limit Middleware - Limits API request frequency
    """
    def __init__(self, app, rate_limit_per_minute=60):
        super().__init__(app)
        self.rate_limit = rate_limit_per_minute
        self.requests = {}  # {ip: [timestamp1, timestamp2, ...]}
        self.window = 60  # Time window (seconds)
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip health check endpoints
        if request.url.path in ["/health", "/vector-status"]:
            return await call_next(request)
        
        # Current time
        now = time.time()
        
        # Initialize client record
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Clean expired request records
        self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < self.window]
        
        # Check if rate limit exceeded
        if len(self.requests[client_ip]) >= self.rate_limit:
            logger.warning(f"Rate limit {client_ip} exceeded limit of {self.rate_limit} requests per minute")
            return Response(
                content={"detail": "Too many requests, please try again later"},
                status_code=429,
                media_type="application/json"
            )
        
        # Record request time
        self.requests[client_ip].append(now)
        
        # Process request
        return await call_next(request)

def setup_middleware(app):
    """
    Configure all middleware
    """
    # Request logging middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    # Rate limit middleware
    app.add_middleware(RateLimitMiddleware, rate_limit_per_minute=120)
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production environment, specify allowed domains
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ) 