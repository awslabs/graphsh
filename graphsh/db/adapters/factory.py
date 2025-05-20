"""
Factory for creating database adapters.
"""

import logging

logger = logging.getLogger(__name__)


def get_adapter_for_type(db_type):
    """Get database adapter class by type.

    Args:
        db_type: Database type.

    Returns:
        Type[DatabaseAdapter]: Database adapter class.

    Raises:
        ValueError: If db_type is not supported.
    """
    if db_type == "neptune":
        from graphsh.db.adapters.neptune import NeptuneAdapter

        return NeptuneAdapter
    elif db_type == "neptune-analytics":
        from graphsh.db.adapters.neptune_analytics import NeptuneAnalyticsAdapter

        return NeptuneAnalyticsAdapter
    elif db_type == "neo4j":
        from graphsh.db.adapters.neo4j import Neo4jAdapter

        return Neo4jAdapter
    elif db_type in ["tinkerpop", "gremlin-server"]:
        # Use the TinkerPop adapter for Gremlin Server
        from graphsh.db.adapters.tinkerpop import TinkerPopAdapter

        return TinkerPopAdapter
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


def get_adapter(db_type, **options):
    """Create and return a database adapter instance.

    Args:
        db_type: Database type.
        **options: Connection options including authentication parameters.

    Returns:
        DatabaseAdapter: Database adapter instance.

    Raises:
        ValueError: If db_type is not supported.
    """
    # Log the adapter creation
    logger.info(f"Creating adapter for database type: {db_type}")

    try:
        # Get adapter class
        adapter_class = get_adapter_for_type(db_type)

        # Create adapter instance
        logger.info(f"Initializing {adapter_class.__name__} with options: {options}")
        return adapter_class(**options)
    except Exception as e:
        logger.error(f"Error creating adapter: {e}")
        raise
