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

from typing import Dict, List, Optional, Tuple
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence


class Shortcut:
    """
    Shortcut configuration model
    """

    def __init__(self,
                 action: str,
                 key: str,
                 modifier: str = None,
                 description: str = "",
                 context: str = "global",
                 enabled: bool = True):
        """
        Initialize shortcut

        :param action: Action identifier (e.g., 'document.open')
        :param key: Key name (e.g., 'O')
        :param modifier: Modifier key (e.g., 'Ctrl', 'Alt', 'Shift')
        :param description: Human-readable description
        :param context: Context where shortcut is active ('global', 'viewer', 'explorer')
        :param enabled: Whether shortcut is enabled
        """
        self.action = action
        self.key = key
        self.modifier = modifier
        self.description = description
        self.context = context
        self.enabled = enabled

    def to_key_sequence(self) -> QKeySequence:
        """
        Convert to QKeySequence

        :return: QKeySequence object
        """
        if self.modifier:
            return QKeySequence(f"{self.modifier}+{self.key}")
        return QKeySequence(self.key)

    def to_string(self) -> str:
        """
        Convert to display string

        :return: Formatted string like "Ctrl+O"
        """
        if self.modifier:
            return f"{self.modifier}+{self.key}"
        return self.key

    def matches(self, key_event) -> bool:
        """
        Check if key event matches this shortcut

        :param key_event: QKeyEvent
        :return: True if matches
        """
        # Check key
        key_name = f"Key_{self.key}"
        if not hasattr(Qt, key_name):
            return False

        key_code = getattr(Qt, key_name)
        if key_event.key() != key_code:
            return False

        # Check modifier
        if self.modifier:
            if self.modifier == "Ctrl" and not key_event.modifiers() & Qt.ControlModifier:
                return False
            if self.modifier == "Alt" and not key_event.modifiers() & Qt.AltModifier:
                return False
            if self.modifier == "Shift" and not key_event.modifiers() & Qt.ShiftModifier:
                return False
        elif key_event.modifiers() != Qt.NoModifier:
            return False

        return True


class ShortcutConflict:
    """
    Shortcut conflict information
    """

    def __init__(self, shortcut1: Shortcut, shortcut2: Shortcut, context: str):
        """
        Initialize conflict

        :param shortcut1: First conflicting shortcut
        :param shortcut2: Second conflicting shortcut
        :param context: Context where conflict occurs
        """
        self.shortcut1 = shortcut1
        self.shortcut2 = shortcut2
        self.context = context


