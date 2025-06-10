"""
Caching utilities for the healthcare SOAP note taking bot.
Provides in-memory caching with TTL and size limits.
"""

import time
import threading
from typing import Any, Optional, Dict, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from collections import OrderedDict
import hashlib
import json
import weakref

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """Represents a single cache entry with metadata"""
    value: T
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    ttl: Optional[float] = None
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def access(self) -> T:
        """Mark entry as accessed and return value"""
        self.last_accessed = time.time()
        self.access_count += 1
        return self.value


class LRUCache:
    """Thread-safe LRU cache with TTL support"""
    
    def __init__(self, max_size: int = 100, default_ttl: Optional[float] = None):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            
            return entry.access()
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Put value in cache"""
        with self._lock:
            # Use default TTL if not specified
            if ttl is None:
                ttl = self.default_ttl
            
            # Create cache entry
            entry = CacheEntry(value=value, ttl=ttl)
            
            # Remove existing entry if present
            if key in self._cache:
                del self._cache[key]
            
            # Add new entry
            self._cache[key] = entry
            
            # Enforce size limit
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)  # Remove least recently used
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed"""
        removed_count = 0
        with self._lock:
            keys_to_remove = []
            for key, entry in self._cache.items():
                if entry.is_expired():
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._cache[key]
                removed_count += 1
        
        return removed_count
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
                'total_requests': total_requests
            }


class TranscriptAnalysisCache:
    """Specialized cache for transcript analysis results"""
    
    def __init__(self, max_size: int = 50, ttl: float = 3600):  # 1 hour TTL
        self._cache = LRUCache(max_size=max_size, default_ttl=ttl)
    
    def _create_key(self, transcript: str, analysis_type: str = "enhanced") -> str:
        """Create cache key from transcript content"""
        # Normalize transcript (remove extra whitespace, convert to lowercase)
        normalized = ' '.join(transcript.lower().split())
        
        # Create hash of normalized transcript + analysis type
        key_data = f"{analysis_type}:{normalized}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_analysis(self, transcript: str, analysis_type: str = "enhanced") -> Optional[Dict[str, Any]]:
        """Get cached analysis for transcript"""
        key = self._create_key(transcript, analysis_type)
        return self._cache.get(key)
    
    def cache_analysis(
        self, 
        transcript: str, 
        analysis: Dict[str, Any], 
        analysis_type: str = "enhanced",
        ttl: Optional[float] = None
    ) -> None:
        """Cache analysis result for transcript"""
        key = self._create_key(transcript, analysis_type)
        self._cache.put(key, analysis, ttl)
    
    def invalidate_transcript(self, transcript: str, analysis_type: str = "enhanced") -> bool:
        """Remove cached analysis for specific transcript"""
        key = self._create_key(transcript, analysis_type)
        return self._cache.delete(key)
    
    def cleanup(self) -> int:
        """Clean up expired entries"""
        return self._cache.cleanup_expired()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self._cache.stats()


class SessionCache:
    """Cache for session-specific data"""
    
    def __init__(self, session_ttl: float = 7200):  # 2 hours
        self._sessions: Dict[str, LRUCache] = {}
        self._session_refs: Dict[str, weakref.ref] = {}
        self._lock = threading.RLock()
        self.session_ttl = session_ttl
    
    def get_session_cache(self, session_id: str) -> LRUCache:
        """Get or create cache for session"""
        with self._lock:
            if session_id not in self._sessions:
                cache = LRUCache(max_size=20, default_ttl=self.session_ttl)
                self._sessions[session_id] = cache
                
                # Create weak reference for cleanup
                def cleanup_session(ref):
                    with self._lock:
                        if session_id in self._sessions:
                            del self._sessions[session_id]
                        if session_id in self._session_refs:
                            del self._session_refs[session_id]
                
                self._session_refs[session_id] = weakref.ref(cache, cleanup_session)
            
            return self._sessions[session_id]
    
    def clear_session(self, session_id: str) -> None:
        """Clear cache for specific session"""
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].clear()
                del self._sessions[session_id]
            if session_id in self._session_refs:
                del self._session_refs[session_id]
    
    def cleanup_all_sessions(self) -> Dict[str, int]:
        """Cleanup expired entries in all sessions"""
        cleanup_stats = {}
        with self._lock:
            for session_id, cache in self._sessions.items():
                removed = cache.cleanup_expired()
                if removed > 0:
                    cleanup_stats[session_id] = removed
        return cleanup_stats


def cache_result(
    cache_instance: LRUCache,
    key_func: Callable[..., str] = None,
    ttl: Optional[float] = None
):
    """Decorator to cache function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
                key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Try to get from cache
            cached_result = cache_instance.get(key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_instance.put(key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# Global cache instances
analysis_cache = TranscriptAnalysisCache()
session_cache = SessionCache()


def cleanup_caches():
    """Cleanup all cache instances"""
    analysis_cache.cleanup()
    session_cache.cleanup_all_sessions()


def get_cache_stats() -> Dict[str, Any]:
    """Get statistics for all caches"""
    return {
        'analysis_cache': analysis_cache.stats(),
        'session_cache_count': len(session_cache._sessions)
    } 