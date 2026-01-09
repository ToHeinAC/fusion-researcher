"""Query caching for LLM responses."""

import hashlib
import time
from typing import Optional, Any
from dataclasses import dataclass
from collections import OrderedDict


@dataclass
class CacheEntry:
    """Cache entry with value and timestamp."""
    value: Any
    timestamp: float
    hit_count: int = 0


class QueryCache:
    """LRU cache for query results with TTL support."""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        Initialize cache.
        
        Args:
            max_size: Maximum number of entries
            ttl_seconds: Time-to-live in seconds (default 1 hour)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
        }
    
    def _make_key(self, query: str) -> str:
        """Create cache key from query."""
        return hashlib.md5(query.encode()).hexdigest()
    
    def get(self, query: str) -> Optional[Any]:
        """
        Get cached result for query.
        
        Args:
            query: The query string
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        key = self._make_key(query)
        
        if key not in self._cache:
            self._stats["misses"] += 1
            return None
        
        entry = self._cache[key]
        
        # Check TTL
        if time.time() - entry.timestamp > self.ttl_seconds:
            del self._cache[key]
            self._stats["misses"] += 1
            return None
        
        # Move to end (most recently used)
        self._cache.move_to_end(key)
        entry.hit_count += 1
        self._stats["hits"] += 1
        
        return entry.value
    
    def set(self, query: str, value: Any) -> None:
        """
        Cache a query result.
        
        Args:
            query: The query string
            value: The result to cache
        """
        key = self._make_key(query)
        
        # Remove oldest if at capacity
        if len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)
            self._stats["evictions"] += 1
        
        self._cache[key] = CacheEntry(
            value=value,
            timestamp=time.time(),
        )
    
    def invalidate(self, query: str) -> bool:
        """
        Remove a specific query from cache.
        
        Args:
            query: The query string
            
        Returns:
            True if entry was removed, False if not found
        """
        key = self._make_key(query)
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> int:
        """
        Clear all cached entries.
        
        Returns:
            Number of entries cleared
        """
        count = len(self._cache)
        self._cache.clear()
        return count
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.
        
        Returns:
            Number of entries removed
        """
        now = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if now - entry.timestamp > self.ttl_seconds
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)
    
    @property
    def size(self) -> int:
        """Current number of cached entries."""
        return len(self._cache)
    
    @property
    def stats(self) -> dict:
        """Cache statistics."""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0.0
        
        return {
            **self._stats,
            "size": self.size,
            "max_size": self.max_size,
            "hit_rate": hit_rate,
        }
    
    def get_or_compute(self, query: str, compute_fn: callable) -> Any:
        """
        Get cached result or compute and cache.
        
        Args:
            query: The query string
            compute_fn: Function to compute result if not cached
            
        Returns:
            Cached or computed result
        """
        result = self.get(query)
        if result is not None:
            return result
        
        result = compute_fn()
        self.set(query, result)
        return result
