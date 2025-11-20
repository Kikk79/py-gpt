# Document Reader Keyboard Shortcuts - Integration Guide

## Overview

This guide provides detailed instructions for integrating the keyboard shortcut system into the Document Reader workflow using Qt/PySide6's QShortcut class.

## Architecture

### Shortcut System Components

```
┌─────────────────────────────────────────────────────┐
│  ShortcutManager (shortcuts.py)                    │
│  - Manages shortcut definitions                    │
│  - Handles context switching                       │
│  - Detects conflicts                               │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│  ShortcutController (access/shortcut_controller.py) │
│  - Registers QShortcut objects                      │
│  - Handles key events                               │
│  - Delegates to action handlers                     │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│  QShortcut Objects (Qt/PySide6)                    │
│  - Real-time key capture                           │
│  - Emits activated signals                         │
│  - Context-aware activation                        │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│  Action Handlers (controller actions)              │
│  - Execute specific functionality                  │
│  - Update UI state                                 │
│  - Handle errors                                   │
└─────────────────────────────────────────────────────┘
```

## Implementation Steps

### Step 1: Install Shortcut Components

#### File: `/mnt/c/Users/klaus/Documents/GIT/py-gpt/src/pygpt_net/data/config/shortcuts.py`

Already created - this contains the ShortcutManager and shortcut definitions.

### Step 2: Create Shortcut Controller

#### File: `/mnt/c/Users/klaus/Documents/GIT/py-gpt/src/pygpt_net/core/access/shortcut_controller.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ================================================== #
# This file is a part of PYGPT package               #
# Website: https://pygpt.net                         #
# GitHub:  https://github.com/szczyglis-dev/py-gpt   #
# MIT License                                        #
# Created By  : Marcin Szczygliński                  #
# Updated Date: 2025.01.20 02:00:00                  #
# ================================================== #

from typing import Dict, Optional, Callable
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import Qt, QObject

from pygpt_net.data.config.shortcuts import ShortcutManager, Shortcut
from pygpt_net.utils import trans


