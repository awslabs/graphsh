"""
Tests for table renderer.
"""

import os
import tempfile

import pytest
from rich.console import Console
from rich.table import Table

from graphsh.renderers import TableRenderer


@pytest.fixture
def sample_results():
    """Create sample query results."""
    return [
        {"id": 1, "name": "Alice", "age": 30},
        {"id": 2, "name": "Bob", "age": 25},
        {"id": 3, "name": "Charlie", "age": 35},
    ]


def test_render_results(sample_results, monkeypatch):
    """Test rendering results as table."""
    # Mock Console.print to capture output
    printed_table = None

    def mock_print(self, table):
        nonlocal printed_table
        printed_table = table

    monkeypatch.setattr(Console, "print", mock_print)

    # Format results
    renderer = TableRenderer()
    renderer.display_results(sample_results)

    # Check that a table was printed
    assert printed_table is not None
    assert isinstance(printed_table, Table)

    # Check that table has correct columns
    assert printed_table.columns[0].header == "id"
    assert printed_table.columns[1].header == "name"
    assert printed_table.columns[2].header == "age"


def test_render_empty_results():
    """Test rendering empty results."""
    renderer = TableRenderer()
    result = renderer.display_results([])
    assert result is None  # display_results returns None, but prints "No results."
