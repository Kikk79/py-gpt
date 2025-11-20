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
Image Document Viewer
Phase 1 Week 3 - B1 UI Component Engineer

Displays image files with zoom, pan, and rotation controls.
Supports common image formats (PNG, JPG, GIF, BMP, SVG, etc.).
"""

from typing import Optional, Dict, Any
from pathlib import Path

from PySide6.QtCore import Qt, QObject, QPoint, QRectF, Signal
from PySide6.QtGui import QImage, QPixmap, QPainter, QWheelEvent, QMouseEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QScrollArea, QFrame, QSizePolicy, QSpacerItem
)

from .base import BaseDocumentViewer


class ImageDocumentViewer(BaseDocumentViewer, QObject):
    """
    Image document viewer with zoom/pan support

    Features:
    - Zoom 25% - 400% with smooth scaling
    - Mouse drag panning
    - Mouse wheel zoom
    - Rotation controls (0°, 90°, 180°, 270°)
    - Fit to width/height/viewport options
    - Support for multiple formats (PNG, JPG, GIF, BMP, SVG)
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize image document viewer

        Args:
            parent: Parent widget
        """
        BaseDocumentViewer.__init__(self, parent)
        QObject.__init__(self, parent)

        self._widget = None
        self._scroll_area = None
        self._image_label = None
        self._original_pixmap = None  # Store original for re-scaling
        self._current_pixmap = None
        self._rotation_angle = 0
        self._pan_start_pos = None
        self._scale_factor = 1.0

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        """Initialize viewer UI components"""
        # Main widget
        self._widget = QWidget(self.parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Controls toolbar
        controls = self._create_image_controls()
        layout.addWidget(controls)

        # Scroll area for image
        self._scroll_area = QScrollArea()
        self._scroll_area.setObjectName("image_scroll_area")
        self._scroll_area.setWidgetResizable(False)
        self._scroll_area.setAlignment(Qt.AlignCenter)
        self._scroll_area.setFrameStyle(QFrame.NoFrame)

        # Enable panning
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Image label
        self._image_label = QLabel()
        self._image_label.setObjectName("image_label")
        self._image_label.setBackgroundRole(QPalette.Base)
        self._image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self._image_label.setScaledContents(False)  # We'll handle scaling manually
        self._image_label.setAlignment(Qt.AlignCenter)
        self._image_label.setCursor(Qt.OpenHandCursor)

        # Install event filter for mouse interactions
        self._image_label.setMouseTracking(True)

        self._scroll_area.setWidget(self._image_label)

        layout.addWidget(self._scroll_area)
        self._widget.setLayout(layout)

        # Connect mouse events
        self._image_label.mousePressEvent = self._on_mouse_press
        self._image_label.mouseMoveEvent = self._on_mouse_move
        self._image_label.mouseReleaseEvent = self._on_mouse_release

    def _create_image_controls(self) -> QWidget:
        """Create image control toolbar"""
        controls = QWidget()
        controls.setObjectName("image_controls")

        layout = QHBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Zoom controls
        zoom_out = QPushButton("−")
        zoom_out.clicked.connect(lambda: self.zoom_out(25))
        zoom_out.setFixedSize(32, 32)
        zoom_out.setToolTip("Zoom out")

        zoom_in = QPushButton("+")
        zoom_in.clicked.connect(lambda: self.zoom_in(25))
        zoom_in.setFixedSize(32, 32)
        zoom_in.setToolTip("Zoom in")

        zoom_reset = QPushButton("100%")
        zoom_reset.clicked.connect(self.reset_zoom)
        zoom_reset.setFixedWidth(60)
        zoom_reset.setToolTip("Reset zoom")

        # Zoom slider
        self._zoom_slider = QSlider(Qt.Horizontal)
        self._zoom_slider.setMinimum(25)
        self._zoom_slider.setMaximum(400)
        self._zoom_slider.setValue(100)
        self._zoom_slider.setTickPosition(QSlider.TicksBelow)
        self._zoom_slider.setTickInterval(50)
        self._zoom_slider.setFixedWidth(150)
        self._zoom_slider.valueChanged.connect(self._on_zoom_slider_changed)

        # Fit options
        self._fit_width_btn = QPushButton("Fit Width")
        self._fit_width_btn.clicked.connect(self.fit_to_width)
        self._fit_width_btn.setToolTip("Fit image to window width")

        self._fit_height_btn = QPushButton("Fit Height")
        self._fit_height_btn.clicked.connect(self.fit_to_height)
        self._fit_height_btn.setToolTip("Fit image to window height")

        self._fit_window_btn = QPushButton("Fit Window")
        self._fit_window_btn.clicked.connect(self.fit_to_window)
        self._fit_window_btn.setToolTip("Fit image to window size")

        # Rotation controls
        rotate_left = QPushButton("↺")
        rotate_left.clicked.connect(lambda: self.rotate(-90))
        rotate_left.setFixedSize(32, 32)
        rotate_left.setToolTip("Rotate left")

        rotate_right = QPushButton("↻")
        rotate_right.clicked.connect(lambda: self.rotate(90))
        rotate_right.setFixedSize(32, 32)
        rotate_right.setToolTip("Rotate right")

        # Assemble layout
        layout.addWidget(QLabel("Zoom:"))
        layout.addWidget(zoom_out)
        layout.addWidget(zoom_in)
        layout.addWidget(zoom_reset)
        layout.addWidget(self._zoom_slider)

        layout.addSpacing(20)

        layout.addWidget(QLabel("Fit:"))
        layout.addWidget(self._fit_width_btn)
        layout.addWidget(self._fit_height_btn)
        layout.addWidget(self._fit_window_btn)

        layout.addSpacing(20)

        layout.addWidget(QLabel("Rotate:"))
        layout.addWidget(rotate_left)
        layout.addWidget(rotate_right)

        layout.addStretch()

        controls.setLayout(layout)
        return controls

    def _on_zoom_slider_changed(self, value: int):
        """Handle zoom slider change"""
        self.set_zoom(value)

    def _on_mouse_press(self, event: QMouseEvent):
        """Handle mouse press for panning"""
        if event.button() == Qt.LeftButton and self._scale_factor > 1.0:
            self._pan_start_pos = event.position()
            self._image_label.setCursor(Qt.ClosedHandCursor)

    def _on_mouse_move(self, event: QMouseEvent):
        """Handle mouse move for panning"""
        if self._pan_start_pos is not None and self._scale_factor > 1.0:
            delta = event.position() - self._pan_start_pos

            # Scroll the scroll area
            hbar = self._scroll_area.horizontalScrollBar()
            vbar = self._scroll_area.verticalScrollBar()

            hbar.setValue(hbar.value() - delta.x())
            vbar.setValue(vbar.value() - delta.y())

            self._pan_start_pos = event.position()

    def _on_mouse_release(self, event: QMouseEvent):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton:
            self._pan_start_pos = None
            self._image_label.setCursor(Qt.OpenHandCursor)

    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming"""
        if event.angleDelta().y() > 0:
            self.zoom_in(10)
        else:
            self.zoom_out(10)

    def load_document(self, file_path: Path, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Load image from file

        Args:
            file_path: Path to image file
            metadata: Optional metadata

        Returns:
            True if loaded successfully
        """
        try:
            self._emit_loading_started()
            self._emit_loading_progress(0)

            self._file_path = file_path

            # Load image
            self._original_pixmap = QPixmap(str(file_path))

            if self._original_pixmap.isNull():
                self._emit_error(f"Failed to load image: {file_path}")
                return False

            self._emit_loading_progress(50)

            # Display image
            self._current_pixmap = self._original_pixmap
            self._image_label.setPixmap(self._current_pixmap)
            self._image_label.resize(self._current_pixmap.size())

            self._emit_loading_progress(100)
            self._emit_loading_finished()

            return True

        except Exception as e:
            self._emit_error(f"Failed to load image: {str(e)}")
            return False

    def load_from_data(self, data: bytes, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Load image from raw data

        Args:
            data: Image data as bytes
            metadata: Optional metadata

        Returns:
            True if loaded successfully
        """
        try:
            self._emit_loading_started()
            self._emit_loading_progress(0)

            # Load from byte array
            self._original_pixmap = QPixmap()
            self._original_pixmap.loadFromData(data)

            if self._original_pixmap.isNull():
                self._emit_error("Failed to load image from data")
                return False

            self._emit_loading_progress(50)

            # Display image
            self._current_pixmap = self._original_pixmap
            self._image_label.setPixmap(self._current_pixmap)
            self._image_label.resize(self._current_pixmap.size())

            self._emit_loading_progress(100)
            self._emit_loading_finished()

            return True

        except Exception as e:
            self._emit_error(f"Failed to load image data: {str(e)}")
            return False

    def _apply_zoom(self):
        """Apply current zoom level"""
        if self._original_pixmap is None:
            return

        self._scale_factor = self._zoom_level / 100.0

        # Scale pixmap
        new_size = self._original_pixmap.size() * self._scale_factor
        self._current_pixmap = self._original_pixmap.scaled(
            new_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        # Update display
        self._image_label.setPixmap(self._current_pixmap)
        self._image_label.resize(self._current_pixmap.size())

    def set_zoom(self, percentage: int):
        """
        Set zoom level for image display

        Args:
            percentage: Zoom percentage
        """
        # Update base zoom level
        BaseDocumentViewer.set_zoom(self, percentage)

        # Apply to image
        self._apply_zoom()

        # Update slider
        self._zoom_slider.blockSignals(True)
        self._zoom_slider.setValue(percentage)
        self._zoom_slider.blockSignals(False)

    def fit_to_width(self):
        """Fit image to window width"""
        if self._original_pixmap is None:
            return

        viewport_width = self._scroll_area.viewport().width()
        image_width = self._original_pixmap.width()

        if image_width > 0:
            zoom_percent = int((viewport_width / image_width) * 100)
            self.set_zoom(zoom_percent)

    def fit_to_height(self):
        """Fit image to window height"""
        if self._original_pixmap is None:
            return

        viewport_height = self._scroll_area.viewport().height()
        image_height = self._original_pixmap.height()

        if image_height > 0:
            zoom_percent = int((viewport_height / image_height) * 100)
            self.set_zoom(zoom_percent)

    def fit_to_window(self):
        """Fit image to window size"""
        if self._original_pixmap is None:
            return

        viewport_size = self._scroll_area.viewport().size()
        image_size = self._original_pixmap.size()

        if image_size.width() > 0 and image_size.height() > 0:
            width_ratio = viewport_size.width() / image_size.width()
            height_ratio = viewport_size.height() / image_size.height()
            zoom_percent = int(min(width_ratio, height_ratio) * 100)
            self.set_zoom(zoom_percent)

    def rotate(self, angle: int):
        """
        Rotate image by angle

        Args:
            angle: Rotation angle in degrees
        """
        if self._original_pixmap is None:
            return

        self._rotation_angle = (self._rotation_angle + angle) % 360

        # Create transformation
        transform = QTransform()
        transform.rotate(self._rotation_angle)

        # Rotate original pixmap
        self._original_pixmap = self._original_pixmap.transformed(
            transform,
            Qt.SmoothTransformation
        )

        # Update display
        self.set_zoom(self._zoom_level)

    def clear(self) -> None:
        """Clear viewer content"""
        self._image_label.clear()
        self._original_pixmap = None
        self._current_pixmap = None
        self._content = None
        self._file_path = None
        self._rotation_angle = 0
        self.reset_zoom()

    def get_content_type(self) -> str:
        """
        Get supported content type

        Returns:
            Image content type
        """
        return 'image/*'

    def has_content(self) -> bool:
        """
        Check if viewer has content

        Returns:
            True if image is loaded
        """
        return self._original_pixmap is not None and not self._original_pixmap.isNull()

    def get_widget(self) -> Optional[QWidget]:
        """Get viewer widget"""
        return self._widget

    @staticmethod
    def supports_zoom() -> bool:
        """Check if viewer supports zoom"""
        return True

    def _apply_styles(self):
        """Apply component styles"""
        if self._widget:
            self._widget.setStyleSheet("""
                #image_controls {
                    background-color: palette(window);
                    border-bottom: 1px solid palette(mid);
                }
                #image_scroll_area {
                    background-color: #f0f0f0;
                }
                #image_label {
                    background-color: palette(base);
                }
            """)
