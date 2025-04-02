"""
Pytest configuration for GraphSh tests.
"""

import os
import tempfile
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_app():
    """Create a mock GraphShApp."""
    from graphsh.cli.app import GraphShApp

    app = MagicMock(spec=GraphShApp)
    app.current_language = "gremlin"
    app.output_format = "table"

    return app
