#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Test script for C3 Unified Document Loaders

"""
Test script for C3 Unified Document Loaders (TXT and MD).

This script tests the migration of existing TXT and MD loaders to the new
C3 UnifiedDocumentLoader interface.
"""

import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pygpt_net.provider.loaders.c3_txt_loader import TxtLoader
from pygpt_net.provider.loaders.c3_md_loader import MarkdownLoader


def create_test_files():
    """Create test files for testing the loaders."""
    # Create test TXT file
    txt_content = """This is a test text file for the C3 Unified Document Loader system.

It contains multiple paragraphs to test chunk-based streaming.

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

The End.
"""

    with open('/mnt/c/Users/klaus/Documents/GIT/py-gpt/test_file.txt', 'w', encoding='utf-8') as f:
        f.write(txt_content)

    # Create test MD file
    md_content = """# Test Markdown Document

## Introduction

This is a test markdown file for the C3 Unified Document Loader system.

### Features Tested

- Heading levels (H1, H2, H3)
- Bold and *italic* text
- Code blocks:

```python
def hello():
    print("Hello, World!")
```

### Lists

1. First item
2. Second item
3. Third item

- Unordered item 1
- Unordered item 2

> This is a blockquote.

```
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
```

**The End.**
"""

    with open('/mnt/c/Users/klaus/Documents/GIT/py-gpt/test_file.md', 'w', encoding='utf-8') as f:
        f.write(md_content)

    print("✓ Created test files: test_file.txt and test_file.md")


def test_txt_loader():
    """Test the TXT loader."""
    print("\n" + "="*60)
    print("Testing TXT Loader")
    print("="*60)

    txt_path = '/mnt/c/Users/klaus/Documents/GIT/py-gpt/test_file.txt'

    # Initialize loader
    loader = TxtLoader(chunk_size=1024)  # Small chunk size for testing

    print(f"✓ Loader initialized for: {txt_path}")
    print(f"✓ Supported types: {[t.value for t in loader.get_supported_types()]}")
    print(f"✓ Can handle file: {loader.can_handle(txt_path)}")

    # Test streaming
    print("\n--- Streaming content (first 3 chunks) ---")
    chunk_count = 0
    for chunk in loader.load_stream(txt_path):
        chunk_count += 1
        print(f"\n[Chunk {chunk_count} - {len(chunk)} chars]")
        print(chunk[:200] + "..." if len(chunk) > 200 else chunk)

        if chunk_count >= 3:
            break

    print(f"\n✓ Total chunks loaded: {chunk_count}")

    # Get metadata
    metadata = loader.get_metadata()
    if metadata:
        print("\n--- Metadata ---")
        print(f"Source: {metadata.source}")
        print(f"Document type: {metadata.document_type.value}")
        print(f"Size: {metadata.size_bytes} bytes")
        print(f"MIME type: {metadata.mime_type}")
        print(f"Title: {metadata.title}")
        print(f"Custom metadata: {metadata.custom_metadata}")

    # Get errors and warnings
    errors = loader.get_errors()
    warnings = loader.get_warnings()

    if errors:
        print(f"\n✗ Errors: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✓ No errors")

    if warnings:
        print(f"\n⚠ Warnings: {len(warnings)}")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("✓ No warnings")

    # Test load_complete
    print("\n--- Testing load_complete() ---")
    result = loader.load_complete(txt_path)
    print(f"✓ Success: {result.success}")
    print(f"✓ Load time: {result.load_time:.3f} seconds")
    print(f"✓ Total chunks loaded: {len(result.content)}")
    print(f"✓ Total characters: {sum(len(chunk) for chunk in result.content)}")


