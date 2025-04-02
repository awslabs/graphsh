"""
Tests for raw renderer.
"""

import pytest
from unittest.mock import patch

from graphsh.renderers import RawRenderer


@pytest.fixture
def sample_results():
    """Sample query results for testing renderers."""
    return [
        {"id": "1", "name": "Alice", "age": 30},
        {"id": "2", "name": "Bob", "age": 25},
        {"id": "3", "name": "Charlie", "age": 35},
    ]


@pytest.fixture
def nested_results():
    """Sample nested query results for testing renderers."""
    return [
        {
            "id": "1",
            "properties": {
                "name": ["Alice"],
                "age": [30],
                "interests": ["coding", "reading"],
            },
        },
        {
            "id": "2",
            "properties": {
                "name": ["Bob"],
                "age": [25],
                "interests": ["gaming", "music"],
            },
        },
    ]


def test_raw_render(sample_results):
    """Test raw renderer with simple results."""
    renderer = RawRenderer()
    result = renderer.render(sample_results)

    # Check that result contains all names
    assert "Alice" in result
    assert "Bob" in result
    assert "Charlie" in result

    # Check it's a string representation of the list
    assert result.startswith("[")
    assert result.endswith("]")


def test_raw_render_nested(nested_results):
    """Test raw renderer with nested results."""
    renderer = RawRenderer()
    result = renderer.render(nested_results)

    # Check that result contains all names
    assert "Alice" in result
    assert "Bob" in result

    # Check it contains nested structures
    assert "properties" in result
    assert "interests" in result

    # Check it's a string representation of the list
    assert result.startswith("[")
    assert result.endswith("]")


def test_raw_render_empty():
    """Test raw renderer with empty results."""
    renderer = RawRenderer()
    result = renderer.render([])

    assert result == "No results"


@patch("rich.console.Console.print")
def test_raw_display_results(mock_print, sample_results):
    """Test display_results method."""
    renderer = RawRenderer()
    renderer.display_results(sample_results)

    # Check that console.print was called
    mock_print.assert_called_once()

    # Check that the argument to console.print contains the expected data
    call_arg = mock_print.call_args[0][0]
    assert isinstance(call_arg, str)
    assert "Alice" in call_arg
    assert "Bob" in call_arg
    assert "Charlie" in call_arg
