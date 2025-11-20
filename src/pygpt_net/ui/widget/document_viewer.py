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
Unified Document Viewer Widget
Phase 1 Week 3 - B1 UI Component Engineer

DocumentViewerHeader: Displays file metadata, loading progress,
and action toolbar for document preview/attachment/indexing.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import (
    Qt, Signal, QTimer, QSize, QPropertyAnimation,
    QEasingCurve, Property
)
from PySide6.QtGui import QIcon, QFont, QPalette, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QFrame, QSizePolicy,
    QToolButton, QSpacerItem
)


class MetadataDisplay(QWidget):
    """
    File metadata information panel
    Displays: filename, size, type, modified date, index status
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("metadata_display")
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # File name row
        name_layout = QHBoxLayout()
        name_layout.setSpacing(8)

        self.file_icon = QLabel()
        self.file_icon.setFixedSize(24, 24)
        self.file_icon.setScaledContents(True)

        self.file_name = QLabel("No document loaded")
        self.file_name.setObjectName("file_name_label")
        font = self.file_name.font()
        font.setPointSize(11)
        font.setBold(True)
        self.file_name.setFont(font)
        self.file_name.setWordWrap(False)

        name_layout.addWidget(self.file_icon)
        name_layout.addWidget(self.file_name, 1)

        # Metadata row (size, type, modified)
        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(12)

        self.file_size = QLabel("")
        self.file_size.setObjectName("metadata_label")

        self.separator1 = QLabel("•")
        self.separator1.setObjectName("metadata_separator")

        self.file_type = QLabel("")
        self.file_type.setObjectName("metadata_label")

        self.separator2 = QLabel("•")
        self.separator2.setObjectName("metadata_separator")

        self.file_modified = QLabel("")
        self.file_modified.setObjectName("metadata_label")

        meta_layout.addWidget(self.file_size)
        meta_layout.addWidget(self.separator1)
        meta_layout.addWidget(self.file_type)
        meta_layout.addWidget(self.separator2)
        meta_layout.addWidget(self.file_modified)
        meta_layout.addStretch()

        # Index status row
        index_layout = QHBoxLayout()
        index_layout.setSpacing(6)

        self.index_icon = QLabel("📑")
        self.index_status = QLabel("Not indexed")
        self.index_status.setObjectName("index_status_label")

        index_layout.addWidget(self.index_icon)
        index_layout.addWidget(self.index_status)
        index_layout.addStretch()

        # Assemble layout
        layout.addLayout(name_layout)
        layout.addLayout(meta_layout)
        layout.addLayout(index_layout)

        self.setLayout(layout)

        # Initially hide metadata until loaded
        self._show_metadata(False)

    def _apply_styles(self):
        """Apply component-specific styles"""
        self.setStyleSheet("""
            #metadata_display {
                padding: 8px 12px;
            }
            #file_name_label {
                color: palette(text);
            }
            #metadata_label {
                color: palette(mid);
                font-size: 10pt;
            }
            #metadata_separator {
                color: palette(mid);
                font-size: 10pt;
            }
            #index_status_label {
                color: palette(mid);
                font-size: 9pt;
                font-style: italic;
            }
        """)

    def update_metadata(self, metadata: Dict[str, Any]):
        """
        Update displayed metadata

        Args:
            metadata: Dictionary containing file information
                - name: str (filename)
                - size: int (bytes)
                - type: str (MIME type or extension)
                - modified: float (timestamp)
                - indexed_in: list[str] (index names)
        """
        if not metadata:
            self._show_metadata(False)
            return

        # Update file name
        name = metadata.get('name', 'Unknown')
        self.file_name.setText(name)

        # Set appropriate icon based on file type
        file_type = metadata.get('type', '')
        icon_path = self._get_icon_for_type(file_type)
        if icon_path:
            icon = QIcon(icon_path)
            pixmap = icon.pixmap(QSize(24, 24))
            self.file_icon.setPixmap(pixmap)

        # Update file size
        size_bytes = metadata.get('size', 0)
        size_str = self._format_file_size(size_bytes)
        self.file_size.setText(size_str)

        # Update file type
        self.file_type.setText(file_type or 'Unknown')

        # Update modified date
        modified_ts = metadata.get('modified', 0)
        if modified_ts:
            modified_dt = datetime.fromtimestamp(modified_ts)
            modified_str = modified_dt.strftime('%Y-%m-%d %H:%M')
            self.file_modified.setText(f"Modified: {modified_str}")

        # Update index status
        indexed_in = metadata.get('indexed_in', [])
        if indexed_in:
            indexes_str = ", ".join(indexed_in)
            self.index_status.setText(f"Indexed in: {indexes_str}")
            self.index_icon.setText("✓")
        else:
            self.index_status.setText("Not indexed")
            self.index_icon.setText("📑")

        self._show_metadata(True)

    def _show_metadata(self, visible: bool):
        """Show or hide metadata fields"""
        self.file_size.setVisible(visible)
        self.file_type.setVisible(visible)
        self.file_modified.setVisible(visible)
        self.separator1.setVisible(visible)
        self.separator2.setVisible(visible)
        self.index_icon.setVisible(visible)
        self.index_status.setVisible(visible)

    @staticmethod
    def _format_file_size(size_bytes: int) -> str:
        """Format file size to human-readable string"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    @staticmethod
    def _get_icon_for_type(file_type: str) -> Optional[str]:
        """Get icon path for file type"""
        # Map file types to icon resources
        icon_mapping = {
            'text': ':/icons/file_text.svg',
            'pdf': ':/icons/file_pdf.svg',
            'image': ':/icons/file_image.svg',
            'video': ':/icons/file_video.svg',
            'audio': ':/icons/file_audio.svg',
            'code': ':/icons/file_code.svg',
        }

        # Simple type matching
        file_type_lower = file_type.lower()
        for key, icon_path in icon_mapping.items():
            if key in file_type_lower:
                return icon_path

        return ':/icons/file.svg'  # Default file icon


