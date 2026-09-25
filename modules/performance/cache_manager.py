"""
Performance Cache Manager

Multi-level caching system for improving performance.

Features:
- Memory cache (LRU)
- Disk cache (persistent)
- Cache invalidation strategies
- TTL support
- Cache statistics

Author: AI-Symp-Controller Team
Date: November 2025
Version: 1.0
"""

import logging
import json
import pickle
import time
from typing import Any, Optional, Callable, Dict
from pathlib import Path
from functools import wraps
from collections import OrderedDict
import hashlib

logger = logging.getLogger(__name__)


class LRUCache:
    """
    Least Recently Used (LRU) Cache implementation.
    
    Thread-safe in-memory cache with size limit.
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of items
        """
        self._cache: OrderedDict = OrderedDict()
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> tuple[bool, Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Tuple of (found, value)
        """
        if key in self._cache:
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return (True, self._cache[key])
        
        self._misses += 1
        return (False, None)
    
    def set(self, key: str, value: Any):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        if key in self._cache:
            # Update existing
            self._cache.move_to_end(key)
        else:
            # Add new
            if len(self._cache) >= self._max_size:
                # Remove least recently used
                self._cache.popitem(last=False)
        
        self._cache[key] = value
    
    def delete(self, key: str) -> bool:
        """
        Delete from cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if deleted
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self):
        """Clear entire cache."""
        self._cache.clear()
        logger.info("LRU cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        
        return {
            'size': len(self._cache),
            'max_size': self._max_size,
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': f"{hit_rate:.1f}%"
        }


class TTLCache:
    """
    Cache with Time-To-Live (TTL) support.
    """
    
    def __init__(self, ttl: float = 300.0):
        """
        Initialize TTL cache.
        
        Args:
            ttl: Time to live in seconds
        """
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._ttl = ttl
    
    def get(self, key: str) -> tuple[bool, Any]:
        """Get value if not expired."""
        if key in self._cache:
            value, expires_at = self._cache[key]
            
            if time.time() < expires_at:
                return (True, value)
            else:
                # Expired
                del self._cache[key]
                logger.debug(f"Cache key expired: {key}")
        
        return (False, None)
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """Set value with TTL."""
        actual_ttl = ttl if ttl is not None else self._ttl
        expires_at = time.time() + actual_ttl
        self._cache[key] = (value, expires_at)
    
    def clear(self):
        """Clear cache."""
        self._cache.clear()


class DiskCache:
    """
    Persistent disk-based cache.
    """
    
    def __init__(self, cache_dir: str = ".cache"):
        """
        Initialize disk cache.
        
        Args:
            cache_dir: Directory for cache files
        """
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Disk cache initialized at {self._cache_dir}")
    
    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path."""
        # Hash key to get filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self._cache_dir / f"{key_hash}.cache"
    
    def get(self, key: str) -> tuple[bool, Any]:
        """Get value from disk."""
        cache_path = self._get_cache_path(key)
        
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    value = pickle.load(f)
                return (True, value)
            except Exception as e:
                logger.error(f"Error reading cache: {e}")
                return (False, None)
        
        return (False, None)
    
    def set(self, key: str, value: Any):
        """Set value on disk."""
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)
        except Exception as e:
            logger.error(f"Error writing cache: {e}")
    
    def delete(self, key: str) -> bool:
        """Delete from disk."""
        cache_path = self._get_cache_path(key)
        
        if cache_path.exists():
            cache_path.unlink()
            return True
        return False
    
    def clear(self):
        """Clear all cache files."""
        count = 0
        for cache_file in self._cache_dir.glob("*.cache"):
            cache_file.unlink()
            count += 1
        logger.info(f"Cleared {count} cache files")


class CacheManager:
    """
    Multi-level cache manager.
    
    Combines memory and disk caching with TTL support.
    """
    
    def __init__(
        self,
        memory_size: int = 100,
        ttl: float = 300.0,
        use_disk: bool = True,
        cache_dir: str = ".cache"
    ):
        """
        Initialize cache manager.
        
        Args:
            memory_size: Max items in memory
            ttl: Time to live in seconds
            use_disk: Enable disk cache
            cache_dir: Disk cache directory
        """
        self._memory_cache = LRUCache(max_size=memory_size)
        self._ttl_cache = TTLCache(ttl=ttl)
        self._disk_cache = DiskCache(cache_dir) if use_disk else None
        self._use_disk = use_disk
        
        logger.info(f"CacheManager initialized (memory: {memory_size}, ttl: {ttl}s, disk: {use_disk})")
    
    def get(self, key: str) -> tuple[bool, Any]:
        """
        Get value from cache (multi-level).
        
        Tries: Memory -> TTL -> Disk
        
        Args:
            key: Cache key
        
        Returns:
            Tuple of (found, value)
        """
        # Try memory cache first (fastest)
        found, value = self._memory_cache.get(key)
        if found:
            logger.debug(f"Cache HIT (memory): {key}")
            return (True, value)
        
        # Try TTL cache
        found, value = self._ttl_cache.get(key)
        if found:
            logger.debug(f"Cache HIT (TTL): {key}")
            # Promote to memory cache
            self._memory_cache.set(key, value)
            return (True, value)
        
        # Try disk cache
        if self._use_disk and self._disk_cache:
            found, value = self._disk_cache.get(key)
            if found:
                logger.debug(f"Cache HIT (disk): {key}")
                # Promote to memory and TTL
                self._memory_cache.set(key, value)
                self._ttl_cache.set(key, value)
                return (True, value)
        
        logger.debug(f"Cache MISS: {key}")
        return (False, None)
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """
        Set value in cache (all levels).
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override
        """
        # Set in all levels
        self._memory_cache.set(key, value)
        self._ttl_cache.set(key, value, ttl)
        
        if self._use_disk and self._disk_cache:
            self._disk_cache.set(key, value)
        
        logger.debug(f"Cache SET: {key}")
    
    def delete(self, key: str):
        """Delete from all cache levels."""
        self._memory_cache.delete(key)
        self._ttl_cache.clear()  # No individual delete in TTL cache
        
        if self._use_disk and self._disk_cache:
            self._disk_cache.delete(key)
        
        logger.debug(f"Cache DELETE: {key}")
    
    def clear(self):
        """Clear all cache levels."""
        self._memory_cache.clear()
        self._ttl_cache.clear()
        
        if self._use_disk and self._disk_cache:
            self._disk_cache.clear()
        
        logger.info("All caches cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'memory': self._memory_cache.get_stats(),
            'ttl_size': len(self._ttl_cache._cache),
            'disk_enabled': self._use_disk
        }


# Decorator for automatic caching
def cached(
    cache_manager: CacheManager,
    key_prefix: str = "",
    ttl: Optional[float] = None
):
    """
    Decorator for automatic function result caching.
    
    Args:
        cache_manager: Cache manager instance
        key_prefix: Prefix for cache keys
        ttl: Time to live override
    
    Example:
        @cached(cache_mgr, "user_", ttl=60)
        def get_user(user_id):
            return fetch_from_db(user_id)
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = "_".join(key_parts)
            
            # Try to get from cache
            found, value = cache_manager.get(cache_key)
            if found:
                return value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    print("=== Cache Manager Test ===\n")
    
    # Create cache manager
    cache = CacheManager(memory_size=10, ttl=5.0, use_disk=True)
    
    # Test basic operations
    print("1. Set value")
    cache.set("user:123", {"name": "John Doe", "age": 30})
    
    print("2. Get value (should hit memory)")
    found, value = cache.get("user:123")
    print(f"Found: {found}, Value: {value}")
    
    print("3. Clear memory only")
    cache._memory_cache.clear()
    
    print("4. Get value (should hit disk)")
    found, value = cache.get("user:123")
    print(f"Found: {found}, Value: {value}")
    
    print("5. Stats")
    print(json.dumps(cache.get_stats(), indent=2))
    
    print("\n6. Test decorator")
    
    @cached(cache, "factorial_", ttl=10)
    def factorial(n):
        print(f"  Computing factorial({n})...")
        if n <= 1:
            return 1
        return n * factorial(n - 1)
    
    print(f"factorial(5) = {factorial(5)}")  # Computed
    print(f"factorial(5) = {factorial(5)}")  # Cached
    
    print("\n7. TTL test")
    cache.set("temp", "expires soon", ttl=2.0)
    found, _ = cache.get("temp")
    print(f"Immediately: {found}")
    
    time.sleep(3)
    found, _ = cache.get("temp")
    print(f"After 3s: {found} (expired)")
    
    # Cleanup
    cache.clear()