def test_md_loader():
    """Test the MD loader."""
    print("\n" + "="*60)
    print("Testing Markdown Loader")
    print("="*60)

    md_path = '/mnt/c/Users/klaus/Documents/GIT/py-gpt/test_file.md'

    # Initialize loader
    loader = MarkdownLoader(chunk_size=2048)  # Larger chunks for markdown

    print(f"✓ Loader initialized for: {md_path}")
    print(f"✓ Supported types: {[t.value for t in loader.get_supported_types()]}")
    print(f"✓ Can handle file: {loader.can_handle(md_path)}")

    # Test streaming
    print("\n--- Streaming content (first 3 chunks) ---")
    chunk_count = 0
    for chunk in loader.load_stream(md_path):
        chunk_count += 1
        print(f"\n[Chunk {chunk_count} - {len(chunk)} chars]")
        print(chunk[:200] + "..." if len(chunk) > 200 else chunk)

        if chunk_count >= 3:
            break

    print(f"\n✓ Total chunks loaded: {chunk_count}")

    # Get metadata
    metadata = loader.get_metadata()
    if metadata:
        print("\n--- Metadata ---")
        print(f"Source: {metadata.source}")
        print(f"Document type: {metadata.document_type.value}")
        print(f"Size: {metadata.size_bytes} bytes")
        print(f"MIME type: {metadata.mime_type}")
        print(f"Title: {metadata.title}")
        print(f"Custom metadata: {metadata.custom_metadata}")

    # Get errors and warnings
    errors = loader.get_errors()
    warnings = loader.get_warnings()

    if errors:
        print(f"\n✗ Errors: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✓ No errors")

    if warnings:
        print(f"\n⚠ Warnings: {len(warnings)}")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("✓ No warnings")

    # Test load_complete
    print("\n--- Testing load_complete() ---")
    result = loader.load_complete(md_path)
    print(f"✓ Success: {result.success}")
    print(f"✓ Load time: {result.load_time:.3f} seconds")
    print(f"✓ Total chunks loaded: {len(result.content)}")
    print(f"✓ Total characters: {sum(len(chunk) for chunk in result.content)}")


def test_loader_registry():
    """Test loader integration with LoaderRegistry."""
    print("\n" + "="*60)
    print("Testing Loader Registry Integration")
    print("="*60)

    from pygpt_net.core.document_processor import LoaderRegistry

    # Create registry
    registry = LoaderRegistry()

    # Register loaders
    txt_loader = TxtLoader()
    md_loader = MarkdownLoader()
    registry.register(txt_loader)
    registry.register(md_loader)

    print("✓ Both loaders registered")

    # Get supported types
    supported_types = registry.get_supported_types()
    print(f"✓ Supported types: {[t.value for t in supported_types]}")

    # Test automatic loader selection
    txt_path = '/mnt/c/Users/klaus/Documents/GIT/py-gpt/test_file.txt'
    md_path = '/mnt/c/Users/klaus/Documents/GIT/py-gpt/test_file.md'

    txt_selected = registry.get_loader(txt_path)
    md_selected = registry.get_loader(md_path)

    print(f"✓ TXT loader selected: {type(txt_selected).__name__ if txt_selected else None}")
    print(f"✓ MD loader selected: {type(md_selected).__name__ if md_selected else None}")

    # Test loader with selected loader
    if txt_selected:
        result = txt_selected.load_complete(txt_path)
        print(f"✓ TXT loaded via registry: {result.success}")

    if md_selected:
        result = md_selected.load_complete(md_path)
        print(f"✓ MD loaded via registry: {result.success}")


def cleanup():
    """Clean up test files."""
    try:
        os.remove('/mnt/c/Users/klaus/Documents/GIT/py-gpt/test_file.txt')
        os.remove('/mnt/c/Users/klaus/Documents/GIT/py-gpt/test_file.md')
        print("\n✓ Cleaned up test files")
    except Exception as e:
        print(f"\n⚠ Cleanup warning: {e}")


def main():
    """Main test function."""
    print("="*60)
    print("C3 Unified Document Loader Test Suite")
    print("Testing TXT and MD Loader Migration")
    print("="*60)

    try:
        # Create test files
        create_test_files()

        # Run tests
        test_txt_loader()
        test_md_loader()
        test_loader_registry()

        print("\n" + "="*60)
        print("All tests completed successfully!")
        print("="*60)

    finally:
        # Cleanup
        cleanup()


if __name__ == "__main__":
    main()