class AnimatedProgressBar(QProgressBar):
    """
    Smooth animated progress bar with percentage display
    Supports linear interpolation for fluid animation
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("animated_progress_bar")

        # Progress animation
        self._target_value = 0
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self._animate_step)
        self._animation_timer.setInterval(16)  # ~60 FPS

        self._animation_speed = 2  # Progress units per frame

        self._setup_ui()

    def _setup_ui(self):
        """Configure progress bar appearance"""
        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(0)
        self.setTextVisible(True)
        self.setFormat("%p%")
        self.setMaximumHeight(12)
        self.setMinimumHeight(8)

        # Apply styling
        self._apply_styles()

    def _apply_styles(self):
        """Apply progress bar styles with theme support"""
        self.setStyleSheet("""
            #animated_progress_bar {
                border: 1px solid palette(mid);
                border-radius: 4px;
                background-color: palette(base);
                text-align: center;
                font-size: 9pt;
            }
            #animated_progress_bar::chunk {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #0765d4,
                    stop: 1 #0a7dff
                );
                border-radius: 3px;
            }
        """)

    def set_progress(self, value: int, animate: bool = True):
        """
        Set progress value with optional animation

        Args:
            value: Progress value (0-100)
            animate: Whether to animate transition
        """
        value = max(0, min(100, value))  # Clamp to 0-100

        if animate:
            self._target_value = value
            if not self._animation_timer.isActive():
                self._animation_timer.start()
        else:
            self.setValue(value)
            self._target_value = value

    def _animate_step(self):
        """Animate progress towards target value"""
        current = self.value()

        if current < self._target_value:
            next_value = min(current + self._animation_speed, self._target_value)
            self.setValue(next_value)
        elif current > self._target_value:
            next_value = max(current - self._animation_speed, self._target_value)
            self.setValue(next_value)
        else:
            # Target reached
            self._animation_timer.stop()

    def reset(self):
        """Reset progress to 0"""
        self._animation_timer.stop()
        self.setValue(0)
        self._target_value = 0


class ActionToolbar(QWidget):
    """
    Action button toolbar with Preview, Attach, Index actions
    Emits signals for button clicks
    """

    # Signals
    preview_clicked = Signal()
    attach_clicked = Signal()
    index_clicked = Signal()
    more_actions_clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("action_toolbar")
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        """Initialize toolbar buttons"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Preview button
        self.preview_btn = QPushButton("Preview")
        self.preview_btn.setObjectName("toolbar_button")
        self.preview_btn.setIcon(QIcon(":/icons/eye.svg"))
        self.preview_btn.setIconSize(QSize(16, 16))
        self.preview_btn.setToolTip("Open in external viewer")
        self.preview_btn.clicked.connect(self.preview_clicked.emit)
        self.preview_btn.setEnabled(False)  # Disabled until document loaded

        # Attach button
        self.attach_btn = QPushButton("Attach")
        self.attach_btn.setObjectName("toolbar_button")
        self.attach_btn.setIcon(QIcon(":/icons/attach.svg"))
        self.attach_btn.setIconSize(QSize(16, 16))
        self.attach_btn.setToolTip("Attach to current chat")
        self.attach_btn.clicked.connect(self.attach_clicked.emit)
        self.attach_btn.setEnabled(False)

        # Index button
        self.index_btn = QPushButton("Index")
        self.index_btn.setObjectName("toolbar_button")
        self.index_btn.setIcon(QIcon(":/icons/index.svg"))
        self.index_btn.setIconSize(QSize(16, 16))
        self.index_btn.setToolTip("Add to vector index")
        self.index_btn.clicked.connect(self.index_clicked.emit)
        self.index_btn.setEnabled(False)

        # More actions button (ellipsis menu)
        self.more_btn = QToolButton()
        self.more_btn.setObjectName("toolbar_more_button")
        self.more_btn.setText("⋮")
        self.more_btn.setToolTip("More actions")
        self.more_btn.clicked.connect(self.more_actions_clicked.emit)
        self.more_btn.setFixedSize(32, 32)

        # Add buttons to layout
        layout.addWidget(self.preview_btn)
        layout.addWidget(self.attach_btn)
        layout.addWidget(self.index_btn)
        layout.addWidget(self.more_btn)
        layout.addStretch()

        self.setLayout(layout)

    def _apply_styles(self):
        """Apply toolbar button styles"""
        self.setStyleSheet("""
            #toolbar_button {
                padding: 6px 12px;
                border: 1px solid palette(mid);
                border-radius: 4px;
                background-color: palette(button);
                min-width: 80px;
            }
            #toolbar_button:hover:enabled {
                background-color: palette(light);
                border-color: palette(highlight);
            }
            #toolbar_button:pressed:enabled {
                background-color: palette(dark);
            }
            #toolbar_button:disabled {
                color: palette(mid);
                border-color: palette(midlight);
            }
            #toolbar_more_button {
                border: 1px solid palette(mid);
                border-radius: 4px;
                background-color: palette(button);
                font-size: 16pt;
                font-weight: bold;
            }
            #toolbar_more_button:hover {
                background-color: palette(light);
            }
        """)

    def set_enabled(self, enabled: bool):
        """Enable or disable all action buttons"""
        self.preview_btn.setEnabled(enabled)
        self.attach_btn.setEnabled(enabled)
        self.index_btn.setEnabled(enabled)


