#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ================================================== #
# This file is a part of PYGPT package              #
# Website: https://pygpt.net                         #
# GitHub:  https://github.com/szczyglis-dev/py-gpt   #
# MIT License                                        #
# Created By  : Marcin Szczygliński                  #
# Updated Date: 2025.11.20                           #
# ================================================== #

"""
Document Cache - LRU Cache for Document Metadata and Content

This module provides a thread-safe LRU (Least Recently Used) cache for storing
document metadata and content. It integrates with UnifiedDocumentLoader to provide
fast access to frequently loaded documents while managing memory usage through
configurable size and count limits.

Key Features:
- LRU eviction policy using OrderedDict
- Thread-safe read/write operations
- Configurable size (MB) and document count limits
- Automatic invalidation on file modification
- Cache hit/miss statistics tracking
- Cache warming for frequently accessed documents
- Optional metadata persistence
"""

from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import Lock, RLock
from typing import Dict, List, Optional, Tuple, Any
import hashlib
import json
import os
import time

from .document_processor import DocumentMetadata, LoadResult


@dataclass
class CacheEntry:
    """
    Single cache entry containing document data and metadata.

    Attributes:
        content: Document content chunks
        metadata: Document metadata (including checksum)
        access_count: Number of times this entry has been accessed
        last_accessed: Timestamp of last access
        size_bytes: Total size of cached data in bytes
        file_modified_at: File modification timestamp at time of caching
    """
    content: List[str]
    metadata: DocumentMetadata
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    size_bytes: int = 0
    file_modified_at: Optional[float] = None

    def __post_init__(self):
        """Calculate size after initialization."""
        if self.size_bytes == 0:
            self.size_bytes = self._calculate_size()

    def _calculate_size(self) -> int:
        """Calculate total size of cached data in bytes."""
        content_size = sum(len(chunk.encode('utf-8')) for chunk in self.content)
        metadata_size = len(str(self.metadata).encode('utf-8'))
        return content_size + metadata_size

    def is_stale(self, source_path: str) -> bool:
        """
        Check if cache entry is stale based on file modification time.

        Args:
            source_path: Path to original file

        Returns:
            True if file has been modified since caching
        """
        try:
            if not os.path.exists(source_path):
                return True  # File deleted

            current_modified = os.path.getmtime(source_path)
            return current_modified > (self.file_modified_at or 0)
        except Exception:
            return True  # Assume stale if we can't check


