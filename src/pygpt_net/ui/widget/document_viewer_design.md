# Unified Document Viewer Widget Design
**B1: UI Component Engineer - Phase 1 Week 2 Deliverable**

## Architecture Overview

```
UnifiedDocumentViewer (QWidget)
├── HeaderBar (QHBoxLayout)
│   ├── FileInfo (name, size, type)
│   ├── ProgressBar (for loading)
│   └── ActionToolbar (preview, attach, index, delete)
├── ContentArea (QStackedWidget - multi-type support)
│   ├── TextViewer (QTextEdit with syntax highlighting)
│   ├── PDFViewer (QWebEngineView or custom)
│   ├── ImageViewer (QLabel with QPixmap)
│   ├── CodeViewer (QPlainTextEdit with lexer)
│   └── MediaPlayer (QMediaPlayer widget)
├── FooterBar (QHBoxLayout)
│   ├── FileStats (lines, words, chars for text)
│   ├── IndexStatus (indexed in: idx1, idx2)
│   └── LastModified (timestamp)
└── ErrorPanel (QMessageBox - collapsible)
```

## Component Specifications

### 1. Header Bar
```python
class DocumentViewerHeader(QWidget):
    """
    Displays file metadata and loading progress
    """
    def __init__(self):
        self.file_label = QLabel()  # "filename.txt (2.3 MB)"
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(8)
        self.progress_bar.setStyleSheet("..."
            # Minimal, clean progress bar
        )
        self.action_toolbar = QToolBar()

        # Actions: Preview | Attach | Index | Delete
        self.action_toolbar.setIconSize(QSize(20, 20))
```

### 2. Content Area - Multi-Type Support

```python
class DocumentContentViewer(QStackedWidget):
    """
    Switches between viewer types based on document type
    """

    # Type-to-Widget mapping
    VIEWERS = {
        DocumentType.TEXT: TextDocumentViewer,
        DocumentType.CODE: CodeDocumentViewer,
        DocumentType.PDF: PDFDocumentViewer,
        DocumentType.IMAGE: ImageDocumentViewer,
        DocumentType.VIDEO: MediaDocumentViewer,
    }

    def display_document(self, path: str, metadata: DocumentMetadata):
        """Load and display document"""
        viewer_class = self.VIEWERS.get(
            metadata.document_type,
            TextDocumentViewer  # Fallback
        )
        viewer = viewer_class()
        self.addWidget(viewer)
        self.setCurrentWidget(viewer)

        # Start loading with progress callbacks
        viewer.load_streaming(path)
```

### 3. Text Document Viewer (for .txt, .md, .json, etc.)

```python
class TextDocumentViewer(QWidget):
    """
    Plain text with syntax highlighting and line numbers
    """
    def __init__(self):
        self.editor = QPlainTextEdit()
        self.editor.setReadOnly(True)

        # Syntax highlighting
        self.highlighter = PythonSyntaxHighlighter(self.editor.document())

        # Line numbers
        self.line_number_area = LineNumberArea(self.editor)

        # Features
        self.editor.setFont(QFont("Courier", 10))
        self.editor.setWordWrapMode(QTextOption.NoWrap)

    def load_streaming(self, path: str, chunk_size: int = 8192):
        """
        Load text with:
        - Skeleton screen while loading
        - Progress updates every 100ms
        - Syntax highlighting applied per chunk
        """
        self.show_skeleton_screen()

        loader = TextDocumentLoader()
        for chunk in loader.load_streaming(path, chunk_size):
            # Insert chunk
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.insertText(chunk)

            # Apply highlighting
            self.highlighter.rehighlight()

            # Update progress
            QApplication.processEvents()  # Keep UI responsive
```

### 4. Code Document Viewer

```python
class CodeDocumentViewer(QWidget):
    """
    Code with language-specific syntax highlighting
    """
    LANGUAGE_MAPPING = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.json': 'json',
        '.html': 'html',
        '.css': 'css',
        '.xml': 'xml',
    }

    def detect_language(self, file_path: str) -> str:
        """Auto-detect language from file extension"""
        ext = Path(file_path).suffix.lower()
        return self.LANGUAGE_MAPPING.get(ext, 'text')
```

