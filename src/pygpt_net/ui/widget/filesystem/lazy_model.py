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

from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict, List, Tuple
import os

from PySide6.QtCore import (
    QAbstractItemModel,
    QModelIndex,
    Qt,
    Signal,
    QObject,
    QFileInfo,
)
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileIconProvider


class LRUMetadataCache:
    """
    LRU (Least Recently Used) cache for file metadata.

    Stores file metadata (size, type, modified date) with automatic eviction
    of oldest entries when cache size limit is reached.

    Uses OrderedDict to maintain access order efficiently.
    """

    def __init__(self, max_size: int = 500):
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of entries to store
        """
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._max_size: int = max_size
        self._hits: int = 0
        self._misses: int = 0

    def get(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a file path.

        Moves accessed entry to end of OrderedDict (most recently used).

        Args:
            file_path: Absolute file path

        Returns:
            Metadata dict or None if not cached
        """
        if file_path in self._cache:
            # Move to end (most recently used)
            self._cache.move_to_end(file_path)
            self._hits += 1
            return self._cache[file_path]

        self._misses += 1
        return None

    def put(self, file_path: str, metadata: Dict[str, Any]) -> None:
        """
        Store metadata for a file path.

        Evicts least recently used entry if cache is full.

        Args:
            file_path: Absolute file path
            metadata: Dict with keys: size, type, modified, icon
        """
        # Remove if exists (to update position)
        if file_path in self._cache:
            del self._cache[file_path]

        # Add to end (most recently used)
        self._cache[file_path] = metadata

        # Evict oldest if over limit
        if len(self._cache) > self._max_size:
            # Remove first item (least recently used)
            self._cache.popitem(last=False)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)

    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dict with hits, misses, size, hit_rate
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0

        return {
            'hits': self._hits,
            'misses': self._misses,
            'size': len(self._cache),
            'hit_rate': hit_rate,
        }


class IconCache:
    """
    Cache for file type icons.

    Stores QIcon objects by file extension to avoid redundant icon lookups.
    """

    def __init__(self):
        """Initialize icon cache."""
        self._cache: Dict[str, QIcon] = {}
        self._icon_provider = QFileIconProvider()

        # Pre-cache common icons
        self._cache['folder'] = self._icon_provider.icon(QFileIconProvider.IconType.Folder)
        self._cache['file'] = self._icon_provider.icon(QFileIconProvider.IconType.File)

    def get_icon(self, file_path: str, is_dir: bool) -> QIcon:
        """
        Get icon for a file or directory.

        Args:
            file_path: File path
            is_dir: True if directory

        Returns:
            QIcon for the file type
        """
        if is_dir:
            return self._cache['folder']

        # Get file extension
        ext = Path(file_path).suffix.lower()

        if ext not in self._cache:
            # Load icon from file info
            file_info = QFileInfo(file_path)
            self._cache[ext] = self._icon_provider.icon(file_info)

        return self._cache[ext]

    def clear(self) -> None:
        """Clear icon cache except pre-cached icons."""
        folder_icon = self._cache.get('folder')
        file_icon = self._cache.get('file')
        self._cache.clear()
        if folder_icon:
            self._cache['folder'] = folder_icon
        if file_icon:
            self._cache['file'] = file_icon


