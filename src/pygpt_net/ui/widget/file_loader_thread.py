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
FileLoaderThread - Asynchronous file loading background worker.

This module provides thread-safe, non-blocking file loading with priority
queue management, retry logic, and proper resource cleanup.
"""

from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from pathlib import Path
from queue import PriorityQueue, Empty
from threading import Lock, Event
from typing import Dict, List, Optional, Tuple, Any
import time

from PySide6.QtCore import QThread, Signal


class LoaderWorker:
    """
    Worker class for loading a single file.

    Handles individual file loading operations with error handling,
    retry logic with exponential backoff, and progress reporting.
    """

    def __init__(
        self,
        file_path: str,
        loader: Any,
        max_retries: int = 3,
        backoff_base: float = 0.1
    ):
        """
        Initialize LoaderWorker.

        Args:
            file_path: Absolute path to the file to load
            loader: UnifiedDocumentLoader instance from C3
            max_retries: Maximum number of retry attempts (default: 3)
            backoff_base: Base delay for exponential backoff in seconds (default: 0.1)
        """
        self.file_path: str = file_path
        self.loader: Any = loader
        self.max_retries: int = max_retries
        self.backoff_base: float = backoff_base
        self._cancelled: bool = False

    def load(self) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]], Optional[str]]:
        """
        Load the file with retry logic and exponential backoff.

        Returns:
            Tuple of (success, file_path, result_data, error_message)
            - success: True if load succeeded, False otherwise
            - file_path: Path to the loaded file
            - result_data: Dict containing 'content' and 'metadata' keys if success
            - error_message: Error description if failure, None otherwise
        """
        last_error: Optional[str] = None

        for attempt in range(self.max_retries):
            if self._cancelled:
                return False, self.file_path, None, "Load cancelled"

            try:
                # Attempt to load the file
                result = self._load_file()
                if result:
                    return True, self.file_path, result, None

            except FileNotFoundError as e:
                last_error = f"File not found: {e}"
                break  # Don't retry for missing files

            except PermissionError as e:
                last_error = f"Permission denied: {e}"
                break  # Don't retry for permission issues

            except Exception as e:
                last_error = f"Load error: {type(e).__name__}: {e}"

                # Exponential backoff before retry
                if attempt < self.max_retries - 1:
                    backoff_delay = self.backoff_base * (2 ** attempt)
                    time.sleep(backoff_delay)

        return False, self.file_path, None, last_error

    def _load_file(self) -> Optional[Dict[str, Any]]:
        """
        Internal method to load file using C3 loader.

        Returns:
            Dict with 'content' and 'metadata' keys if successful, None otherwise

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file cannot be read
            Exception: For other loading errors
        """
        file_path = Path(self.file_path)

        # Verify file exists and is readable
        if not file_path.exists():
            raise FileNotFoundError(f"File does not exist: {self.file_path}")

        if not file_path.is_file():
            raise ValueError(f"Not a file: {self.file_path}")

        # Use C3 UnifiedDocumentLoader to load the file
        # The loader should return content and metadata
        try:
            content = self.loader.load(str(file_path))
            metadata = self._extract_metadata(file_path)

            return {
                'content': content,
                'metadata': metadata
            }
        except Exception as e:
            raise Exception(f"Loader failed: {e}")

    def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract file metadata.

        Args:
            file_path: Path object for the file

        Returns:
            Dictionary containing file metadata
        """
        stat = file_path.stat()

        return {
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'created': stat.st_ctime,
            'extension': file_path.suffix,
            'name': file_path.name,
            'path': str(file_path)
        }

    def cancel(self) -> None:
        """Cancel the load operation."""
        self._cancelled = True