### 5. PDF Viewer

```python
class PDFDocumentViewer(QWidget):
    """
    PDF with scrollable pages (using QPdfDocument if available)
    """
    def __init__(self):
        # Option 1: QPdfDocument (Qt 5.10+)
        self.pdf_view = QPdfView()
        self.pdf_doc = QPdfDocument()

        # Option 2: QWebEngineView fallback
        self.web_view = QWebEngineView()
```

### 6. Image Viewer

```python
class ImageDocumentViewer(QWidget):
    """
    Image with zoom controls
    """
    def __init__(self):
        self.image_label = QLabel()
        self.image_label.setScaledContents(False)
        self.image_label.setAlignment(Qt.AlignCenter)

        # Zoom buttons
        self.zoom_in_btn = QPushButton("+")
        self.zoom_out_btn = QPushButton("-")
        self.fit_btn = QPushButton("Fit")

        self.scale_factor = 1.0
```

## Progressive Loading & Skeleton Screen

```python
class SkeletonScreen(QWidget):
    """
    Placeholder while loading
    """
    def __init__(self):
        self.layout = QVBoxLayout()

        # Animated shimmer effect
        self.animation = QPropertyAnimation(self, b"color")
        self.animation.setStartValue(QColor(200, 200, 200))
        self.animation.setEndValue(QColor(240, 240, 240))
        self.animation.setDuration(1000)
        self.animation.start(QAbstractAnimation.Looping)

        # Skeleton lines
        for i in range(5):
            skeleton_line = QLabel()
            skeleton_line.setFixedHeight(20)
            skeleton_line.setStyleSheet("background: #e0e0e0; border-radius: 4px;")
            self.layout.addWidget(skeleton_line)
```

## Error State Handling

```python
class DocumentErrorPanel(QWidget):
    """
    Displays errors without blocking interface
    """
    SEVERITY_COLORS = {
        ErrorSeverity.WARNING: "#FFF3CD",
        ErrorSeverity.ERROR: "#F8D7DA",
        ErrorSeverity.CRITICAL: "#F5C6CB",
    }

    def show_error(self, error: LoadError):
        self.error_icon = QLabel("⚠️")
        self.error_msg = QLabel(error.message)
        self.suggestion = QLabel(f"💡 {error.suggestion}")
        self.suggestion.setStyleSheet("color: #0066cc; font-weight: bold;")

        # Collapsible details
        self.details = QTextEdit()
        self.details.setPlainText(error.traceback)
        self.details.hide()
```

## Action Toolbar Layout

```
[File Icon] filename.txt (2.3 MB)  [Progress: ▓▓▓░░ 60%]  | Preview | Attach | Index | ⋮ Delete
```

### Actions
- **Preview**: Open in external viewer
- **Attach**: Add to current chat
- **Index**: Add to selected index (submenu)
- **Delete**: Remove file
- **Copy Path**: Copy to clipboard

## Responsive Design

### Desktop (1920x1080)
- Full width document viewer
- Header: 60px
- Footer: 40px
- Content: full remaining

### Tablet (768x1024)
- Single column layout
- Optimized button sizes
- Touch-friendly (44px minimum tap targets)

### Mobile (375x667)
- Stacked layout
- Action buttons in bottom sheet
- Zoom controls visible

## Success Metrics

- ✅ Supports all 5 document types
- ✅ Loading shows progress every 100ms
- ✅ Skeleton screen visible for >500ms loads
- ✅ Error display doesn't crash viewer
- ✅ <16ms render time per chunk
- ✅ <100ms total action response time

## Performance Optimizations

1. **Lazy rendering**: Only render visible area (virtual scrolling)
2. **Chunk-based updates**: Process text in 8KB chunks
3. **Syntax highlighting debounce**: Update every 500ms, not every keystroke
4. **Image scaling**: Pre-scale large images before display
5. **Memory cleanup**: Release document memory after viewing
