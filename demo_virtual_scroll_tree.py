#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ================================================== #
# Demo script for VirtualScrollTreeView
# ================================================== #

"""
Demonstration script for VirtualScrollTreeView with 10000+ items.

This script creates a test environment with a large number of files to demonstrate:
- Virtual scrolling performance
- Lazy loading capabilities
- Memory efficiency
- Smooth 60 FPS scrolling
- Integration with FileLoaderThread
"""

import os
import sys
import tempfile
import time
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QPushButton,
    QSpinBox,
    QGroupBox,
    QTextEdit,
    QSplitter,
    QStatusBar,
)
from PySide6.QtCore import Qt, QTimer

from pygpt_net.ui.widget.filesystem.virtual_scroll_tree import VirtualScrollTreeView
from pygpt_net.ui.widget.filesystem.lazy_model import LazyFileSystemModel
from pygpt_net.ui.widget.file_loader_thread import FileLoaderThread


class UnifiedDocumentLoader:
    """Mock document loader for testing."""

    def load(self, file_path: str) -> str:
        """Simulate loading a file."""
        # Simulate some processing time
        time.sleep(0.001)
        return f"Content of {os.path.basename(file_path)}"


class VirtualScrollDemo(QMainWindow):
    """Main demo window for VirtualScrollTreeView."""

    def __init__(self, test_dir: str):
        """
        Initialize demo window.

        Args:
            test_dir: Path to directory with test files
        """
        super().__init__()

        self.test_dir = test_dir
        self.start_time = time.time()

        self.setWindowTitle("VirtualScrollTreeView Demo - 10000+ Items Performance Test")
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout = QHBoxLayout(central_widget)

        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Create left panel (tree view)
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        # Create right panel (controls and stats)
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        # Set splitter sizes
        splitter.setSizes([800, 400])

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Initialize tree view
        self._setup_tree_view()

        # Set up file loader
        self._setup_file_loader()

        # Update stats timer
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self._update_stats)
        self.stats_timer.start(1000)  # Update every second

        # Performance metrics
        self.scroll_count = 0
        self.last_scroll_time = time.time()

    def _create_left_panel(self) -> QWidget:
        """Create left panel with tree view."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Create tree view
        self.tree_view = VirtualScrollTreeView()
        layout.addWidget(self.tree_view)

        return panel

    def _create_right_panel(self) -> QWidget:
        """Create right panel with controls and stats."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Test directory info
        dir_group = QGroupBox("Test Directory")
        dir_layout = QVBoxLayout(dir_group)

        self.dir_info_label = QLabel(f"Path: {self.test_dir}")
        dir_layout.addWidget(self.dir_info_label)

        file_count = len(os.listdir(self.test_dir))
        self.file_count_label = QLabel(f"Total files: {file_count:,}")
        dir_layout.addWidget(self.file_count_label)

        layout.addWidget(dir_group)

        # Performance controls
        control_group = QGroupBox("Performance Controls")
        control_layout = QVBoxLayout(control_group)

        # Fetch distance control
        fetch_layout = QHBoxLayout()
        fetch_layout.addWidget(QLabel("Fetch Distance:"))
        self.fetch_spinbox = QSpinBox()
        self.fetch_spinbox.setRange(10, 200)
        self.fetch_spinbox.setValue(50)
        self.fetch_spinbox.valueChanged.connect(self._on_fetch_distance_changed)
        fetch_layout.addWidget(self.fetch_spinbox)
        control_layout.addLayout(fetch_layout)

        # Batch size control
        batch_layout = QHBoxLayout()
        batch_layout.addWidget(QLabel("Batch Size:"))
        self.batch_spinbox = QSpinBox()
        self.batch_spinbox.setRange(10, 500)
        self.batch_spinbox.setValue(100)
        self.batch_spinbox.valueChanged.connect(self._on_batch_size_changed)
        batch_layout.addWidget(self.batch_spinbox)
        control_layout.addLayout(batch_layout)

        layout.addWidget(control_group)

        # Performance stats
        stats_group = QGroupBox("Performance Statistics")
        stats_layout = QVBoxLayout(stats_group)

        self.scroll_fps_label = QLabel("Scroll FPS: 0")
        stats_layout.addWidget(self.scroll_fps_label)

        self.memory_usage_label = QLabel("Memory Usage: Calculating...")
        stats_layout.addWidget(self.memory_usage_label)

        self.cache_stats_label = QLabel("Cache Stats: Loading...")
        stats_layout.addWidget(self.cache_stats_label)

        self.visible_items_label = QLabel("Visible Items: 0")
        stats_layout.addWidget(self.visible_items_label)

        self.loading_time_label = QLabel("Loading Time: 0s")
        stats_layout.addWidget(self.loading_time_label)

        layout.addWidget(stats_group)

        # Actions
        action_group = QGroupBox("Actions")
        action_layout = QVBoxLayout(action_group)

        self.refresh_button = QPushButton("Refresh View")
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        action_layout.addWidget(self.refresh_button)

        self.clear_cache_button = QPushButton("Clear Cache")
        self.clear_cache_button.clicked.connect(self._on_clear_cache_clicked)
        action_layout.addWidget(self.clear_cache_button)

        scroll_top_button = QPushButton("Scroll to Top")
        scroll_top_button.clicked.connect(self._on_scroll_top_clicked)
        action_layout.addWidget(scroll_top_button)

        scroll_bottom_button = QPushButton("Scroll to Bottom")
        scroll_bottom_button.clicked.connect(self._on_scroll_bottom_clicked)
        action_layout.addWidget(scroll_bottom_button)

        layout.addWidget(action_group)

        # Log output
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

        layout.addStretch()

        return panel

    def _setup_tree_view(self) -> None:
        """Set up the tree view with model."""
        # Create model
        self.model = LazyFileSystemModel()
        self.model.setRootPath(self.test_dir)

        # Set model on tree view
        self.tree_view.setModel(self.model)

        # Connect signals
        self.tree_view.items_prefetched.connect(self._on_items_prefetched)
        self.tree_view.viewport_changed.connect(self._on_viewport_changed)
        self.tree_view.load_progress.connect(self._on_load_progress)

        # Log initial setup
        self._log_message(f"Tree view initialized with {self.model.rowCount():,} items")

    def _setup_file_loader(self) -> None:
        """Set up file loader thread."""
        # Create loader
        loader = UnifiedDocumentLoader()
        self.file_loader = FileLoaderThread(loader, max_workers=4, batch_size=50)
        self.file_loader.load_started.connect(self._on_loader_started)
        self.file_loader.load_finished.connect(self._on_loader_finished)

        # Set loader on tree view
        self.tree_view.setFileLoader(self.file_loader)

        # Start loader thread
        self.file_loader.start()

        self._log_message("File loader thread started")

    def _log_message(self, message: str) -> None:
        """Add message to log."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def _on_fetch_distance_changed(self, value: int) -> None:
        """Handle fetch distance change."""
        self.tree_view.setFetchDistance(value)
        self._log_message(f"Fetch distance changed to {value}")

    def _on_batch_size_changed(self, value: int) -> None:
        """Handle batch size change."""
        # Note: This requires modifying the model's BATCH_SIZE
        # For now, just log the change
        self._log_message(f"Batch size changed to {value} (restart required)")

    def _on_refresh_clicked(self) -> None:
        """Handle refresh button click."""
        self._log_message("Refreshing view...")
        self.tree_view.refresh()

    def _on_clear_cache_clicked(self) -> None:
        """Handle clear cache button click."""
        self._log_message("Clearing caches...")
        self.tree_view.clearCache()
        self.model._metadata_cache.clear()

    def _on_scroll_top_clicked(self) -> None:
        """Handle scroll to top button click."""
        self.tree_view.verticalScrollBar().setValue(0)
        self._log_message("Scrolled to top")

    def _on_scroll_bottom_clicked(self) -> None:
        """Handle scroll to bottom button click."""
        self.tree_view.verticalScrollBar().setValue(
            self.tree_view.verticalScrollBar().maximum()
        )
        self._log_message("Scrolled to bottom")

    def _on_items_prefetched(self, start: int, end: int) -> None:
        """Handle items prefetched signal."""
        self._log_message(f"Prefetching items {start}-{end}")

    def _on_viewport_changed(self, first: int, last: int) -> None:
        """Handle viewport changed signal."""
        self.scroll_count += 1
        self.visible_items_label.setText(f"Visible Items: {first}-{last}")

        # Calculate FPS (rough estimate)
        current_time = time.time()
        if current_time - self.last_scroll_time > 1.0:
            self.scroll_fps_label.setText(f"Scroll FPS: {self.scroll_count}")
            self.scroll_count = 0
            self.last_scroll_time = current_time

    def _on_load_progress(self, current: int, total: int) -> None:
        """Handle load progress signal."""
        self._log_message(f"Loading progress: {current}/{total}")

    def _on_loader_started(self) -> None:
        """Handle loader started signal."""
        self._log_message("Background loading started")

    def _on_loader_finished(self) -> None:
        """Handle loader finished signal."""
        self._log_message("Background loading finished")

    def _update_stats(self) -> None:
        """Update performance statistics."""
        # Update memory usage
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_usage_label.setText(f"Memory Usage: {memory_mb:.1f} MB")
        except ImportError:
            self.memory_usage_label.setText("Memory Usage: psutil not available")

        # Update cache stats
        cache_stats = self.tree_view.getCacheStats()
        if cache_stats:
            hit_rate = cache_stats.get('hit_rate', 0)
            cache_size = cache_stats.get('size', 0)
            self.cache_stats_label.setText(
                f"Cache: {cache_size} items, {hit_rate:.1f}% hit rate"
            )

        # Update loading time
        elapsed = time.time() - self.start_time
        self.loading_time_label.setText(f"Loading Time: {elapsed:.1f}s")

        # Update status bar
        model = self.model
        total_items = model.rowCount()
        self.status_bar.showMessage(
            f"Ready | Total items: {total_items:,} | "
            f"Elapsed time: {elapsed:.1f}s"
        )

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        if self.file_loader:
            self.file_loader.stop()
        event.accept()


def create_test_files(test_dir: str, count: int = 10000) -> None:
    """
    Create test files for demonstration.

    Args:
        test_dir: Directory to create files in
        count: Number of files to create
    """
    print(f"Creating {count} test files in {test_dir}...")

    os.makedirs(test_dir, exist_ok=True)

    for i in range(count):
        file_name = f"test_file_{i:06d}.txt"
        file_path = os.path.join(test_dir, file_name)

        # Write some content
        with open(file_path, 'w') as f:
            f.write(f"This is test file #{i}\n")
            f.write("Content line 1\n")
            f.write("Content line 2\n")
            f.write("Content line 3\n")

        if i % 1000 == 0:
            print(f"Created {i}/{count} files...")

    print(f"✓ Created {count} test files in {test_dir}")


def main():
    """Main entry point."""
    print("=" * 60)
    print("VirtualScrollTreeView Demo")
    print("=" * 60)

    # Create test directory
    test_dir = tempfile.mkdtemp(prefix="virtual_scroll_test_")
    print(f"Test directory: {test_dir}")

    # Create test files
    create_test_files(test_dir, count=10000)

    # Create Qt application
    app = QApplication(sys.argv)

    # Create and show demo window
    window = VirtualScrollDemo(test_dir)
    window.show()

    print("\nDemo window opened. Test the virtual scrolling performance!")
    print("\nTry:")
    print("  - Scrolling through the list")
    print("  - Changing fetch distance")
    print("  - Refreshing the view")
    print("  - Monitoring memory usage")

    # Execute application
    exit_code = app.exec()

    # Cleanup
    print("\nCleaning up test files...")
    import shutil
    shutil.rmtree(test_dir)

    print("Demo completed!")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
