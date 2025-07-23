import time
from typing import Dict, Tuple, Optional
from threading import Lock


class SecretCache:
    """Cache for secret existence checks to reduce expensive backend calls"""
    
    def __init__(self, ttl_seconds: int = 3600):  # Default 1 hour
        self.cache: Dict[str, Tuple[bool, float]] = {}
        self.ttl_seconds = ttl_seconds
        self.lock = Lock()
    
    def get(self, key: str) -> Optional[bool]:
        """Get cached result for a secret key"""
        with self.lock:
            if key in self.cache:
                result, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl_seconds:
                    return result
                else:
                    # Expired, remove from cache
                    del self.cache[key]
            return None
    
    def set(self, key: str, exists: bool) -> None:
        """Cache a secret existence result"""
        with self.lock:
            self.cache[key] = (exists, time.time())
    
    def invalidate(self, key: str) -> None:
        """Invalidate a specific cache entry"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
    
    def clear(self) -> None:
        """Clear all cached entries"""
        with self.lock:
            self.cache.clear()
    
    def cleanup_expired(self) -> None:
        """Remove expired entries from cache"""
        current_time = time.time()
        with self.lock:
            expired_keys = [
                key for key, (_, timestamp) in self.cache.items()
                if current_time - timestamp >= self.ttl_seconds
            ]
            for key in expired_keys:
                del self.cache[key]


# Global cache instance
_secret_cache = SecretCache()


def get_secret_cache() -> SecretCache:
    """Get the global secret cache instance"""
    return _secret_cache


def cached_has_secret(secret_backend, key: str) -> bool:
    """Check if a secret exists using cache to avoid repeated expensive calls"""
    cache = get_secret_cache()
    
    # Try to get from cache first
    cached_result = cache.get(key)
    if cached_result is not None:
        return cached_result
    
    # Not in cache, check with backend
    try:
        exists = secret_backend.has_secret(key)
        cache.set(key, exists)
        return exists
    except Exception:
        # If backend check fails, cache as False to avoid repeated failures
        cache.set(key, False)
        return False 