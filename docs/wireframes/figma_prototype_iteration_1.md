# Figma Interactive Prototype - Iteration 1 Specification
**D1: Workflow Designer - Phase 1 Week 3 Day 1 Deliverable**

**Date**: November 21, 2025
**Version**: 1.0
**Status**: SPECIFICATION READY FOR FIGMA IMPLEMENTATION
**Target Completion**: Interactive prototype with 12+ interactive frames

---

## 📋 Overview

This document specifies the exact Figma components, frames, interactions, and animations needed for **Iteration 1** of the Document Reader Workflow prototype. This specification is detailed enough for direct implementation in Figma.

**Scope**: 3 workflows × 4-5 frames each = 12+ interactive frames with microinteractions

---

## 🎨 Design System Specifications

### Color Scheme

**Dark Theme (Primary)**:
```
Background:      #1a1a1a (near-black)
Surface:         #2a2a2a (darker gray)
Surface Alt:     #3a3a3a (medium gray)
Primary:         #4a9eff (bright blue)
Secondary:       #ff9d4a (warm orange)
Success:         #4ade80 (bright green)
Warning:         #facc15 (yellow)
Error:           #ef4444 (red)
Text Primary:    #f5f5f5 (off-white)
Text Secondary:  #a0a0a0 (light gray)
Border:          #404040 (dark gray)
```

**Light Theme (Alternative)**:
```
Background:      #ffffff (white)
Surface:         #f5f5f5 (light gray)
Surface Alt:     #e5e5e5 (medium gray)
Primary:         #0066ff (deep blue)
Secondary:       #ff7a00 (warm orange)
Success:         #22c55e (green)
Warning:         #eab308 (amber)
Error:           #dc2626 (red)
Text Primary:    #1a1a1a (black)
Text Secondary:  #666666 (medium gray)
Border:          #d0d0d0 (light gray)
```

### Typography

```
Heading 1:   Inter Bold, 28px, line-height 1.2
Heading 2:   Inter SemiBold, 20px, line-height 1.3
Heading 3:   Inter SemiBold, 16px, line-height 1.4
Body:        Inter Regular, 14px, line-height 1.5
Caption:     Inter Regular, 12px, line-height 1.4
Button:      Inter Medium, 14px, letter-spacing 0.5px
```

### Spacing & Grid

- **Base Unit**: 8px grid
- **Standard Padding**: 8px, 16px, 24px, 32px
- **Corner Radius**: 6px (controls), 8px (cards), 12px (modals)
- **Border Width**: 1px (standard), 2px (focus states)

### Animation Timings

```
Quick:      150ms cubic-bezier(0.4, 0, 0.2, 1)  // Micro-interactions
Standard:   300ms cubic-bezier(0.4, 0, 0.2, 1)  // Main animations
Slow:       500ms cubic-bezier(0.4, 0, 0.2, 1)  // Entrance/exit
```

---

## 🎯 Workflow A: Document Import & Index

### Frame A1: File Selection State
```
┌─────────────────────────────────────────────────────────────────┐
│ PyGPT - Files [•••] [Settings]                                  │
├─────────────────────────────────────────────────────────────────┤
│ HOME > DOCUMENTS > PROJECT    [📁] [↻] [⊞]                      │
├──────────────────────────────┬────────────────────────────────┬─┤
│ 📁 Folder1                   │ 📄 report.pdf                  │ I │
│ 📁 Folder2                   │ Size: 2.3 MB                   │ n │
│ 📄 file1.txt          ← SEL  │ Type: PDF                      │ f │
│ 📄 file2.pdf                 │ Modified: Nov 20, 14:30        │ o │
│ 📄 file3.py                  │                                │   │
│                              │ [👁 Preview] [📎 Attach]      │ P │
│                              │ [🗂 Index] [⋮ More]            │ a │
└──────────────────────────────┴────────────────────────────────┴─┘
```

**Elements**:
- **Explorer List** (left 30%):
  - Selected item: highlighted with `#404040` background
  - Hover state: `#3a3a3a` background, 100ms ease-in
  - Item height: 32px, 8px padding