class FileLoaderThread(QThread):
    """
    Background thread for asynchronous file loading with priority queue.

    Manages concurrent file loading using ThreadPoolExecutor, priority-based
    scheduling, and proper resource cleanup. All work is performed off the
    main UI thread to prevent blocking.
    """

    # Signals for file loading events
    file_loaded = Signal(str, str, dict)  # file_path, content, metadata
    file_failed = Signal(str, str)  # file_path, error_message
    batch_progress = Signal(int, int)  # current_count, total_count
    load_started = Signal()
    load_finished = Signal()

    # Priority constants
    PRIORITY_HIGH = 1  # Visible files
    PRIORITY_NORMAL = 5  # Recently accessed
    PRIORITY_LOW = 10  # Background preloading

    def __init__(
        self,
        loader: Any,
        max_workers: int = 4,
        batch_size: int = 50,
        parent: Optional[Any] = None
    ):
        """
        Initialize FileLoaderThread.

        Args:
            loader: UnifiedDocumentLoader instance from C3
            max_workers: Maximum concurrent loading workers (default: 4)
            batch_size: Number of files to process per batch (default: 50)
            parent: Parent QObject (optional)
        """
        super().__init__(parent)

        self.loader: Any = loader
        self.max_workers: int = max_workers
        self.batch_size: int = batch_size

        # Thread-safe priority queue for file loading tasks
        self._queue: PriorityQueue = PriorityQueue()
        self._queue_lock: Lock = Lock()

        # Track active and completed tasks
        self._active_workers: Dict[str, LoaderWorker] = {}
        self._workers_lock: Lock = Lock()

        # Control flags
        self._stop_event: Event = Event()
        self._executor: Optional[ThreadPoolExecutor] = None

        # Batch tracking
        self._total_tasks: int = 0
        self._completed_tasks: int = 0
        self._batch_lock: Lock = Lock()

        # File path to retry count mapping
        self._retry_counts: Dict[str, int] = {}

    def add_file(
        self,
        file_path: str,
        priority: int = PRIORITY_NORMAL
    ) -> None:
        """
        Add a file to the loading queue.

        Args:
            file_path: Absolute path to the file
            priority: Loading priority (lower = higher priority)
        """
        with self._queue_lock:
            # Check if already in queue or being processed
            if file_path in self._active_workers:
                return

            # Add to priority queue
            # Use file path as tiebreaker for same priority
            self._queue.put((priority, time.time(), file_path))

            with self._batch_lock:
                self._total_tasks += 1

    def add_batch(
        self,
        file_paths: List[str],
        priority: int = PRIORITY_NORMAL
    ) -> None:
        """
        Add multiple files to the loading queue.

        Args:
            file_paths: List of absolute file paths
            priority: Loading priority for all files
        """
        for file_path in file_paths:
            self.add_file(file_path, priority)

    def add_visible_files(self, file_paths: List[str]) -> None:
        """
        Add visible files with high priority.

        Args:
            file_paths: List of currently visible file paths
        """
        self.add_batch(file_paths, self.PRIORITY_HIGH)

    def cancel_all(self) -> None:
        """Cancel all pending and active loading operations."""
        # Set stop flag
        self._stop_event.set()

        # Cancel all active workers
        with self._workers_lock:
            for worker in self._active_workers.values():
                worker.cancel()

        # Clear the queue
        with self._queue_lock:
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except Empty:
                    break

    def run(self) -> None:
        """
        Main thread execution loop.

        Processes files from priority queue using thread pool executor.
        Continues until stop event is set and all tasks complete.
        """
        self.load_started.emit()

        # Create thread pool executor
        self._executor = ThreadPoolExecutor(max_workers=self.max_workers)

        try:
            while not self._stop_event.is_set() or not self._queue.empty():
                self._process_batch()

                # Small sleep to prevent busy waiting
                time.sleep(0.01)

        finally:
            # Clean shutdown
            self._shutdown_executor()
            self.load_finished.emit()

    def _process_batch(self) -> None:
        """
        Process a batch of files from the queue.

        Submits up to batch_size files to the thread pool executor
        and collects results as they complete.
        """
        if not self._executor:
            return

        # Collect batch of files to process
        batch: List[Tuple[int, float, str]] = []

        with self._queue_lock:
            for _ in range(min(self.batch_size, self._queue.qsize())):
                try:
                    item = self._queue.get_nowait()
                    batch.append(item)
                except Empty:
                    break

        if not batch:
            return

        # Submit batch to executor
        futures: Dict[Future, str] = {}

        for priority, timestamp, file_path in batch:
            if self._stop_event.is_set():
                break

            # Create worker
            worker = LoaderWorker(file_path, self.loader)

            with self._workers_lock:
                self._active_workers[file_path] = worker

            # Submit to executor
            future = self._executor.submit(worker.load)
            futures[future] = file_path

        # Process completed futures
        for future in as_completed(futures):
            if self._stop_event.is_set():
                break

            file_path = futures[future]

            try:
                success, path, result, error = future.result()

                if success and result:
                    # Emit success signal
                    self.file_loaded.emit(
                        path,
                        result['content'],
                        result['metadata']
                    )
                else:
                    # Handle failure
                    self._handle_failure(path, error)

            except Exception as e:
                self._handle_failure(file_path, f"Future exception: {e}")

            finally:
                # Clean up worker
                with self._workers_lock:
                    self._active_workers.pop(file_path, None)

                # Update progress
                with self._batch_lock:
                    self._completed_tasks += 1
                    self.batch_progress.emit(
                        self._completed_tasks,
                        self._total_tasks
                    )

    def _handle_failure(self, file_path: str, error: Optional[str]) -> None:
        """
        Handle file loading failure with retry logic.

        Args:
            file_path: Path to the failed file
            error: Error message describing the failure
        """
        # Track retry count
        retry_count = self._retry_counts.get(file_path, 0)

        if retry_count < 3:
            # Retry with lower priority
            self._retry_counts[file_path] = retry_count + 1
            self.add_file(file_path, self.PRIORITY_LOW)
        else:
            # Max retries exceeded, emit failure
            self.file_failed.emit(file_path, error or "Unknown error")
            self._retry_counts.pop(file_path, None)

    def _shutdown_executor(self) -> None:
        """Safely shutdown the thread pool executor."""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None

    def stop(self) -> None:
        """Stop the thread gracefully."""
        self.cancel_all()
        self.wait()

    def reset_progress(self) -> None:
        """Reset batch progress counters."""
        with self._batch_lock:
            self._total_tasks = 0
            self._completed_tasks = 0
        self._retry_counts.clear()


