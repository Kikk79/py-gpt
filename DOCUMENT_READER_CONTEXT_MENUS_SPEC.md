# Document Reader Context Menu Redesign Specification

## Overview

This specification redesigns the context menu system for the Document Reader workflow, reducing complexity from 30+ actions to 10 essential, context-aware actions.

## Design Principles

1. **Simplicity**: Only show relevant actions based on context
2. **Clarity**: Use clear labels and icons that communicate purpose
3. **Efficiency**: Group related actions to reduce cognitive load
4. **Consistency**: Follow platform conventions and guidelines
5. **Accessibility**: Keyboard accessible and screen reader friendly

---

## Current State Analysis

### Problem Areas

1. **Action Overload**: 30+ actions overwhelm users
2. **Poor Organization**: Related actions scattered throughout menu
3. **Inconsistent State**: Same action appears in multiple places
4. **Hidden Functionality**: Important features buried in submenus
5. **Lack of Context**: All actions shown regardless of selection

### User Pain Points

- Long visual scan time to find desired action
- Accidental clicks on wrong actions
- Difficulty discovering advanced features
- Inconsistent behavior across different menus

---

## New Design: 10 Essential Actions

### Core Action Set

All context menus will include up to 10 actions, organized into logical groups:

```
┌────────────────────────────┐
│ ⓘ Document Info            │  Group 1: Information
├────────────────────────────┤
│ 📂 Open                    │  Group 2: Primary Actions
│ 🧩 Attach to Chat          │
├────────────────────────────┤
│ 🏷️ Edit Tags...           │  Group 3: Metadata
│ 📁 Move to Folder...      │
│ ✨ Index Document          │
├────────────────────────────┤
│ 📋 Duplicate               │  Group 4: Utilities
│ ⤴️ Export...              │
│ 🗑️ Move to Trash          │
└────────────────────────────┘
```

### Action Reference

| # | Action | Icon | Description | Contexts |
|---|---|---|---|---|
| 1 | Document Info | ⓘ | Show file metadata | All |
| 2 | Open | 📂 | Open in viewer | All |
| 3 | Attach to Chat | 🧩 | Send to AI context | Explorer, Viewer |
| 4 | Edit Tags | 🏷️ | Manage tags | All |
| 5 | Move to Folder | 📁 | Organize document | All |
| 6 | Index Document | ✨ | Enable AI search | Explorer, Viewer, Unindexed |
| 7 | Duplicate | 📋 | Create copy | All |
| 8 | Export | ⤴️ | Export in various formats | All |
| 9 | Move to Trash | 🗑️ | Delete document | All |
| 10 | Preview | 👁️ | Quick preview toggle | Explorer |

---

## Context-Aware Menu Specification

### 1. Document Explorer Context Menu

**Trigger**: Right-click on document item in explorer/grid view

**Actions** (max 10):

```
┌────────────────────────────┐
│ 📄 AI_ML_Research_Paper.pdf│  Header: Document name (non-interactive)
├────────────────────────────┤
│ ⓘ Document Info            │  Group 1: Information
├────────────────────────────┤
│ 📂 Open                    │  Group 2: Primary Actions
│ 👁️ Preview                 │
│ 🧩 Attach to Chat          │
├────────────────────────────┤
│ 🏷️ Edit Tags...           │  Group 3: Metadata & AI
│ 📁 Move to Folder...      │
│ ✨ Index Document          │  [Disabled if already indexed]
├────────────────────────────┤
│ 📋 Duplicate               │  Group 4: File Operations
│ ⤴️ Export...              │
│ 🗑️ Move to Trash          │
└────────────────────────────┘
```

**Dynamic Elements**:
- **Index Document**: Disabled (grayed out) if document is already indexed
- **Attach to Chat**: Enabled only if chat is active
- **Preview**: Enabled only if preview panel is available

### 2. Document Viewer Context Menu

**Trigger**: Right-click on document content in viewer

**Actions** (max 10):

```
┌────────────────────────────┐
│ 🖊️ Highlight Selected     │  Group 1: Selection Actions
│ 📝 Add Note...            │
├────────────────────────────┤
│ 🧩 Attach Section to Chat │  Group 2: AI Integration
│ 🔍 Search Selected        │
├────────────────────────────┤
│ ⓘ Document Info           │  Group 3: Document Actions
│ 📂 Open in New Tab        │
├────────────────────────────┤
│ 📋 Copy Text              │  Group 4: Utilities
│ ⤴️ Export Page...        │
│ 🗑️ Move to Trash          │
└────────────────────────────┘
```

