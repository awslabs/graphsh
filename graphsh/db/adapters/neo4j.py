"""
Neo4j database adapter for GraphSh.
"""

import logging
from typing import Any, Dict, Optional

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

from graphsh.db.adapters.base import DatabaseAdapter
from graphsh.db.converters.neo4j import Neo4jCypherConverter

logger = logging.getLogger(__name__)


class Neo4jAdapter(DatabaseAdapter):
    """Adapter for Neo4j graph database."""

    def __init__(
        self,
        endpoint: str,
        port: Optional[int] = None,
        **options,
    ):
        """Initialize Neo4j adapter.

        Args:
            endpoint: Neo4j server endpoint.
            port: Neo4j server port.
            **options: Additional options including:
                - username: Neo4j username (required)
                - password: Neo4j password (required)
        """
        super().__init__(**options)
        self.driver = None
        self.session = None

        if not options.get("username"):
            raise ValueError("Username is required for Neo4j connection")

        if not options.get("password"):
            raise ValueError("Password is required for Neo4j connection")

        # Neo4j always uses basic auth
        self.username = options.get("username")
        self.password = options.get("password")

        # Parse endpoint
        self.endpoint = options.get("endpoint", "bolt://localhost:7687")

        # Parse endpoint
        self.protocol, self.host, self.port, self.use_ssl = self.parse_endpoint(
            endpoint, **options
        )

    def connect(self) -> bool:
        """Establish connection to Neo4j.

        Returns:
            bool: True if connection successful, False otherwise.
        """
        if self.driver:
            return True

        if not self.port:
            self.port = 7687  # Default Neo4j Bolt port

        uri = f"bolt://{self.host}:{self.port}"

        # Get authentication credentials
        auth = (self.username, self.password)

        # Filter out options that are not supported by Neo4j driver
        driver_options = {}
        for key, value in self.options.items():
            if key not in [
                "username",
                "password",
                "auth_type",
                "aws_profile",
                "region",
                "ssl",
                "profile",
                "type",
            ]:
                driver_options[key] = value

        try:
            self.driver = GraphDatabase.driver(uri, auth=auth, **driver_options)
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info(f"Connected to Neo4j at {uri}")
            return True
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.driver = None
            return False

    def close(self) -> None:
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            self.driver = None
            logger.info("Neo4j connection closed")

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
        if not self.driver:
            if not self.connect():
                raise RuntimeError("Not connected to Neo4j")

        if language.lower() not in ["cypher", "opencypher"]:
            raise ValueError(
                f"Neo4j adapter only supports Cypher language, got {language}"
            )

        try:
            with self.driver.session() as session:
                result = session.run(query, params)
                records = list(result)

                # Convert to standard format
                columns = result.keys()
                rows = []

                for record in records:
                    row = {}
                    for i, key in enumerate(columns):
                        row[key] = record[key]
                    rows.append(row)

                # Convert the results using the Neo4jCypherConverter
                rows = Neo4jCypherConverter.convert_results(rows)

                return {
                    "columns": columns,
                    "results": rows,
                    "stats": result.consume().counters,
                }
        except Exception as e:
            logger.warning(f"Error executing Neo4j query: {e}")
            return [{"error": str(e)}]
