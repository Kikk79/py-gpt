# Quick Start: DocumentViewerHeader
## 5-Minute Integration Guide

---

## 🚀 Instant Usage

### 1. Import
```python
from pygpt_net.ui.widget.document_viewer import DocumentViewerHeader
```

### 2. Create Widget
```python
header = DocumentViewerHeader()
```

### 3. Connect Signals
```python
header.preview_requested.connect(on_preview)
header.attach_requested.connect(on_attach)
header.index_requested.connect(on_index)
header.more_actions_requested.connect(on_more)
```

### 4. Load Document
```python
header.update_metadata({
    'name': 'document.pdf',
    'size': 1048576,  # bytes
    'type': 'PDF Document',
    'modified': 1699999999.0,  # timestamp
    'indexed_in': ['index1']
})
```

### 5. Show Progress
```python
header.start_loading()
header.set_progress(50)  # 0-100
header.finish_loading()
```

**Done! You have a fully functional document header.**

---

## 📋 Common Patterns

### Pattern 1: Streaming File Load
```python
def load_document(file_path):
    # Start
    header.start_loading()
    header.update_metadata(extract_metadata(file_path))

    # Stream with progress
    for progress in stream_load(file_path):
        header.set_progress(progress)

    # Finish
    header.finish_loading()
```

### Pattern 2: Error Handling
```python
try:
    load_document(path)
except FileNotFoundError:
    header.show_error("File not found", "error")
except PermissionError:
    header.show_error("Permission denied", "warning")
```

### Pattern 3: Action Handlers
```python
def on_preview():
    subprocess.run(['xdg-open', current_file])

def on_attach():
    chat.add_attachment(current_file)

def on_index():
    show_index_selection_dialog()
```

---

## 🎯 Essential API

### Metadata Update
```python
header.update_metadata({
    'name': str,           # Required: filename
    'size': int,           # Required: bytes
    'type': str,           # Required: file type
    'modified': float,     # Optional: timestamp
    'indexed_in': list     # Optional: index names
})
```

### Progress Control
```python
header.set_progress(50)        # Set to 50%
header.set_progress(75, True)  # Animate to 75%
header.start_loading()         # Reset to 0%
header.finish_loading()        # Animate to 100%, then hide
```

### Error Display
```python
header.show_error(msg, "warning")   # Yellow
header.show_error(msg, "error")     # Red
header.show_error(msg, "critical")  # Dark red
header.hide_error()                 # Dismiss
```

### State Management
```python
header.clear()              # Reset all
is_loading = header.is_loading()
metadata = header.get_metadata()
```

---

## 🔌 Integration Checklist

- [ ] Import DocumentViewerHeader
- [ ] Create instance
- [ ] Connect 4 signals (preview, attach, index, more)
- [ ] Add to layout (QVBoxLayout)
- [ ] Call update_metadata() on document load
- [ ] Call set_progress() during streaming
- [ ] Handle show_error() for failures

---

## 📐 Layout Example

```python
# Vertical layout
layout = QVBoxLayout()
layout.addWidget(header)           # Fixed height (100-160px)
layout.addWidget(content_viewer)   # Expandable

# In main window
dock = QDockWidget("Documents")
dock.setWidget(viewer_widget)
window.addDockWidget(Qt.RightDockWidgetArea, dock)
```

---

## 🎨 Styling (Optional)

Uses Qt palette by default. To customize:

```python
header.setStyleSheet("""
    #document_viewer_header {
        background-color: #2b2b2b;
    }
    #toolbar_button {
        padding: 8px 14px;
    }
""")
```

---

## ⚡ Performance Tips

1. **Batch Progress Updates**: Update every 100ms minimum
2. **Animate Progress**: Use `animate=True` for smooth UX
3. **Lazy Metadata**: Only extract when needed
4. **Signal Throttling**: Debounce rapid updates

---

## 🐛 Troubleshooting

### Icons Not Showing
```python
# Ensure Qt resources are initialized
# In main:
import sys
from PySide6.QtCore import QResource
QResource.registerResource("resources.rcc")
```

### Progress Not Animating
```python
# Ensure Qt event loop is running
QApplication.processEvents()
```

### Buttons Not Responding
```python
# Check if metadata is set (buttons disabled without it)
header.update_metadata({'name': 'test', 'size': 100, 'type': 'text'})
```

---

## 📚 Full Documentation

- **Implementation**: `src/pygpt_net/ui/widget/document_viewer.py`
- **README**: `DOCUMENT_VIEWER_HEADER_README.md`
- **Integration**: `document_viewer_integration_example.py`
- **Tests**: `test_document_viewer_header.py`
- **Deliverable**: `PHASE1_WEEK3_DAY1-2_DELIVERABLE.md`

---

## 🤝 Support

For questions or issues:
1. Check inline docstrings in `document_viewer.py`
2. Run test script: `python3 test_document_viewer_header.py`
3. Review integration example: `document_viewer_integration_example.py`

---

**That's it! You're ready to use DocumentViewerHeader in 5 minutes.**