class LazyFileSystemModel(QAbstractItemModel):
    """
    Custom file system model with lazy loading for large directories.

    Features:
    - Batch loading: Loads BATCH_SIZE files per batch
    - LRU caching: Caches CACHE_SIZE metadata entries
    - Pre-fetching: Loads ahead of viewport by FETCH_DISTANCE
    - Virtual scrolling: rowCount() returns total without loading all files
    - Async support: Ready for background thread integration

    Columns:
    0: Name (with icon)
    1: Size (formatted bytes)
    2: Type (file extension or "Folder")
    3: Modified (timestamp)
    """

    # Configuration constants
    BATCH_SIZE: int = 50
    CACHE_SIZE: int = 500
    FETCH_DISTANCE: int = 5

    # Column definitions
    COL_NAME: int = 0
    COL_SIZE: int = 1
    COL_TYPE: int = 2
    COL_MODIFIED: int = 3
    COL_COUNT: int = 4

    # Signals
    batch_loaded = Signal(int, int)  # start_index, end_index
    metadata_updated = Signal(str)  # file_path
    loading_started = Signal()
    loading_finished = Signal()
    error_occurred = Signal(str)  # error_message

    def __init__(self, parent: Optional[QObject] = None):
        """
        Initialize lazy file system model.

        Args:
            parent: Parent QObject
        """
        super().__init__(parent)

        # Current directory
        self._root_path: str = ""
        self._entries: List[str] = []  # List of file names (not full paths)
        self._total_count: int = 0

        # Caching
        self._metadata_cache = LRUMetadataCache(max_size=self.CACHE_SIZE)
        self._icon_cache = IconCache()

        # Batch loading state
        self._loaded_batches: set[int] = set()  # Set of loaded batch indices
        self._is_loading: bool = False

        # Sorting
        self._sort_column: int = self.COL_NAME
        self._sort_order: Qt.SortOrder = Qt.SortOrder.AscendingOrder

        # Column headers
        self._headers: List[str] = [
            "Name",
            "Size",
            "Type",
            "Modified",
        ]

    def setRootPath(self, path: str) -> None:
        """
        Set root directory path to display.

        Resets model and loads file list without metadata.

        Args:
            path: Directory path to display
        """
        if not os.path.isdir(path):
            self.error_occurred.emit(f"Invalid directory: {path}")
            return

        # Reset state
        self.beginResetModel()

        self._root_path = path
        self._entries.clear()
        self._loaded_batches.clear()
        self._metadata_cache.clear()

        # Load file list (names only, no metadata)
        try:
            self._entries = self._load_file_list(path)
            self._total_count = len(self._entries)
        except Exception as e:
            self.error_occurred.emit(f"Error loading directory: {str(e)}")
            self._entries = []
            self._total_count = 0

        self.endResetModel()

    def rootPath(self) -> str:
        """
        Get current root directory path.

        Returns:
            Root directory path
        """
        return self._root_path

    def _load_file_list(self, path: str) -> List[str]:
        """
        Load list of file names in directory.

        Does NOT load metadata - only file names for efficient rowCount().

        Args:
            path: Directory path

        Returns:
            List of file names (not full paths)
        """
        try:
            # Use os.listdir for speed (no stat calls)
            entries = os.listdir(path)

            # Optionally filter hidden files (starting with .)
            # entries = [e for e in entries if not e.startswith('.')]

            return sorted(entries)
        except Exception as e:
            self.error_occurred.emit(f"Error listing directory: {str(e)}")
            return []

    def _get_file_path(self, index: int) -> str:
        """
        Get full file path for entry index.

        Args:
            index: Entry index

        Returns:
            Full file path
        """
        if 0 <= index < len(self._entries):
            return os.path.join(self._root_path, self._entries[index])
        return ""

    def _load_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Load metadata for a file.

        Performs stat() call to get size, type, modified date.
        Should be called from background thread for large batches.

        Args:
            file_path: Full file path

        Returns:
            Metadata dict with keys: size, type, modified, is_dir
        """
        try:
            stat_info = os.stat(file_path)
            is_dir = os.path.isdir(file_path)

            # Format file type
            if is_dir:
                file_type = "Folder"
            else:
                ext = Path(file_path).suffix
                file_type = ext[1:].upper() if ext else "File"

            metadata = {
                'size': stat_info.st_size if not is_dir else 0,
                'type': file_type,
                'modified': stat_info.st_mtime,
                'is_dir': is_dir,
            }

            return metadata

        except Exception as e:
            # Return placeholder metadata on error
            return {
                'size': 0,
                'type': "Unknown",
                'modified': 0,
                'is_dir': False,
            }

    def _format_size(self, size: int) -> str:
        """
        Format file size in human-readable format.

        Args:
            size: Size in bytes

        Returns:
            Formatted string (e.g., "1.5 MB")
        """
        if size == 0:
            return ""

        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size_float = float(size)

        while size_float >= 1024 and unit_index < len(units) - 1:
            size_float /= 1024
            unit_index += 1

        if unit_index == 0:
            return f"{int(size_float)} {units[unit_index]}"
        else:
            return f"{size_float:.1f} {units[unit_index]}"

    def _format_date(self, timestamp: float) -> str:
        """
        Format timestamp as date string.

        Args:
            timestamp: Unix timestamp

        Returns:
            Formatted date string
        """
        if timestamp == 0:
            return ""

        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return ""

    def _ensure_batch_loaded(self, index: int) -> None:
        """
        Ensure batch containing index is loaded.

        Triggers batch loading if not already loaded.

        Args:
            index: Row index
        """
        batch_index = index // self.BATCH_SIZE

        if batch_index not in self._loaded_batches:
            self._load_batch(batch_index)

    def _load_batch(self, batch_index: int) -> None:
        """
        Load a batch of file metadata.

        Args:
            batch_index: Batch number to load
        """
        if batch_index in self._loaded_batches:
            return

        start_index = batch_index * self.BATCH_SIZE
        end_index = min(start_index + self.BATCH_SIZE, self._total_count)

        self.loading_started.emit()

        # Load metadata for batch
        for i in range(start_index, end_index):
            file_path = self._get_file_path(i)
            if file_path and not self._metadata_cache.get(file_path):
                metadata = self._load_metadata(file_path)
                self._metadata_cache.put(file_path, metadata)
                self.metadata_updated.emit(file_path)

        # Mark batch as loaded
        self._loaded_batches.add(batch_index)

        # Emit data changed for batch
        start_model_index = self.index(start_index, 0)
        end_model_index = self.index(end_index - 1, self.COL_COUNT - 1)
        self.dataChanged.emit(start_model_index, end_model_index)

        self.batch_loaded.emit(start_index, end_index)
        self.loading_finished.emit()

    def prefetch(self, visible_start: int, visible_end: int) -> None:
        """
        Pre-fetch batches ahead of visible range.

        Loads batches within FETCH_DISTANCE of visible range.

        Args:
            visible_start: First visible row
            visible_end: Last visible row
        """
        # Calculate batch range to prefetch
        start_batch = max(0, (visible_start - self.FETCH_DISTANCE) // self.BATCH_SIZE)
        end_batch = ((visible_end + self.FETCH_DISTANCE) // self.BATCH_SIZE) + 1

        # Load batches
        for batch_index in range(start_batch, end_batch):
            if batch_index * self.BATCH_SIZE < self._total_count:
                self._load_batch(batch_index)

    def getCacheStats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats
        """
        stats = self._metadata_cache.get_stats()
        stats['loaded_batches'] = len(self._loaded_batches)
        stats['total_batches'] = (self._total_count + self.BATCH_SIZE - 1) // self.BATCH_SIZE
        return stats

    # QAbstractItemModel interface implementation

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        """
        Create model index for row and column.

        Args:
            row: Row number
            column: Column number
            parent: Parent index (unused - flat list)

        Returns:
            QModelIndex for the item
        """
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        return self.createIndex(row, column, None)

    def parent(self, index: QModelIndex) -> QModelIndex:
        """
        Get parent index (always invalid - flat list).

        Args:
            index: Child index

        Returns:
            Invalid QModelIndex (no hierarchy)
        """
        return QModelIndex()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Get number of rows.

        Returns total count without loading all metadata (efficient).

        Args:
            parent: Parent index

        Returns:
            Number of rows
        """
        if parent.isValid():
            return 0

        return self._total_count

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Get number of columns.

        Args:
            parent: Parent index

        Returns:
            Number of columns (4)
        """
        return self.COL_COUNT

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """
        Get data for model index.

        Loads metadata on-demand for first access.

        Args:
            index: Model index
            role: Data role

        Returns:
            Data for the role
        """
        if not index.isValid():
            return None

        row = index.row()
        column = index.column()

        if row < 0 or row >= self._total_count:
            return None

        file_path = self._get_file_path(row)
        if not file_path:
            return None

        # Display role - show data
        if role == Qt.ItemDataRole.DisplayRole:
            if column == self.COL_NAME:
                return self._entries[row]

            # For other columns, need metadata
            metadata = self._metadata_cache.get(file_path)

            if not metadata:
                # Load metadata on-demand
                self._ensure_batch_loaded(row)
                metadata = self._metadata_cache.get(file_path)

                if not metadata:
                    return "Loading..."

            if column == self.COL_SIZE:
                return self._format_size(metadata['size'])
            elif column == self.COL_TYPE:
                return metadata['type']
            elif column == self.COL_MODIFIED:
                return self._format_date(metadata['modified'])

        # Decoration role - show icon
        elif role == Qt.ItemDataRole.DecorationRole:
            if column == self.COL_NAME:
                metadata = self._metadata_cache.get(file_path)
                is_dir = metadata['is_dir'] if metadata else os.path.isdir(file_path)
                return self._icon_cache.get_icon(file_path, is_dir)

        # Tooltip role
        elif role == Qt.ItemDataRole.ToolTipRole:
            return file_path

        # Sort role - return raw values for sorting
        elif role == Qt.ItemDataRole.UserRole:
            if column == self.COL_NAME:
                return self._entries[row].lower()

            metadata = self._metadata_cache.get(file_path)
            if metadata:
                if column == self.COL_SIZE:
                    return metadata['size']
                elif column == self.COL_TYPE:
                    return metadata['type'].lower()
                elif column == self.COL_MODIFIED:
                    return metadata['modified']

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """
        Get header data.

        Args:
            section: Column or row number
            orientation: Horizontal or vertical
            role: Data role

        Returns:
            Header text
        """
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if 0 <= section < len(self._headers):
                    return self._headers[section]

        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        """
        Get item flags.

        Args:
            index: Model index

        Returns:
            Item flags
        """
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        """
        Sort model by column.

        Note: This requires loading all metadata for accurate sorting.
        For large directories, consider sorting only loaded batches.

        Args:
            column: Column to sort by
            order: Sort order (ascending/descending)
        """
        if column < 0 or column >= self.COL_COUNT:
            return

        self._sort_column = column
        self._sort_order = order

        self.layoutAboutToBeChanged.emit()

        # Load metadata for all entries if sorting by metadata columns
        if column != self.COL_NAME:
            for i in range(self._total_count):
                file_path = self._get_file_path(i)
                if file_path and not self._metadata_cache.get(file_path):
                    metadata = self._load_metadata(file_path)
                    self._metadata_cache.put(file_path, metadata)

        # Sort entries based on column
        def sort_key(entry: str) -> Any:
            """Get sort key for entry."""
            file_path = os.path.join(self._root_path, entry)

            if column == self.COL_NAME:
                return entry.lower()

            metadata = self._metadata_cache.get(file_path)
            if not metadata:
                return 0

            if column == self.COL_SIZE:
                return metadata['size']
            elif column == self.COL_TYPE:
                return metadata['type'].lower()
            elif column == self.COL_MODIFIED:
                return metadata['modified']

            return 0

        self._entries.sort(key=sort_key, reverse=(order == Qt.SortOrder.DescendingOrder))

        self.layoutChanged.emit()

    def getFileInfo(self, index: QModelIndex) -> Optional[Dict[str, Any]]:
        """
        Get file information for model index.

        Args:
            index: Model index

        Returns:
            Dict with file info or None
        """
        if not index.isValid():
            return None

        row = index.row()
        file_path = self._get_file_path(row)

        if not file_path:
            return None

        # Ensure metadata is loaded
        metadata = self._metadata_cache.get(file_path)
        if not metadata:
            metadata = self._load_metadata(file_path)
            self._metadata_cache.put(file_path, metadata)

        return {
            'path': file_path,
            'name': self._entries[row],
            'size': metadata['size'],
            'type': metadata['type'],
            'modified': metadata['modified'],
            'is_dir': metadata['is_dir'],
        }

    def refresh(self) -> None:
        """Refresh the current directory."""
        if self._root_path:
            self.setRootPath(self._root_path)
