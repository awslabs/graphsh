"""
Integration tests for renderers.
"""

import pytest

from graphsh.renderers import (
    get_renderer,
    TableRenderer,
    RawRenderer,
)


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


def test_get_renderer():
    """Test getting renderers by name."""
    # Test valid renderers
    assert isinstance(get_renderer("table"), TableRenderer)
    assert isinstance(get_renderer("raw"), RawRenderer)

    # Test invalid renderer
    with pytest.raises(ValueError):
        get_renderer("invalid")


def test_table_renderer_simple(sample_results):
    """Test table renderer with simple results."""
    renderer = TableRenderer()
    result = renderer.render(sample_results)

    # For table renderer, we get a rich.table.Table object
    # Just check it's not empty
    assert result is not None


def test_raw_renderer_simple(sample_results):
    """Test raw renderer with simple results."""
    renderer = RawRenderer()
    result = renderer.render(sample_results)

    # Check that result contains all names as a string representation
    assert "Alice" in result
    assert "Bob" in result
    assert "Charlie" in result

    # Check it's a string representation of the list
    assert result.startswith("[")
    assert result.endswith("]")
