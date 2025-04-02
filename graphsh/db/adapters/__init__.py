"""
Database adapters for GraphSh.
"""

from graphsh.db.adapters.base import DatabaseAdapter
from graphsh.db.adapters.factory import get_adapter, get_adapter_for_type

__all__ = [
    "DatabaseAdapter",
    "get_adapter",
    "get_adapter_for_type",
]