class FileLoaderManager:
    """
    FileLoaderManager - Singleton manager for FileLoaderThread instances.

    Integrates with DocumentProcessingService to provide:
    - Single source of truth for loading operations
    - Connection between C3 loaders and B2 threading
    - Progress tracking and status management
    - Resource cleanup and lifecycle management

    Usage:
        >>> manager = FileLoaderManager.get_instance()
        >>> manager.load_file("document.pdf", priority=1)
        >>> manager.batch_load(["file1.txt", "file2.csv"])
    """

    _instance: Optional['FileLoaderManager'] = None
    _instance_lock = threading.Lock()

    def __init__(self):
        """Initialize file loader manager."""
        self._thread: Optional[FileLoaderThread] = None
        self._loader: Optional[Any] = None
        self._is_started = False
        self._connections: Dict[str, Any] = {}

        # Track all loading operations
        self._active_operations: Dict[str, Dict[str, Any]] = {}
        self._operation_lock = threading.Lock()

        # Batch processing state
        self._batch_queue: List[Tuple[str, int]] = []
        self._batch_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> 'FileLoaderManager':
        """Get singleton instance of FileLoaderManager."""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def initialize(
        self,
        loader: Optional[Any] = None,
        max_workers: int = 4,
        batch_size: int = 50
    ) -> None:
        """
        Initialize the manager with C3 loader.

        Args:
            loader: UnifiedDocumentLoader instance from C3
            max_workers: Maximum concurrent workers
            batch_size: Files per batch

        Example:
            >>> from src.pygpt_net.core.document_processing_service import get_document_processing_service
            >>> service = get_document_processing_service()
            >>> manager.initialize(service._registry.get_loader(".txt"))
        """
        if self._is_started:
            self.stop()

        self._loader = loader
        self._thread = FileLoaderThread(
            loader=loader,
            max_workers=max_workers,
            batch_size=batch_size
        )

        # Connect signals by default
        self._connect_default_signals()

    def start(self) -> None:
        """Start the file loader thread."""
        if self._thread and not self._is_started:
            self._thread.start()
            self._is_started = True

    def stop(self) -> None:
        """Stop the file loader thread and cleanup."""
        if self._thread and self._is_started:
            self._thread.stop()
            self._thread = None
            self._loader = None
            self._is_started = False

            # Clear all operations
            with self._operation_lock:
                self._active_operations.clear()

            with self._batch_lock:
                self._batch_queue.clear()

    def load_file(
        self,
        file_path: str,
        priority: int = FileLoaderThread.PRIORITY_NORMAL
    ) -> str:
        """
        Load a single file.

        Args:
            file_path: Absolute path to file
            priority: Priority (1=high, 5=normal, 10=low)

        Returns:
            Operation ID for tracking

        Example:
            >>> op_id = manager.load_file("/path/to/document.pdf", priority=1)
        """
        if not self._thread or not self._is_started:
            raise RuntimeError("FileLoaderManager not initialized or started")

        op_id = f"load_{file_path}_{time.time()}"

        # Track operation
        with self._operation_lock:
            self._active_operations[op_id] = {
                "path": file_path,
                "status": "pending",
                "priority": priority,
                "start_time": time.time(),
                "progress": 0,
            }

        # Add to thread queue
        self._thread.add_file(file_path, priority)

        return op_id

    def load_batch(
        self,
        file_paths: List[str],
        priority: int = FileLoaderThread.PRIORITY_NORMAL
    ) -> List[str]:
        """
        Load multiple files as a batch.

        Args:
            file_paths: List of file paths
            priority: Priority for all files

        Returns:
            List of operation IDs

        Example:
            >>> op_ids = manager.batch_load(["file1.txt", "file2.csv"])
        """
        op_ids = []
        for file_path in file_paths:
            op_id = self.load_file(file_path, priority)
            op_ids.append(op_id)
        return op_ids

    def load_visible_files(self, file_paths: List[str]) -> List[str]:
        """
        Load visible files with high priority.

        Args:
            file_paths: Currently visible file paths

        Returns:
            List of operation IDs
        """
        return self.load_batch(file_paths, FileLoaderThread.PRIORITY_HIGH)

    def cancel_operation(self, op_id: str) -> bool:
        """
        Cancel a specific operation.

        Args:
            op_id: Operation ID to cancel

        Returns:
            True if cancelled, False if not found
        """
        with self._operation_lock:
            if op_id in self._active_operations:
                self._active_operations[op_id]["status"] = "cancelled"
                return True
        return False

    def cancel_all(self) -> int:
        """
        Cancel all operations.

        Returns:
            Number of operations cancelled
        """
        count = 0
        with self._operation_lock:
            for op_id in list(self._active_operations.keys()):
                if self.cancel_operation(op_id):
                    count += 1

        if self._thread:
            self._thread.cancel_all()

        return count

    def get_operation_status(self, op_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of an operation.

        Args:
            op_id: Operation ID

        Returns:
            Dict with status info or None if not found
        """
        with self._operation_lock:
            return self._active_operations.get(op_id)

    def get_all_operations(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all active operations.

        Returns:
            Dict mapping operation ID to status dict
        """
        with self._operation_lock:
            return dict(self._active_operations)

    def is_loading(self, file_path: str) -> bool:
        """
        Check if a file is currently loading.

        Args:
            file_path: File path to check

        Returns:
            True if loading
        """
        with self._operation_lock:
            for op in self._active_operations.values():
                if op["path"] == file_path and op["status"] == "loading":
                    return True
        return False

    def _connect_default_signals(self) -> None:
        """Connect default signal handlers."""
        if not self._thread:
            return

        # Connect progress tracking
        self._thread.batch_progress.connect(self._on_batch_progress)

        # Connect completion tracking
        self._thread.file_loaded.connect(self._on_file_loaded)
        self._thread.file_failed.connect(self._on_file_failed)

    def _on_batch_progress(self, current: int, total: int) -> None:
        """Handle batch progress updates."""
        progress = (current / total * 100) if total > 0 else 0

        # Update operation statuses
        with self._operation_lock:
            for op in self._active_operations.values():
                if op["status"] == "loading":
                    op["progress"] = progress

    def _on_file_loaded(self, file_path: str, content: str, metadata: dict) -> None:
        """Handle successful file load."""
        with self._operation_lock:
            # Find operation for this file
            for op_id, op in self._active_operations.items():
                if op["path"] == file_path and op["status"] == "loading":
                    op["status"] = "completed"
                    op["progress"] = 100
                    op["metadata"] = metadata
                    break

    def _on_file_failed(self, file_path: str, error: str) -> None:
        """Handle failed file load."""
        with self._operation_lock:
            # Find operation for this file
            for op_id, op in self._active_operations.items():
                if op["path"] == file_path:
                    op["status"] = "failed"
                    op["error"] = error
                    break

    def reset_stats(self) -> None:
        """Reset all statistics and clear completed operations."""
        with self._operation_lock:
            # Remove completed operations
            to_remove = [
                op_id for op_id, op in self._active_operations.items()
                if op["status"] in ["completed", "failed", "cancelled"]
            ]

            for op_id in to_remove:
                del self._active_operations[op_id]

        if self._thread:
            self._thread.reset_progress()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get loading statistics.

        Returns:
            Dict with stats: active, completed, failed, total
        """
        stats = {
            "active": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
            "pending": 0,
            "total": 0
        }

        with self._operation_lock:
            stats["total"] = len(self._active_operations)

            for op in self._active_operations.values():
                status = op.get("status", "unknown")
                if status in stats:
                    stats[status] += 1

        return stats


# ============================================================================
# End of file_loader_thread.py
# ============================================================================