@dataclass
class CacheStats:
    """
    Cache statistics for performance monitoring.

    Attributes:
        hits: Number of cache hits
        misses: Number of cache misses
        evictions: Number of cache evictions
        total_accesses: Total number of cache access attempts
        hit_rate: Cache hit rate (hits / total_accesses)
        current_size_mb: Current cache size in MB
        current_count: Number of entries in cache
        total_loaded_mb: Total MB loaded from cache
        total_saved_mb: Total MB saved by cache (avoided reloads)
    """
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_accesses: int = 0
    total_loaded_bytes: int = 0
    total_saved_bytes: int = 0
    current_size_bytes: int = 0
    current_count: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate as percentage."""
        if self.total_accesses == 0:
            return 0.0
        return (self.hits / self.total_accesses) * 100.0

    @property
    def current_size_mb(self) -> float:
        """Get current cache size in MB."""
        return self.current_size_bytes / (1024 * 1024)

    @property
    def total_loaded_mb(self) -> float:
        """Get total loaded from cache in MB."""
        return self.total_loaded_bytes / (1024 * 1024)

    @property
    def total_saved_mb(self) -> float:
        """Get total saved by cache in MB."""
        return self.total_saved_bytes / (1024 * 1024)


class DocumentCache:
    """
    Thread-safe LRU cache for document metadata and content.

    This cache stores loaded documents to avoid redundant loading operations.
    It uses an LRU eviction policy based on both memory size and document count.
    Cache entries are automatically invalidated when source files are modified.

    Features:
    - Automatic loader selection from registry
    - LRU eviction with configurable limits
    - Thread-safe operations
    - File modification detection
    - Statistics tracking
    - Cache warming support

    Example:
        >>> cache = DocumentCache(
        ...     max_size_mb=100,
        ...     max_documents=1000
        ... )
        >>> # Cache automatically uses appropriate loader
        >>> result = cache.get("document.txt")
        >>> if result:
        ...     print(f"Loaded from cache: {result.metadata.source}")
        >>> else:
        ...     print("Cache miss - loading from disk")
    """

    def __init__(
        self,
        max_size_mb: int = 100,
        max_documents: int = 1000,
        enable_stats: bool = True,
        enable_warming: bool = True,
        persist_metadata: bool = False,
        metadata_path: Optional[str] = None
    ):
        """
        Initialize the document cache.

        Args:
            max_size_mb: Maximum cache size in megabytes (default: 100MB)
            max_documents: Maximum number of documents (default: 1000)
            enable_stats: Whether to track cache statistics (default: True)
            enable_warming: Whether to enable cache warming (default: True)
            persist_metadata: Whether to persist cache metadata (default: False)
            metadata_path: Path to persist metadata (if persist_metadata=True)
        """
        # Cache storage (OrderedDict preserves insertion order for LRU)
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()

        # Configuration
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_documents = max_documents
        self.enable_stats = enable_stats
        self.enable_warming = enable_warming
        self.persist_metadata = persist_metadata
        self.metadata_path = metadata_path or "cache_metadata.json"

        # Statistics
        self.stats = CacheStats()

        # Thread safety
        self._lock = RLock()  # Reentrant lock for nested operations
        self._shutdown = False

        # Track total size for fast eviction decisions
        self._current_size_bytes = 0

        # Document loader registry for automatic loading
        from .document_processor import create_default_registry
        self._loader_registry = create_default_registry()

        # Load persisted metadata if enabled
        if self.persist_metadata:
            self._load_metadata()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - persist metadata if enabled."""
        if self.persist_metadata:
            self._save_metadata()
        self._shutdown = True

    def get(
        self,
        source: str,
        loader: Optional[Any] = None
    ) -> Optional[LoadResult]:
        """
        Get document from cache or load it if not cached.

        This method first checks the cache for the document. If found and not
        stale, it returns the cached content. Otherwise, it loads the document
        using the appropriate loader and caches it.

        Args:
            source: Path, URL, or identifier of document source
            loader: Optional specific loader to use (auto-detected if None)

        Returns:
            LoadResult with content and metadata, or None if loading fails
        """
        if self._shutdown:
            return None

        cache_key = self._make_cache_key(source)

        with self._lock:
            self.stats.total_accesses += 1

            # Check cache
            entry = self._cache.get(cache_key)

            if entry and not entry.is_stale(source):
                # Cache hit - update access tracking
                entry.access_count += 1
                entry.last_accessed = time.time()

                # Move to end (most recently used)
                self._cache.move_to_end(cache_key)

                # Update statistics
                if self.enable_stats:
                    self.stats.hits += 1
                    self.stats.total_loaded_bytes += entry.size_bytes

                # Return as LoadResult
                return LoadResult(
                    success=True,
                    content=entry.content,
                    metadata=entry.metadata,
                    load_time=0.0
                )

            # Cache miss
            if self.enable_stats:
                self.stats.misses += 1

        # Load document (outside lock to avoid blocking during I/O)
        result = self._load_document(source, loader)

        if result and result.success:
            # Cache the loaded document
            self.put(source, result)

        return result

    def put(self, source: str, result: LoadResult) -> bool:
        """
        Store a loaded document in the cache.

        Args:
            source: Path, URL, or identifier of document source
            result: LoadResult containing content and metadata

        Returns:
            True if successfully cached, False otherwise
        """
        if self._shutdown or not result or not result.success:
            return False

        cache_key = self._make_cache_key(source)

        with self._lock:
            # Create cache entry
            try:
                file_modified_at = 0.0
                if os.path.exists(source):
                    file_modified_at = os.path.getmtime(source)

                entry = CacheEntry(
                    content=result.content,
                    metadata=result.metadata,
                    file_modified_at=file_modified_at,
                    access_count=1,
                    last_accessed=time.time()
                )

                # Check if we need to evict before adding
                self._ensure_capacity(entry.size_bytes)

                # Add to cache
                self._cache[cache_key] = entry
                self._current_size_bytes += entry.size_bytes

                return True

            except Exception as e:
                # Don't fail the whole operation if caching fails
                print(f"Warning: Failed to cache {source}: {e}")
                return False

    def invalidate(self, source: str) -> bool:
        """
        Invalidate (remove) a specific document from cache.

        Args:
            source: Path, URL, or identifier of document source

        Returns:
            True if entry was removed, False if not found
        """
        cache_key = self._make_cache_key(source)

        with self._lock:
            if cache_key in self._cache:
                entry = self._cache[cache_key]
                self._current_size_bytes -= entry.size_bytes
                del self._cache[cache_key]
                return True

        return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache entries matching a pattern.

        Args:
            pattern: Glob pattern to match source paths

        Returns:
            Number of entries invalidated
        """
        import fnmatch
        invalidated = 0

        with self._lock:
            keys_to_remove = []

            for cache_key, entry in self._cache.items():
                if fnmatch.fnmatch(entry.metadata.source, pattern):
                    keys_to_remove.append(cache_key)

            for key in keys_to_remove:
                entry = self._cache[key]
                self._current_size_bytes -= entry.size_bytes
                del self._cache[key]
                invalidated += 1

        return invalidated

    def invalidate_stale(self) -> int:
        """
        Remove all stale entries from cache (files modified since caching).

        Returns:
            Number of stale entries removed
        """
        stale_count = 0

        with self._lock:
            keys_to_remove = []

            for cache_key, entry in self._cache.items():
                if entry.is_stale(entry.metadata.source):
                    keys_to_remove.append(cache_key)

            for key in keys_to_remove:
                entry = self._cache[key]
                self._current_size_bytes -= entry.size_bytes
                del self._cache[key]
                stale_count += 1

        return stale_count

    def clear(self) -> None:
        """Clear all entries from cache."""
        with self._lock:
            self._cache.clear()
            self._current_size_bytes = 0

    def warm_cache(self, sources: List[str]) -> Dict[str, bool]:
        """
        Pre-load documents into cache (cache warming).

        Useful for pre-loading frequently accessed documents during startup
        or during idle periods.

        Args:
            sources: List of document sources to load

        Returns:
            Dictionary mapping source to success status
        """
        if not self.enable_warming:
            return {source: False for source in sources}

        results = {}
        for source in sources:
            try:
                result = self.get(source)
                results[source] = result is not None and result.success
            except Exception:
                results[source] = False

        return results

    def get_stats(self) -> CacheStats:
        """
        Get current cache statistics.

        Returns:
            CacheStats object with hit rate, size, etc.
        """
        with self._lock:
            # Create a new stats object with current values
            return CacheStats(
                hits=self.stats.hits,
                misses=self.stats.misses,
                evictions=self.stats.evictions,
                total_accesses=self.stats.total_accesses,
                total_loaded_bytes=self.stats.total_loaded_bytes,
                total_saved_bytes=self.stats.total_saved_bytes,
                current_size_bytes=self._current_size_bytes,
                current_count=len(self._cache)
            )

    def get_cache_keys(self) -> List[str]:
        """
        Get list of all cache keys.

        Returns:
            List of cache keys (source paths)
        """
        with self._lock:
            return list(self._cache.keys())

    def get_access_frequency(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get most frequently accessed documents.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of (source, access_count) tuples sorted by access count
        """
        with self._lock:
            frequencies = [
                (entry.metadata.source, entry.access_count)
                for entry in self._cache.values()
            ]
            frequencies.sort(key=lambda x: x[1], reverse=True)
            return frequencies[:limit]

    def _make_cache_key(self, source: str) -> str:
        """
        Create cache key from source path.

        Uses source path as key. If file doesn't exist, use source string directly.

        Args:
            source: Path, URL, or identifier of document source

        Returns:
            Cache key string
        """
        try:
            # Resolve to absolute path if it's a file
            if os.path.exists(source):
                return str(Path(source).resolve().absolute())
        except Exception:
            pass

        # For URLs or non-files, use as-is
        return source

    def _load_document(
        self,
        source: str,
        loader: Optional[Any] = None
    ) -> Optional[LoadResult]:
        """
        Load document using appropriate loader.

        Args:
            source: Path, URL, or identifier of document source
            loader: Optional specific loader (auto-detected if None)

        Returns:
            LoadResult with content and metadata, or None on failure
        """
        try:
            # Use provided loader or auto-detect
            if loader is not None:
                doc_loader = loader
            else:
                doc_loader = self._loader_registry.get_loader(source)

            if doc_loader is None:
                return None

            # Load complete document
            return doc_loader.load_complete(source)

        except Exception as e:
            print(f"Failed to load document {source}: {e}")
            return None

    def _ensure_capacity(self, required_bytes: int) -> None:
        """
        Ensure cache has capacity for new entry by evicting LRU entries.

        Evicts entries based on LRU order until both size and count limits are met.

        Args:
            required_bytes: Size of new entry to be added
        """
        # While we're over limits, evict LRU entries
        while (
            (self._current_size_bytes + required_bytes > self.max_size_bytes) or
            (len(self._cache) >= self.max_documents)
        ):
            if not self._cache:
                break  # Nothing left to evict

            # Evict least recently used (first item in OrderedDict)
            lru_key, lru_entry = self._cache.popitem(last=False)
            self._current_size_bytes -= lru_entry.size_bytes

            if self.enable_stats:
                self.stats.evictions += 1
                self.stats.total_saved_bytes += lru_entry.size_bytes

    def _load_metadata(self) -> None:
        """Load cache metadata from persistent storage."""
        try:
            if not os.path.exists(self.metadata_path):
                return

            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Restore statistics
            if 'stats' in data:
                stats_data = data['stats']
                self.stats = CacheStats(
                    hits=stats_data.get('hits', 0),
                    misses=stats_data.get('misses', 0),
                    evictions=stats_data.get('evictions', 0),
                    total_accesses=stats_data.get('total_accesses', 0),
                    total_loaded_bytes=stats_data.get('total_loaded_bytes', 0),
                    total_saved_bytes=stats_data.get('total_saved_bytes', 0)
                )

        except Exception as e:
            print(f"Warning: Failed to load cache metadata: {e}")

    def _save_metadata(self) -> None:
        """Save cache metadata to persistent storage."""
        try:
            metadata = {
                'created_at': datetime.now().isoformat(),
                'stats': {
                    'hits': self.stats.hits,
                    'misses': self.stats.misses,
                    'evictions': self.stats.evictions,
                    'total_accesses': self.stats.total_accesses,
                    'total_loaded_bytes': self.stats.total_loaded_bytes,
                    'total_saved_bytes': self.stats.total_saved_bytes,
                    'current_size_bytes': self._current_size_bytes,
                    'current_count': len(self._cache)
                }
            }

            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

        except Exception as e:
            print(f"Warning: Failed to save cache metadata: {e}")


# ============================================================================
# Convenience Functions
# ============================================================================

def create_default_cache(**kwargs) -> DocumentCache:
    """
    Create a DocumentCache with default settings.

    Args:
        **kwargs: Arguments passed to DocumentCache constructor

    Returns:
        DocumentCache instance with default configuration

    Example:
        >>> cache = create_default_cache(max_size_mb=200)
        >>> result = cache.get("document.txt")
    """
    defaults = {
        'max_size_mb': 100,
        'max_documents': 1000,
        'enable_stats': True,
        'enable_warming': True
    }
    defaults.update(kwargs)
    return DocumentCache(**defaults)


# ============================================================================
# End of document_cache.py
# ============================================================================
