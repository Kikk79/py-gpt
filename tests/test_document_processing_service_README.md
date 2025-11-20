# DocumentProcessingService Tests - Quick Reference

## Overview
> Test file: `tests/test_document_processing_service.py`
> Total tests: 70+
> Target coverage: >85%

## Installation

```bash
# Install pytest and test dependencies
pip install pytest pytest-cov pytest-timeout pytest-asyncio pytest-xdist

# Or use requirements file
cd /mnt/c/Users/klaus/Documents/GIT/py-gpt
pip install -r requirements-dev.txt  # if exists
```

## Running Tests

### Run all tests
```bash
cd /mnt/c/Users/klaus/Documents/GIT/py-gpt
pytest tests/test_document_processing_service.py -v
```

### Run specific test class
```bash
# Test async loading
pytest tests/test_document_processing_service.py::TestAsyncLoading -v

# Test cache functionality
pytest tests/test_document_processing_service.py::TestCacheFunctionality -v

# Test operation tracking
pytest tests/test_document_processing_service.py::TestOperationTracking -v

# Test integration
pytest tests/test_document_processing_service.py::TestServiceLayerIntegration -v
```

### Run specific test
```bash
pytest tests/test_document_processing_service.py::TestAsyncLoading::test_load_async_successful -v
```

### Run with coverage
```bash
pytest tests/test_document_processing_service.py --cov=src/pygpt_net/core/document_processing_service --cov-report=term-missing --cov-report=html

# View HTML report
open htmlcov/index.html
```

### Run in parallel (faster)
```bash
pytest tests/test_document_processing_service.py -n 4  # Use 4 processes
```

### Stop on first failure
```bash
pytest tests/test_document_processing_service.py -x
```

### Run with more verbose output
```bash
pytest tests/test_document_processing_service.py -vv
```

## Test Categories

### ✓ Async Loading Tests (8 tests)
- ThreadPoolExecutor functionality
- Async callback invocation
- Exception handling
- Concurrent operations

### ✓ LRU Cache Tests (8 tests)
- Metadata caching
- LRU eviction (500 entries)
- Cache hit/miss
- Thread-safe operations

### ✓ Operation Tracking Tests (7 tests)
- Operation ID generation
- Cancellation API
- Cleanup after completion
- Active operation tracking

### ✓ Progress Callbacks Tests (4 tests)
- Progress updates
- Completion callbacks
- Error callbacks
- Optional callback handling

### ✓ Error Handling Tests (6 tests)
- Error severity levels
- LoadError creation
- LoadResult with errors
- Multiple error scenarios

### ✓ Preview Generation Tests (5 tests)
- Preview loading
- Line limits
- Size limits
- Chunk size optimization

### ✓ File Information Tests (6 tests)
- File metadata
- Size formatting
- Type detection
- Path handling

### ✓ Service Management Tests (9 tests)
- Service lifecycle
- Global singleton
- Statistics reporting
- Shutdown cleanup

### ✓ Integration Tests (3 tests)
- Backend → Frontend (C3 → B1)
- UI update patterns
- Batch processing
- Concurrent UI operations

### ✓ Edge Cases & Performance (11 tests)
- Boundary conditions
- Thread safety
- Resource cleanup
- Scalability

## Test Fixtures

```python
@pytest.fixture
def service()
    """Create DocumentProcessingService instance."""

@pytest.fixture
def mock_loader()
    """Mock UnifiedDocumentLoader."""

@pytest.fixture
def sample_metadata()
    """Sample DocumentMetadata."""

@pytest.fixture
def sample_load_result()
    """Sample successful LoadResult."""
```

## Common Issues

### Issue: "No module named 'pytest'"
```bash
pip install pytest
```

### Issue: Import errors
Make sure you're in the project root:
```bash
cd /mnt/c/Users/klaus/Documents/GIT/py-gpt
pytest tests/test_document_processing_service.py
```

### Issue: Tests timeout
Increase timeout or use threading more carefully:
```bash
pytest tests/test_document_processing_service.py --timeout=30
```

### Issue: Qt-related errors
Tests avoid Qt dependencies by mocking FileLoaderManager. If you see Qt errors:
- Ensure mocks are properly configured
- Check that you're not importing Qt in the service layer

## Writing New Tests

### Template for new test

```python
def test_new_feature(service, mock_loader):
    """Test description."""
    # Arrange
    service._registry.get_loader = Mock(return_value=mock_loader)
    mock_loader.method = Mock(return_value=expected_value)

    # Act
    result = service.method_under_test()

    # Assert
    assert result == expected_value
    mock_loader.method.assert_called_once()
```

### Template for async test

```python
def test_async_feature(service, mock_loader):
    """Test async method."""
    # Arrange
    service._registry.get_loader = Mock(return_value=mock_loader)
    mock_loader.load_complete = Mock(return_value=sample_load_result)

    callback_results = []

    def on_complete(result):
        callback_results.append(result)

    # Act
    op_id = service.load_async("test.txt", on_complete=on_complete)
    future = service._active_loads[op_id]
    result = future.result(timeout=2)

    # Assert
    assert len(callback_results) == 1
    assert result.success is True
```

## Expected Results

```bash
# Success output
======================== test session starts =========================
tests/test_document_processing_service.py::TestAsyncLoading::test_load_async_successful PASSED [  1%]
tests/test_document_processing_service.py::TestAsyncLoading::test_load_async_no_loader_error PASSED [  2%]
...
tests/test_document_processing_service.py::TestPerformance::test_cache_memory_efficiency PASSED [100%]

======================== 70+ passed in 5.47s =========================

# Coverage report example
Name                                     Stmts   Miss  Cover
----------------------------------------------------------
document_processing_service.py            200      25    88%
```

## Test Maintenance

### When to update tests
- Add new service features → add tests
- Change service behavior → update affected tests
- Bug fix → add regression test

### Best practices
- Keep tests independent (don't rely on execution order)
- Use descriptive test names
- Cleanup in fixtures (shutdown() calls)
- Mock external dependencies
- Test one thing per test

## Debugging Tests

### Enable pytest debug output
```bash
pytest tests/test_document_processing_service.py -vv --tb=long
```

### Run single test with print statements
```python
def test_debug():
    print("Debug info")
    # Test code
    assert something
```

### Use pytest.set_trace()
```python
import pytest

def test_with_debug():
    result = service.method()
    pytest.set_trace()  # Drop to debugger
    assert result
```

## Performance Benchmarks

Expected performance on standard hardware:

| Operation | Expected Time | Max Time |
|-----------|--------------|----------|
| Single async load | < 100ms | < 1s |
| 10 concurrent loads | < 500ms | < 2s |
| Cache operations (1000) | < 100ms | < 1s |
| File info retrieval | < 50ms | < 500ms |

## Integration with Development Workflow

### Pre-commit hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
pytest tests/test_document_processing_service.py -q || exit 1
```

### GitHub Actions (simplified)
```yaml
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - run: pip install poetry
    - run: poetry install
    - run: poetry run pytest tests/test_document_processing_service.py --cov --cov-report=xml
```

## References

- [pytest documentation](https://docs.pytest.org/)
- [Testing Python Applications](https://realpython.com/python-testing/)
- [DocumentProcessingService Code](src/pygpt_net/core/document_processing_service.py)
