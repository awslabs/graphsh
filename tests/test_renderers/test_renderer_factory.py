"""
Tests for renderer factory.
"""

import pytest

from graphsh.renderers import get_renderer, TableRenderer, RawRenderer


def test_get_renderer_table():
    """Test getting table renderer."""
    renderer = get_renderer("table")
    assert isinstance(renderer, TableRenderer)


def test_get_renderer_raw():
    """Test getting raw renderer."""
    renderer = get_renderer("raw")
    assert isinstance(renderer, RawRenderer)


def test_get_renderer_invalid():
    """Test getting invalid renderer."""
    with pytest.raises(ValueError):
        get_renderer("invalid")
