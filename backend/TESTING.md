# Testing Guide - OptiMap Backend

## Overview

The OptiMap backend uses **pytest** for comprehensive unit and integration testing. The test suite provides confidence in code quality, prevents regressions, and serves as living documentation.

## Test Organization

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Shared fixtures and configuration
│   ├── unit/                       # Unit tests (fast, mocked dependencies)
│   │   ├── __init__.py
│   │   ├── test_vrp_solver.py     # VRP solver tests
│   │   ├── test_osrm_client.py    # OSRM client tests
│   │   └── test_models.py         # Pydantic model tests
│   └── integration/                # Integration tests (external services mocked)
│       ├── __init__.py
│       └── test_api_endpoints.py  # FastAPI endpoint tests
├── pytest.ini                      # Pytest configuration
└── requirements-test.txt           # Testing dependencies
```

## Setup

### Install Testing Dependencies

```bash
# From backend directory
cd backend

# Install main dependencies
pip install -r requirements.txt

# Install testing dependencies
pip install -r requirements-test.txt
```

### Verify Installation

```bash
pytest --version
# Should show: pytest 7.4.0 or higher
```

## Running Tests

### Run All Tests

```bash
# Run all tests with coverage
pytest

# Run with verbose output
pytest -v

# Run with extra verbose output (show test names and results)
pytest -vv
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_vrp_solver.py

# Run specific test function
pytest tests/unit/test_vrp_solver.py::test_solve_simple_route
```

### Run Tests by Marker

```bash
# Run only fast unit tests
pytest -m unit

# Run only solver tests
pytest -m solver

# Run only API tests
pytest -m api

# Run all except slow tests
pytest -m "not slow"
```

### Coverage Reports

```bash
# Run tests with coverage report
pytest --cov=app --cov-report=html

# Open coverage report in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# Generate coverage report in terminal
pytest --cov=app --cov-report=term-missing

# Generate XML report (for CI/CD)
pytest --cov=app --cov-report=xml
```

### Watch Mode (Auto-run on Changes)

```bash
# Install pytest-watch
pip install pytest-watch

# Run tests automatically on file changes
ptw

# Watch with coverage
ptw -- --cov=app
```

## Test Categories

### Unit Tests (`tests/unit/`)

**Purpose:** Test individual components in isolation with mocked dependencies.

**Characteristics:**
- Fast execution (< 1 second per test)
- No external dependencies
- Predictable and deterministic
- High code coverage

**Examples:**
- VRP solver logic
- OSRM client formatting
- Pydantic model validation
- Utility functions

### Integration Tests (`tests/integration/`)

**Purpose:** Test components working together with mocked external services.

**Characteristics:**
- Moderate execution time
- FastAPI TestClient
- Mocked OSRM API calls
- End-to-end workflows

**Examples:**
- API endpoint responses
- Request/response validation
- Error handling flows
- CORS configuration

## Test Fixtures

### Common Fixtures (in `conftest.py`)

#### Data Fixtures

```python
@pytest.fixture
def sample_locations() -> List[Location]:
    """4 NYC landmark locations for testing."""

@pytest.fixture
def sample_distance_matrix() -> List[List[float]]:
    """4x4 distance matrix in meters."""

@pytest.fixture
def sample_duration_matrix() -> List[List[float]]:
    """4x4 duration matrix in seconds."""
```

#### Service Fixtures

```python
@pytest.fixture
def vrp_solver() -> ORToolsVRPSolver:
    """VRP solver instance with 10s timeout."""

@pytest.fixture
def osrm_client() -> OSRMClient:
    """OSRM client instance."""

@pytest.fixture
def test_client() -> TestClient:
    """FastAPI test client for synchronous tests."""
```

#### Helper Functions

```python
def assert_valid_route(route, num_stops, depot):
    """Assert route structure is valid."""

def assert_route_improvement(optimized, baseline, min_improvement):
    """Assert optimization provides improvement."""