- **Preview Panel** (center 50%):
  - Shows selected file metadata
  - Icon: 64px file icon
  - Text fields: name, size, type, modified
  - Button layout: 2 rows × 2 buttons, 8px gap

- **Info Panel** (right 20%):
  - Light scrollable area
  - Minimal styling

**Animations**:
- File selection: Slide highlight 150ms ease-in
- Preview panel fade in: 200ms ease-in when file selected

**Interactive States**:
- Click on different files → Preview panel updates with 200ms fade transition
- Hover on file → Highlight changes to `#3a3a3a`

---

### Frame A2: Index Menu Opens
```
┌─────────────────────────────────────────────────────────────────┐
│ PyGPT - Files [•••] [Settings]                                  │
├─────────────────────────────────────────────────────────────────┤
│ HOME > DOCUMENTS > PROJECT    [📁] [↻] [⊞]                      │
├──────────────────────────────┬────────────────────────────────┬─┤
│ 📁 Folder1                   │ 📄 report.pdf                  │   │
│ 📁 Folder2                   │ Size: 2.3 MB                   │   │
│ 📄 file1.txt                 │ Type: PDF                      │   │
│ 📄 file2.pdf                 │ Modified: Nov 20, 14:30        │   │
│ 📄 file3.py                  │                                │   │
│                              │ [👁 Preview] [📎 Attach]      │   │
│                              │ ┌─ [🗂 Index ▼] ─┐             │   │
│                              │ │ • Research     │             │   │
│                              │ │ • Work         │             │   │
│                              │ │ + New Index    │             │   │
│                              │ └────────────────┘             │   │
│                              │ [⋮ More]                       │   │
└──────────────────────────────┴────────────────────────────────┴─┘
```

**Elements**:
- **Dropdown Menu**:
  - Width: 180px
  - Position: Below `[🗂 Index]` button
  - Border: 1px `#404040`
  - Background: `#2a2a2a`
  - Items: 24px height, 8px padding
  - Hover: `#3a3a3a` background

**Animations**:
- Menu open: Scale 0.95 → 1.0, 150ms ease-out from button center
- Menu items: Fade in staggered 50ms each

**Interactive States**:
- Hover on menu item → `#3a3a3a` background
- Click on "Research" → Proceed to Frame A3

---

### Frame A3: Index Selected
```
┌─────────────────────────────────────────────────────────────────┐
│ PyGPT - Files [•••] [Settings]                                  │
├─────────────────────────────────────────────────────────────────┤
│ HOME > DOCUMENTS > PROJECT    [📁] [↻] [⊞]                      │
├──────────────────────────────┬────────────────────────────────┬─┤
│ 📁 Folder1                   │ 📄 report.pdf                  │   │
│ 📁 Folder2                   │ Size: 2.3 MB                   │   │
│ 📄 file1.txt                 │ Type: PDF                      │   │
│ 📄 file2.pdf                 │ Modified: Nov 20, 14:30        │   │
│ 📄 file3.py                  │                                │   │
│                              │ [👁 Preview] [📎 Attach]      │   │
│                              │ [🗂 Index: Research ✓]        │   │
│                              │ [⚡ Processing...]             │   │
│                              │ [▓▓▓▓▓░░░░] 50%                │   │
│                              │ [⋮ More]                       │   │
└──────────────────────────────┴────────────────────────────────┴─┘
```

**Elements**:
- **Status Indicator**:
  - Icon: ⚡ (animated pulse)
  - Text: "Processing..." (animated ellipsis)

- **Progress Bar**:
  - Height: 4px
  - Background: `#404040`
  - Filled: Linear gradient from primary → secondary
  - Border radius: 2px

**Animations**:
- Status icon pulse: Scale 1.0 → 1.15 → 1.0, repeating 600ms
- Progress bar fill: Smooth animation at 5% per second
- Text ellipsis: Cycle "." → ".." → "..." every 600ms

**Interactive States**:
- Can still navigate and select other files while processing
- Click `[⋮ More]` shows additional options

---

