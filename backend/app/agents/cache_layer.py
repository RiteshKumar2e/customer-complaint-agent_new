import json
import hashlib
from functools import wraps
from datetime import datetime, timedelta
from app.memory.redis_store import redis_client

# ========================================
# RESPONSE CACHING LAYER
# ========================================
# Reduces API calls and improves response speed significantly

CACHE_EXPIRY = 86400  # 24 hours in seconds

def generate_cache_key(prefix: str, text: str) -> str:
    """Generate a unique cache key based on text hash"""
    text_hash = hashlib.md5(text.lower().strip().encode()).hexdigest()
    return f"{prefix}:{text_hash}"


def cache_response(prefix: str, expiry: int = CACHE_EXPIRY):
    """Decorator to cache function responses in Redis"""
    def decorator(func):
        @wraps(func)
        def wrapper(text: str, *args, **kwargs):
            cache_key = generate_cache_key(prefix, text)
            
            # Try to get from cache
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                print(f"⚠ Cache retrieval failed: {e}")
            
            # Call function if not cached
            result = func(text, *args, **kwargs)
            
            # Store in cache
            try:
                redis_client.setex(cache_key, expiry, json.dumps(result))
            except Exception as e:
                print(f"⚠ Cache storage failed: {e}")
            
            return result
        return wrapper
    return decorator


def cache_complaint_analysis(expiry: int = CACHE_EXPIRY):
    """Decorator to cache full complaint analysis"""
    def decorator(func):
        @wraps(func)
        def wrapper(text: str, *args, **kwargs):
            cache_key = generate_cache_key("complaint_analysis", text)
            
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass
            
            result = func(text, *args, **kwargs)
            
            try:
                redis_client.setex(cache_key, expiry, json.dumps(result))
            except Exception:
                pass
            
            return result
        return wrapper
    return decorator


def get_similar_cached_complaints(text: str, category: str, limit: int = 3):
    """Retrieve similar complaints from cache"""
    cache_key = f"similar:{category}"
    try:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)[:limit]
    except Exception:
        pass
    return []


def cache_clear(pattern: str = None):
    """Clear specific cache entries"""
    try:
        if pattern:
            keys = redis_client.keys(f"{pattern}:*")
            if keys:
                redis_client.delete(*keys)
        return True
    except Exception as e:
        print(f"⚠ Cache clear failed: {e}")
        return False


# Statistics for cache performance
class CacheStats:
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.total_time_saved = 0.0  # in seconds
    
    def record_hit(self, time_saved: float = 1.0):
        """Record a cache hit"""
        self.hits += 1
        self.total_time_saved += time_saved
    
    def record_miss(self):
        """Record a cache miss"""
        self.misses += 1
    
    def get_stats(self):
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "total_time_saved": f"{self.total_time_saved:.2f}s"
        }

cache_stats = CacheStats()