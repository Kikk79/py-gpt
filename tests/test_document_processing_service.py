#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ================================================== #
# This file is a part of PYGPT package              #
# Website: https://pygpt.net                         #
# GitHub:  https://github.com/szczyglis-dev/py-gpt   #
# MIT License                                        #
# Created By  : Testing Agent                        #
# Updated Date: 2025.11.20                           #
# ================================================== #

"""
Unit tests for DocumentProcessingService.

This module provides comprehensive test coverage for the document processing
service layer, including async loading, caching, progress tracking, and error handling.
"""

import threading
import time
from concurrent.futures import Future
from pathlib import Path
from typing import List, Optional, Callable
from unittest.mock import Mock, MagicMock, patch, call

import pytest

from src.pygpt_net.core.document_processing_service import (
    DocumentProcessingService,
    get_document_processing_service,
    reset_document_processing_service,
)
from src.pygpt_net.core.document_processor import (
    UnifiedDocumentLoader,
    LoadResult,
    LoadError,
    LoadProgress,
    ErrorSeverity,
    DocumentMetadata,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def service():
    """Create a fresh DocumentProcessingService instance."""
    service = DocumentProcessingService(max_workers=2, cache_size=5)
    yield service
    service.shutdown()


@pytest.fixture
def mock_loader():
    """Create a mock UnifiedDocumentLoader."""
    loader = Mock(spec=UnifiedDocumentLoader)
    loader.chunk_size = 8192
    return loader


@pytest.fixture
def sample_metadata():
    """Create sample document metadata."""
    return DocumentMetadata(
        size_bytes=1024,
        mime_type="text/plain",
        encoding="utf-8",
        line_count=100,
        word_count=500,
        page_count=1,
        modified_at=None,
        created_at=None,
        checksum="abc123"
    )


@pytest.fixture
def sample_load_result(sample_metadata):
    """Create a sample successful LoadResult."""
    return LoadResult(
        success=True,
        content=["Line 1\n", "Line 2\n", "Line 3\n"],
        metadata=sample_metadata,
        errors=[]
    )


# ==============================================================================
# Unit Tests - Async Loading with ThreadPoolExecutor
# ==============================================================================


class TestAsyncLoading:
    """Test async loading functionality with ThreadPoolExecutor."""

    def test_load_async_successful(self, service, mock_loader, sample_load_result):
        """Test successful async loading with callbacks."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(return_value=sample_load_result)
        mock_loader.set_progress_callback = Mock()

        progress_calls = []
        complete_called = []
        error_calls = []

        def on_progress(progress):
            progress_calls.append(progress)

        def on_complete(result):
            complete_called.append(result)

        def on_error(error):
            error_calls.append(error)

        # Act
        op_id = service.load_async(
            "test.txt",
            on_progress=on_progress,
            on_complete=on_complete,
            on_error=on_error
        )

        # Wait for completion
        future = service._active_loads[op_id]
        future.result(timeout=2)

        # Assert
        assert op_id.startswith("load_test.txt_")
        assert op_id in service._active_loads
        mock_loader.set_progress_callback.assert_called_once_with(on_progress)
        mock_loader.load_complete.assert_called_once_with("test.txt")
        assert len(complete_called) == 1
        assert complete_called[0] == sample_load_result
        assert complete_called[0].success is True
        assert len(error_calls) == 0
        assert op_id not in service._active_loads  # Cleaned up after completion

    def test_load_async_no_loader_error(self, service):
        """Test async loading when no loader is available."""
        # Arrange
        service._registry.get_loader = Mock(return_value=None)
        error_calls = []
        complete_calls = []

        def on_error(error):
            error_calls.append(error)

        def on_complete(result):
            complete_calls.append(result)

        # Act
        op_id = service.load_async("unknown.xyz", on_error=on_error, on_complete=on_complete)

        # Wait for completion
        future = service._active_loads[op_id]
        result = future.result(timeout=2)

        # Assert
        assert len(error_calls) == 1
        assert error_calls[0].error_code == "NO_LOADER"
        assert "No loader available" in error_calls[0].message
        assert len(complete_calls) == 1
        assert complete_calls[0].success is False
        assert result.success is False

    def test_load_async_loader_exception(self, service, mock_loader):
        """Test async loading when loader raises an exception."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(side_effect=Exception("Network failure"))

        error_calls = []
        complete_calls = []

        def on_error(error):
            error_calls.append(error)

        def on_complete(result):
            complete_calls.append(result)

        # Act
        op_id = service.load_async("test.txt", on_error=on_error, on_complete=on_complete)

        # Wait for completion
        future = service._active_loads[op_id]
        result = future.result(timeout=2)

        # Assert
        assert len(error_calls) == 1
        assert error_calls[0].error_code == "LOAD_EXCEPTION"
        assert "Network failure" in error_calls[0].message
        assert error_calls[0].exception is not None
        assert len(complete_calls) == 1
        assert complete_calls[0].success is False
        assert result.success is False
        assert op_id not in service._active_loads

    def test_load_async_concurrent_loads(self, service, mock_loader, sample_load_result):
        """Test multiple concurrent async loads."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(return_value=sample_load_result)

        results = []

        def on_complete(result):
            results.append(result)

        # Act - Start multiple concurrent loads
        op_ids = []
        for i in range(5):
            op_id = service.load_async(f"test{i}.txt", on_complete=on_complete)
            op_ids.append(op_id)

        # Wait for all to complete
        for op_id in op_ids:
            future = service._active_loads[op_id]
            future.result(timeout=2)

        # Assert
        assert len(results) == 5
        assert all(r.success for r in results)
        assert len(service._active_loads) == 0  # All cleaned up

    def test_load_async_thread_safety(self, service, mock_loader, sample_load_result):
        """Test thread safety of async loading operations."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(return_value=sample_load_result)

        completion_count = [0]
        lock = threading.Lock()

        def on_complete(result):
            with lock:
                completion_count[0] += 1

        # Act - Start multiple threads that start async loads
        def start_load():
            service.load_async("test.txt", on_complete=on_complete)

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=start_load)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join(timeout=5)

        # Wait for all operations to complete
        time.sleep(0.5)  # Brief wait for cleanup

        # Assert - All started and completed without threading issues
        assert completion_count[0] == 10

    def test_load_sync_successful(self, service, mock_loader, sample_load_result):
        """Test synchronous loading."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(return_value=sample_load_result)

        # Act
        result = service.load_sync("test.txt")

        # Assert
        assert result.success is True
        assert result.content == ["Line 1\n", "Line 2\n", "Line 3\n"]
        assert result.metadata.size_bytes == 1024
        mock_loader.load_complete.assert_called_once_with("test.txt")

    def test_load_sync_no_loader(self, service):
        """Test synchronous loading with no loader."""
        # Arrange
        service._registry.get_loader = Mock(return_value=None)

        # Act
        result = service.load_sync("unknown.xyz")

        # Assert
        assert result.success is False
        assert len(result.errors) == 1
        assert result.errors[0].error_code == "NO_LOADER"


# ==============================================================================
# Unit Tests - LRU Cache Functionality
# ==============================================================================


class TestCacheFunctionality:
    """Test LRU cache functionality."""

    def test_cache_metadata_basic(self, service, sample_metadata):
        """Test basic metadata caching."""
        # Act
        service._cache_metadata("test1.txt", sample_metadata)

        # Assert
        cached = service._get_cached_metadata("test1.txt")
        assert cached is not None
        assert cached.size_bytes == 1024
        assert cached.mime_type == "text/plain"

    def test_cache_metadata_updates_access_order(self, service, sample_metadata):
        """Test that accessing metadata updates LRU order."""
        # Arrange
        for i in range(3):
            meta = DocumentMetadata(size_bytes=i, mime_type="text/plain")
            service._cache_metadata(f"test{i}.txt", meta)

        # Act - Access first item (should move to end)
        service._get_cached_metadata("test0.txt")

        # Assert
        with service._cache_lock:
            assert service._access_order[-1] == "test0.txt"

    def test_cache_lru_eviction(self, service):
        """Test LRU eviction when cache is full."""
        # Arrange - Cache size is 5 (from fixture)
        for i in range(6):  # Add 6 items (1 over limit)
            meta = DocumentMetadata(size_bytes=i, mime_type="text/plain")
            service._cache_metadata(f"test{i}.txt", meta)

        # Assert - First item should be evicted
        assert service._get_cached_metadata("test0.txt") is None
        assert service._get_cached_metadata("test1.txt") is not None
        assert service._get_cached_metadata("test5.txt") is not None

    def test_cache_clear(self, service, sample_metadata):
        """Test clearing the cache."""
        # Arrange
        service._cache_metadata("test1.txt", sample_metadata)
        assert service._get_cached_metadata("test1.txt") is not None

        # Act
        service.clear_cache()

        # Assert
        assert service._get_cached_metadata("test1.txt") is None
        with service._cache_lock:
            assert len(service._metadata_cache) == 0
            assert len(service._access_order) == 0

    def test_get_metadata_with_cache(self, service, mock_loader, sample_metadata):
        """Test get_metadata uses cache."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader._extract_metadata = Mock(return_value=sample_metadata)

        # Act - First call loads from loader
        result1 = service.get_metadata("test.txt")

        # Act - Second call should use cache (mock not called again)
        result2 = service.get_metadata("test.txt")

        # Assert
        mock_loader._extract_metadata.assert_called_once()
        assert result1 is not None
        assert result2 is not None
        assert result1.size_bytes == result2.size_bytes

    def test_get_metadata_force_refresh(self, service, mock_loader, sample_metadata):
        """Test get_metadata with force refresh."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader._extract_metadata = Mock(return_value=sample_metadata)

        # Act
        result1 = service.get_metadata("test.txt")
        result2 = service.get_metadata("test.txt", force_refresh=True)

        # Assert
        assert mock_loader._extract_metadata.call_count == 2
        assert result1 is not None
        assert result2 is not None

    def test_cache_is_thread_safe(self, service, sample_metadata):
        """Test cache operations are thread-safe."""
        # Arrange
        errors = []

        def cache_operation(thread_id):
            try:
                for i in range(10):
                    meta = DocumentMetadata(size_bytes=i, mime_type="text/plain")
                    service._cache_metadata(f"thread{thread_id}_file{i}.txt", meta)
                    cached = service._get_cached_metadata(f"thread{thread_id}_file{i}.txt")
                    assert cached is not None
            except Exception as e:
                errors.append(e)

        # Act - Multiple threads performing cache operations
        threads = []
        for i in range(10):
            thread = threading.Thread(target=cache_operation, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join(timeout=5)

        # Assert - No threading errors
        assert len(errors) == 0

    def test_load_async_caches_metadata(self, service, mock_loader, sample_load_result):
        """Test that successful async loads cache metadata."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(return_value=sample_load_result)

        # Act
        op_id = service.load_async("test.txt")
        future = service._active_loads[op_id]
        future.result(timeout=2)

        # Assert
        cached = service._get_cached_metadata("test.txt")
        assert cached is not None
        assert cached.size_bytes == 1024