**Selection-Specific Actions**:
- **Highlight Selected**: Appears only when text is selected
- **Add Note**: Active when selection exists
- **Search Selected**: Searches for selected text in document
- **Copy Text**: Standard clipboard operation

### 3. Library/Folder Context Menu

**Trigger**: Right-click on empty space or folder in library

**Actions**:

```
┌────────────────────────────┐
│ 📁 Current Folder          │  Header: Current folder
├────────────────────────────┤
│ 📂 Open in Explorer        │  Group 1: Folder Operations
│ 🔄 Refresh                 │
├────────────────────────────┤
│ 📁 New Folder...          │  Group 2: Create Actions
│ 📄 New Document...         │
│ ⤴️ Import Documents...    │
├────────────────────────────┤
│ 🏷️ Add Tags to All...     │  Group 3: Batch Operations
│ 📋 Select All              │
├────────────────────────────┤
│ Ⓘ Properties               │  Group 4: Information
└────────────────────────────┘
```

**State-Based Actions**:
- **Add Tags to All**: Only enabled if documents exist in folder
- **Select All**: Uses Ctrl+A or right-click option

### 4. Multi-Select Context Menu

**Trigger**: Right-click with multiple documents selected

**Actions**:

```
┌────────────────────────────┐
│ 5 documents selected       │  Header: Selection count
├────────────────────────────┤
│ 📂 Open All                │  Group 1: Bulk Actions
│ 🧩 Attach All to Chat      │
├────────────────────────────┤
│ 🏷️ Edit Tags...           │  Group 2: Metadata
│ 📁 Move to Folder...      │
│ ✨ Index All               │
├────────────────────────────┤
│ 📋 Duplicate All           │  Group 3: File Operations
│ ⤴️ Export All...          │
│ 🗑️ Move All to Trash      │
└────────────────────────────┘
```

**Changes from Single Selection**:
- All actions apply to entire selection
- **Open All**: Opens documents in tabs or sequential viewer
- Confirmation dialogs for destructive actions (delete)

### 5. Search Results Context Menu

**Trigger**: Right-click on result item

**Actions**:

```
┌────────────────────────────┐
│ Found: "machine learning"  │  Header: Search term
│ in AI_ML_Research.pdf      │  Subheader: Document info
├────────────────────────────┤
│ 📂 Open Document           │  Group 1: Navigation
│ 🎯 Jump to Match           │  Group 2: Search Actions
│ 📋 Copy Match Text         │
├────────────────────────────┤
│ 🧩 Attach to Chat          │  Group 3: AI Integration
│ 🔍 Search Similar          │
└────────────────────────────┘
```

**Search-Specific Features**:
- **Jump to Match**: Navigates to exact location in document
- **Copy Match Text**: Copies the context snippet
- **Search Similar**: Finds similar documents

---

## Visual Design Specifications

### Menu Styling

**Dimensions**:
- Width: 220-280px (auto-adjust based on content)
- Padding: 8px vertical, 16px horizontal
- Item height: 32px minimum

**Typography**:
- Font size: 14px
- Font weight: Normal (400)
- Label truncation: Show ellipsis for long names (>30 chars)

**Icons**:
- Size: 16x16px
- Position: Left of label, 8px margin
- Style: Consistent icon set (Feather or Tabler)

