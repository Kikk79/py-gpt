#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Example: DocumentViewerHeader with PyGPT
Shows how to integrate the header with controllers and backend
"""

from datetime import datetime
from typing import Optional
from pathlib import Path


class DocumentController:
    """
    Example controller showing integration patterns
    This demonstrates how C3 (backend) and the UI work together
    """

    def __init__(self, window):
        self.window = window
        self.current_document = None
        self.header = None  # Will be set during UI initialization

    def setup_header(self, header):
        """
        Connect header to controller actions
        Called during UI initialization
        """
        self.header = header

        # Connect signals to controller methods
        self.header.preview_requested.connect(self.preview_document)
        self.header.attach_requested.connect(self.attach_to_chat)
        self.header.index_requested.connect(self.show_index_menu)
        self.header.more_actions_requested.connect(self.show_context_menu)

        print("✅ Header connected to controller")

    def load_document(self, file_path: str):
        """
        Load document with streaming progress
        This is where C3's streaming backend integrates
        """
        path = Path(file_path)

        if not path.exists():
            self.header.show_error(
                f"File not found: {path.name}",
                severity="error"
            )
            return

        # Start loading state
        self.header.start_loading()

        # Extract metadata
        metadata = self._extract_metadata(path)
        self.header.update_metadata(metadata)

        # Simulate streaming load with progress callbacks
        self._stream_load_document(path)

    def _extract_metadata(self, path: Path) -> dict:
        """
        Extract file metadata for header display
        In real implementation, this would use C3's metadata extractor
        """
        stat = path.stat()

        # Determine file type
        mime_types = {
            '.pdf': 'PDF Document',
            '.txt': 'Text Document',
            '.md': 'Markdown Document',
            '.py': 'Python Script',
            '.json': 'JSON Data',
            '.jpg': 'JPEG Image',
            '.png': 'PNG Image',
        }
        file_type = mime_types.get(path.suffix.lower(), 'Unknown')

        # Check index status (would query vector database)
        indexed_in = self._check_index_status(path)

        return {
            'name': path.name,
            'size': stat.st_size,
            'type': file_type,
            'modified': stat.st_mtime,
            'indexed_in': indexed_in
        }

    def _check_index_status(self, path: Path) -> list:
        """
        Check which indexes contain this document
        In real implementation, queries idx controller
        """
        # Example: Query vector database
        # return self.window.controller.idx.get_document_indexes(str(path))

        # Mock implementation
        return ['default_index'] if path.suffix in ['.txt', '.md', '.pdf'] else []

    def _stream_load_document(self, path: Path):
        """
        Simulate streaming document load with progress
        In real implementation, uses C3's streaming loader
        """
        from PySide6.QtCore import QTimer

        file_size = path.stat().st_size
        bytes_loaded = 0
        chunk_size = max(file_size // 20, 1024)  # 20 updates

        def load_chunk():
            nonlocal bytes_loaded

            # Simulate chunk loading
            bytes_loaded += chunk_size

            # Calculate progress
            progress = min(100, int((bytes_loaded / file_size) * 100))

            # Update header progress
            self.header.set_progress(progress)

            # Continue or finish
            if bytes_loaded >= file_size:
                timer.stop()
                self.header.finish_loading()
                self._on_document_loaded(path)
            else:
                # Emit progress signal for other components
                self.window.signals.document_load_progress.emit(progress)

        # Create timer for chunk loading (simulates async I/O)
        timer = QTimer()
        timer.timeout.connect(load_chunk)
        timer.start(100)  # Update every 100ms (as per spec)

    def _on_document_loaded(self, path: Path):
        """
        Called when document loading completes
        """
        self.current_document = str(path)
        print(f"✅ Document loaded: {path.name}")

        # Emit completion signal
        # self.window.signals.document_loaded.emit(str(path))

    # Action handlers (connected to header signals)

    def preview_document(self):
        """
        Open document in external viewer
        Connected to: header.preview_requested
        """
        if not self.current_document:
            return

        print(f"🔍 Previewing: {self.current_document}")

        # Example: Open with system default application
        # import subprocess
        # subprocess.run(['xdg-open', self.current_document])

        # Or use PyGPT's file opener
        # self.window.controller.files.open_external(self.current_document)

    def attach_to_chat(self):
        """
        Attach document to current chat context
        Connected to: header.attach_requested
        """
        if not self.current_document:
            return

        print(f"📎 Attaching to chat: {self.current_document}")

        # Example: Add to attachment controller
        # self.window.controller.attachment.add_file(self.current_document)

    def show_index_menu(self):
        """
        Show index selection menu
        Connected to: header.index_requested
        """
        if not self.current_document:
            return

        print(f"📑 Showing index menu for: {self.current_document}")

        # Example: Show index selection dialog
        # self.window.controller.idx.show_add_dialog(self.current_document)

    def show_context_menu(self):
        """
        Show more actions context menu
        Connected to: header.more_actions_requested
        """
        if not self.current_document:
            return

        print(f"⋮ Showing context menu for: {self.current_document}")

        # Example: Create context menu
        # from PySide6.QtWidgets import QMenu
        # menu = QMenu()
        # menu.addAction("Copy Path", self._copy_path)
        # menu.addAction("Delete", self._delete_document)
        # menu.addAction("Properties", self._show_properties)
        # menu.exec_(QCursor.pos())


class DocumentViewerWidget:
    """
    Example showing full widget integration
    This is what B2 will implement for content area
    """

    def __init__(self, window):
        self.window = window

        # Create header (from document_viewer.py)
        from pygpt_net.ui.widget.document_viewer import DocumentViewerHeader
        self.header = DocumentViewerHeader()

        # Create content area (placeholder for B2's implementation)
        # from PySide6.QtWidgets import QStackedWidget
        # self.content_area = QStackedWidget()

        # Create controller
        self.controller = DocumentController(window)
        self.controller.setup_header(self.header)

    def build_layout(self):
        """
        Build complete document viewer layout
        """
        from PySide6.QtWidgets import QVBoxLayout, QWidget

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add header
        layout.addWidget(self.header)

        # Add content area (B2's work)
        # layout.addWidget(self.content_area, 1)

        widget = QWidget()
        widget.setLayout(layout)
        return widget


# Integration with PyGPT main window
class MainWindowIntegration:
    """
    Shows how to integrate into existing PyGPT window
    """

    @staticmethod
    def add_document_viewer(window):
        """
        Add document viewer to main window
        Called during window initialization
        """
        # Create document viewer widget
        viewer = DocumentViewerWidget(window)
        viewer_widget = viewer.build_layout()

        # Add to main layout (example locations)

        # Option 1: Add as new dock widget
        # from PySide6.QtWidgets import QDockWidget
        # dock = QDockWidget("Document Viewer", window)
        # dock.setWidget(viewer_widget)
        # window.addDockWidget(Qt.RightDockWidgetArea, dock)

        # Option 2: Add to tab widget
        # window.tabs.addTab(viewer_widget, "Documents")

        # Option 3: Add to splitter
        # window.splitter.addWidget(viewer_widget)

        # Store reference
        window.document_viewer = viewer

        print("✅ Document viewer integrated into main window")

        return viewer


# Example usage in controller
def example_controller_usage():
    """
    Example showing how controllers use the document viewer
    """
    # Assuming window is already initialized
    # window = MainWindow()

    # Add document viewer
    # viewer = MainWindowIntegration.add_document_viewer(window)

    # Load a document
    # viewer.controller.load_document("/path/to/document.pdf")

    print("""
    Integration Example:

    1. Create DocumentViewerHeader widget
    2. Create DocumentController
    3. Connect signals:
       - preview_requested → controller.preview_document
       - attach_requested → controller.attach_to_chat
       - index_requested → controller.show_index_menu
       - more_actions_requested → controller.show_context_menu

    4. On document load:
       - Extract metadata → header.update_metadata()
       - Start streaming → header.start_loading()
       - Update progress every 100ms → header.set_progress(%)
       - On completion → header.finish_loading()

    5. Handle errors:
       - header.show_error(message, severity)

    ✅ Ready for C3 backend integration
    ✅ Ready for B2 content area integration
    """)


if __name__ == "__main__":
    example_controller_usage()
