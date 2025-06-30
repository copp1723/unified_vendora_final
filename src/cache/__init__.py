"""
VENDORA Cache Module
Provides Redis-based distributed caching
"""

from .redis_cache import RedisCache

__all__ = ['RedisCache']