**Colors**:
- Background: --context-menu-bg (#2a2a2a in dark, #ffffff in light)
- Text: --text-primary (#e0e0e0 in dark, #212121 in light)
- Disabled: --text-disabled (opacity: 0.5)
- Hover: --hover-bg (rgba(255,255,255,0.1) in dark)

**Borders**:
- Radius: 8px
- Shadow: Drop shadow with blur (0 4px 12px rgba(0,0,0,0.15))
- Separator: 1px solid --border-color (#404040 in dark)

### Interactive States

**Normal**:
- Full opacity (1.0)
- Cursor: pointer
- Background: transparent

**Hover**:
- Background: --hover-bg
- Cursor: pointer
- Transition: 150ms ease-in-out

**Disabled**:
- Opacity: 0.5
- Cursor: not-allowed
- No hover effect

**Active/Pressed**:
- Background: --active-bg (slightly darker than hover)
- Brief scale effect (scale: 0.98)
- Duration: 100ms

### Submenu Indicators

**Submenu Arrow**:
- Icon: "▶" (U+25B6)
- Position: Right side, 8px padding
- Color: --text-secondary
- Rotation: 0deg (normal), 90deg (expanded)

---

## Implementation Architecture

### Context Menu Builder Pattern

```python
# Menu builder for creating context menus dynamically
class DocumentContextMenuBuilder:
    """
    Builder for creating context-aware document menus
    """

    def __init__(self, window=None):
        self.window = window
        self.menu = QMenu()
        self.separator_after_header = False

    def add_header(self, title: str, subtitle: str = None):
        """Add document/folder header"""
        header = self._create_header_widget(title, subtitle)
        action = QWidgetAction(self.menu)
        action.setDefaultWidget(header)
        self.menu.addAction(action)
        self.separator_after_header = True
        return self

    def add_action(self, text: str, icon=None, callback=None, enabled=True, shortcut=None):
        """Add menu action"""
        if self.separator_after_header:
            self.menu.addSeparator()
            self.separator_after_header = False

        action = QAction(text, self.menu)
        if icon:
            action.setIcon(icon)
        if shortcut:
            action.setShortcut(shortcut)
        action.setEnabled(enabled)

        if callback:
            action.triggered.connect(callback)

        self.menu.addAction(action)
        return self

    def add_separator(self):
        """Add separator"""
        self.menu.addSeparator()
        return self

    def build(self) -> QMenu:
        """Build and return menu"""
        return self.menu
```

### Context Detection System

```python
class ContextDetector:
    """
    Detects context for context menu creation
    """

    def __init__(self, window=None):
        self.window = window

    def get_context(self, position, selected_items) -> MenuContext:
        """
        Detect context for menu creation

        :param position: QPosition of right-click
        :param selected_items: List of selected items
        :return: MenuContext enum
        """
        if len(selected_items) == 0:
            return MenuContext.LIBRARY
        elif len(selected_items) == 1:
            item = selected_items[0]
            if item.type == "document":
                return MenuContext.EXPLORER
        elif len(selected_items) > 1:
            return MenuContext.MULTI_SELECT

        return MenuContext.EXPLORER

    def get_document_state(self, document_id: str) -> DocumentState:
        """
        Get document state for enabling/disabling actions

        :param document_id: Document ID
        :return: DocumentState object
        """
        # Check if indexed
        is_indexed = self.window.core.document.is_indexed(document_id)

        # Check if attached
        is_attached = self.window.core.attachments.has_document(document_id)

        return DocumentState(
            indexed=is_indexed,
            attached=is_attached,
            has_selection=False  # Based on viewer state
        )
```

### Factory Pattern for Menu Creation

```python
class ContextMenuFactory:
    """
    Factory for creating context-specific menus
    """

    def __init__(self, window=None):
        self.window = window
        self.builders = {
            MenuContext.EXPLORER: DocumentExplorerMenuBuilder(window),
            MenuContext.VIEWER: DocumentViewerMenuBuilder(window),
            MenuContext.LIBRARY: LibraryMenuBuilder(window),
            MenuContext.MULTI_SELECT: MultiSelectMenuBuilder(window),
            MenuContext.SEARCH_RESULTS: SearchResultsMenuBuilder(window)
        }

    def create_menu(self, context: MenuContext, **kwargs) -> QMenu:
        """
        Create context menu

        :param context: MenuContext type
        :param kwargs: Additional parameters
        :return: QMenu instance
        """
        builder = self.builders.get(context)
        if not builder:
            return QMenu()

        return builder.build(**kwargs)
```

---

## Action Grouping Strategy

### Group 1: Information (Contextual Awareness)

**Purpose**: Provide context about the item
- Shows what user has clicked
- Displays relevant metadata
- Offers preview before action

**Actions**:
- Document Info (ⓘ)
- Properties (folder)
- Document/folder header

### Group 2: Primary Actions (Most Frequent)

**Purpose**: Most commonly used actions
- Based on user research and analytics
- Always visible and accessible
- Large touch targets

**Actions**:
- Open (📂)
- Preview (👁️)
- Attach to Chat (🧩)
- Jump to Match (search results)

### Group 3: Metadata & AI (Intelligent Features)

**Purpose**: AI-powered and metadata operations
- Context-aware enabling/disabling
- Progressive disclosure
- Intelligent defaults

**Actions**:
- Edit Tags (🏷️)
- Move to Folder (📁)
- Index Document (✨)
- Search Similar (🔍)

### Group 4: Utilities & Destructive (Less Frequent)

**Purpose**: Utilities and dangerous actions
- Confirmation for destructive actions
- Grouped together for safety
- Clear visual distinction

**Actions**:
- Duplicate (📋)
- Export (⤴️)
- Move to Trash (🗑️)

---

## State Management

### Document States

```python
class DocumentState:
    """
    State information for enabling/disabling actions
    """

    def __init__(self,
                 indexed: bool = False,
                 has_annotations: bool = False,
                 is_starred: bool = False,
                 has_selection: bool = False,
                 chat_active: bool = False):
        self.indexed = indexed
        self.has_annotations = has_annotations
        self.is_starred = is_starred
        self.has_selection = has_selection
        self.chat_active = chat_active
```

### Action State Matrix

| Action | No Selection | Single Doc | Multi-Select | No Doc Indexed | Chat Active | Has Selection |
|---|---|---|---|---|---|---|
| Open | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Preview | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Attach | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Index | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ |
| Delete | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Annotate | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ |

**Legend**:
- ✅: Action enabled
- ❌: Action disabled
- Action text may change (plural for multi-select)

---

## Accessibility Considerations

### Keyboard Navigation

**Menu Navigation**:
- Up/Down arrow keys navigate items
- Enter selects focused item
- Escape closes menu
- Home/End jump to first/last item
- Type to jump to item by first letter

**Shortcut Display**:
- Show keyboard shortcuts in menus
- Right-align in menu items
- Consistent formatting (Ctrl+O)

### Screen Reader Support

**ARIA Labels**:
- `role="menu"` for context menu
- `role="menuitem"` for actions
- `aria-disabled="true"` for disabled items
- `aria-checked` for toggle actions

**Announced Information**:
- "Context menu, 10 items"
- "Open, Ctrl+O, menu item"
- "Index Document, unavailable, menu item"

---

## Migration Strategy

### Phase 1: New Menu System (Side-by-Side)

- Implement new context menu system
- Keep old menus temporarily accessible
- Gather user feedback
- Measure usage analytics

### Phase 2: Deprecation

- Old menu opt-in only (advanced settings)
- New menus as default
- User preference for old menu available
- Monitor complaints/feedback

### Phase 3: Full Migration

- Remove old menu code
- Clean up legacy action handlers
- Update documentation
- Remove user preference toggle

---

## Testing Protocol

### Functionality Tests

- [ ] All 10 actions work correctly
- [ ] Disabled actions appear grayed out
- [ ] Multi-select changes action labels appropriately
- [ ] Context detection works accurately
- [ ] Keyboard navigation functions properly

### User Experience Tests

- [ ] Users can find actions quickly
- [ ] Common tasks take fewer clicks
- [ ] Error rate reduced for common operations
- [ ] Menu doesn't overflow screen edges
- [ ] Submenus appear in correct position

### Performance Tests

- [ ] Menu opens within 100ms
- [ ] No lag when right-clicking
- [ ] Memory usage reasonable (< 10MB for menu system)
- [ ] No memory leaks on repeated opening

---

## Future Enhancements

### Phase 2 Features

**Smart Suggestions**:
- AI-powered action suggestions
- Frequently used actions at top
- Time-based context (e.g., "Archive" for old docs)

**Customizable Menus**:
- User-defined action ordering
- Hide/show rarely used actions
- Custom action groups

**Quick Actions**:
- Pin frequently used actions
- Custom keyboard shortcuts for actions
- Action favoriting system

---

## Appendix

### Icon Set Recommendation

**Recommended**: Tabler Icons (open source, consistent style)
- Consistent 24x24 outline style
- 1,000+ icons available
- MIT licensed
- Webfont and SVG formats

**Alternative**: Feather Icons (similar, smaller set)

### Animation Specification

**Menu Open**:
- Duration: 200ms
- Easing: ease-out
- Transform: scale(0.95) to scale(1.0)
- Opacity: 0 to 1

**Menu Close**:
- Duration: 150ms
- Easing: ease-in
- No scale (avoids visual jump)
- Opacity: 1 to 0

**Hover State**:
- Duration: 150ms
- Background color fade
- Subtle scale (1.0 to 1.01 for feedback)

---

Version: 1.0
Date: 2025-01-20
Status: Draft
Compatible With: PyGPT Document Reader Workflow v1.0