### Frame A4: Index Complete
```
┌─────────────────────────────────────────────────────────────────┐
│ PyGPT - Files [•••] [Settings]                                  │
├─────────────────────────────────────────────────────────────────┤
│ HOME > DOCUMENTS > PROJECT    [📁] [↻] [⊞]                      │
├──────────────────────────────┬────────────────────────────────┬─┤
│ 📁 Folder1                   │ 📄 report.pdf                  │   │
│ 📁 Folder2                   │ Size: 2.3 MB                   │   │
│ 📄 file1.txt                 │ Type: PDF                      │   │
│ 📄 file2.pdf                 │ Modified: Nov 20, 14:30        │   │
│ 📄 file3.py                  │                                │   │
│                              │ [👁 Preview] [📎 Attach]      │   │
│                              │ [🗂 Indexed in Research ✓]    │   │
│                              │ [▓▓▓▓▓▓▓▓▓▓] 100% ✓           │   │
│                              │ [⋮ More]                       │   │
└──────────────────────────────┴────────────────────────────────┴─┘
```

**Elements**:
- **Success State**:
  - Icon: ✓ (green checkmark)
  - Text: "Indexed in Research ✓"
  - Progress bar: 100% filled, green tint

**Animations**:
- Checkmark fade-in: 150ms ease-in
- Progress bar final fill: 200ms ease-out
- Text color fade to success green: 300ms

---

## 📖 Workflow B: Document Reading

### Frame B1: File Click (Initial State)
```
┌─────────────────────────────────────────────────────────────────┐
│ PyGPT - Files [•••] [Settings]                                  │
├─────────────────────────────────────────────────────────────────┤
│ HOME > DOCUMENTS > PROJECT    [📁] [↻] [⊞]                      │
├──────────────────────────────┬────────────────────────────────┬─┤
│ 📁 Folder1                   │ 📄 document.pdf                │   │
│ 📁 Folder2                   │ [Loading...]                   │   │
│ 📄 file1.txt          ← CLICK│ ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒             │   │
│ 📄 file2.pdf                 │ ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒             │   │
│ 📄 file3.py                  │                                │   │
│                              │                                │   │
│                              │ [👁 Preview] [📎 Attach]      │   │
│                              │ [🗂 Index]    [⋮ More]        │   │
└──────────────────────────────┴────────────────────────────────┴─┘
```

**Elements**:
- **Skeleton Screens**:
  - 4-5 skeleton lines, 60px width each
  - Border radius: 4px
  - Animation: Shimmer effect (left → right gradient)

**Animations**:
- Skeleton shimmer: 1000ms linear repeat
  - Gradient: transparent → white @ 50% opacity → transparent
  - Gradient position: -100px → 500px

---

### Frame B2: Content Loading
```
┌─────────────────────────────────────────────────────────────────┐
│ PyGPT - Files [•••] [Settings]                                  │
├─────────────────────────────────────────────────────────────────┤
│ HOME > DOCUMENTS > PROJECT    [📁] [↻] [⊞]                      │
├──────────────────────────────┬────────────────────────────────┬─┤
│ 📁 Folder1                   │ 📄 document.pdf                │   │
│ 📁 Folder2                   │ [▓▓▓░░░░░░░░░░] 35%            │   │
│ 📄 file1.txt          ✓ SEL  │                                │   │
│ 📄 file2.pdf                 │ Table of Contents              │   │
│ 📄 file3.py                  │ 1. Introduction...             │   │
│                              │ 2. Methodology...             │   │
│                              │ 3. Results...                 │   │
│                              │ 4. Conclusions...             │   │
│                              │                                │   │
│                              │ [👁 Preview] [📎 Attach]      │   │
│                              │ [🗂 Index]    [⋮ More]        │   │
└──────────────────────────────┴────────────────────────────────┴─┘
```

**Elements**:
- **Progress Bar** (top):
  - 35% filled
  - Gradient: Primary → Secondary

- **Content Preview**:
  - Scrollable text area
  - Text fades in from top with 100ms stagger

**Animations**:
- Content fade in: 200ms ease-in staggered per line (50ms delay)
- Progress bar smooth fill animation

---

