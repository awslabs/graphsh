"""
Database connection module for GraphSh.
"""

from typing import Dict, Any, List
import logging
from graphsh.db.adapters import get_adapter

logger = logging.getLogger(__name__)


class Connection:
    """Database connection manager."""

    def __init__(self):
        """Initialize connection manager."""
        self.current_connection = None
        self.connection_params = {}
        self.adapter = None
        self.current_language = None  # Track the current language

    def _get_recommended_language(self, db_type: str) -> str:
        """Get recommended query language based on database type.

        Args:
            db_type: Database type.

        Returns:
            str: Recommended query language.
        """
        # Map database types to their primary query languages
        db_language_map = {
            "neo4j": "cypher",
            "neptune": "gremlin",  # Neptune supports multiple languages, but Gremlin is common
            "neptune-analytics": "cypher",
            "tinkerpop": "gremlin",
        }

        return db_language_map.get(
            db_type.lower(), "gremlin"
        )  # Default to gremlin if unknown

    def connect(self, **kwargs) -> bool:
        """Connect to database.

        Args:
            **kwargs: Connection parameters.

        Returns:
            bool: True if connection successful, False otherwise.
        """
        try:
            # Store connection parameters
            self.connection_params = kwargs

            # Debug log the connection parameters
            logger.info(f"Connection parameters: {kwargs}")

            # Determine database type
            if "type" not in kwargs:
                raise ValueError("Database type (--type) is required")
            db_type = kwargs.get("type")

            # Create adapter - pass all options
            try:
                self.adapter = get_adapter(db_type, **kwargs)
            except Exception as e:
                logger.error(f"Failed to create adapter: {e}")
                return False

            # Connect
            try:
                if self.adapter.connect():
                    self.current_connection = True
                    logger.info(f"Connected to {db_type} database")

                    # Determine the appropriate language based on database type
                    recommended_language = self._get_recommended_language(db_type)

                    # Store the database type for future reference
                    self.db_type = db_type

                    # Set the recommended language if no language is currently set
                    # or if the current language isn't compatible with this database
                    if recommended_language:
                        if not self.current_language:
                            self.current_language = recommended_language
                            logger.info(
                                f"Setting default language to {recommended_language} based on database type"
                            )
                        elif not self._is_language_compatible(
                            db_type, self.current_language
                        ):
                            old_language = self.current_language
                            self.current_language = recommended_language
                            logger.info(
                                f"Switching language from {old_language} to {recommended_language} for compatibility with {db_type}"
                            )

                    return True
                else:
                    self.current_connection = None
                    self.adapter = None
                    logger.error(f"Failed to connect to {db_type} database")
                    return False
            except Exception as e:
                logger.error(f"Connection error during connect(): {e}")
                self.current_connection = None
                self.adapter = None
                return False

        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.current_connection = None
            self.adapter = None
            return False

    def _is_language_compatible(self, db_type: str, language: str) -> bool:
        """Check if a language is compatible with a database type.

        Args:
            db_type: Database type.
            language: Query language.

        Returns:
            bool: True if language is compatible with database type.
        """
        # Define compatibility matrix
        compatibility = {
            "neo4j": ["cypher"],
            "neptune": ["gremlin", "sparql", "cypher"],  # Neptune supports all three
            "neptune-analytics": ["cypher"],
            "tinkerpop": ["gremlin"],
        }

        # Get compatible languages for this database type
        compatible_languages = compatibility.get(db_type.lower(), [])

        # Check if the language is compatible
        return language.lower() in compatible_languages

    def execute(self, query: str) -> List[Dict[str, Any]]:
        """Execute query.

        Args:
            query: Query string.

        Returns:
            List[Dict[str, Any]]: Query results.

        Raises:
            RuntimeError: If not connected to a database.
        """
        if not self.current_connection or not self.adapter:
            raise RuntimeError("Not connected to a database")

        try:
            # Determine language from connection parameters or current language
            language = self.connection_params.get("language", "gremlin")

            # If the app has set a specific language, use that instead
            if hasattr(self, "current_language") and self.current_language:
                language = self.current_language

            # Execute query using adapter
            result = self.adapter.execute_query(query, language)

            # If result has proper structure, return it
            if isinstance(result, dict) and "results" in result:
                return result["results"]

            # Otherwise, return a simple result structure
            return [{"result": result}]

        except Exception as e:
            logger.error(f"Query execution error: {e}")
            return [{"error": str(e)}]

    def disconnect(self) -> None:
        """Disconnect from database."""
        if self.adapter:
            self.adapter.close()

        self.current_connection = None
        self.connection_params = {}
        self.adapter = None
