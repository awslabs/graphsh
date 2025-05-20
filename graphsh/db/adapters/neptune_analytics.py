"""
Amazon Neptune Analytics adapter for GraphSh.

This adapter uses boto3's neptune-graph APIs to interact with Neptune Analytics.
"""

import json
import logging
import os
from typing import Any, Dict, List

import boto3
from botocore.exceptions import ClientError

from graphsh.db.adapters.base import DatabaseAdapter
from graphsh.db.converters.neptune import NeptuneCypherConverter

logger = logging.getLogger(__name__)


class NeptuneAnalyticsAdapter(DatabaseAdapter):
    """Adapter for Amazon Neptune Analytics using boto3 neptune-graph APIs."""

    def __init__(self, **options):
        """Initialize Neptune Analytics adapter.

        Args:
            endpoint_str: Neptune Analytics endpoint identifier (can be cluster ID, ARN, or full endpoint URL).
            **options: Additional connection options including:
                - aws_profile: AWS profile name
                - region: AWS region
                - graph_id: Neptune Analytics graph ID (required if not in endpoint)
        """
        # Initialize base class but don't use its default endpoint parsing
        self.options = options
        self.client = None

        # Read aws related details
        self.aws_profile = options.get("aws_profile")
        self.region = options.get("region") or os.environ.get("AWS_REGION", "us-east-1")

        # Initialize graph id
        self.graph_id = options.get("graph_id")
        if not self.graph_id:
            # Parse graph id from endpoint
            self.parse_graph_id(options.get("endpoint"))

    def parse_graph_id(self, endpoint_str: str) -> str:
        """Parse Neptune Analytics endpoint string.

        This method extracts graph id from endpoint:
        - Full endpoint URL: g-12345.us-east-1.neptune-graph.amazonaws.com

        Args:
            endpoint_str: Raw endpoint string.
        """
        # If endpoint is a full URL (contains neptune-graph.amazonaws.com)
        if "neptune-graph.amazonaws.com" in endpoint_str:
            # Extract graph ID from endpoint (g-12345.us-east-1.neptune-graph.amazonaws.com)
            try:
                self.graph_id = endpoint_str.split(".")[0]
                # Extract region if not provided
                if not self.region and len(endpoint_str.split(".")) > 1:
                    self.region = endpoint_str.split(".")[1]
            except (IndexError, AttributeError):
                if not self.graph_id:
                    raise ValueError(
                        f"Invalid Neptune Analytics endpoint: {endpoint_str}"
                    )

        # Validate we have a graph ID
        if not self.graph_id:
            raise ValueError(f"Invalid Neptune Analytics endpoint: {endpoint_str}")

        logger.info(
            f"Neptune Analytics adapter configured with graph ID: {self.graph_id}, region: {self.region}"
        )

    def connect(self) -> bool:
        """Establish connection to Neptune Analytics.

        Returns:
            bool: True if connection successful, False otherwise.
        """
        if self.client:
            return True

        try:
            # Initialize boto3 session with profile if provided
            if self.aws_profile:
                session = boto3.Session(
                    profile_name=self.aws_profile, region_name=self.region
                )
            else:
                session = boto3.Session(region_name=self.region)

            # Create neptune-graph client
            self.client = session.client("neptune-graph", region_name=self.region)

            # Test connection by describing the graph
            try:
                response = self.client.get_graph(graphIdentifier=self.graph_id)
                logger.info(f"Connected to Neptune Analytics graph: {self.graph_id}")
                return True
            except ClientError as e:
                logger.error(f"Failed to connect to Neptune Analytics graph: {e}")
                self.client = None
                return False

        except Exception as e:
            logger.error(f"Failed to initialize Neptune Analytics connection: {e}")
            self.client = None
            return False

    def close(self) -> None:
        """Close database connection."""
        # boto3 clients don't need explicit closing
        self.client = None

    def execute_query(
        self, query: str, language: str = "cypher", **params
    ) -> List[Dict[str, Any]]:
        """Execute query in specified language.

        Args:
            query: Query string.
            language: Query language (cypher).
            **params: Additional query parameters.

        Returns:
            List[Dict[str, Any]]: Query results.

        Raises:
            ValueError: If language is not supported.
        """
        if language == "cypher":
            return self._execute_cypher(query, **params)
        else:
            raise ValueError(f"Unsupported language: {language}")

    def _execute_cypher(self, query: str, **params) -> List[Dict[str, Any]]:
        """Execute OpenCypher query using boto3 neptune-graph API.

        Args:
            query: OpenCypher query string.
            **params: Additional query parameters.

        Returns:
            List[Dict[str, Any]]: Query results.
        """
        if not self.client:
            self.connect()

        try:
            # Prepare parameters if any
            parameters = {}
            if params:
                parameters = params

            # Execute query via boto3
            response = self.client.execute_query(
                graphIdentifier=self.graph_id,
                queryString=query,
                language="OPEN_CYPHER",
                parameters=parameters,
            )

            # Process the response
            response = json.loads(response["payload"].read())
            if "results" in response and isinstance(response["results"], list):
                # Convert the results using the NeptuneCypherConverter
                results = response["results"]
                return NeptuneCypherConverter.convert_results(results)
            else:
                # Handle case where results might be in a different format
                return [{"result": response.get("results", {})}]

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            logger.warning(
                f"Error executing OpenCypher query: {error_code} - {error_message}"
            )
            return [{"error": f"{error_code}: {error_message}"}]
        except Exception as e:
            logger.warning(f"Error executing OpenCypher query: {e}")
            return [{"error": str(e)}]
