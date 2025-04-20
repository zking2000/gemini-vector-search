"""
Cache Service - For caching vectors and query results to improve performance
"""
import time
import logging
from functools import wraps
from typing import Dict, Any, Callable, Optional, List, Tuple

# Configure logging
logger = logging.getLogger("cache_service")

# Memory cache, structure {key: {"value": value, "expires_at": timestamp}}
_cache: Dict[str, Dict[str, Any]] = {}

def get_cache(key: str) -> Optional[Any]:
    """
    Get value from cache
    
    Parameters:
        key: Cache key
        
    Returns:
        Cached value, or None if not exists or expired
    """
    if key not in _cache:
        return None
        
    cache_item = _cache[key]
    
    # Check if expired
    if "expires_at" in cache_item and time.time() > cache_item["expires_at"]:
        del _cache[key]
        return None
        
    return cache_item["value"]

def set_cache(key: str, value: Any, ttl: int = 3600) -> None:
    """
    Set cache
    
    Parameters:
        key: Cache key
        value: Value to cache
        ttl: Cache time-to-live (seconds), default 3600 seconds (1 hour)
    """
    expires_at = time.time() + ttl if ttl > 0 else None
    
    _cache[key] = {
        "value": value,
        "expires_at": expires_at
    }

def delete_cache(key: str) -> bool:
    """
    Delete cache
    
    Parameters:
        key: Cache key
        
    Returns:
        Whether successfully deleted
    """
    if key in _cache:
        del _cache[key]
        return True
    return False

def clear_cache() -> None:
    """
    Clear all cache
    """
    _cache.clear()

def clean_expired_cache() -> int:
    """
    Clean all expired cache items
    
    Returns:
        Number of cache items cleaned
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
    Function cache decorator
    
    Parameters:
        ttl: Cache time-to-live (seconds), default 3600 seconds (1 hour)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_result = get_cache(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_result
                
            # Execute function
            result = await func(*args, **kwargs)
            
            # Set cache
            set_cache(cache_key, result, ttl)
            
            return result
            
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_result = get_cache(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_result
                
            # Execute function
            result = func(*args, **kwargs)
            
            # Set cache
            set_cache(cache_key, result, ttl)
            
            return result
            
        return async_wrapper if func.__code__.co_flags & 0x80 else sync_wrapper
        
    return decorator

# Cache statistics
def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics
    
    Returns:
        Dictionary containing statistics
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

# Start periodic task to clean expired cache
def start_cleanup_task():
    """
    Start periodic task to clean expired cache items
    """
    import threading
    
    def cleanup_task():
        while True:
            try:
                cleaned = clean_expired_cache()
                if cleaned > 0:
                    logger.info(f"Cache cleanup: Deleted {cleaned} expired items")
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                
            # Execute once every hour
            time.sleep(3600)
    
    # Create daemon thread for cleanup
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    logger.info("Cache cleanup task started") 