class ErrorDisplay(QWidget):
    """
    Non-blocking inline error display
    Shows errors without interrupting user workflow
    """

    # Signals
    dismiss_clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("error_display")
        self._setup_ui()
        self._apply_styles()
        self.hide()  # Initially hidden

    def _setup_ui(self):
        """Initialize error display UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        # Error icon
        self.error_icon = QLabel("⚠️")
        self.error_icon.setFixedSize(20, 20)

        # Error message
        self.error_message = QLabel()
        self.error_message.setObjectName("error_message_label")
        self.error_message.setWordWrap(True)

        # Dismiss button
        self.dismiss_btn = QPushButton("✕")
        self.dismiss_btn.setObjectName("dismiss_button")
        self.dismiss_btn.setFixedSize(24, 24)
        self.dismiss_btn.setToolTip("Dismiss error")
        self.dismiss_btn.clicked.connect(self._on_dismiss)

        layout.addWidget(self.error_icon)
        layout.addWidget(self.error_message, 1)
        layout.addWidget(self.dismiss_btn)

        self.setLayout(layout)

    def _apply_styles(self):
        """Apply error display styles"""
        self.setStyleSheet("""
            #error_display {
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                border-radius: 4px;
                margin: 4px 0;
            }
            #error_message_label {
                color: #721c24;
                font-size: 10pt;
            }
            #dismiss_button {
                border: none;
                background: transparent;
                color: #721c24;
                font-weight: bold;
                font-size: 12pt;
            }
            #dismiss_button:hover {
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 12px;
            }
        """)

    def show_error(self, message: str, severity: str = "error"):
        """
        Display error message

        Args:
            message: Error message text
            severity: Error severity (warning, error, critical)
        """
        self.error_message.setText(message)

        # Update styling based on severity
        if severity == "warning":
            bg_color = "#fff3cd"
            border_color = "#ffeaa7"
            text_color = "#856404"
            icon = "⚠️"
        elif severity == "critical":
            bg_color = "#f5c6cb"
            border_color = "#f1aeb5"
            text_color = "#58151c"
            icon = "❌"
        else:  # error
            bg_color = "#f8d7da"
            border_color = "#f5c6cb"
            text_color = "#721c24"
            icon = "⚠️"

        self.error_icon.setText(icon)

        self.setStyleSheet(f"""
            #error_display {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                margin: 4px 0;
            }}
            #error_message_label {{
                color: {text_color};
                font-size: 10pt;
            }}
            #dismiss_button {{
                border: none;
                background: transparent;
                color: {text_color};
                font-weight: bold;
                font-size: 12pt;
            }}
            #dismiss_button:hover {{
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 12px;
            }}
        """)

        self.show()

    def _on_dismiss(self):
        """Handle dismiss button click"""
        self.hide()
        self.dismiss_clicked.emit()


class DocumentViewerHeader(QWidget):
    """
    Document Viewer Header Component

    Displays file metadata, loading progress, and action toolbar.
    Supports dark/light themes and responsive layout (300-1920px).

    Signals:
        preview_requested: User clicked Preview button
        attach_requested: User clicked Attach button
        index_requested: User clicked Index button
        more_actions_requested: User clicked more actions menu

    Usage:
        header = DocumentViewerHeader()
        header.preview_requested.connect(on_preview)
        header.update_metadata({'name': 'doc.pdf', 'size': 1024})
        header.set_progress(50)
    """

    # Signals
    preview_requested = Signal()
    attach_requested = Signal()
    index_requested = Signal()
    more_actions_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("document_viewer_header")

        # State
        self._current_metadata = None
        self._is_loading = False

        # Initialize UI
        self._setup_ui()
        self._connect_signals()
        self._apply_styles()

        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumWidth(300)
        self.setMinimumHeight(100)
        self.setMaximumHeight(160)

    def _setup_ui(self):
        """Initialize header UI components"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(8)

        # Top row: Metadata and Action Toolbar
        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)

        # Metadata display (left side)
        self.metadata_display = MetadataDisplay()

        # Action toolbar (right side)
        self.action_toolbar = ActionToolbar()

        top_layout.addWidget(self.metadata_display, 1)
        top_layout.addWidget(self.action_toolbar, 0)

        # Progress bar row
        self.progress_bar = AnimatedProgressBar()
        self.progress_bar.hide()  # Hidden until loading starts

        # Error display row
        self.error_display = ErrorDisplay()

        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setObjectName("header_separator")

        # Assemble main layout
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.error_display)
        main_layout.addWidget(separator)

        self.setLayout(main_layout)

    def _connect_signals(self):
        """Connect internal signals"""
        self.action_toolbar.preview_clicked.connect(self.preview_requested.emit)
        self.action_toolbar.attach_clicked.connect(self.attach_requested.emit)
        self.action_toolbar.index_clicked.connect(self.index_requested.emit)
        self.action_toolbar.more_actions_clicked.connect(self.more_actions_requested.emit)
        self.error_display.dismiss_clicked.connect(self._on_error_dismissed)

    def _apply_styles(self):
        """Apply header styles with theme support"""
        self.setStyleSheet("""
            #document_viewer_header {
                background-color: palette(window);
                border-bottom: 1px solid palette(mid);
            }
            #header_separator {
                color: palette(mid);
                margin: 4px 0;
            }
        """)

    def update_metadata(self, metadata: Dict[str, Any]):
        """
        Update displayed file metadata

        Args:
            metadata: Dictionary containing file information
                Required keys: name, size, type
                Optional keys: modified, indexed_in
        """
        self._current_metadata = metadata
        self.metadata_display.update_metadata(metadata)

        # Enable action buttons when metadata is loaded
        has_metadata = metadata and metadata.get('name')
        self.action_toolbar.set_enabled(has_metadata)

    def set_progress(self, value: int, animate: bool = True):
        """
        Update loading progress

        Args:
            value: Progress value (0-100)
            animate: Whether to animate progress change
        """
        self.progress_bar.set_progress(value, animate)

        # Show/hide progress bar based on value
        if value > 0 and value < 100:
            self.progress_bar.show()
            self._is_loading = True
        elif value >= 100:
            # Keep visible briefly then hide
            QTimer.singleShot(500, self._hide_progress)
        elif value == 0:
            self.progress_bar.hide()
            self._is_loading = False

    def _hide_progress(self):
        """Hide progress bar after completion"""
        self.progress_bar.hide()
        self._is_loading = False

    def start_loading(self):
        """Start loading state (show progress at 0%)"""
        self.progress_bar.reset()
        self.progress_bar.show()
        self._is_loading = True
        self.action_toolbar.set_enabled(False)

    def finish_loading(self):
        """Finish loading state (animate to 100% then hide)"""
        self.set_progress(100)
        self.action_toolbar.set_enabled(True)

    def show_error(self, message: str, severity: str = "error"):
        """
        Display error message

        Args:
            message: Error message text
            severity: Error severity (warning, error, critical)
        """
        self.error_display.show_error(message, severity)

    def hide_error(self):
        """Hide error display"""
        self.error_display.hide()

    def _on_error_dismissed(self):
        """Handle error dismissal"""
        # Could emit signal or log dismissal here
        pass

    def clear(self):
        """Clear all header content"""
        self._current_metadata = None
        self.metadata_display.update_metadata({})
        self.progress_bar.reset()
        self.progress_bar.hide()
        self.error_display.hide()
        self.action_toolbar.set_enabled(False)
        self._is_loading = False

    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """Get current metadata"""
        return self._current_metadata

    def is_loading(self) -> bool:
        """Check if currently in loading state"""
        return self._is_loading


