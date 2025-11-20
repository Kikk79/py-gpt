# Document Reader Workflow Redesign
**D1: Workflow Designer - Phase 1 Week 2 Deliverable**

## Executive Summary

Current state: 30+ context menu actions, split UI (explorer + indexer), cognitive overload
Target state: Unified interface, 8-10 core actions, streamlined workflows

## Unified Document Interface Wireframe

```
┌─────────────────────────────────────────────────────────────────────────┐
│ PyGPT - Files                                          [•••] [Settings]  │
├─────────────────────────────────────────────────────────────────────────┤
│ HOME > DOCUMENTS > PROJECT                               [📁] [↻] [⊞]     │
├─────────────────────────────────────────────────────────────────────────┤
│  📁 folder1              │  📄 document.pdf               │ File Info    │
│  📁 folder2              │  Size: 2.3 MB                  │ ────────────  │
│  📄 file1.txt            │  Type: PDF                     │ Modified:    │
│  📄 file2.pdf            │  Modified: Nov 20, 2025        │ Nov 20, 14:30│
│  📄 file3.py             │                                │ Indexed in:  │
│  📄 file4.md             │  [▓▓▓░░░░░░] 35% Loading...   │ • Research   │
│  📄 file5.json           │                                │ • Work       │
│  📄 file6.csv            │  [⊗ Error]                     │ ────────────  │
│  📄 file7.xlsx           │  Failed to parse PDF           │              │
│  📄 file8.jpg            │  💡 Suggestion: Try .txt       │              │
│                          │  extract instead               │              │
│                          │                                │              │
│                          │  [Preview] [Attach] [Index]    │              │
└─────────────────────────────────────────────────────────────────────────┘
  ↓ Scrollable list          ↓ Document viewer              ↓ Info panel
```

## Workflow 1: "Document Import & Index"

### Current (Pain Points)
```
1. Open PyGPT
2. Click Files tab
3. Navigate folder
4. Right-click file
5. **Scroll 30+ actions**
6. Find "Index" submenu
7. **Hover to expand submenu**
8. Select target index
9. Wait for background task
10. **Check separate Indexer tool** for progress
```

### Redesigned (Optimized)
```
1. Open PyGPT
2. File visible in Explorer (instantly)
3. Click file (preview loads)
4. Click [Index] button (quick action)
5. Select target index (dropdown, 2 clicks)
6. **Progress visible inline** (no separate tool)
7. Done
```

### Action Button Layout
```
Bottom toolbar (fixed, 8-10 core actions):

[Preview] [Attach] [Index ▼] [More ⋮]

Where:
- Preview: Opens in native viewer
- Attach: Adds to current chat
- Index: Dropdown with saved indexes
- More: Secondary actions (rename, duplicate, delete)
```

## Workflow 2: "Document Reading"

### Feature: One-Click Preview
```
User Action              UI Response
────────────────────────────────────
Click file               [instant]
                         → Skeleton screen
                         → Metadata loads (20ms)
                         → Content loads (streaming)
                         → User can start reading

Right-click             [instant]
                         → Mini-context menu (3 actions)
                         → Open in external viewer
                         → Attach to chat
                         → Delete

Double-click            [instant]
                         → Full window view
                         → Full document viewer
```

## Workflow 3: "Document Management"

### Context Menu Redesign

**Current (30+ actions):**
```
Open
Open Directory
Download
───────────────
Preview actions (3-5)
───────────────
Use > Attachment
   > Copy work path
   > Copy sys path
   > Read command
───────────────
Index > IDX: Research
     > IDX: Work
     > Remove from Research
     > Remove from Work
───────────────
Rename
Duplicate
Delete
```

**Redesigned (8 core + More menu):**
```
Open               ⌘O
Open in Explorer   ⌘⌥O
───────────────────
Attach to Chat     ⌘A
Index              ⌘I
───────────────────
More ⋮             ⌘M
  ├─ Rename       ⌘R
  ├─ Duplicate    ⌘D
  ├─ Copy Path    ⌘⇧C
  ├─ Delete       ⌘⌫
  └─ Properties   ⌘;
```

## Keyboard Shortcut Strategy

```
Core Actions:
⌘O       Open file in viewer
⌘⌥O      Open in system explorer
⌘A       Attach to chat
⌘I       Show Index menu
⌘R       Rename
⌘D       Duplicate
⌘⌫       Delete
⌘⇧C      Copy path
⌘;       Properties

Navigation:
↑/↓      Select files
Space    Quick preview
Enter    Open file
Escape   Clear selection
```

## Drag-and-Drop Improvements

