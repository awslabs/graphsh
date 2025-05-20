"""
TinkerPop Gremlin Server adapter for GraphSh.
"""

import logging
from typing import Any, Dict, Optional

from gremlin_python.driver.client import Client
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal

from graphsh.db.adapters.base import DatabaseAdapter
from graphsh.db.converters.tinkerpop import TinkerpopGremlinConverter

logger = logging.getLogger(__name__)


class TinkerPopAdapter(DatabaseAdapter):
    """Adapter for TinkerPop Gremlin Server."""

    def __init__(
        self,
        endpoint: str,
        port: Optional[int] = None,
        **options,
    ):
        """Initialize TinkerPop adapter.

        Args:
            endpoint: Gremlin Server endpoint.
            port: Gremlin Server port.
            **options: Additional options.
        """
        super().__init__(**options)
        self.client = None
        self.g = None
        self.use_ssl = options.get("ssl", False)
        self.endpoint = options.get("endpoint", "wss://localhost:8182")
        self.protocol, self.host, self.port, self.use_ssl = self.parse_endpoint(
            endpoint, **options
        )

    def connect(self) -> bool:
        """Establish connection to Gremlin Server.

        Returns:
            bool: True if connection successful, False otherwise.
        """
        if self.client:
            return True

        if not self.port:
            self.port = 8182  # Default Gremlin Server port

        # Determine protocol (ws or wss)
        protocol = "wss" if self.use_ssl else "ws"
        uri = f"{protocol}://{self.endpoint}:{self.port}/gremlin"

        try:
            # Create client with appropriate options
            connection_options = {}

            # Set SSL verification option
            if protocol == "wss" and not self.options.get("verify_ssl", True):
                connection_options["ssl"] = False

            # Log connection attempt
            logger.info(f"Attempting to connect to Gremlin Server at {uri}")
            logger.info(f"SSL enabled: {self.use_ssl}")

            # Create client
            self.client = Client(uri, "g", **connection_options)

            # Test connection with a simple query
            try:
                result = self.client.submit("g.V().limit(1)").all().result()
                logger.info(f"Connected to Gremlin Server at {uri}")
            except Exception as e:
                # If the test query fails but doesn't raise a connection error,
                # we'll still consider the connection successful but log the issue
                logger.warning(
                    f"Connected to Gremlin Server but test query failed: {e}"
                )

            # Create traversal source
            remote_conn = DriverRemoteConnection(uri, "g", **connection_options)
            self.g = traversal().withRemote(remote_conn)

            return True
        except Exception as e:
            logger.error(f"Failed to connect to Gremlin Server: {e}")
            self.client = None
            self.g = None
            return False

    def close(self) -> None:
        """Close Gremlin Server connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.g = None
            logger.info("Gremlin Server connection closed")

    def execute_query(self, query: str, language: str, **params) -> Dict[str, Any]:
        """Execute query in specified language.

        Args:
            query: Query string.
            language: Query language.
            **params: Query parameters.

        Returns:
            Dict[str, Any]: Query results.

        Raises:
            ValueError: If language is not supported.
            RuntimeError: If not connected.
        """
        if not self.client:
            if not self.connect():
                raise RuntimeError("Not connected to Gremlin Server")

        if language.lower() != "gremlin":
            raise ValueError(
                f"TinkerPop adapter only supports Gremlin language, got {language}"
            )

        try:
            # Execute query
            result = self.client.submit(query, params).all().result()

            # Convert results using the TinkerpopGremlinConverter
            converted_results = TinkerpopGremlinConverter.convert_results(result)

            # If the result is a list of non-dict items, wrap each in a dict
            if not converted_results and result:
                converted_results = [
                    {"result": TinkerpopGremlinConverter.convert_value(item)}
                    for item in result
                ]

            # Convert to standard format
            return {
                "columns": ["result"],
                "results": converted_results,
            }
        except Exception as e:
            logger.warning(f"Error executing Gremlin query: {e}")
            return [{"error": str(e)}]