# Example usage and testing
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    # Create test window
    window = QMainWindow()
    window.setWindowTitle("DocumentViewerHeader Test")
    window.resize(800, 200)

    # Create header
    header = DocumentViewerHeader()

    # Connect signals
    header.preview_requested.connect(lambda: print("Preview requested"))
    header.attach_requested.connect(lambda: print("Attach requested"))
    header.index_requested.connect(lambda: print("Index requested"))
    header.more_actions_requested.connect(lambda: print("More actions requested"))

    # Test metadata
    test_metadata = {
        'name': 'example_document.pdf',
        'size': 2457600,  # 2.4 MB
        'type': 'PDF Document',
        'modified': datetime.now().timestamp(),
        'indexed_in': ['default_index', 'project_docs']
    }

    header.update_metadata(test_metadata)

    # Simulate loading progress
    def simulate_loading():
        header.start_loading()
        progress = 0

        def update_progress():
            nonlocal progress
            progress += 10
            header.set_progress(progress)

            if progress >= 100:
                timer.stop()
                header.finish_loading()

        timer = QTimer()
        timer.timeout.connect(update_progress)
        timer.start(200)  # Update every 200ms

    # Start loading simulation after 1 second
    QTimer.singleShot(1000, simulate_loading)

    # Test error display after 5 seconds
    QTimer.singleShot(5000, lambda: header.show_error(
        "Failed to load document: File not found",
        "warning"
    ))

    window.setCentralWidget(header)
    window.show()

    sys.exit(app.exec())