### Frame B3: Content Loaded
```
┌─────────────────────────────────────────────────────────────────┐
│ PyGPT - Files [•••] [Settings]                                  │
├─────────────────────────────────────────────────────────────────┤
│ HOME > DOCUMENTS > PROJECT    [📁] [↻] [⊞]                      │
├──────────────────────────────┬────────────────────────────────┬─┤
│ 📁 Folder1                   │ 📄 document.pdf                │   │
│ 📁 Folder2                   │ [▓▓▓▓▓▓▓▓▓▓▓▓▓▓] 100% ✓       │   │
│ 📄 file1.txt          ✓ SEL  │                                │   │
│ 📄 file2.pdf                 │ Research Paper on AI Safety    │   │
│ 📄 file3.py                  │ ==========================    │   │
│                              │                                │   │
│                              │ Abstract                       │   │
│                              │ This research investigates... │   │
│                              │ ↕ [Scrollable content]        │   │
│                              │ [👁 Preview] [📎 Attach]      │   │
│                              │ [🗂 Index]    [⋮ More]        │   │
└──────────────────────────────┴────────────────────────────────┴─┘
```

**Elements**:
- **Full Content**: Scrollable text area with all content loaded
- **Progress Bar**: 100% with checkmark

---

## ⚙️ Workflow C: Document Management

### Frame C1: Right-Click Context Menu
```
┌─────────────────────────────────────────────────────────────────┐
│ PyGPT - Files [•••] [Settings]                                  │
├─────────────────────────────────────────────────────────────────┤
│ HOME > DOCUMENTS > PROJECT    [📁] [↻] [⊞]                      │
├──────────────────────────────┬────────────────────────────────┬─┤
│ 📁 Folder1                   │                                │   │
│ 📁 Folder2           ┌────────────────────┐                  │   │
│ 📄 file1.txt        │ Open          ⌘O   │                  │   │
│ 📄 file2.pdf (RMB) │ Open in Explorer   │                  │   │
│ 📄 file3.py        │ ─────────────────── │                  │   │
│                    │ Attach to Chat ⌘A  │                  │   │
│                    │ Index          ⌘I  │                  │   │
│                    │ ─────────────────── │                  │   │
│                    │ More ⋮              │                  │   │
│                    └────────────────────┘                  │   │
│                                          [👁 Preview]      │   │
│                                          [📎 Attach]       │   │
│                                          [🗂 Index]        │   │
│                                          [⋮ More]         │   │
└──────────────────────────────────────────────────────────────┴─┘
```

**Elements**:
- **Context Menu**:
  - Width: 220px
  - Item height: 32px
  - Separators: 1px border `#404040`
  - Hover: `#3a3a3a` background
  - Right-aligned shortcuts in lighter text

**Animations**:
- Menu appear: Scale 0.95 → 1.0 at cursor position, 150ms ease-out
- Menu items: Staggered fade-in 30ms each
- Hover state: 100ms ease-in to `#3a3a3a`

---

### Frame C2: More Menu Expands
```
Context menu same as C1, but "More ⋮" is highlighted with submenu:

                    ┌────────────────────┐
                    │ Open          ⌘O   │
                    │ Open in Explorer   │
                    │ ─────────────────── │
                    │ Attach to Chat ⌘A  │
                    │ Index          ⌘I  │
                    │ ─────────────────── │
                    │ More ⋮      ╲      ├─────────────────┐
                    └────────────────────┤ Rename      ⌘R   │
                                         │ Duplicate   ⌘D   │
                                         │ Copy Path   ⌘⇧C  │
                                         │ Delete      ⌘⌫   │
                                         │ Properties  ⌘;   │
                                         └─────────────────┘
```

**Elements**:
- **Submenu**:
  - Appears to the right with 4px gap
  - Same styling as main menu
  - Width: 200px

**Animations**:
- Submenu slide in: 100ms ease-out from left edge (4px offset)
- Items fade in staggered 30ms each

---

### Frame C3: Action Execution (Rename)
```
                    ┌────────────────────┐
                    │ Open          ⌘O   │
                    │ Open in Explorer   │
                    │ ─────────────────── │
                    │ Attach to Chat ⌘A  │
                    │ Index          ⌘I  │
                    │ ─────────────────── │
                    │ More ⋮              │
                    └────────────────────┘

Menu fades out, inline editor appears in explorer:

┌──────────────────────────────┐
│ ✎ [file2.pdf              ] │  (editable text field)
└──────────────────────────────┘
```