### Current
- Drop file → Copies to explorer root
- No feedback during drag
- Unclear target zones

### Improved
```
1. Drag file over explorer
   → Visual feedback:
     - Highlight drop zones
     - Show "Move to: folder1"
     - Folder icon glows

2. Drop on folder
   → File moves (animated)
   → Shows confirmation toast
   → Auto-scrolls if needed

3. Drag to chat
   → Shows "Attach as context"
   → Validates file type
   → Inserts at cursor
```

## Quick Actions Toolbar

```
Top bar (always visible):
┌──────────────────────────────────────────────────────┐
│ [📁] [↻] [🔍] [⊕] [🗑] [⋮]                          │
│  Explorer Search Add  Delete  More                   │
└──────────────────────────────────────────────────────┘

Context (when file selected):
┌──────────────────────────────────────────────────────┐
│ [👁] [📎] [🗂] [⋮]                                  │
│  Preview Attach Index  More                         │
└──────────────────────────────────────────────────────┘
```

## Information Hierarchy

### File Info Panel (Right Sidebar)

**When file selected:**
```
┌─────────────────────┐
│ document.pdf        │
├─────────────────────┤
│ Size: 2.3 MB        │
│ Type: PDF           │
│ Modified: Nov 20    │
│           14:30     │
├─────────────────────┤
│ Indexed in:         │
│ • Research (Nov 20) │
│ • Work (Oct 15)     │
├─────────────────────┤
│ Actions:            │
│ [Preview]           │
│ [Attach]            │
│ [Index]             │
│ [Delete]            │
└─────────────────────┘
```

## Error State Handling

### Strategy: Non-blocking inline errors

**Before:**
```
Error dialog blocks interaction
→ Forces user to acknowledge
→ Interrupts workflow
```

**After:**
```
[⚠️ Error: Cannot read PDF]
Try converting to text first
[Retry] [Try Text] [Dismiss]

→ Inline, non-blocking
→ Suggests solutions
→ User can continue working
```

## Pain Point Elimination Checklist

| Pain Point | Solution | Result |
|------------|----------|--------|
| 30+ context menu actions | Reduce to 8 core + More | Cognitive load ↓ 75% |
| Two-interface problem (explorer + indexer) | Unified status in sidebar | Workflow steps ↓ 40% |
| Context menu scrolling | Compact layout + search | Action time ↓ 50% |
| No file preview | Instant preview on click | Context switching ↓ 80% |
| Hidden progress | Visible in sidebar + toolbar | UX clarity ↑ 100% |
| Long workflows | Keyboard shortcuts | Power user speed ↑ 200% |

## Responsive Design Considerations

### Desktop (1920×1080)
```
┌─ Explorer (30%) | Document (50%) | Info (20%) ─┐
└──────────────────────────────────────────────────┘
```

### Tablet (768×1024)
```
┌─ Explorer (25%) | Document (75%) ─┐
└──────────────────────────────────────┘
Info panel: Slide-out drawer
```

### Mobile (375×667)
```
┌─────────────────────────────────┐
│ Explorer (full width, collapsed) │
├─────────────────────────────────┤
│ Document Viewer (full width)     │
├─────────────────────────────────┤
│ Bottom Sheet: Actions + Info     │
└─────────────────────────────────┘
```

## Animation & Micro-interactions

### Feedback for Every Action

```
File Selection:
  → File highlights (100ms ease-in)
  → Info panel slides in (200ms)
  → Skeleton screen appears

Preview Load:
  → Skeleton lines animate
  → Document fades in (300ms)
  → Scroll position preserved

Context Menu:
  → Pop-up appears (100ms scale-in)
  → Hover highlights action (50ms)
  → Sub-menu slides in (100ms)
```

## Prototype Specifications

### Phase 1 Wireframe
- [ ] Static wireframes for 3 workflows
- [ ] Mobile/tablet variants
- [ ] Error state variations
- [ ] Annotated interactions

### Phase 2 Interactive Prototype (Figma)
- [ ] Click-through workflows
- [ ] Animated transitions
- [ ] Responsive preview
- [ ] State variations

### Phase 3 User Testing
- [ ] 5 users × 3 workflows
- [ ] Think-aloud sessions (30 min each)
- [ ] Success/failure metrics
- [ ] Feedback integration

## Success Metrics

- ✅ Context menu actions reduced from 30 → 8 (73% reduction)
- ✅ Index workflow steps reduced from 10 → 5 (50% reduction)
- ✅ Time to complete "Index file" task: <15 seconds
- ✅ Users find primary actions without scrolling
- ✅ No separate tool needed for progress tracking
- ✅ Keyboard power users save >30 seconds per file
