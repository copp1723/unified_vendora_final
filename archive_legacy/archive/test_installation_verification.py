#!/usr/bin/env python3
"""
Installation Verification Test Script
=====================================

This script verifies that pytest, pytest-asyncio, and pytest-mock
packages are properly installed and functional.
"""

import sys
import pytest
import pytest_asyncio
import pytest_mock
import asyncio


def test_basic_pytest():
    """Basic pytest functionality test."""
    assert True
    assert 2 + 2 == 4
    print("✅ Basic pytest functionality: PASSED")


def test_pytest_mock(mocker):
    """Test pytest-mock functionality."""
    # Mock a function
    mock_function = mocker.Mock(return_value=42)
    result = mock_function()
    
    assert result == 42
    assert mock_function.called
    print("✅ pytest-mock functionality: PASSED")


@pytest.mark.asyncio
async def test_pytest_asyncio():
    """Test pytest-asyncio functionality."""
    async def async_function():
        await asyncio.sleep(0.01)  # Small delay
        return "async_result"
    
    result = await async_function()
    assert result == "async_result"
    print("✅ pytest-asyncio functionality: PASSED")


if __name__ == "__main__":
    print("Python Package Installation Verification")
    print("=" * 45)
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check package versions
    print(f"pytest version: {pytest.__version__}")
    print(f"pytest-asyncio version: {pytest_asyncio.__version__}")
    print(f"pytest-mock available: {hasattr(pytest_mock, '__version__')}")
    
    print("\nRunning verification tests...")
    
    # Basic import test
    try:
        import pytest
        import pytest_asyncio
        import pytest_mock
        print("✅ All packages imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        sys.exit(1)
    
    print("\nTo run the full test suite with pytest:")
    print("source venv/bin/activate && pytest test_installation_verification.py -v")