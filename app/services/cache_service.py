"""
缓存服务 - 用于缓存向量和查询结果，提高性能
"""
import time
import logging
from functools import wraps
from typing import Dict, Any, Callable, Optional, List, Tuple

# 配置日志
logger = logging.getLogger("cache_service")

# 内存缓存，结构 {key: {"value": value, "expires_at": timestamp}}
_cache: Dict[str, Dict[str, Any]] = {}

def get_cache(key: str) -> Optional[Any]:
    """
    从缓存获取值
    
    参数:
        key: 缓存键
        
    返回:
        缓存的值，如果不存在或已过期则返回None
    """
    if key not in _cache:
        return None
        
    cache_item = _cache[key]
    
    # 检查是否过期
    if "expires_at" in cache_item and time.time() > cache_item["expires_at"]:
        del _cache[key]
        return None
        
    return cache_item["value"]

def set_cache(key: str, value: Any, ttl: int = 3600) -> None:
    """
    设置缓存
    
    参数:
        key: 缓存键
        value: 要缓存的值
        ttl: 缓存有效期（秒），默认3600秒（1小时）
    """
    expires_at = time.time() + ttl if ttl > 0 else None
    
    _cache[key] = {
        "value": value,
        "expires_at": expires_at
    }

def delete_cache(key: str) -> bool:
    """
    删除缓存
    
    参数:
        key: 缓存键
        
    返回:
        是否成功删除
    """
    if key in _cache:
        del _cache[key]
        return True
    return False

def clear_cache() -> None:
    """
    清空所有缓存
    """
    _cache.clear()

def clean_expired_cache() -> int:
    """
    清理所有过期的缓存项
    
    返回:
        清理的缓存项数量
    """
    now = time.time()
    expired_keys = [
        key for key, item in _cache.items() 
        if "expires_at" in item and item["expires_at"] is not None and now > item["expires_at"]
    ]
    
    for key in expired_keys:
        del _cache[key]
        
    return len(expired_keys)

def cached(ttl: int = 3600):
    """
    函数缓存装饰器
    
    参数:
        ttl: 缓存有效期（秒），默认3600秒（1小时）
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试从缓存获取
            cached_result = get_cache(cache_key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_result
                
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 设置缓存
            set_cache(cache_key, result, ttl)
            
            return result
            
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试从缓存获取
            cached_result = get_cache(cache_key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_result
                
            # 执行函数
            result = func(*args, **kwargs)
            
            # 设置缓存
            set_cache(cache_key, result, ttl)
            
            return result
            
        return async_wrapper if func.__code__.co_flags & 0x80 else sync_wrapper
        
    return decorator

# 缓存统计
def get_cache_stats() -> Dict[str, Any]:
    """
    获取缓存统计信息
    
    返回:
        包含统计信息的字典
    """
    now = time.time()
    total_items = len(_cache)
    expired_items = sum(
        1 for item in _cache.values() 
        if "expires_at" in item and item["expires_at"] is not None and now > item["expires_at"]
    )
    
    return {
        "total_items": total_items,
        "active_items": total_items - expired_items,
        "expired_items": expired_items
    }

# 启动周期性任务清理过期缓存
def start_cleanup_task():
    """
    启动周期性任务，清理过期缓存项
    """
    import threading
    
    def cleanup_task():
        while True:
            try:
                cleaned = clean_expired_cache()
                if cleaned > 0:
                    logger.info(f"缓存清理：已删除 {cleaned} 个过期项")
            except Exception as e:
                logger.error(f"缓存清理出错: {e}")
                
            # 每小时执行一次
            time.sleep(3600)
    
    # 创建守护线程执行清理
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    logger.info("缓存清理任务已启动") 