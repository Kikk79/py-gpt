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
Document Processing Service - Core Service Layer (C3)

This module provides a unified service layer that orchestrates document loading,
caching, threading, and metadata management. It connects the UI layer with the
underlying document processor and provides a clean async API.

Responsibilities:
- Manage document loader registry and selection
- Coordinate file loader threading for async operations
- Provide metadata caching and retrieval
- Generate previews for UI display
- Handle batch processing operations
- Emit progress and status signals
"""

from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, Iterator, Union
from concurrent.futures import Future, ThreadPoolExecutor
import threading
import time

from src.pygpt_net.core.document_processor import (
    UnifiedDocumentLoader,
    LoaderRegistry,
    LoadResult,
    LoadProgress,
    LoadError,
    ErrorSeverity,
    DocumentMetadata,
    create_default_registry,
)
from src.pygpt_net.ui.widget.file_loader_thread import FileLoaderManager


class DocumentProcessingService:
    """
    Central service for document loading, caching, and processing operations.

    This service provides:
    - Automatic loader selection based on file type
    - Asynchronous loading with progress tracking
    - Metadata caching for performance
    - Preview generation for UI display
    - Batch processing capabilities
    - Thread-safe operations

    Example:
        >>> service = DocumentProcessingService()
        >>> service.load_async("document.pdf", on_progress=update_ui)
        >>> preview = service.get_preview("large_file.txt", max_lines=50)
        >>> metadata = service.get_metadata("data.csv")
    """

    def __init__(
        self,
        max_workers: int = 4,
        cache_size: int = 500,
        preview_max_size: int = 1024 * 1024,  # 1MB preview limit
    ):
        """
        Initialize document processing service.

        Args:
            max_workers: Maximum number of thread pool workers
            cache_size: Maximum metadata cache size
            preview_max_size: Maximum size for preview content (bytes)
        """
        self.max_workers = max_workers
        self.preview_max_size = preview_max_size

        # Document loader registry
        self._registry: LoaderRegistry = create_default_registry()

        # Thread pool for async operations
        self._executor: ThreadPoolExecutor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="DocumentLoader"
        )

        # File loader manager for Qt integration
        self._file_loader_manager: FileLoaderManager = FileLoaderManager()

        # Metadata cache
        self._metadata_cache: Dict[str, DocumentMetadata] = {}
        self._cache_lock = threading.Lock()
        self._cache_size = cache_size
        self._access_order: List[str] = []  # For LRU eviction

        # Active loading operations
        self._active_loads: Dict[str, Future] = {}
        self._active_lock = threading.Lock()

    def load_async(
        self,
        source: str,
        on_progress: Optional[Callable[[LoadProgress], None]] = None,
        on_complete: Optional[Callable[[LoadResult], None]] = None,
        on_error: Optional[Callable[[LoadError], None]] = None,
    ) -> str:
        """
        Load document asynchronously in background thread.

        Args:
            source: Path or URL to document
            on_progress: Callback for progress updates
            on_complete: Callback for completion (with LoadResult)
            on_error: Callback for errors

        Returns:
            Operation ID for tracking/cancellation

        Example:
            >>> def handle_progress(progress):
            ...     ui.update_progress(progress.percentage)
            >>>
            >>> def handle_complete(result):
            ...     ui.display_content(result.content)
            >>>
            >>> op_id = service.load_async("document.pdf",
            ...                              on_progress=handle_progress,
            ...                              on_complete=handle_complete)
        """
        operation_id = f"load_{source}_{time.time()}"

        def load_task():
            """Wrapper for async loading with callbacks."""
            try:
                # Get appropriate loader
                loader = self._registry.get_loader(source)
                if not loader:
                    error = LoadError(
                        severity=ErrorSeverity.ERROR,
                        message=f"No loader available for: {source}",
                        error_code="NO_LOADER",
                        source=source
                    )
                    if on_error:
                        on_error(error)
                    return LoadResult(success=False, errors=[error])

                # Set progress callback if provided
                if on_progress:
                    loader.set_progress_callback(on_progress)

                # Load document
                result = loader.load_complete(source)

                # Cache metadata if successful
                if result.success and result.metadata:
                    self._cache_metadata(source, result.metadata)

                # Call completion callback
                if on_complete:
                    on_complete(result)

                return result

            except Exception as e:
                error = LoadError(
                    severity=ErrorSeverity.ERROR,
                    message=f"Loading failed: {str(e)}",
                    error_code="LOAD_EXCEPTION",
                    source=source,
                    exception=e
                )
                if on_error:
                    on_error(error)
                return LoadResult(success=False, errors=[error])

            finally:
                # Cleanup from active loads
                with self._active_lock:
                    self._active_loads.pop(operation_id, None)

        # Submit to thread pool
        future = self._executor.submit(load_task)

        # Track active operation
        with self._active_lock:
            self._active_loads[operation_id] = future

        return operation_id

    def load_sync(self, source: str) -> LoadResult:
        """
        Load document synchronously (blocking).

        WARNING: This blocks the calling thread. Use load_async() for UI operations.

        Args:
            source: Path or URL to document

        Returns:
            LoadResult with content and metadata

        Example:
            >>> result = service.load_sync("config.json")
            >>> if result.success:
            ...     config = json.loads("".join(result.content))
        """
        loader = self._registry.get_loader(source)
        if not loader:
            error = LoadError(
                severity=ErrorSeverity.ERROR,
                message=f"No loader available for: {source}",
                error_code="NO_LOADER",
                source=source
            )
            return LoadResult(success=False, errors=[error])

        result = loader.load_complete(source)

        # Cache metadata if successful
        if result.success and result.metadata:
            self._cache_metadata(source, result.metadata)

        return result

    def get_preview(self, source: str, max_lines: int = 50) -> Optional[str]:
        """
        Get preview content for a document.

        Loads only enough content for preview display, optimized for UI previews.

        Args:
            source: Path or URL to document
            max_lines: Maximum lines to load (default: 50)

        Returns:
            Preview text or None if cannot load

        Example:
            >>> preview = service.get_preview("large_log_file.log", max_lines=100)
            >>> ui.set_preview_text(preview)
        """
        # Check cache first
        cached = self._get_cached_content(source, max_lines)
        if cached:
            return cached

        loader = self._registry.get_loader(source)
        if not loader:
            return None

        # Store original chunk size
        original_chunk_size = loader.chunk_size

        try:
            # Adjust chunk size for preview (smaller = faster)
            loader.chunk_size = min(original_chunk_size, 4096)

            preview_chunks = []
            line_count = 0

            # Stream chunks until we have enough lines
            for chunk in loader.load_stream(source):
                preview_chunks.append(chunk)
                line_count += chunk.count("\n")

                if line_count >= max_lines:
                    break

                # Stop if we exceed preview size limit
                total_size = sum(len(c.encode()) for c in preview_chunks)
                if total_size > self.preview_max_size:
                    break

            # Cache the preview
            preview_text = "".join(preview_chunks)
            self._cache_preview_content(source, preview_text, max_lines)

            return preview_text

        finally:
            # Restore original chunk size
            loader.chunk_size = original_chunk_size

    def get_metadata(self, source: str, force_refresh: bool = False) -> Optional[DocumentMetadata]:
        """
        Get metadata for a document.

        Checks cache first, then loads if not cached or force_refresh=True.

        Args:
            source: Path or URL to document
            force_refresh: Force reload from source

        Returns:
            DocumentMetadata or None if cannot load

        Example:
            >>> metadata = service.get_metadata("presentation.pdf")
            >>> print(f"Pages: {metadata.page_count}, Size: {metadata.size_bytes}")
        """
        if not force_refresh:
            cached = self._get_cached_metadata(source)
            if cached:
                return cached

        loader = self._registry.get_loader(source)
        if not loader:
            return None

        try:
            metadata = loader._extract_metadata(source)
            self._cache_metadata(source, metadata)
            return metadata
        except Exception:
            return None

    def get_file_info(self, source: str) -> Optional[Dict[str, Any]]:
        """
        Get simplified file information for display.

        Combines metadata with display-friendly formatting.

        Args:
            source: Path or URL to document

        Returns:
            Dict with formatted info for UI display

        Example:
            >>> info = service.get_file_info("report.pdf")
            >>> ui.set_title(info["name"])
            >>> ui.set_size(info["formatted_size"])
        """
        if not Path(source).exists():
            return None

        metadata = self.get_metadata(source)
        if not metadata:
            return None

        path = Path(source)

        return {
            "name": path.name,
            "path": str(source),
            "size": metadata.size_bytes,
            "formatted_size": self._format_size(metadata.size_bytes),
            "type": metadata.mime_type or self._get_file_type(source),
            "modified": (
                metadata.modified_at.timestamp()
                if metadata.modified_at
                else path.stat().st_mtime
            ),
            "indexed_in": [],  # Would come from index system
        }

    def cancel_load(self, operation_id: str) -> bool:
        """
        Cancel an active loading operation.

        Args:
            operation_id: Operation ID from load_async()

        Returns:
            True if operation was cancelled, False if not found/completed
        """
        with self._active_lock:
            future = self._active_loads.get(operation_id)
            if future and not future.done():
                cancelled = future.cancel()
                if cancelled:
                    self._active_loads.pop(operation_id, None)
                return cancelled
        return False

    def cancel_all_loads(self) -> int:
        """
        Cancel all active loading operations.

        Returns:
            Number of operations cancelled
        """
        cancelled_count = 0
        with self._active_lock:
            operation_ids = list(self._active_loads.keys())
            for op_id in operation_ids:
                if self.cancel_load(op_id):
                    cancelled_count += 1
        return cancelled_count

    def get_active_operations(self) -> List[str]:
        """
        Get list of active operation IDs.

        Returns:
            List of operation IDs
        """
        with self._active_lock:
            return list(self._active_loads.keys())

    def is_loading(self, source: str) -> bool:
        """
        Check if a document is currently being loaded.

        Args:
            source: Document path or URL

        Returns:
            True if currently loading
        """
        with self._active_lock:
            for operation_id, future in self._active_loads.items():
                if source in operation_id and not future.done():
                    return True
        return False

    def register_loader(self, loader: UnifiedDocumentLoader) -> None:
        """
        Register a custom document loader.

        Args:
            loader: Loader instance to register

        Example:
            >>> custom_loader = CustomDocumentLoader()
            >>> service.register_loader(custom_loader)
        """
        self._registry.register(loader)

    def get_supported_types(self) -> List[str]:
        """
        Get list of supported document types.

        Returns:
            List of file extensions and type descriptions
        """
        types = self._registry.get_supported_types()
        return [t.value for t in types]

    def can_handle(self, source: str) -> bool:
        """
        Check if a document can be loaded.

        Args:
            source: Path or URL to check

        Returns:
            True if a loader is available
        """
        return self._registry.get_loader(source) is not None

    def clear_cache(self) -> None:
        """Clear all cached metadata and preview content."""
        with self._cache_lock:
            self._metadata_cache.clear()
            self._access_order.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache size, hit rate, and metadata
        """
        with self._cache_lock:
            return {
                "metadata_cache_size": len(self._metadata_cache),
                "metadata_cache_entries": len(self._access_order),
                "max_cache_size": self._cache_size,
                "active_operations": len(self._active_loads),
                "supported_types": len(self.get_supported_types()),
            }

    def shutdown(self) -> None:
        """Shutdown the service and cleanup resources."""
        # Cancel all active operations
        self.cancel_all_loads()

        # Shutdown thread pool
        self._executor.shutdown(wait=True)

        # Clear cache
        self.clear_cache()

    # =======================================================================
    # Protected methods
    # =======================================================================

    def _cache_metadata(self, source: str, metadata: DocumentMetadata) -> None:
        """Cache document metadata with LRU eviction."""
        with self._cache_lock:
            # Remove if exists (update position)
            if source in self._metadata_cache:
                self._access_order.remove(source)

            # Add/update cache
            self._metadata_cache[source] = metadata
            self._access_order.append(source)

            # Evict oldest if over limit
            if len(self._metadata_cache) > self._cache_size:
                oldest = self._access_order.pop(0)
                self._metadata_cache.pop(oldest, None)

    def _get_cached_metadata(self, source: str) -> Optional[DocumentMetadata]:
        """Get cached metadata and update access order."""
        with self._cache_lock:
            metadata = self._metadata_cache.get(source)
            if metadata:
                # Update access order (move to end)
                if source in self._access_order:
                    self._access_order.remove(source)
                self._access_order.append(source)
            return metadata

    def _cache_preview_content(self, source: str, content: str, max_lines: int) -> None:
        """Cache preview content (simplified - full implementation would use separate cache)."""
        # In a full implementation, this would use a separate LRU cache for preview content
        # For now, we rely on the metadata cache
        pass

    def _get_cached_content(self, source: str, max_lines: int) -> Optional[str]:
        """Get cached preview content."""
        # Simplified implementation - in production would check preview cache
        return None

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes == 0:
            return "0 B"

        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(size_bytes)
        unit_index = 0

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}"

    @staticmethod
    def _get_file_type(source: str) -> str:
        """Get file type from extension."""
        ext = Path(source).suffix.lower()
        type_map = {
            ".txt": "Text Document",
            ".md": "Markdown Document",
            ".pdf": "PDF Document",
            ".csv": "CSV File",
            ".json": "JSON File",
            ".xml": "XML File",
            ".py": "Python Script",
            ".docx": "Word Document",
            ".xlsx": "Excel Spreadsheet",
        }
        return type_map.get(ext, "Unknown")


# Global service instance
_default_service: Optional[DocumentProcessingService] = None
_service_lock = threading.Lock()


def get_document_processing_service() -> DocumentProcessingService:
    """
    Get global document processing service instance.

    Returns:
        DocumentProcessingService singleton instance

    Example:
        >>> service = get_document_processing_service()
        >>> service.load_async("document.pdf", on_complete=handle_load)
    """
    global _default_service

    if _default_service is None:
        with _service_lock:
            if _default_service is None:
                _default_service = DocumentProcessingService()

    return _default_service


def reset_document_processing_service() -> None:
    """Reset the global service instance (useful for testing)."""
    global _default_service
    with _service_lock:
        if _default_service:
            _default_service.shutdown()
        _default_service = None


# ============================================================================
# End of document_processing_service.py
# ============================================================================
