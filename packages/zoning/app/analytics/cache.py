"""
Analytics caching system for expensive calculations.

This module provides a caching layer for Earth Engine analysis results,
AI predictions, and other expensive computations with Redis support
and in-memory fallback.
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
from functools import wraps

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available, using in-memory cache")

# Configure logging
logger = logging.getLogger(__name__)


class AnalyticsCache:
    """
    Caching system for analytics results with Redis support and in-memory fallback.
    """
    
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None,
        default_ttl: int = 3600,  # 1 hour default
        max_memory_items: int = 1000
    ):
        """
        Initialize the analytics cache.
        
        Args:
            redis_host: Redis host address
            redis_port: Redis port
            redis_db: Redis database number
            redis_password: Redis password (if required)
            default_ttl: Default time-to-live in seconds (1 hour)
            max_memory_items: Maximum items in memory cache
        """
        self.default_ttl = default_ttl
        self.max_memory_items = max_memory_items
        self.redis_client = None
        self.memory_cache = {}
        self.cache_timestamps = {}
        
        # Try to connect to Redis
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    password=redis_password,
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Connected to Redis cache")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Using in-memory cache.")
                self.redis_client = None
        
    def _generate_cache_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """
        Generate a cache key based on prefix and parameters.
        
        Args:
            prefix: Key prefix (e.g., 'zone_analysis', 'ai_prediction')
            params: Dictionary of parameters to hash
            
        Returns:
            Cache key string
        """
        # Sort params for consistent hashing
        sorted_params = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()
        return f"{prefix}:{param_hash}"
    
    def _generate_zone_key(self, zone_geometry: Dict[str, Any], analysis_type: str) -> str:
        """
        Generate a cache key specifically for zone-based analysis.
        
        Args:
            zone_geometry: GeoJSON geometry of the zone
            analysis_type: Type of analysis (e.g., 'earth_engine', 'population')
            
        Returns:
            Cache key string
        """
        # Create a hash of the geometry
        geometry_str = json.dumps(zone_geometry, sort_keys=True)
        geometry_hash = hashlib.md5(geometry_str.encode()).hexdigest()[:16]
        return f"zone:{analysis_type}:{geometry_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        try:
            # Try Redis first
            if self.redis_client:
                try:
                    value = self.redis_client.get(key)
                    if value:
                        return json.loads(value)
                except Exception as e:
                    logger.error(f"Redis get error: {e}")
            
            # Fallback to memory cache
            if key in self.memory_cache:
                # Check if expired
                timestamp = self.cache_timestamps.get(key, 0)
                if time.time() - timestamp < self.default_ttl:
                    return self.memory_cache[key]
                else:
                    # Remove expired entry
                    del self.memory_cache[key]
                    del self.cache_timestamps[key]
            
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            ttl = ttl or self.default_ttl
            
            # Try Redis first
            if self.redis_client:
                try:
                    serialized = json.dumps(value)
                    self.redis_client.setex(key, ttl, serialized)
                    return True
                except Exception as e:
                    logger.error(f"Redis set error: {e}")
            
            # Fallback to memory cache
            # Implement simple LRU by removing oldest items if at capacity
            if len(self.memory_cache) >= self.max_memory_items:
                oldest_key = min(self.cache_timestamps, key=self.cache_timestamps.get)
                del self.memory_cache[oldest_key]
                del self.cache_timestamps[oldest_key]
            
            self.memory_cache[key] = value
            self.cache_timestamps[key] = time.time()
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def invalidate(self, key: str) -> bool:
        """
        Invalidate (delete) a cache entry.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success = False
            
            # Try Redis first
            if self.redis_client:
                try:
                    self.redis_client.delete(key)
                    success = True
                except Exception as e:
                    logger.error(f"Redis delete error: {e}")
            
            # Also remove from memory cache
            if key in self.memory_cache:
                del self.memory_cache[key]
                del self.cache_timestamps[key]
                success = True
            
            return success
            
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.
        
        Args:
            pattern: Pattern to match (e.g., 'zone:*' for all zone keys)
            
        Returns:
            Number of keys invalidated
        """
        count = 0
        
        try:
            # Redis invalidation
            if self.redis_client:
                try:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        count += self.redis_client.delete(*keys)
                except Exception as e:
                    logger.error(f"Redis pattern delete error: {e}")
            
            # Memory cache invalidation
            keys_to_delete = []
            for key in self.memory_cache:
                if self._matches_pattern(key, pattern):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self.memory_cache[key]
                del self.cache_timestamps[key]
                count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Cache pattern invalidate error: {e}")
            return count
    
    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """
        Simple pattern matching for memory cache.
        
        Args:
            key: Key to check
            pattern: Pattern with * wildcards
            
        Returns:
            True if matches, False otherwise
        """
        import fnmatch
        return fnmatch.fnmatch(key, pattern)
    
    def get_partial(self, key: str, field: str) -> Optional[Any]:
        """
        Get a specific field from a cached result.
        
        Args:
            key: Cache key
            field: Field name to retrieve
            
        Returns:
            Field value or None if not found
        """
        result = self.get(key)
        if result and isinstance(result, dict):
            return result.get(field)
        return None
    
    def set_partial(self, key: str, field: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a specific field in a cached result.
        
        Args:
            key: Cache key
            field: Field name to set
            value: Field value
            ttl: Time-to-live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        # Get existing result or create new dict
        result = self.get(key)
        if not result:
            result = {}
        elif not isinstance(result, dict):
            logger.error(f"Cannot set partial on non-dict value for key: {key}")
            return False
        
        # Update field
        result[field] = value
        
        # Save back to cache
        return self.set(key, result, ttl)
    
    def cache_earth_engine_result(
        self,
        zone_geometry: Dict[str, Any],
        result: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache Earth Engine analysis result for a zone.
        
        Args:
            zone_geometry: GeoJSON geometry of the zone
            result: Analysis result to cache
            ttl: Custom TTL (defaults to 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        key = self._generate_zone_key(zone_geometry, "earth_engine")
        return self.set(key, result, ttl)
    
    def get_earth_engine_result(self, zone_geometry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get cached Earth Engine analysis result for a zone.
        
        Args:
            zone_geometry: GeoJSON geometry of the zone
            
        Returns:
            Cached result or None
        """
        key = self._generate_zone_key(zone_geometry, "earth_engine")
        return self.get(key)
    
    def cache_ai_prediction(
        self,
        zone_geometry: Dict[str, Any],
        prediction: Dict[str, Any],
        model_type: str = "default",
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache AI prediction result for a zone.
        
        Args:
            zone_geometry: GeoJSON geometry of the zone
            prediction: AI prediction result
            model_type: Type of AI model used
            ttl: Custom TTL
            
        Returns:
            True if successful, False otherwise
        """
        key = self._generate_zone_key(zone_geometry, f"ai_prediction:{model_type}")
        return self.set(key, prediction, ttl)
    
    def get_ai_prediction(
        self,
        zone_geometry: Dict[str, Any],
        model_type: str = "default"
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached AI prediction for a zone.
        
        Args:
            zone_geometry: GeoJSON geometry of the zone
            model_type: Type of AI model
            
        Returns:
            Cached prediction or None
        """
        key = self._generate_zone_key(zone_geometry, f"ai_prediction:{model_type}")
        return self.get(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        stats = {
            "backend": "redis" if self.redis_client else "memory",
            "memory_items": len(self.memory_cache),
            "memory_max_items": self.max_memory_items,
            "default_ttl": self.default_ttl
        }
        
        if self.redis_client:
            try:
                info = self.redis_client.info()
                stats["redis_connected"] = True
                stats["redis_used_memory"] = info.get("used_memory_human", "N/A")
                stats["redis_keys"] = self.redis_client.dbsize()
            except:
                stats["redis_connected"] = False
        
        return stats


def cached_analysis(
    cache: AnalyticsCache,
    cache_key_prefix: str,
    ttl: Optional[int] = None
):
    """
    Decorator for caching function results.
    
    Args:
        cache: AnalyticsCache instance
        cache_key_prefix: Prefix for cache keys
        ttl: Time-to-live in seconds
    
    Usage:
        @cached_analysis(cache, "my_analysis")
        def expensive_analysis(zone_id, params):
            # Expensive computation
            return result
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function arguments
            cache_params = {
                "args": args,
                "kwargs": kwargs
            }
            cache_key = cache._generate_cache_key(cache_key_prefix, cache_params)
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {cache_key_prefix}")
                return result
            
            # Compute result
            logger.debug(f"Cache miss for {cache_key_prefix}, computing...")
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# Global cache instance (can be initialized by the app)
_global_cache = None


def init_global_cache(**kwargs) -> AnalyticsCache:
    """
    Initialize the global cache instance.
    
    Args:
        **kwargs: Arguments to pass to AnalyticsCache constructor
        
    Returns:
        AnalyticsCache instance
    """
    global _global_cache
    _global_cache = AnalyticsCache(**kwargs)
    return _global_cache


def get_global_cache() -> Optional[AnalyticsCache]:
    """
    Get the global cache instance.
    
    Returns:
        Global AnalyticsCache instance or None
    """
    return _global_cache
