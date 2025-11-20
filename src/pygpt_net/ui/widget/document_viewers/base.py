#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ================================================== #
# This file is a part of PYGPT package               #
# Website: https://pygpt.net                         #
# GitHub:  https://github.com/szczyglis-dev/py-gpt   #
# MIT License                                        #
# Created By  : Marcin Szczygliński                  #
# Updated Date: 2025.11.20 00:00:00                  #
# ================================================== #

"""
Base Document Viewer Interface
Phase 1 Week 3 - B1 UI Component Engineer

Abstract base class for all document viewer implementations.
Provides common interface and shared functionality.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pathlib import Path

from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QWidget


class BaseDocumentViewer(ABC):
    """
    Abstract base class for document viewers

    All document viewers must implement:
    - load_document(): Load content from file or data
    - clear(): Clear viewer content
    - get_content_type(): Return supported content type
    - has_content(): Check if viewer has content

    Signals:
        loading_started: Emitted when document loading begins
        loading_progress: Emitted during loading (value 0-100)
        loading_finished: Emitted when document loading completes
        error_occurred: Emitted when error occurs (message, severity)
        zoom_changed: Emitted when zoom level changes (percentage)
    """

    loading_started = Signal()
    loading_progress = Signal(int)  # progress value (0-100)
    loading_finished = Signal()
    error_occurred = Signal(str, str)  # message, severity
    zoom_changed = Signal(int)  # zoom percentage

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize base document viewer

        Args:
            parent: Parent widget
        """
        self.parent = parent
        self._file_path: Optional[Path] = None
        self._content: Optional[Any] = None
        self._is_loading = False
        self._zoom_level = 100  # Default 100%

    @abstractmethod
    def load_document(self, file_path: Path, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Load document from file path

        Args:
            file_path: Path to document file
            metadata: Optional metadata dictionary

        Returns:
            True if loaded successfully, False otherwise
        """
        pass

    @abstractmethod
    def load_from_data(self, data: bytes, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Load document from raw data

        Args:
            data: Raw document data as bytes
            metadata: Optional metadata dictionary

        Returns:
            True if loaded successfully, False otherwise
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear viewer content"""
        pass

    @abstractmethod
    def get_content_type(self) -> str:
        """
        Get supported content type (MIME type or extension)

        Returns:
            Content type string (e.g., 'text/plain', 'application/pdf')
        """
        pass

    @abstractmethod
    def has_content(self) -> bool:
        """
        Check if viewer has content loaded

        Returns:
            True if content is loaded, False otherwise
        """
        pass

    def get_widget(self) -> Optional[QWidget]:
        """
        Get the viewer widget for embedding in layouts

        Returns:
            QWidget instance or None if viewer is not GUI-based
        """
        return None

    def set_zoom(self, percentage: int) -> None:
        """
        Set zoom level (if supported)

        Args:
            percentage: Zoom percentage (e.g., 50, 100, 200)
        """
        self._zoom_level = max(10, min(500, percentage))  # Clamp to 10-500%
        self.zoom_changed.emit(self._zoom_level)

    def get_zoom(self) -> int:
        """
        Get current zoom level

        Returns:
            Current zoom percentage
        """
        return self._zoom_level

    def zoom_in(self, step: int = 25) -> None:
        """
        Zoom in by specified percentage step

        Args:
            step: Zoom step size (default 25%)
        """
        self.set_zoom(self._zoom_level + step)

    def zoom_out(self, step: int = 25) -> None:
        """
        Zoom out by specified percentage step

        Args:
            step: Zoom step size (default 25%)
        """
        self.set_zoom(self._zoom_level - step)

    def reset_zoom(self) -> None:
        """Reset zoom to 100%"""
        self.set_zoom(100)

    def _emit_error(self, message: str, severity: str = "error") -> None:
        """
        Emit error signal

        Args:
            message: Error message
            severity: Error severity ('error', 'warning', 'critical')
        """
        self.error_occurred.emit(message, severity)

    def _emit_loading_started(self) -> None:
        """Emit loading started signal and update state"""
        self._is_loading = True
        self.loading_started.emit()

    def _emit_loading_progress(self, value: int) -> None:
        """
        Emit loading progress signal

        Args:
            value: Progress value (0-100)
        """
        self.loading_progress.emit(value)

    def _emit_loading_finished(self) -> None:
        """Emit loading finished signal and update state"""
        self._is_loading = False
        self.loading_finished.emit()

    def is_loading(self) -> bool:
        """
        Check if viewer is currently loading

        Returns:
            True if loading, False otherwise
        """
        return self._is_loading

    def get_file_path(self) -> Optional[Path]:
        """
        Get currently loaded file path

        Returns:
            Path object or None if not loaded from file
        """
        return self._file_path

    @staticmethod
    def supports_zoom() -> bool:
        """
        Check if viewer supports zoom functionality

        Returns:
            True if zoom is supported, False otherwise
        """
        return False

    @staticmethod
    def supports_pagination() -> bool:
        """
        Check if viewer supports pagination

        Returns:
            True if pagination is supported, False otherwise
        """
        return False