class ShortcutController:
    """
    Shortcut controller for registering and managing QShortcut objects
    """

    def __init__(self, window=None):
        """
        Initialize shortcut controller

        :param window: Main window instance
        """
        self.window = window
        self.shortcut_manager = ShortcutManager()
        self.registered_shortcuts: Dict[str, QShortcut] = {}
        self.context_handlers: Dict[str, Callable] = {}
        self.setup_context_handlers()

    def setup_context_handlers(self):
        """
        Setup action handlers for different contexts
        """
        # Explorer context handlers
        self.context_handlers["explorer.open"] = self.handle_explorer_open
        self.context_handlers["explorer.preview"] = self.handle_explorer_preview
        self.context_handlers["explorer.attach"] = self.handle_explorer_attach
        self.context_handlers["explorer.index"] = self.handle_explorer_index
        self.context_handlers["explorer.delete"] = self.handle_explorer_delete
        self.context_handlers["explorer.search"] = self.handle_explorer_search
        self.context_handlers["explorer.refresh"] = self.handle_explorer_refresh
        self.context_handlers["explorer.select_all"] = self.handle_explorer_select_all
        self.context_handlers["explorer.new_folder"] = self.handle_explorer_new_folder
        self.context_handlers["explorer.import"] = self.handle_explorer_import

        # Viewer context handlers
        self.context_handlers["viewer.close"] = self.handle_viewer_close
        self.context_handlers["viewer.search"] = self.handle_viewer_search
        self.context_handlers["viewer.next_match"] = self.handle_viewer_next_match
        self.context_handlers["viewer.prev_match"] = self.handle_viewer_prev_match
        self.context_handlers["viewer.next_page"] = self.handle_viewer_next_page
        self.context_handlers["viewer.prev_page"] = self.handle_viewer_prev_page
        self.context_handlers["viewer.zoom_in"] = self.handle_viewer_zoom_in
        self.context_handlers["viewer.zoom_out"] = self.handle_viewer_zoom_out
        self.context_handlers["viewer.zoom_fit"] = self.handle_viewer_zoom_fit
        self.context_handlers["viewer.fullscreen"] = self.handle_viewer_fullscreen
        self.context_handlers["viewer.first_page"] = self.handle_viewer_first_page
        self.context_handlers["viewer.last_page"] = self.handle_viewer_last_page
        self.context_handlers["viewer.annotate"] = self.handle_viewer_annotate
        self.context_handlers["viewer.bookmark"] = self.handle_viewer_bookmark
        self.context_handlers["viewer.print"] = self.handle_viewer_print

        # Global context handlers
        self.context_handlers["global.toggle_explorer"] = self.handle_global_toggle_explorer
        self.context_handlers["global.new_document"] = self.handle_global_new_document
        self.context_handlers["global.focus_search"] = self.handle_global_focus_search
        self.context_handlers["global.help"] = self.handle_global_help

    def register_all_shortcuts(self, parent_widget):
        """
        Register all shortcuts for the given widget

        :param parent_widget: Parent widget for shortcuts
        """
        self.unregister_all()

        # Get shortcuts for active context
        shortcuts = self.shortcut_manager.get_active_shortcuts()

        for action, shortcut in shortcuts.items():
            if not shortcut.enabled:
                continue

            self.register_shortcut(parent_widget, action, shortcut)

    def register_shortcut(self, parent_widget, action: str, shortcut: Shortcut):
        """
        Register a single shortcut

        :param parent_widget: Parent widget
        :param action: Action identifier
        :param shortcut: Shortcut configuration
        """
        # Create QKeySequence
        key_sequence = shortcut.to_key_sequence()

        # Create QShortcut
        qshortcut = QShortcut(key_sequence, parent_widget)

        # Set context
        if shortcut.context == "global":
            qshortcut.setContext(Qt.ApplicationShortcut)
        else:
            qshortcut.setContext(Qt.WidgetShortcut)

        # Connect to handler
        if action in self.context_handlers:
            handler = self.context_handlers[action]
            qshortcut.activated.connect(handler)

        # Store reference
        self.registered_shortcuts[action] = qshortcut

    def unregister_all(self):
        """
        Unregister all shortcuts
        """
        for action, qshortcut in self.registered_shortcuts.items():
            qshortcut.setEnabled(False)
            qshortcut.deleteLater()

        self.registered_shortcuts.clear()

    def switch_context(self, context: str):
        """
        Switch active context and update shortcuts

        :param context: New context ('explorer', 'viewer', 'global')
        """
        self.shortcut_manager.set_context(context)

        # Re-register shortcuts with new context
        if self.window and hasattr(self.window, 'ui'):
            self.register_all_shortcuts(self.window)

    def handle_explorer_open(self):
        """
        Handle: Open selected document in explorer
        """
        if not hasattr(self.window, 'controller'):
            return

        # Use document controller to open selected document
        ctrl = self.window.controller

        # Check if document explorer is available
        if hasattr(ctrl, 'document'):
            ctrl.document.open_selected()
        else:
            # Fallback: send notification
            self.window.ui.status("Open document: Opening selected document...")

    def handle_explorer_preview(self):
        """
        Handle: Toggle preview panel in explorer
        """
        if not hasattr(self.window, 'controller'):
            return

        ctrl = self.window.controller
        if hasattr(ctrl, 'document'):
            ctrl.document.toggle_preview()

    def handle_explorer_attach(self):
        """
        Handle: Attach selected document to current chat
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("Attach: Attaching document to chat...")

        # TODO: Implement attach logic with attachment controller
        if hasattr(self.window.controller, 'attachments'):
            # Add selected document to attachments
            pass

    def handle_explorer_index(self):
        """
        Handle: Index selected documents
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("Index: Indexing selected documents...")

        # TODO: Implement index logic with index controller
        if hasattr(self.window.controller, 'idx'):
            # Trigger indexing for selected documents
            pass

    def handle_explorer_delete(self):
        """
        Handle: Delete selected documents
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("Delete: Deleting selected documents...")

        # TODO: Implement delete logic
        # Show confirmation dialog first
        # Then delete selected documents
        if hasattr(self.window.controller, 'document'):
            # Delete selected documents
            pass

    def handle_explorer_search(self):
        """
        Handle: Focus search in explorer
        """
        if not hasattr(self.window, 'controller'):
            return

        # TODO: Focus search box in document explorer
        self.window.ui.status("Search: Focus search box...")

    def handle_explorer_refresh(self):
        """
        Handle: Refresh document list
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("Refresh: Refreshing document list...")

        # TODO: Refresh explorer
        if hasattr(self.window.controller, 'document'):
            # Reload document list
            pass

    def handle_explorer_select_all(self):
        """
        Handle: Select all documents
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("Select all: Selecting all documents...")

        # TODO: Select all documents in explorer
        if hasattr(self.window.ui, 'document_explorer'):
            # Select all items
            pass

    def handle_explorer_new_folder(self):
        """
        Handle: Create new folder
        """
        # TODO: Show dialog to create new folder
        self.window.ui.status("New folder: Creating new folder...")

    def handle_explorer_import(self):
        """
        Handle: Import documents
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("Import: Opening import dialog...")

        # TODO: Open import dialog
        if hasattr(self.window.controller, 'document'):
            # Show import dialog
            pass

    def handle_viewer_close(self):
        """
        Handle: Close document viewer
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("Close: Closing document viewer...")

        # TODO: Close viewer
        if hasattr(self.window.controller, 'document_viewer'):
            self.window.controller.document_viewer.close()

    def handle_viewer_search(self):
        """
        Handle: Show search in document viewer
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("Search: Opening search panel...")

        # TODO: Open search panel in viewer
        if hasattr(self.window.ui, 'document_viewer'):
            # Focus search input
            pass

    def handle_viewer_next_match(self):
        """
        Handle: Next search result
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("Next match: Going to next search result...")

        # TODO: Navigate to next search result
        if hasattr(self.window.controller, 'document_viewer'):
            # Navigate to next match
            pass

    def handle_viewer_prev_match(self):
        """
        Handle: Previous search result
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("Previous match: Going to previous search result...")

        # TODO: Navigate to previous search result
        if hasattr(self.window.controller, 'document_viewer'):
            # Navigate to previous match
            pass

    def handle_viewer_next_page(self):
        """
        Handle: Next page
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("Next page: Going to next page...")

        # TODO: Go to next page
        if hasattr(self.window.controller, 'document_viewer'):
            self.window.controller.document_viewer.next_page()

    def handle_viewer_prev_page(self):
        """
        Handle: Previous page
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("Previous page: Going to previous page...")

        # TODO: Go to previous page
        if hasattr(self.window.controller, 'document_viewer'):
            self.window.controller.document_viewer.prev_page()

    def handle_viewer_zoom_in(self):
        """
        Handle: Zoom in
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("Zoom in: Zooming in...")

        # TODO: Zoom in
        if hasattr(self.window.controller, 'document_viewer'):
            self.window.controller.document_viewer.zoom_in()

    def handle_viewer_zoom_out(self):
        """
        Handle: Zoom out
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("Zoom out: Zooming out...")

        # TODO: Zoom out
        if hasattr(self.window.controller, 'document_viewer'):
            self.window.controller.document_viewer.zoom_out()

    def handle_viewer_zoom_fit(self):
        """
        Handle: Fit to width
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("Zoom fit: Fitting to width...")

        # TODO: Fit to width
        if hasattr(self.window.controller, 'document_viewer'):
            self.window.controller.document_viewer.zoom_fit()

    def handle_viewer_fullscreen(self):
        """
        Handle: Toggle fullscreen
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("Fullscreen: Toggling fullscreen mode...")

        # TODO: Toggle fullscreen
        if hasattr(self.window.controller, 'document_viewer'):
            self.window.controller.document_viewer.toggle_fullscreen()

    def handle_viewer_first_page(self):
        """
        Handle: First page
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("First page: Going to first page...")

        # TODO: Go to first page
        if hasattr(self.window.controller, 'document_viewer'):
            self.window.controller.document_viewer.first_page()

    def handle_viewer_last_page(self):
        """
        Handle: Last page
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("Last page: Going to last page...")

        # TODO: Go to last page
        if hasattr(self.window.controller, 'document_viewer'):
            self.window.controller.document_viewer.last_page()

    def handle_viewer_annotate(self):
        """
        Handle: Add annotation
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("Annotate: Adding highlight...")

        # TODO: Add highlight/annotation
        if hasattr(self.window.controller, 'document_viewer'):
            self.window.controller.document_viewer.add_highlight()

    def handle_viewer_bookmark(self):
        """
        Handle: Toggle bookmark
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("Bookmark: Toggling bookmark...")

        # TODO: Toggle bookmark
        if hasattr(self.window.controller, 'document_viewer'):
            self.window.controller.document_viewer.toggle_bookmark()

    def handle_viewer_print(self):
        """
        Handle: Print document
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("Print: Opening print dialog...")

        # TODO: Open print dialog
        if hasattr(self.window.controller, 'document_viewer'):
            self.window.controller.document_viewer.print()

    def handle_global_toggle_explorer(self):
        """
        Handle: Toggle document explorer panel
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("Toggle explorer: Toggling document explorer...")

        # TODO: Toggle visibility of document explorer
        if hasattr(self.window.controller, 'layout'):
            self.window.controller.layout.toggle_explorer()

    def handle_global_new_document(self):
        """
        Handle: Create new document
        """
        self.window.ui.status("New document: Creating new document...")

        # TODO: Show dialog to create new document
        # Could be blank text file or from template

    def handle_global_focus_search(self):
        """
        Handle: Focus search bar
        """
        if not hasattr(self.window, 'controller'):
            return

        self.window.ui.status("Focus search: Moving focus to search...")

        # TODO: Focus appropriate search box based on context
        if self.shortcut_manager.active_context == "explorer":
            # Focus explorer search
            pass
        elif self.shortcut_manager.active_context == "viewer":
            # Focus viewer search
            pass

    def handle_global_help(self):
        """
        Handle: Show keyboard shortcuts help
        """
        # Show shortcuts dialog
        self.show_shortcuts_help()

    def show_shortcuts_help(self):
        """
        Show keyboard shortcuts help dialog
        """
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton

        dialog = QDialog(self.window)
        dialog.setWindowTitle(trans("shortcuts.help.title"))
        dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout()

        # Get help text
        help_text = self.get_shortcuts_text()

        # Text area
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(help_text)
        layout.addWidget(text_edit)

        # Close button
        close_btn = QPushButton(trans("dialog.close"))
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def get_shortcuts_text(self) -> str:
        """
        Get formatted shortcuts text

        :return: Formatted text
        """
        text = trans("shortcuts.help.title") + "\n"
        text += "=" * 50 + "\n\n"

        # Get shortcuts by context
        contexts = {
            "global": trans("shortcuts.context.global"),
            "explorer": trans("shortcuts.context.explorer"),
            "viewer": trans("shortcuts.context.viewer")
        }

        for context_key, context_label in contexts.items():
            shortcuts = self.shortcut_manager.get_shortcuts_by_context(context_key)

            if not shortcuts:
                continue

            # Add section header
            text += f"{context_label}\n"
            text += "-" * 30 + "\n"

            # Add shortcuts in this context
            for action, shortcut in sorted(shortcuts.items(), key=lambda x: x[1].to_string()):
                if not shortcut.enabled:
                    continue

                key_str = shortcut.to_string().ljust(15)
                desc = shortcut.description
                text += f"  {key_str}  {desc}\n"

            text += "\n"

        return text

    def check_conflicts(self) -> list:
        """
        Check for shortcut conflicts

        :return: List of conflicts
        """
        conflicts = self.shortcut_manager.detect_conflicts()

        if conflicts:
            # Log conflicts
            for conflict in conflicts:
                print(f"Shortcut conflict: {conflict.shortcut1.action} and "
                      f"{conflict.shortcut2.action} in context {conflict.context}")

        return conflicts