class ShortcutManager:
    """
    Shortcut manager for Document Reader workflow
    Handles registration, conflict detection, and context switching
    """

    # Predefined shortcut sets for different contexts
    DEFAULT_SHORTCUTS = {
        # Document Explorer Shortcuts (available in library/explorer)
        "explorer.open": Shortcut(
            action="explorer.open",
            key="O",
            modifier="Ctrl",
            description="Open selected document",
            context="explorer"
        ),
        "explorer.preview": Shortcut(
            action="explorer.preview",
            key="Space",
            modifier=None,
            description="Toggle preview panel",
            context="explorer"
        ),
        "explorer.attach": Shortcut(
            action="explorer.attach",
            key="A",
            modifier="Ctrl",
            description="Attach to current chat",
            context="explorer"
        ),
        "explorer.index": Shortcut(
            action="explorer.index",
            key="I",
            modifier="Ctrl",
            description="Index selected documents",
            context="explorer"
        ),
        "explorer.delete": Shortcut(
            action="explorer.delete",
            key="Delete",
            modifier=None,
            description="Delete selected documents",
            context="explorer"
        ),
        "explorer.search": Shortcut(
            action="explorer.search",
            key="F",
            modifier="Ctrl",
            description="Search documents",
            context="explorer"
        ),
        "explorer.refresh": Shortcut(
            action="explorer.refresh",
            key="R",
            modifier="Ctrl",
            description="Refresh document list",
            context="explorer"
        ),
        "explorer.select_all": Shortcut(
            action="explorer.select_all",
            key="A",
            modifier="Ctrl",
            description="Select all documents",
            context="explorer"
        ),
        "explorer.new_folder": Shortcut(
            action="explorer.new_folder",
            key="N",
            modifier="Ctrl+Shift",
            description="Create new folder",
            context="explorer"
        ),
        "explorer.import": Shortcut(
            action="explorer.import",
            key="I",
            modifier="Ctrl+Shift",
            description="Import documents",
            context="explorer"
        ),

        # Document Viewer Shortcuts (available in reading mode)
        "viewer.close": Shortcut(
            action="viewer.close",
            key="W",
            modifier="Ctrl",
            description="Close document",
            context="viewer"
        ),
        "viewer.search": Shortcut(
            action="viewer.search",
            key="F",
            modifier="Ctrl",
            description="Find in document",
            context="viewer"
        ),
        "viewer.next_match": Shortcut(
            action="viewer.next_match",
            key="F3",
            modifier=None,
            description="Next search match",
            context="viewer"
        ),
        "viewer.prev_match": Shortcut(
            action="viewer.prev_match",
            key="F3",
            modifier="Shift",
            description="Previous search match",
            context="viewer"
        ),
        "viewer.next_page": Shortcut(
            action="viewer.next_page",
            key="ArrowDown",
            modifier=None,
            description="Next page",
            context="viewer"
        ),
        "viewer.prev_page": Shortcut(
            action="viewer.prev_page",
            key="ArrowUp",
            modifier=None,
            description="Previous page",
            context="viewer"
        ),
        "viewer.zoom_in": Shortcut(
            action="viewer.zoom_in",
            key="Plus",
            modifier="Ctrl",
            description="Zoom in",
            context="viewer"
        ),
        "viewer.zoom_out": Shortcut(
            action="viewer.zoom_out",
            key="Minus",
            modifier="Ctrl",
            description="Zoom out",
            context="viewer"
        ),
        "viewer.zoom_fit": Shortcut(
            action="viewer.zoom_fit",
            key="0",
            modifier="Ctrl",
            description="Fit to width",
            context="viewer"
        ),
        "viewer.fullscreen": Shortcut(
            action="viewer.fullscreen",
            key="F11",
            modifier=None,
            description="Toggle fullscreen",
            context="viewer"
        ),
        "viewer.first_page": Shortcut(
            action="viewer.first_page",
            key="Home",
            modifier=None,
            description="First page",
            context="viewer"
        ),
        "viewer.last_page": Shortcut(
            action="viewer.last_page",
            key="End",
            modifier=None,
            description="Last page",
            context="viewer"
        ),
        "viewer.annotate": Shortcut(
            action="viewer.annotate",
            key="H",
            modifier="Ctrl",
            description="Add highlight",
            context="viewer"
        ),
        "viewer.bookmark": Shortcut(
            action="viewer.bookmark",
            key="D",
            modifier="Ctrl",
            description="Toggle bookmark",
            context="viewer"
        ),
        "viewer.print": Shortcut(
            action="viewer.print",
            key="P",
            modifier="Ctrl",
            description="Print document",
            context="viewer"
        ),

        # Global Shortcuts (available everywhere)
        "global.toggle_explorer": Shortcut(
            action="global.toggle_explorer",
            key="E",
            modifier="Ctrl+Shift",
            description="Toggle document explorer",
            context="global"
        ),
        "global.new_document": Shortcut(
            action="global.new_document",
            key="N",
            modifier="Ctrl+Shift+D",
            description="Create new document",
            context="global"
        ),
        "global.focus_search": Shortcut(
            action="global.focus_search",
            key="/",
            modifier=None,
            description="Focus search bar",
            context="global"
        ),
        "global.help": Shortcut(
            action="global.help",
            key="?",
            modifier=None,
            description="Show keyboard shortcuts",
            context="global"
        )
    }

    def __init__(self):
        """
        Initialize shortcut manager
        """
        self.shortcuts: Dict[str, Shortcut] = {}
        self.active_context: str = "global"
        self.load_default_shortcuts()

    def load_default_shortcuts(self):
        """
        Load default shortcuts
        """
        self.shortcuts = self.DEFAULT_SHORTCUTS.copy()

    def get_shortcut(self, action: str) -> Optional[Shortcut]:
        """
        Get shortcut by action

        :param action: Action identifier
        :return: Shortcut object or None
        """
        return self.shortcuts.get(action)

    def get_shortcuts_by_context(self, context: str) -> Dict[str, Shortcut]:
        """
        Get all shortcuts for a context

        :param context: Context name ('global', 'explorer', 'viewer')
        :return: Dictionary of shortcuts
        """
        return {
            action: shortcut
            for action, shortcut in self.shortcuts.items()
            if shortcut.context == context or shortcut.context == "global"
        }

    def get_active_shortcuts(self) -> Dict[str, Shortcut]:
        """
        Get shortcuts for currently active context

        :return: Dictionary of active shortcuts
        """
        return self.get_shortcuts_by_context(self.active_context)

    def register_shortcut(self, shortcut: Shortcut):
        """
        Register a new shortcut

        :param shortcut: Shortcut object to register
        """
        self.shortcuts[shortcut.action] = shortcut

    def unregister_shortcut(self, action: str):
        """
        Unregister a shortcut

        :param action: Action identifier
        """
        if action in self.shortcuts:
            del self.shortcuts[action]

    def update_shortcut(self, action: str, key: str, modifier: str = None):
        """
        Update existing shortcut key combination

        :param action: Action identifier
        :param key: New key
        :param modifier: New modifier
        """
        if action in self.shortcuts:
            self.shortcuts[action].key = key
            self.shortcuts[action].modifier = modifier

    def enable_shortcut(self, action: str):
        """
        Enable a shortcut

        :param action: Action identifier
        """
        if action in self.shortcuts:
            self.shortcuts[action].enabled = True

    def disable_shortcut(self, action: str):
        """
        Disable a shortcut

        :param action: Action identifier
        """
        if action in self.shortcuts:
            self.shortcuts[action].enabled = False

    def set_context(self, context: str):
        """
        Set active context

        :param context: Context name
        """
        self.active_context = context

    def detect_conflicts(self) -> List[ShortcutConflict]:
        """
        Detect shortcut conflicts within contexts

        :return: List of conflicts
        """
        conflicts = []
        contexts = ["global", "explorer", "viewer"]

        for context in contexts:
            shortcuts = self.get_shortcuts_by_context(context)
            seen = {}

            for action, shortcut in shortcuts.items():
                if not shortcut.enabled:
                    continue

                key_combo = shortcut.to_string()

                if key_combo in seen:
                    conflicts.append(ShortcutConflict(
                        shortcut1=seen[key_combo],
                        shortcut2=shortcut,
                        context=context
                    ))
                else:
                    seen[key_combo] = shortcut

        return conflicts

    def resolve_conflict(self, action: str, new_key: str, new_modifier: str = None):
        """
        Resolve conflict by reassigning shortcut

        :param action: Action to reassign
        :param new_key: New key
        :param new_modifier: New modifier
        """
        self.update_shortcut(action, new_key, new_modifier)

    def export_config(self) -> Dict:
        """
        Export shortcuts configuration

        :return: Configuration dictionary
        """
        config = {}
        for action, shortcut in self.shortcuts.items():
            config[action] = {
                "key": shortcut.key,
                "modifier": shortcut.modifier,
                "description": shortcut.description,
                "context": shortcut.context,
                "enabled": shortcut.enabled
            }
        return config

    def import_config(self, config: Dict):
        """
        Import shortcuts configuration

        :param config: Configuration dictionary
        """
        for action, shortcut_config in config.items():
            shortcut = Shortcut(
                action=action,
                key=shortcut_config.get("key", ""),
                modifier=shortcut_config.get("modifier", None),
                description=shortcut_config.get("description", ""),
                context=shortcut_config.get("context", "global"),
                enabled=shortcut_config.get("enabled", True)
            )
            self.shortcuts[action] = shortcut

    def get_shortcut_help(self, context: str = None) -> List[Tuple[str, str, str]]:
        """
        Get formatted help text for shortcuts

        :param context: Context to filter by (None for all)
        :return: List of tuples (key, description, context)
        """
        help_text = []

        shortcuts = self.shortcuts.values()
        if context:
            shortcuts = [s for s in shortcuts if s.context == context or s.context == "global"]

        # Group by context
        contexts = ["global", "explorer", "viewer"]

        for ctx in contexts:
            if context and ctx not in [context, "global"]:
                continue

            ctx_shortcuts = [s for s in shortcuts if s.context == ctx]
            if not ctx_shortcuts:
                continue

            for shortcut in sorted(ctx_shortcuts, key=lambda s: s.to_string()):
                if shortcut.enabled:
                    help_text.append((
                        shortcut.to_string(),
                        shortcut.description,
                        shortcut.context
                    ))

        return help_text


def create_default_shortcut_manager() -> ShortcutManager:
    """
    Create shortcut manager with default shortcuts

    :return: Configured ShortcutManager instance
    """
    return ShortcutManager()