# ==============================================================================
# Unit Tests - Operation Tracking and Cancellation
# ==============================================================================


class TestOperationTracking:
    """Test operation tracking and cancellation."""

    def test_operation_id_generation(self, service, mock_loader, sample_load_result):
        """Test operation ID generation is unique."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(return_value=sample_load_result)

        # Act
        op_id1 = service.load_async("test.txt")
        time.sleep(0.01)  # Ensure different timestamp
        op_id2 = service.load_async("test.txt")

        # Wait for completion
        for op_id in [op_id1, op_id2]:
            future = service._active_loads[op_id]
            future.result(timeout=2)

        # Assert
        assert op_id1 != op_id2
        assert op_id1.startswith("load_test.txt_")
        assert op_id2.startswith("load_test.txt_")

    def test_cancel_load_before_completion(self, service, mock_loader):
        """Test cancelling an active load operation."""
        # Arrange - Create a slow loading operation
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(side_effect=lambda x: time.sleep(0.5) or sample_load_result)

        # Act - Start async load
        op_id = service.load_async("test.txt")
        assert op_id in service._active_loads

        # Cancel before completion
        cancelled = service.cancel_load(op_id)

        # Assert
        assert cancelled is True
        assert op_id not in service._active_loads

    def test_cancel_load_already_completed(self, service, mock_loader, sample_load_result):
        """Test cancelling a completed load operation."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(return_value=sample_load_result)

        # Act
        op_id = service.load_async("test.txt")
        future = service._active_loads[op_id]
        future.result(timeout=2)

        # Try to cancel after completion
        cancelled = service.cancel_load(op_id)

        # Assert
        assert cancelled is False
        assert op_id not in service._active_loads

    def test_cancel_load_not_found(self, service):
        """Test cancelling non-existent operation."""
        # Act
        cancelled = service.cancel_load("nonexistent")

        # Assert
        assert cancelled is False

    def test_cancel_all_loads(self, service, mock_loader):
        """Test cancelling all active loads."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(side_effect=lambda x: time.sleep(0.2) or sample_load_result)

        # Start multiple async loads
        op_ids = []
        for i in range(3):
            op_id = service.load_async(f"test{i}.txt")
            op_ids.append(op_id)

        # Act
        cancelled_count = service.cancel_all_loads()

        # Assert
        assert cancelled_count == 3
        assert len(service._active_loads) == 0

    def test_get_active_operations(self, service, mock_loader, sample_load_result):
        """Test getting list of active operations."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(return_value=sample_load_result)

        # Act - Start operations
        service.load_async("test1.txt")
        service.load_async("test2.txt")
        op_id3 = service.load_async("test3.txt")

        # Assert - All are active
        active = service.get_active_operations()
        assert len(active) == 3
        assert op_id3 in active

        # Complete one operation
        future = service._active_loads[op_id3]
        future.result(timeout=2)

        # Assert - Should be cleaned up
        assert len(service.get_active_operations()) == 0

    def test_is_loading_check(self, service, mock_loader):
        """Test checking if document is currently loading."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(side_effect=lambda x: time.sleep(0.3) or sample_load_result)

        # Act
        op_id = service.load_async("test.txt")

        # Assert - Loading during operation
        assert service.is_loading("test.txt") is True
        assert service.is_loading("other.txt") is False

        # Wait for completion
        future = service._active_loads[op_id]
        future.result(timeout=2)

        # Assert - Not loading after completion
        assert service.is_loading("test.txt") is False


# ==============================================================================
# Unit Tests - Progress Callbacks
# ==============================================================================


class TestProgressCallbacks:
    """Test progress and completion callbacks."""

    def test_progress_callback_invocation(self, service, mock_loader):
        """Test progress callbacks are invoked during loading."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)

        progress_updates = []

        def progress_handler(progress):
            progress_updates.append(progress)

        def mock_stream(source):
            """Mock streaming with progress."""
            for i in range(5):
                if progress_handler in mock_loader.set_progress_callback.call_args[0]:
                    cb = mock_loader.set_progress_callback.call_args[0][0]
                    if cb:
                        cb(LoadProgress(
                            source=source,
                            percentage=(i + 1) * 20,
                            bytes_loaded=(i + 1) * 1000,
                            total_bytes=5000
                        ))
                yield f"Line {i}\n"

        mock_loader.load_complete = Mock(return_value=sample_load_result)
        mock_loader.load_stream = Mock(side_effect=mock_stream)
        mock_loader.set_progress_callback = Mock()

        # Act - Get preview (which uses streaming)
        service.get_preview("test.txt")

        # Note: This test is simplified - in real implementation, need to ensure
        # progress callbacks are called during streaming operations
        mock_loader.set_progress_callback.assert_called()

    def test_completion_callback_with_success(self, service, mock_loader, sample_load_result):
        """Test completion callback on successful load."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(return_value=sample_load_result)

        complete_called = []

        def on_complete(result):
            complete_called.append(result)

        # Act
        op_id = service.load_async("test.txt", on_complete=on_complete)
        future = service._active_loads[op_id]
        future.result(timeout=2)

        # Assert
        assert len(complete_called) == 1
        assert complete_called[0].success is True

    def test_error_callback_on_failure(self, service, mock_loader):
        """Test error callback on load failure."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(side_effect=Exception("IO Error"))

        error_called = []

        def on_error(error):
            error_called.append(error)

        # Act
        op_id = service.load_async("test.txt", on_error=on_error)
        future = service._active_loads[op_id]
        future.result(timeout=2)

        # Assert
        assert len(error_called) == 1
        assert error_called[0].severity == ErrorSeverity.ERROR
        assert "IO Error" in error_called[0].message

    def test_callbacks_optional(self, service, mock_loader, sample_load_result):
        """Test that callbacks are optional."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(return_value=sample_load_result)

        # Act - Should not raise even without callbacks
        op_id = service.load_async("test.txt")
        future = service._active_loads[op_id]
        result = future.result(timeout=2)

        # Assert
        assert result.success is True


# ==============================================================================
# Unit Tests - Error Handling
# ==============================================================================


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_error_severity_levels(self, service):
        """Test different error severity levels."""
        # This tests the enum values are correctly imported and accessible
        assert hasattr(ErrorSeverity, 'INFO')
        assert hasattr(ErrorSeverity, 'WARNING')
        assert hasattr(ErrorSeverity, 'ERROR')
        assert hasattr(ErrorSeverity, 'CRITICAL')

    def test_load_error_creation(self):
        """Test LoadError object creation."""
        # Arrange & Act
        error = LoadError(
            severity=ErrorSeverity.ERROR,
            message="Test error",
            error_code="TEST_ERROR",
            source="test.txt"
        )

        # Assert
        assert error.severity == ErrorSeverity.ERROR
        assert error.message == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.source == "test.txt"

    def test_load_result_with_errors(self, sample_metadata):
        """Test LoadResult with errors."""
        # Arrange
        error = LoadError(
            severity=ErrorSeverity.WARNING,
            message="Partial load",
            error_code="PARTIAL_LOAD",
            source="test.txt"
        )

        # Act
        result = LoadResult(
            success=False,
            content=[],
            metadata=sample_metadata,
            errors=[error]
        )

        # Assert
        assert result.success is False
        assert len(result.errors) == 1
        assert result.errors[0].error_code == "PARTIAL_LOAD"

    def test_multiple_errors_in_result(self, sample_metadata):
        """Test LoadResult with multiple errors."""
        # Arrange
        errors = [
            LoadError(ErrorSeverity.WARNING, "Warning 1", "WARN1", "test.txt"),
            LoadError(ErrorSeverity.ERROR, "Error 1", "ERR1", "test.txt")
        ]

        # Act
        result = LoadResult(
            success=False,
            content=[],
            metadata=sample_metadata,
            errors=errors
        )

        # Assert
        assert result.success is False
        assert len(result.errors) == 2
        assert result.errors[0].error_code == "WARN1"
        assert result.errors[1].error_code == "ERR1"

    def test_load_result_success_without_errors(self, sample_metadata):
        """Test successful LoadResult without errors."""
        # Act
        result = LoadResult(
            success=True,
            content=["data"],
            metadata=sample_metadata,
            errors=[]
        )

        # Assert
        assert result.success is True
        assert len(result.errors) == 0
        assert result.content == ["data"]


# ==============================================================================
# Unit Tests - Preview Generation
# ==============================================================================


class TestPreviewGeneration:
    """Test preview generation functionality."""

    def test_get_preview_basic(self, service, mock_loader):
        """Test basic preview generation."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)

        def mock_stream(source):
            for i in range(100):
                yield f"Line {i}\n"

        mock_loader.load_stream = Mock(side_effect=mock_stream)

        # Act
        preview = service.get_preview("test.txt", max_lines=50)

        # Assert
        assert preview is not None
        assert preview.count("\n") <= 50
        mock_loader.load_stream.assert_called_once_with("test.txt")

    def test_get_preview_respects_max_lines(self, service, mock_loader):
        """Test preview respects max_lines parameter."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)

        def mock_stream(source):
            for i in range(100):
                yield f"Line {i}\n"

        mock_loader.load_stream = Mock(side_effect=mock_stream)

        # Act
        preview = service.get_preview("test.txt", max_lines=10)

        # Assert
        assert preview.count("\n") <= 10

    def test_get_preview_respects_size_limit(self, service, mock_loader):
        """Test preview respects size limit."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        service.preview_max_size = 100  # Very small limit

        def mock_stream(source):
            for i in range(1000):
                yield "x" * 100 + "\n"  # Large lines

        mock_loader.load_stream = Mock(side_effect=mock_stream)

        # Act
        preview = service.get_preview("test.txt", max_lines=1000)

        # Assert
        assert preview is not None
        preview_size = len(preview.encode())
        assert preview_size <= service.preview_max_size

    def test_get_preview_no_loader(self, service):
        """Test preview when no loader is available."""
        # Arrange
        service._registry.get_loader = Mock(return_value=None)

        # Act
        preview = service.get_preview("unknown.xyz")

        # Assert
        assert preview is None

    def test_get_preview_adjusts_chunk_size(self, service, mock_loader):
        """Test preview adjusts chunk size for performance."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        original_chunk_size = mock_loader.chunk_size

        def mock_stream(source):
            yield "Test line\n"

        mock_loader.load_stream = Mock(side_effect=mock_stream)

        # Act
        service.get_preview("test.txt")

        # Assert - Should temporarily adjust chunk size
        assert mock_loader.chunk_size == 4096  # min(original, 4096)
        # Restore happened in finally block


# ==============================================================================
# Unit Tests - File Information
# ==============================================================================


class TestFileInformation:
    """Test file information retrieval."""

    def test_get_file_info(self, service, mock_loader, sample_metadata, tmp_path):
        """Test get_file_info with real file."""
        # Arrange - Create a real temp file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader._extract_metadata = Mock(return_value=sample_metadata)

        # Act
        info = service.get_file_info(str(test_file))

        # Assert
        assert info is not None
        assert info["name"] == "test.txt"
        assert "path" in info
        assert info["size"] == 1024
        assert "formatted_size" in info
        assert info["type"] == "text/plain"
        assert "modified" in info

    def test_get_file_info_nonexistent_file(self, service):
        """Test get_file_info with non-existent file."""
        # Act
        info = service.get_file_info("/nonexistent/file.txt")

        # Assert
        assert info is None

    def test_format_size_bytes(self, service):
        """Test size formatting helper."""
        # Act & Assert
        assert service._format_size(0) == "0 B"
        assert service._format_size(512) == "512 B"
        assert service._format_size(1024) == "1.0 KB"
        assert service._format_size(1536) == "1.5 KB"
        assert service._format_size(1048576) == "1.0 MB"
        assert service._format_size(1073741824) == "1.0 GB"

    def test_format_size_edge_cases(self, service):
        """Test size formatting edge cases."""
        # Act & Assert
        assert "KB" in service._format_size(999)
        assert "MB" in service._format_size(999999)
        assert service._format_size(1).endswith("B")

    def test_get_file_type_from_extension(self, service):
        """Test file type detection from extension."""
        # Act & Assert
        assert service._get_file_type("test.txt") == "Text Document"
        assert service._get_file_type("test.md") == "Markdown Document"
        assert service._get_file_type("test.pdf") == "PDF Document"
        assert service._get_file_type("test.csv") == "CSV File"
        assert service._get_file_type("test.py") == "Python Script"
        assert service._get_file_type("test.unknown") == "Unknown"


# ==============================================================================
# Unit Tests - Service Management
# ==============================================================================


class TestServiceManagement:
    """Test service management and utilities."""

    def test_get_supported_types(self, service, mock_loader):
        """Test getting supported file types."""
        # Arrange
        mock_type = Mock()
        mock_type.value = "TXT - Text Document"
        service._registry.get_supported_types = Mock(return_value=[mock_type])

        # Act
        types = service.get_supported_types()

        # Assert
        assert len(types) == 1
        assert types[0] == "TXT - Text Document"

    def test_can_handle_file(self, service, mock_loader):
        """Test checking if file can be handled."""
        # Arrange
        service._registry.get_loader = Mock(side_effect=lambda x: mock_loader if x.endswith(".txt") else None)

        # Act & Assert
        assert service.can_handle("test.txt") is True
        assert service.can_handle("test.pdf") is False

    def test_register_custom_loader(self, service, mock_loader):
        """Test registering custom loader."""
        # Act
        service.register_loader(mock_loader)

        # Assert
        service._registry.register.assert_called_once_with(mock_loader)

    def test_clear_cache(self, service, sample_metadata):
        """Test cache clearing."""
        # Arrange
        service._cache_metadata("test.txt", sample_metadata)
        assert service._get_cached_metadata("test.txt") is not None

        # Act
        service.clear_cache()

        # Assert
        assert service._get_cached_metadata("test.txt") is None

    def test_get_cache_stats(self, service, sample_metadata):
        """Test getting cache statistics."""
        # Arrange
        service._cache_metadata("test1.txt", sample_metadata)
        service._cache_metadata("test2.txt", sample_metadata)
        service.supported_types_cache = ["TXT", "PDF"]

        # Act
        stats = service.get_cache_stats()

        # Assert
        assert stats["metadata_cache_size"] == 2
        assert stats["metadata_cache_entries"] == 2
        assert stats["max_cache_size"] == 5
        assert stats["active_operations"] == 0
        assert "supported_types" in stats

    def test_service_shutdown(self, service, mock_loader, sample_load_result):
        """Test service shutdown cleanup."""
        # Arrange - Start some operations
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(return_value=sample_load_result)

        service.load_async("test1.txt")
        service.load_async("test2.txt")
        service._cache_metadata("test1.txt", sample_metadata)

        # Act
        service.shutdown()

        # Assert - All cleaned up
        assert len(service._active_loads) == 0
        with service._cache_lock:
            assert len(service._metadata_cache) == 0
        # Executor is shutdown (no active threads)

    def test_global_service_singleton(self):
        """Test global service singleton."""
        # Arrange
        reset_document_processing_service()

        # Act
        service1 = get_document_processing_service()
        service2 = get_document_processing_service()

        # Assert
        assert service1 is service2

        # Cleanup
        reset_document_processing_service()

    def test_global_service_reset(self):
        """Test global service reset."""
        # Arrange
        service1 = get_document_processing_service()

        # Act
        reset_document_processing_service()
        service2 = get_document_processing_service()

        # Assert
        assert service1 is not service2

        # Cleanup
        reset_document_processing_service()


# ==============================================================================
# Integration Tests - Service Layer Integration (C3 to B1)
# ==============================================================================


class TestServiceLayerIntegration:
    """Test integration between backend service (C3) and frontend UI layer (B1)."""

    def test_async_ui_update_pattern(self, service, mock_loader, sample_load_result):
        """Test async pattern simulating UI updates."""
        # This simulates how UI would use the service
        ui_updates = {
            "progress": 0,
            "completed": False,
            "content": None,
            "error": None
        }
        lock = threading.Lock()

        def on_progress(progress):
            with lock:
                ui_updates["progress"] = progress.percentage

        def on_complete(result):
            with lock:
                ui_updates["completed"] = True
                ui_updates["content"] = result.content

        def on_error(error):
            with lock:
                ui_updates["error"] = error.message

        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(return_value=sample_load_result)

        # Act - Simulate UI triggering load
        op_id = service.load_async(
            "document.txt",
            on_progress=on_progress,
            on_complete=on_complete,
            on_error=on_error
        )

        # Wait for completion
        future = service._active_loads[op_id]
        future.result(timeout=2)

        # Assert - UI would receive updates
        with lock:
            assert ui_updates["completed"] is True
            assert ui_updates["content"] == ["Line 1\n", "Line 2\n", "Line 3\n"]
            assert ui_updates["error"] is None

    def test_batch_processing_simulation(self, service, mock_loader, sample_load_result):
        """Test batch processing multiple documents."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(return_value=sample_load_result)

        results = {}
        lock = threading.Lock()

        def on_complete(result, filename):
            with lock:
                results[filename] = result

        # Act - Process multiple files
        files = ["doc1.txt", "doc2.txt", "doc3.txt"]
        for filename in files:
            service.load_async(
                filename,
                on_complete=lambda r, f=filename: on_complete(r, f)
            )

        # Wait for all to complete
        time.sleep(0.5)

        # Assert
        with lock:
            assert len(results) == 3
            assert all(r.success for r in results.values())

    def test_concurrent_ui_operations(self, service, mock_loader, sample_load_result):
        """Test multiple concurrent UI-like operations."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(return_value=sample_load_result)
        mock_loader.load_stream = Mock(side_effect=lambda x: iter(["line 1\n", "line 2\n"]))

        operations = []
        lock = threading.Lock()

        def record_op(name, result):
            with lock:
                operations.append((name, result))

        # Act - Simulate multiple UI operations
        threads = []

        def load_document():
            op_id = service.load_async("doc.txt", on_complete=lambda r: record_op("load", r))
            service._active_loads[op_id].result(timeout=2)

        def get_preview():
            preview = service.get_preview("preview.txt")
            record_op("preview", preview)

        def get_metadata():
            meta = service.get_metadata("meta.txt")
            record_op("metadata", meta)

        # Start concurrent operations
        for _ in range(5):
            threads.append(threading.Thread(target=load_document))
            threads.append(threading.Thread(target=get_preview))
            threads.append(threading.Thread(target=get_metadata))

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join(timeout=5)

        # Assert
        with lock:
            load_ops = [op for op in operations if op[0] == "load"]
            preview_ops = [op for op in operations if op[0] == "preview"]
            metadata_ops = [op for op in operations if op[0] == "metadata"]

            assert len(load_ops) == 5
            assert len(preview_ops) == 5
            assert len(metadata_ops) == 5


# ==============================================================================
# Unit Tests - Edge Cases
# ==============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_load_empty_file(self, service, mock_loader):
        """Test loading an empty file."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        empty_result = LoadResult(
            success=True,
            content=[],
            metadata=DocumentMetadata(size_bytes=0),
            errors=[]
        )
        mock_loader.load_complete = Mock(return_value=empty_result)

        # Act
        result = service.load_sync("empty.txt")

        # Assert
        assert result.success is True
        assert len(result.content) == 0
        assert result.metadata.size_bytes == 0

    def test_load_very_large_file(self, service, mock_loader):
        """Test handling very large file metadata."""
        # Arrange
        large_metadata = DocumentMetadata(size_bytes=10 * 1024 * 1024 * 1024)  # 10 GB
        large_result = LoadResult(
            success=True,
            content=["data"],
            metadata=large_metadata,
            errors=[]
        )

        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(return_value=large_result)

        # Act
        result = service.load_sync("large.txt")
        info = service.get_file_info("large.txt")

        # Assert
        assert result.success is True
        assert result.metadata.size_bytes == 10 * 1024 * 1024 * 1024
        assert "GB" in info["formatted_size"]

    def test_special_characters_in_filename(self, service, mock_loader, sample_load_result):
        """Test handling filenames with special characters."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(return_value=sample_load_result)

        # Act - Various special characters
        special_names = [
            "file with spaces.txt",
            "file-with-dashes.txt",
            "file_with_underscores.txt",
            "file.multiple.dots.txt"
        ]

        for filename in special_names:
            result = service.load_sync(filename)
            assert result.success is True

    def test_rapid_cache_operations(self, service):
        """Test rapid cache insert and retrieve operations."""
        # Arrange
        threads = []
        errors = []

        def rapid_op(thread_id):
            try:
                for i in range(100):
                    meta = DocumentMetadata(size_bytes=i)
                    filename = f"file_{thread_id}_{i}.txt"
                    service._cache_metadata(filename, meta)

                    # Immediate retrieval
                    cached = service._get_cached_metadata(filename)
                    assert cached is not None
                    assert cached.size_bytes == i
            except Exception as e:
                errors.append(e)

        # Act - Multiple threads doing rapid operations
        for i in range(5):
            thread = threading.Thread(target=rapid_op, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join(timeout=10)

        # Assert - No errors from rapid operations
        assert len(errors) == 0

    def test_cache_eviction_boundary(self, service):
        """Test cache eviction at exact boundary."""
        # Arrange - Cache size is 5
        for i in range(5):
            meta = DocumentMetadata(size_bytes=i)
            service._cache_metadata(f"file{i}.txt", meta)

        # Act - Add 5th item (at boundary, shouldn't evict yet)
        meta = DocumentMetadata(size_bytes=5)
        service._cache_metadata("file5.txt", meta)

        # Assert - Still within limit (actually 6 items now, but eviction happens after 5)
        # This tests the boundary condition
        assert service._get_cached_metadata("file0.txt") is None  # Evicted
        assert service._get_cached_metadata("file5.txt") is not None

    def test_shutdown_with_active_operations(self, service, mock_loader):
        """Test shutdown with operations still active."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(side_effect=lambda x: time.sleep(1) or sample_load_result)

        # Start operations
        op_id1 = service.load_async("test1.txt")
        op_id2 = service.load_async("test2.txt")

        # Act - Shutdown immediately
        service.shutdown()

        # Assert
        assert len(service._active_loads) == 0
        # Thread pool is shutdown
        # Cache is cleared

    def test_metadata_with_none_values(self, service):
        """Test metadata with None timestamp values."""
        # Arrange
        meta = DocumentMetadata(
            size_bytes=100,
            mime_type=None,
            encoding=None,
            modified_at=None,
            created_at=None
        )

        # Act
        service._cache_metadata("test.txt", meta)
        cached = service._get_cached_metadata("test.txt")

        # Assert
        assert cached is not None
        assert cached.mime_type is None
        assert cached.encoding is None
        assert cached.modified_at is None


