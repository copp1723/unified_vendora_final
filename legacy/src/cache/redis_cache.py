"""
Redis Cache Implementation for VENDORA
Replaces in-memory caching with distributed Redis cache
"""

import json
import logging
import hashlib
import time
from typing import Any, Optional, Dict
from datetime import timedelta
import redis.asyncio as redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RedisCache:
    """Distributed Redis cache for VENDORA query results"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", 
                 default_ttl: int = 3600, key_prefix: str = "vendora:"):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self.redis_client: Optional[redis.Redis] = None
        self.connected = False
    
    async def connect(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            self.connected = True
            logger.info("✅ Redis cache connected")
            
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.connected = False
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self.connected = False
    
    def _get_cache_key(self, query: str, dealership_id: str, context: Dict = None) -> str:
        """Generate cache key from query parameters"""
        cache_data = f"{query.lower().strip()}:{dealership_id}"
        if context:
            cache_data += f":{json.dumps(context, sort_keys=True)}"
        
        key_hash = hashlib.md5(cache_data.encode()).hexdigest()
        return f"{self.key_prefix}query:{key_hash}"
    
    async def get(self, query: str, dealership_id: str, context: Dict = None) -> Optional[Dict[str, Any]]:
        """Get cached query result"""
        if not self.connected:
            return None
        
        try:
            cache_key = self._get_cache_key(query, dealership_id, context)
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                result = json.loads(cached_data)
                logger.info(f"Cache HIT for key: {cache_key[:20]}...")
                return result
            
            return None
            
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    async def set(self, query: str, dealership_id: str, result: Dict[str, Any], 
                  context: Dict = None, ttl: Optional[int] = None) -> bool:
        """Cache query result"""
        if not self.connected:
            return False
        
        try:
            cache_key = self._get_cache_key(query, dealership_id, context)
            cache_ttl = ttl or self.default_ttl
            
            cached_result = {
                **result,
                "cached_at": str(int(time.time())),
                "cache_ttl": cache_ttl
            }
            
            await self.redis_client.setex(
                cache_key,
                cache_ttl,
                json.dumps(cached_result, default=str)
            )
            
            return True
            
        except (RedisError, json.JSONEncodeError) as e:
            logger.warning(f"Cache set error: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.connected:
            return {"connected": False}
        
        try:
            info = await self.redis_client.info()
            pattern = f"{self.key_prefix}query:*"
            keys = await self.redis_client.keys(pattern)
            
            return {
                "connected": True,
                "total_keys": len(keys),
                "memory_usage": info.get("used_memory_human", "Unknown"),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0)
            }
            
        except RedisError as e:
            return {"connected": False, "error": str(e)}