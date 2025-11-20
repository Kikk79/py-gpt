#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocumentCache Integration Example

This example demonstrates practical integration of DocumentCache with
the existing document processing infrastructure in PyGPT.
"""

import os
import time
from typing import Optional

# Import cache and document processor
from src.pygpt_net.core.document_cache import DocumentCache, create_default_cache
from src.pygpt_net.core.document_processor import load_document, LoaderRegistry, TxtLoader, CsvLoader


def example_1_basic_integration():
    """Example 1: Basic cache integration with document processor."""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Basic Cache Integration")
    print("=" * 60)

    # Create a cache instance
    cache = create_default_cache(
        max_size_mb=50,
        max_documents=100,
        enable_stats=True
    )

    # Example document paths
    documents = [
        "README.md",
        "setup.py",
        "pyproject.toml"
    ]

    print("\nLoading documents with cache:")
    for doc_path in documents:
        if os.path.exists(doc_path):
            print(f"\n  Loading: {doc_path}")

            # First access - will load from disk and cache
            start_time = time.time()
            result = cache.get(doc_path)
            load_time = time.time() - start_time

            if result and result.success:
                print(f"    ✓ Loaded ({len(result.content)} chunks)")
                print(f"    ✓ Size: {result.metadata.size_bytes} bytes")
                print(f"    ✓ Load time: {load_time*1000:.2f}ms")

                # Second access - will retrieve from cache
                start_time = time.time()
                result2 = cache.get(doc_path)
                cache_time = time.time() - start_time

                if result2:
                    print(f"    ✓ Cache retrieval: {cache_time*1000:.2f}ms")

    # Show final statistics
    stats = cache.get_stats()
    print(f"\nCache Statistics:")
    print(f"  Hit rate: {stats.hit_rate:.1f}%")
    print(f"  Total accesses: {stats.total_accesses}")
    print(f"  Cache hits: {stats.hits}")
    print(f"  Cache misses: {stats.misses}")


def example_2_performance_comparison():
    """Example 2: Cache performance comparison."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Performance Comparison")
    print("=" * 60)

    # Create documents for testing
    test_file = "temp_test_file.txt"
    with open(test_file, 'w') as f:
        f.write("Performance test content\n" * 1000)

    try:
        # Method 1: Direct loading (no cache)
        print("\nMethod 1: Direct Loading (No Cache)")
        direct_times = []
        for i in range(5):
            start = time.time()
            result = load_document(test_file)
            elapsed = time.time() - start
            direct_times.append(elapsed)
            print(f"  Load {i+1}: {elapsed*1000:.2f}ms")

        # Method 2: Cached loading
        print("\nMethod 2: Cached Loading")
        cache = create_default_cache(max_size_mb=10)

        cached_times = []
        for i in range(5):
            start = time.time()
            result = cache.get(test_file)
            elapsed = time.time() - start
            cached_times.append(elapsed)
            print(f"  Load {i+1}: {elapsed*1000:.2f}ms")

        # Compare results
        avg_direct = sum(direct_times) / len(direct_times)
        avg_cached = sum(cached_times) / len(cached_times)

        print(f"\nPerformance Summary:")
        print(f"  Average direct load: {avg_direct*1000:.2f}ms")
        print(f"  Average cache load: {avg_cached*1000:.2f}ms")
        print(f"  Speed improvement: {avg_direct/avg_cached:.1f}x")

        # Show cache statistics
        stats = cache.get_stats()
        print(f"\nCache Statistics:")
        print(f"  Hit rate: {stats.hit_rate:.1f}%")
        print(f"  Total loaded: {stats.total_loaded_mb:.3f} MB")

    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def example_3_document_processor_with_cache():
    """Example 3: Document processor with cache integration."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Document Processor with Cache")
    print("=" * 60)

    # Initialize cache and document registry
    cache = create_default_cache(max_documents=50)

    # Register loaders
    registry = LoaderRegistry()
    registry.register(TxtLoader())
    registry.register(CsvLoader())

    print("\nProcessing documents with caching:")

    # Process a mix of documents
    documents = []

    # Create sample documents
    sample_csv = "sample_data.csv"
    with open(sample_csv, 'w') as f:
        f.write("name,department,salary\n")
        f.write("Alice,Engineering,120000\n")
        f.write("Bob,Sales,95000\n")
        f.write("Charlie,Marketing,85000\n")
    documents.append(sample_csv)

    sample_txt = "sample_notes.txt"
    with open(sample_txt, 'w') as f:
        f.write("Important project notes:\n")
        f.write("- Review architecture\n")
        f.write("- Update documentation\n")
        f.write("- Schedule team meeting\n")
    documents.append(sample_txt)

    try:
        for doc_path in documents:
            print(f"\n  Processing: {doc_path}")

            # Get loader
            loader = registry.get_loader(doc_path)
            if not loader:
                print(f"    ✗ No loader available")
                continue

            # Get from cache (or load if not cached)
            result = cache.get(doc_path, loader=loader)

            if result and result.success:
                print(f"    ✓ Loaded successfully")
                print(f"    ✓ Type: {result.metadata.document_type.value}")
                print(f"    ✓ Chunks: {len(result.content)}")
                print(f"    ✓ Size: {result.metadata.size_bytes} bytes")

                # Show preview of first chunk
                if result.content:
                    preview = result.content[0][:100].replace('\n', ' ')
                    print(f"    ✓ Preview: {preview}...")

        # Cache statistics
        stats = cache.get_stats()
        print(f"\nFinal Cache Statistics:")
        print(f"  Documents cached: {stats.current_count}")
        print(f"  Cache size: {stats.current_size_mb:.3f} MB")
        print(f"  Hit rate: {stats.hit_rate:.1f}%")

    finally:
        for doc in documents:
            if os.path.exists(doc):
                os.remove(doc)


def example_4_cache_invalidation_scenario():
    """Example 4: Cache invalidation in action."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Cache Invalidation Scenario")
    print("=" * 60)

    # Create a test file
    test_file = "dynamic_content.txt"
    with open(test_file, 'w') as f:
        f.write("Version 1: Initial content\n")

    try:
        cache = create_default_cache(max_documents=10)

        # First load and cache
        print("\nStep 1: Initial load and cache")
        result = cache.get(test_file)
        if result:
            print(f"  ✓ Loaded: {result.content[0].strip()}")

        # Verify cache hit
        result = cache.get(test_file)
        stats = cache.get_stats()
        print(f"  ✓ Cache hit: {stats.hits}")

        # Modify the file
        print("\nStep 2: File modification")
        with open(test_file, 'w') as f:
            f.write("Version 2: Updated content\n")
        print("  ✓ File modified")

        # Access again - should detect stale cache
        print("\nStep 3: Access after modification")
        result = cache.get(test_file)
        stats = cache.get_stats()

        if result:
            print(f"  ✓ Reloaded: {result.content[0].strip()}")
            print(f"  ✓ Cache miss (reload): {stats.misses}")

        # Demonstrate manual invalidation
        print("\nStep 4: Manual cache invalidation")
        with open(test_file, 'w') as f:
            f.write("Version 3: Final content\n")

        # Manually invalidate before accessing
        invalidated = cache.invalidate(test_file)
        print(f"  ✓ Manually invalidated: {invalidated}")

        result = cache.get(test_file)
        if result:
            print(f"  ✓ Reloaded after invalidation: {result.content[0].strip()}")

    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def example_5_real_world_document_pipeline():
    """Example 5: Real-world document processing pipeline."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Real-World Document Pipeline")
    print("=" * 60)

    # Create document processing pipeline with caching
    class CachedDocumentPipeline:
        def __init__(self, cache: DocumentCache):
            self.cache = cache
            self.registry = LoaderRegistry()
            self._register_loaders()

        def _register_loaders(self):
            """Register available document loaders."""
            self.registry.register(TxtLoader())
            self.registry.register(CsvLoader())
            # Add more loaders as needed

        def process_document(self, source: str):
            """Process a document with caching."""
            print(f"\n  Processing: {source}")

            # Get appropriate loader
            loader = self.registry.get_loader(source)
            if not loader:
                print(f"    ✗ No loader for this file type")
                return None

            # Get from cache (loads if needed)
            result = self.cache.get(source, loader=loader)

            if not result or not result.success:
                print(f"    ✗ Failed to process")
                return None

            print(f"    ✓ Successfully processed")
            return result

        def process_batch(self, sources: list):
            """Process multiple documents."""
            results = []
            for source in sources:
                result = self.process_document(source)
                if result:
                    results.append(result)
            return results

        def get_stats(self):
            """Get cache statistics."""
            return self.cache.get_stats()

    # Initialize pipeline
    cache = create_default_cache(max_size_mb=20, max_documents=50)
    pipeline = CachedDocumentPipeline(cache)

    # Create sample documents
    doc1 = "report.txt"
    with open(doc1, 'w') as f:
        f.write("Q4 Sales Report\n")
        f.write("Revenue: $1.2M\n")
        f.write("Growth: +15%\n")

    doc2 = "data.csv"
    with open(doc2, 'w') as f:
        f.write("product,units,revenue\n")
        f.write("A100,150,45000\n")
        f.write("B250,200,60000\n")
        f.write("C300,175,52500\n")

    documents = [doc1, doc2]

    try:
        print("\nProcessing document batch:")
        results = pipeline.process_batch(documents)

        print(f"\nSuccessfully processed: {len(results)} documents")

        # Second batch - should use cache
        print("\nRe-processing same documents (from cache):")
        results2 = pipeline.process_batch(documents)

        # Show statistics
        stats = pipeline.get_stats()
        print(f"\nPipeline Statistics:")
        print(f"  Documents in cache: {stats.current_count}")
        print(f"  Cache hit rate: {stats.hit_rate:.1f}%")
        print(f"  Cache size: {stats.current_size_mb:.3f} MB")

    finally:
        for doc in documents:
            if os.path.exists(doc):
                os.remove(doc)


def main():
    """Run all examples."""
    print("DocumentCache Integration Examples")
    print("Demonstrates practical integration with PyGPT document processing")

    try:
        example_1_basic_integration()
        example_2_performance_comparison()
        example_3_document_processor_with_cache()
        example_4_cache_invalidation_scenario()
        example_5_real_world_document_pipeline()

        print("\n" + "=" * 60)
        print("All integration examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
