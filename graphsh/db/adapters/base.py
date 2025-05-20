"""
Base database adapter for GraphSh.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from urllib.parse import urlparse


class DatabaseAdapter(ABC):
    """Base class for database adapters."""

    def __init__(self, **options):
        """Initialize database adapter.

        Args:
            endpoint_str: Raw endpoint string (URL, ARN, identifier, etc.)
            **options: Additional connection options.
        """
        self.options = options

    def parse_endpoint(self, endpoint_str: str, **options):
        """Parse endpoint string into components needed by the adapter.

        This default implementation parses a URL-style endpoint.
        Subclasses should override this method if they need different parsing logic.

        Args:
            endpoint_str: Raw endpoint string.
            **options: Additional options that might affect endpoint parsing.
        """
        # Default values
        protocol = "https"
        host = "localhost"
        port = 443
        use_ssl = False

        # Check if endpoint has a protocol
        if "://" in endpoint_str:
            # Parse URL
            parsed_url = urlparse(endpoint_str)
            protocol = parsed_url.scheme
            host = parsed_url.netloc

            # Extract port if present in netloc
            if ":" in host:
                host_parts = host.split(":")
                host = host_parts[0]
                if len(host_parts) > 1 and host_parts[1].isdigit():
                    port = int(host_parts[1])
        else:
            # No protocol specified, assume it's just host[:port]
            if ":" in endpoint_str:
                host_parts = endpoint_str.split(":")
                host = host_parts[0]
                if len(host_parts) > 1 and host_parts[1].isdigit():
                    port = int(host_parts[1])
            else:
                host = endpoint_str

        # Determine if SSL should be used
        use_ssl = protocol.lower() in ["https", "wss"]

        # Override port if explicitly provided in options
        if "port" in options and options["port"]:
            port = int(options["port"])

        return (protocol, host, port, use_ssl)

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to database.

        Returns:
            bool: True if connection successful, False otherwise.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    def execute_query(
        self, query: str, language: str, **params
    ) -> List[Dict[str, Any]]:
        """Execute query in specified language.

        Args:
            query: Query string.
            language: Query language.
            **params: Additional query parameters.

        Returns:
            List[Dict[str, Any]]: Query results.
        """
        pass