**Elements**:
- **Inline Editor**:
  - Background: `#3a3a3a`
  - Border: 2px `#4a9eff`
  - Text selected for editing
  - Icon: ✎ pencil icon

**Animations**:
- Menu fade out: 150ms ease-out
- Editor appear: Slide down 200ms ease-out
- Text auto-select: 100ms after appear

---

## 🎬 Animation & Microinteraction Specifications

### Button States

**Idle**:
- Background: `#4a9eff`
- Text: White
- Border radius: 6px

**Hover**:
- Background: Lighten `#4a9eff` by 10%
- Transition: 100ms ease-in
- Scale: 1.02

**Active/Pressed**:
- Background: Darken `#4a9eff` by 10%
- Scale: 0.98

**Disabled**:
- Background: `#3a3a3a`
- Text: `#666666`
- Opacity: 50%

### Progress Bar Animation

```
Loop Duration: 1.5 seconds
Progress value 0-100%

Timeline:
- 0ms:    [▓░░░░░░░░] 0%
- 100ms:  [▓▓░░░░░░░] 10%
- 200ms:  [▓▓▓░░░░░░] 20%
...
- 1500ms: [▓▓▓▓▓▓▓▓▓░] 90% (continues incrementally)

After 100% reached:
- Hold at 100% for 300ms
- Fade to success green (#4ade80) over 200ms
- Show checkmark overlay
```

### Skeleton Screen Shimmer

```
Gradient animation: -100px → 500px over 1000ms (ease-in-out infinite)

HTML-like representation:
[████████]  ← skeleton line 1 with shimmer
[██████████████]  ← skeleton line 2
[████████]  ← skeleton line 3

Shimmer: white @ 30% opacity moving left-to-right
```

### Menu Appearance

```
Origin: Cursor position (for right-click menu) or button center (for dropdown)
Scale: 0.95 → 1.0 over 150ms cubic-bezier(0.34, 1.56, 0.64, 1) [ease-out-back]
Shadow: 0 4px 12px rgba(0,0,0,0.3)
```

---

## 📐 Responsive Breakpoints

### Desktop (1920px+)
- 3-column layout: Explorer 30% | Preview 50% | Info 20%
- Full context menus with keyboard shortcuts visible

### Tablet (768-1024px)
- 2-column layout: Explorer 25% | Preview 75%
- Info panel becomes slide-out drawer from right
- Context menu simplified (hide shortcuts)

### Mobile (375-600px)
- Full-width stacked layout
- Explorer: collapsible accordion
- Preview: full-width with bottom sheet for actions
- Menus: slide up from bottom

---

## ✅ Validation Checklist for Figma Build

- [ ] All 12 frames created and linked
- [ ] Keyboard shortcuts visible in menu items
- [ ] Animations set to correct timings
- [ ] Color palette matches specifications
- [ ] Typography matches specifications
- [ ] Spacing follows 8px grid
- [ ] All interactive states defined
- [ ] Hover states configured
- [ ] Click interactions flow between frames
- [ ] Responsive variants created (desktop, tablet, mobile)
- [ ] Dark and light theme variants created
- [ ] Component library established (buttons, menus, inputs)
- [ ] Shared styles applied globally
- [ ] Prototype preview tested with 3+ browsers

---

## 🚀 Next Steps

1. **Week 3 Day 1 (Complete)**: Specification created ✅
2. **Week 3 Day 1-2**: Build frames in Figma (12 frames, ~8 hours)
3. **Week 3 Day 2**: Connect interactions and animations
4. **Week 3 Day 2-3**: Test prototype in Figma viewer
5. **Week 3 Day 3-4**: Collect feedback, plan refinements
6. **Week 3 Day 4-5**: User testing with 5 participants
7. **Week 3 Day 5**: Document findings, iterate

---

**Specification Version**: 1.0
**Created**: November 21, 2025
**Status**: Ready for Figma Implementation
**Estimated Figma Build Time**: 12-16 hours for all 12 frames with animations