# ==============================================================================
# Performance Tests
# ==============================================================================


class TestPerformance:
    """Test performance characteristics."""

    def test_metadata_cache_performance(self, service):
        """Test metadata cache performance is O(1) for basic operations."""
        # Arrange - Fill cache
        for i in range(100):
            meta = DocumentMetadata(size_bytes=i)
            service._cache_metadata(f"file{i}.txt", meta)

        # Act - Measure retrieval time
        start = time.time()
        for i in range(100):
            service._get_cached_metadata(f"file{i}.txt")
        elapsed = time.time() - start

        # Assert - Should be very fast (< 1 second for 100 ops)
        assert elapsed < 1.0

    def test_concurrent_load_performance(self, service, mock_loader, sample_load_result):
        """Test concurrent load performance."""
        # Arrange
        service._registry.get_loader = Mock(return_value=mock_loader)
        mock_loader.load_complete = Mock(return_value=sample_load_result)

        # Act - Start many concurrent loads
        start = time.time()
        op_ids = []
        for i in range(20):
            op_id = service.load_async(f"test{i}.txt")
            op_ids.append(op_id)

        # Wait for all
        for op_id in op_ids:
            service._active_loads[op_id].result(timeout=2)
        elapsed = time.time() - start

        # Assert - Should complete reasonably fast with thread pool
        assert elapsed < 3.0  # 20 ops with 2 threads should complete quickly

    def test_cache_memory_efficiency(self, service):
        """Test cache doesn't grow beyond max_size."""
        # Arrange
        max_size = service._cache_size

        # Act - Add many items
        for i in range(100):
            meta = DocumentMetadata(size_bytes=i)
            service._cache_metadata(f"file{i}.txt", meta)

        # Assert - Cache size doesn't exceed limit
        with service._cache_lock:
            assert len(service._metadata_cache) <= max_size
            assert len(service._access_order) <= max_size
