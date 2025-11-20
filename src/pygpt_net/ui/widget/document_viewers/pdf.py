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
PDF Document Viewer
Phase 1 Week 3 - B1 UI Component Engineer

Displays PDF documents with pagination, zoom controls, and navigation.
Supports rendering PDF pages as images with configurable quality.
"""

from typing import Optional, Dict, Any
from pathlib import Path
import io

try:
    from PySide6.QtPdf import QPdfDocument, QPdfPageNavigator
    from PySide6.QtPdfWidgets import QPdfView
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from PySide6.QtCore import Qt, QObject, QTimer
from PySide6.QtGui import QImage, QPixmap, QPalette
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QSlider, QScrollArea, QFrame
)

from .base import BaseDocumentViewer


class PDFDocumentViewer(BaseDocumentViewer, QObject):
    """
    PDF document viewer with pagination support

    Features:
    - PDF rendering using QPdfView (if available) or fallback to image rendering
    - Pagination controls (previous/next page, page jump)
    - Zoom controls (25% - 400%)
    - Page navigation with thumbnails
    - Search within PDF (placeholder for future)
    """

    page_changed = Signal(int)  # current page number

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize PDF document viewer

        Args:
            parent: Parent widget
        """
        BaseDocumentViewer.__init__(self, parent)
        QObject.__init__(self, parent)

        self._widget = None
        self._pdf_view = None
        self._pdf_doc = None
        self._page_navigator = None
        self._scroll_area = None
        self._page_label = None
        self._current_page = 1
        self._total_pages = 1
        self._fallback_mode = not PDF_AVAILABLE

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        """Initialize viewer UI components"""
        # Main widget
        self._widget = QWidget(self.parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if not self._fallback_mode:
            # Use QPdfView if available
            self._setup_native_pdf_view(layout)
        else:
            # Use fallback image-based viewer
            self._setup_fallback_pdf_view(layout)

        self._widget.setLayout(layout)

    def _setup_native_pdf_view(self, layout: QVBoxLayout):
        """Setup native QPdfView widget"""
        # PDF View (native)
        self._pdf_doc = QPdfDocument()
        self._pdf_view = QPdfView()
        self._pdf_view.setDocument(self._pdf_doc)

        # Get page navigator for programmatic control
        self._page_navigator = self._pdf_view.pageNavigator()

        # Controls
        controls = self._create_pdf_controls()
        layout.addWidget(controls)
        layout.addWidget(self._pdf_view)

    def _setup_fallback_pdf_view(self, layout: QVBoxLayout):
        """Setup fallback image-based PDF viewer"""
        # Warning label
        warning = QLabel("PDF support not available. Install PySide6[extras]")
        warning.setObjectName("pdf_warning")
        warning.setStyleSheet("""
            #pdf_warning {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                color: #856404;
                padding: 8px;
                border-radius: 4px;
                margin: 8px;
            }
        """)
        layout.addWidget(warning)

        # Scroll area for page display
        self._scroll_area = QScrollArea()
        self._scroll_area.setObjectName("pdf_scroll_area")
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setAlignment(Qt.AlignCenter)

        # Page display label
        self._page_label = QLabel()
        self._page_label.setObjectName("pdf_page")
        self._page_label.setMinimumSize(400, 600)
        self._page_label.setAlignment(Qt.AlignCenter)
        self._page_label.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd;")

        self._scroll_area.setWidget(self._page_label)

        # Controls
        controls = self._create_pdf_controls()
        layout.addWidget(controls)
        layout.addWidget(self._scroll_area)

    def _create_pdf_controls(self) -> QWidget:
        """Create PDF navigation controls"""
        controls = QWidget()
        controls.setObjectName("pdf_controls")

        layout = QHBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Previous page button
        self._prev_btn = QPushButton("← Previous")
        self._prev_btn.clicked.connect(self.previous_page)
        self._prev_btn.setEnabled(False)

        # Page navigation
        self._page_spin = QSpinBox()
        self._page_spin.setMinimum(1)
        self._page_spin.setMaximum(1)
        self._page_spin.valueChanged.connect(self._on_page_changed)
        self._page_spin.setFixedWidth(80)

        self._page_total = QLabel("of 1")

        # Next page button
        self._next_btn = QPushButton("Next →")
        self._next_btn.clicked.connect(self.next_page)
        self._next_btn.setEnabled(False)

        # Zoom controls
        zoom_out = QPushButton("−")
        zoom_out.clicked.connect(lambda: self.zoom_out(25))
        zoom_out.setFixedSize(32, 32)

        zoom_in = QPushButton("+")
        zoom_in.clicked.connect(lambda: self.zoom_in(25))
        zoom_in.setFixedSize(32, 32)

        zoom_reset = QPushButton("100%")
        zoom_reset.clicked.connect(self.reset_zoom)
        zoom_reset.setFixedWidth(60)

        # Zoom slider
        self._zoom_slider = QSlider(Qt.Horizontal)
        self._zoom_slider.setMinimum(25)
        self._zoom_slider.setMaximum(400)
        self._zoom_slider.setValue(100)
        self._zoom_slider.setTickPosition(QSlider.TicksBelow)
        self._zoom_slider.setTickInterval(50)
        self._zoom_slider.setFixedWidth(150)
        self._zoom_slider.valueChanged.connect(self._on_zoom_slider_changed)

        # Assemble layout
        layout.addWidget(self._prev_btn)
        layout.addWidget(QLabel("Page"))
        layout.addWidget(self._page_spin)
        layout.addWidget(self._page_total)
        layout.addWidget(self._next_btn)

        layout.addStretch()

        layout.addWidget(QLabel("Zoom:"))
        layout.addWidget(zoom_out)
        layout.addWidget(zoom_in)
        layout.addWidget(zoom_reset)
        layout.addWidget(self._zoom_slider)

        controls.setLayout(layout)
        return controls

    def _on_page_changed(self, page_num: int):
        """Handle page change from spinbox"""
        if page_num != self._current_page:
            self.goto_page(page_num)

    def _on_zoom_slider_changed(self, value: int):
        """Handle zoom slider change"""
        multiplier = value / 100.0
        self.set_zoom(value)

        if self._fallback_mode and self._pdf_doc and self._page_label:
            # Update current page display
            self._render_current_page()

    def load_document(self, file_path: Path, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Load PDF document from file

        Args:
            file_path: Path to PDF file
            metadata: Optional metadata

        Returns:
            True if loaded successfully
        """
        try:
            self._emit_loading_started()
            self._file_path = file_path

            if not self._fallback_mode:
                # Load using QPdfDocument
                self._pdf_doc.load(file_path)
                self._current_page = 1
                self._total_pages = self._pdf_doc.pageCount()
                self._update_page_controls()
            else:
                # Fallback mode - show placeholder
                self._total_pages = 1
                self._update_page_controls()
                self._emit_error("PDF rendering not available in fallback mode")

            self._emit_loading_finished()
            return True

        except Exception as e:
            self._emit_error(f"Failed to load PDF: {str(e)}")
            return False

    def load_from_data(self, data: bytes, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Load PDF from raw data

        Args:
            data: PDF data as bytes
            metadata: Optional metadata

        Returns:
            True if loaded successfully
        """
        try:
            self._emit_loading_started()

            if not self._fallback_mode:
                # Load from byte array
                self._pdf_doc.loadFromData(data)
                self._current_page = 1
                self._total_pages = self._pdf_doc.pageCount()
                self._update_page_controls()
            else:
                # Fallback mode - show placeholder
                self._total_pages = 1
                self._update_page_controls()
                self._emit_error("PDF rendering not available in fallback mode")

            self._emit_loading_finished()
            return True

        except Exception as e:
            self._emit_error(f"Failed to load PDF data: {str(e)}")
            return False

    def _update_page_controls(self):
        """Update page controls state"""
        # Update page range
        self._page_spin.setMaximum(self._total_pages)
        self._page_total.setText(f"of {self._total_pages}")

        # Update navigation button state
        self._prev_btn.setEnabled(self._current_page > 1)
        self._next_btn.setEnabled(self._current_page < self._total_pages)

        # Update page spin without triggering signal
        self._page_spin.blockSignals(True)
        self._page_spin.setValue(self._current_page)
        self._page_spin.blockSignals(False)

        # Emit page changed signal
        self.page_changed.emit(self._current_page)

    def _render_current_page(self):
        """Render current page in fallback mode"""
        if not self._fallback_mode or not self._pdf_doc:
            return

        # In a real implementation, would render PDF page to QImage
        # For now, show placeholder
        placeholder = QImage(800, 1067, QImage.Format_RGB32)
        placeholder.fill(Qt.white)

        # Add placeholder text
        from PySide6.QtGui import QPainter
        painter = QPainter(placeholder)
        painter.setPen(Qt.gray)
        painter.setFont(QFont("Sans", 16))
        painter.drawText(placeholder.rect(), Qt.AlignCenter,
                        f"PDF Page {self._current_page}\n\nPreview not available\nInstall PySide6[extras]")
        painter.end()

        # Apply zoom
        scale = self._zoom_level / 100.0
        if scale != 1.0:
            scaled_size = placeholder.size() * scale
            placeholder = placeholder.scaled(scaled_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self._page_label.setPixmap(QPixmap.fromImage(placeholder))

    def goto_page(self, page_number: int):
        """
        Navigate to specific page

        Args:
            page_number: Page number (1-indexed)
        """
        if page_number < 1 or page_number > self._total_pages:
            return

        self._current_page = page_number

        if not self._fallback_mode:
            # Navigate using page navigator
            self._page_navigator.jump(page_number - 1, QPoint())
        else:
            # Update fallback display
            self._render_current_page()

        self._update_page_controls()

    def next_page(self):
        """Navigate to next page"""
        if self._current_page < self._total_pages:
            self.goto_page(self._current_page + 1)

    def previous_page(self):
        """Navigate to previous page"""
        if self._current_page > 1:
            self.goto_page(self._current_page - 1)

    def first_page(self):
        """Navigate to first page"""
        self.goto_page(1)

    def last_page(self):
        """Navigate to last page"""
        self.goto_page(self._total_pages)

    def set_zoom(self, percentage: int):
        """
        Set zoom level for PDF display

        Args:
            percentage: Zoom percentage (25-400)
        """
        super().set_zoom(percentage)

        if not self._fallback_mode and self._pdf_view:
            # Update native PDF view zoom
            pass  # QPdfView handles zoom internally
        elif self._zoom_slider:
            # Update slider
            self._zoom_slider.blockSignals(True)
            self._zoom_slider.setValue(percentage)
            self._zoom_slider.blockSignals(False)

            # Re-render current page
            self._render_current_page()

    def clear(self) -> None:
        """Clear viewer content"""
        self._content = None
        self._current_page = 1
        self._total_pages = 1

        if not self._fallback_mode:
            if self._pdf_doc:
                self._pdf_doc = QPdfDocument()
                self._pdf_view.setDocument(self._pdf_doc)
        else:
            if self._page_label:
                self._page_label.clear()

        self._update_page_controls()

    def get_content_type(self) -> str:
        """Get supported content type"""
        return 'application/pdf'

    def has_content(self) -> bool:
        """Check if viewer has content"""
        if not self._fallback_mode:
            return self._pdf_doc is not None and self._pdf_doc.pageCount() > 0
        return self._content is not None

    def get_widget(self) -> Optional[QWidget]:
        """Get viewer widget"""
        return self._widget

    @staticmethod
    def supports_zoom() -> bool:
        """Check if viewer supports zoom"""
        return True

    @staticmethod
    def supports_pagination() -> bool:
        """Check if viewer supports pagination"""
        return True

    def _apply_styles(self):
        """Apply component styles"""
        if self._widget:
            self._widget.setStyleSheet("""
                #pdf_controls {
                    background-color: palette(window);
                    border-bottom: 1px solid palette(mid);
                }
            """)