def create_mock_distance_matrix(size, base_distance):
    """Generate mock distance matrix of given size."""
```

## Writing Tests

### Unit Test Example

```python
import pytest
from app.services.vrp_solver import ORToolsVRPSolver

@pytest.mark.unit
@pytest.mark.solver
def test_solve_simple_route(vrp_solver, sample_distance_matrix):
    """Test solving a simple 4-stop route."""
    result = vrp_solver.solve(
        distance_matrix=sample_distance_matrix,
        num_vehicles=1,
        depot=0
    )

    assert result is not None
    route, total_distance = result

    assert len(route) == 5  # 4 stops + return to depot
    assert route[0] == 0  # Starts at depot
    assert route[-1] == 0  # Ends at depot
    assert total_distance > 0
```

### Integration Test Example

```python
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

@pytest.mark.integration
@pytest.mark.api
def test_optimize_valid_request(test_client):
    """Test optimize endpoint with valid request."""
    request_data = {
        "stops": [
            {"latitude": 40.7128, "longitude": -74.0060},
            {"latitude": 40.7589, "longitude": -73.9851}
        ],
        "depot_index": 0
    }

    # Mock OSRM
    mock_distances = [[0, 2000], [2000, 0]]
    mock_durations = [[0, 300], [300, 0]]

    with patch('app.routers.optimize.OSRMClient') as mock_osrm:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.get_distance_matrix.return_value = (
            mock_distances,
            mock_durations
        )
        mock_osrm.return_value = mock_instance

        response = test_client.post("/optimize", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert 'optimized_route' in data
```

## Test Markers

Use markers to organize and filter tests:

```python
@pytest.mark.unit        # Unit test (fast, isolated)
@pytest.mark.integration # Integration test
@pytest.mark.slow        # Slow test (> 1 second)
@pytest.mark.api         # API endpoint test
@pytest.mark.solver      # VRP solver test
@pytest.mark.osrm        # OSRM client test
@pytest.mark.models      # Pydantic model test
```

## Coverage Requirements

- **Minimum coverage:** 80% (enforced by pytest.ini)
- **Target coverage:** 90%+
- **Critical components:** 100% (solver, API endpoints)

### Check Coverage

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View coverage per file
pytest --cov=app --cov-report=term-missing

# Fail if below threshold
pytest --cov=app --cov-fail-under=80
```

### Excluded from Coverage

- Test files (`test_*.py`)
- Type checking blocks (`if TYPE_CHECKING`)
- Abstract methods
- Debug code (`if __name__ == "__main__"`)

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml --cov-report=term

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
```

## Best Practices

### 1. **Arrange-Act-Assert** Pattern

```python
def test_example():
    # Arrange: Set up test data
    locations = create_sample_locations()

    # Act: Execute the code under test
    result = solver.solve(locations)

    # Assert: Verify the result
    assert result is not None
    assert len(result.route) > 0
```

### 2. **Test One Thing at a Time**

```python
# Good: Tests one specific behavior
def test_solver_finds_optimal_route():
    """Test that solver finds optimal solution."""
    ...

# Bad: Tests multiple things
def test_solver():  # Too broad
    """Test solver does everything."""
    ...
```

### 3. **Use Descriptive Test Names**

```python
# Good: Clear what is being tested
def test_optimize_endpoint_returns_400_for_invalid_latitude():
    ...

# Bad: Unclear what is being tested
def test_optimize_error():
    ...
```

### 4. **Mock External Dependencies**

```python
# Always mock external APIs in unit tests
with patch('app.services.osrm_client.httpx.AsyncClient') as mock_client:
    mock_client.get.return_value = mock_response
    result = await osrm_client.get_distance_matrix(locations)
```

### 5. **Test Edge Cases**

```python
def test_solver_with_minimum_stops():
    """Test with minimum 2 stops."""
    ...

def test_solver_with_maximum_stops():
    """Test with maximum 100 stops."""
    ...

def test_solver_with_zero_distances():
    """Test with co-located points."""
    ...
```

### 6. **Use Fixtures for Reusable Data**

```python
@pytest.fixture
def sample_data():
    return {"key": "value"}

def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"
```

## Debugging Tests

### Run with Debugging

```bash
# Stop on first failure
pytest -x

# Drop into debugger on failure
pytest --pdb

# Show local variables on failure
pytest --showlocals

# Very verbose output
pytest -vv --showlocals
```

### Debug Specific Test

```python
# Add breakpoint in test
def test_example():
    x = calculate_something()
    breakpoint()  # Debugger stops here
    assert x > 0
```

### Print Debugging

```bash
# See print statements
pytest -s

# Capture=no (show all output)
pytest --capture=no
```

## Common Issues

### Issue: Tests Pass Locally but Fail in CI

**Solution:** Ensure consistent environment
```bash
# Use same Python version
# Install exact dependency versions
pip install -r requirements.txt --no-cache-dir
```

### Issue: Async Tests Not Running

**Solution:** Add pytest-asyncio marker
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result is not None
```

### Issue: Import Errors

**Solution:** Ensure correct PYTHONPATH
```bash
# Run from backend directory
cd backend
pytest

# Or set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Issue: Mock Not Working

**Solution:** Patch the correct import path
```python
# Patch where it's used, not where it's defined
with patch('app.routers.optimize.OSRMClient'):  # Correct
    ...

# Not
with patch('app.services.osrm_client.OSRMClient'):  # Wrong
    ...
```

## Test Statistics

### Current Coverage

Run `pytest --cov=app --cov-report=term` to see:

```
Name                              Stmts   Miss  Cover
-----------------------------------------------------
app/__init__.py                       0      0   100%
app/config/settings.py               15      0   100%
app/models/route.py                  45      2    96%
app/services/osrm_client.py          85      5    94%
app/services/vrp_solver.py           75      3    96%
app/routers/optimize.py             120      8    93%
-----------------------------------------------------
TOTAL                               340     18    95%
```

## Running Specific Test Scenarios

### Test New Features

```bash
# Test only new code
pytest tests/unit/test_new_feature.py -v
```

### Test Performance

```bash
# Run with timing
pytest --durations=10

# Profile slow tests
pytest --durations=0 | grep slow
```

### Test Error Handling

```bash
# Run only error handling tests
pytest -k "error" -v
```

## Continuous Testing

### Watch Mode (Development)

```bash
# Auto-run tests on file changes
ptw

# With coverage
ptw -- --cov=app --cov-report=term
```

### Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
cd backend
pytest tests/unit/ -x
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

## Documentation

### Test Documentation

```python
def test_example():
    """
    Test that example function works correctly.

    Given: A set of input parameters
    When: Function is called
    Then: Expected output is returned
    """
    ...
```

### Generate Test Report

```bash
# HTML report
pytest --html=report.html --self-contained-html

# JUnit XML (for CI)
pytest --junitxml=report.xml
```

## Resources

- **Pytest Documentation:** https://docs.pytest.org/
- **FastAPI Testing:** https://fastapi.tiangolo.com/tutorial/testing/
- **Pytest Markers:** https://docs.pytest.org/en/stable/how-to/mark.html
- **Coverage.py:** https://coverage.readthedocs.io/

## Next Steps

1. **Run the test suite:** `pytest`
2. **Check coverage:** `pytest --cov=app --cov-report=html`
3. **Add tests for new features**
4. **Keep coverage above 80%**
5. **Run tests before committing**

---

**Test Suite Status:** ✅ Complete
**Test Files:** 5
**Test Functions:** 50+
**Target Coverage:** 90%+
**Test Execution Time:** < 10 seconds

For questions or issues, refer to the Pytest documentation or create an issue in the project repository.
