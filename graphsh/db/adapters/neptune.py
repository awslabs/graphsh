"""
Amazon Neptune adapter for GraphSh.
"""

import json
import logging
import os
from typing import Any, Dict, List
from urllib.parse import urlparse

import boto3
import botocore.auth
import botocore.awsrequest
import requests

from rdflib.plugins.sparql.parser import parseUpdate

from graphsh.db.adapters.base import DatabaseAdapter
from graphsh.db.converters.neptune import (
    NeptuneGremlinConverter,
    NeptuneCypherConverter,
    NeptuneSparqlConverter,
)

logger = logging.getLogger(__name__)


class NeptuneAdapter(DatabaseAdapter):
    """Adapter for Amazon Neptune."""

    def __init__(self, **options):
        """Initialize Neptune adapter.

        Args:
            endpoint_str: Neptune endpoint URL or identifier.
            **options: Additional connection options including:
                - auth_type: Authentication type ('iam' or 'none')
                - aws_profile: AWS profile name (for IAM auth)
                - region: AWS region (for IAM auth)
                - ssl: Whether to use SSL (default: True)
                - verify_ssl: Whether to verify SSL certificates (default: True)
                - port: Optional port override
        """
        super().__init__(**options)
        self.http_session = None
        self.auth_type = options.get("auth_type", "none")

        # Validate auth type is one of none or iam
        if self.auth_type not in ["none", "iam"]:
            raise ValueError("Invalid auth_type. Must be 'none' or 'iam'.")

        # Retrieve necessary aws profile details
        self.aws_profile = options.get("aws_profile")
        self.region = options.get("region") or os.environ.get("AWS_REGION", "us-east-1")

        # Validate cluster/endpoint
        self.endpoint = options.get("endpoint")

        # If endpoint is not supplied or IAM auth is turned on, we need to initialize
        # the connection to retrieve the endpoint
        if not self.endpoint or self.auth_type == "iam":
            try:
                self.aws_session = boto3.Session(
                    profile_name=self.aws_profile, region_name=self.region
                )
                # Test if credentials are available
                creds = self.aws_session.get_credentials()
                if creds is None:
                    logger.warning(
                        "No AWS credentials found for profile: %s", self.aws_profile
                    )
            except Exception as e:
                logger.error("Error initializing AWS session: %s", e)
                self.aws_session = boto3.Session(
                    region_name=self.region
                )  # Try default credentials

            # If endpoint is not specified but check if cluster name is mentioned
            cluster_identifier = options.get("cluster_id")
            if not cluster_identifier and not self.endpoint:
                raise ValueError(
                    "Either endpoint or cluster-identifier must be specified."
                )

            # Initialize Neptune client
            if not self.endpoint:
                neptune_client = self.aws_session.client("neptune")
                response = neptune_client.describe_db_clusters(
                    DBClusterIdentifier=cluster_identifier,
                )

                # Retrieve endpoint from response
                self.endpoint = (
                    "https://"
                    + response["DBClusters"][0]["Endpoint"]
                    + ":"
                    + str(response["DBClusters"][0]["Port"])
                )

        # Parse endpoint string
        self.protocol, self.host, self.port, self.use_ssl = self.parse_endpoint(
            self.endpoint, **options
        )

    def connect(self) -> bool:
        """Establish connection to Neptune."""
        if self.http_session:
            return True

        try:
            # Set up HTTP client for all query languages
            self.http_session = requests.Session()

            # Handle SSL verification
            if self.use_ssl and not self.options.get("verify_ssl", True):
                self.http_session.verify = False

            # Apply authentication if needed
            if self.auth_type == "iam":
                self.http_session.auth = self._aws_sigv4_auth

            # Test connection with a simple status check
            try:
                # Determine protocol based on SSL setting
                protocol = "https" if self.use_ssl else "http"
                status_endpoint = f"{protocol}://{self.host}:{self.port}/status"

                response = self.http_session.get(status_endpoint)
                response.raise_for_status()

                logger.info(f"Connected to Neptune at {self.host}:{self.port}")
                return True
            except Exception as e:
                logger.error(f"Failed to connect to Neptune: {e}")
                self.http_session = None
                return False

        except Exception as e:
            logger.error(f"Failed to initialize Neptune connection: {e}")
            self.http_session = None
            return False

    def close(self) -> None:
        """Close database connection."""
        if self.http_session:
            self.http_session.close()
            self.http_session = None

    def execute_query(
        self, query: str, language: str = "gremlin", **params
    ) -> List[Dict[str, Any]]:
        """Execute query in specified language.

        Args:
            query: Query string.
            language: Query language (gremlin, sparql, cypher).
            **params: Additional query parameters.

        Returns:
            List[Dict[str, Any]]: Query results.

        Raises:
            ValueError: If language is not supported.
        """
        if language == "gremlin":
            return self._execute_gremlin(query, **params)
        elif language == "sparql":
            return self._execute_sparql(query, **params)
        elif language == "cypher":
            return self._execute_cypher(query, **params)
        else:
            raise ValueError(f"Unsupported language: {language}")

    def _execute_gremlin(self, query: str, **params) -> List[Dict[str, Any]]:
        """Execute Gremlin query using HTTP API.

        Args:
            query: Gremlin query string.
            **params: Additional query parameters.

        Returns:
            List[Dict[str, Any]]: Query results.
        """
        if not self.http_session:
            self.connect()

        # Determine protocol based on SSL setting
        protocol = "https" if self.use_ssl else "http"
        gremlin_endpoint = f"{protocol}://{self.host}:{self.port}/gremlin"

        try:
            # Prepare request payload - Neptune expects a different format than standard Gremlin Server
            payload = {"gremlin": query}

            # For Neptune, parameters need to be in the "bindings" field
            if params:
                payload["bindings"] = params

            # Log the request for debugging
            logger.debug(f"Gremlin request to {gremlin_endpoint}: {payload}")

            # Execute query via HTTP POST
            response = self.http_session.post(
                gremlin_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            # Log the response status for debugging
            logger.debug(f"Gremlin response status: {response.status_code}")

            # Check for HTTP errors
            response.raise_for_status()

            # Parse response
            result_json = response.json()

            # Log the response content for debugging
            logger.debug(f"Gremlin response content: {result_json}")

            # Neptune Gremlin HTTP API returns results in this format:
            # {
            #   "requestId": "...",
            #   "status": {
            #     "message": "",
            #     "code": 200,
            #     "attributes": {}
            #   },
            #   "result": {
            #     "data": [...],
            #     "meta": {}
            #   }
            # }

            # Check for error status in the response
            if (
                "status" in result_json
                and result_json["status"].get("code", 200) != 200
            ):
                error_msg = result_json["status"].get("message", "Unknown error")
                logger.debug(f"Gremlin query error: {error_msg}")
                return [{"error": error_msg}]

            # Extract and process the results
            if "result" in result_json and "data" in result_json["result"]:
                raw_results = result_json["result"]["data"]

                # Log the raw results for debugging
                logger.debug(f"Gremlin raw results: {raw_results}")

                # Convert results using the NeptuneGremlinConverter
                converted_results = NeptuneGremlinConverter.convert_results(raw_results)
                return converted_results
            elif "result" in result_json:
                # Handle case where "data" might be missing but we have a result
                logger.warning("Unexpected result format: 'data' field missing")
                return [{"result": result_json["result"]}]
            else:
                # Handle empty results
                logger.warning("Empty or unexpected result format")
                return []

        except Exception as e:
            logger.warning(f"Error executing Gremlin query: {e}")
            return [{"error": str(e)}]

    def _execute_sparql(self, query: str, **params) -> List[Dict[str, Any]]:
        """Execute SPARQL query.

        Args:
            query: SPARQL query string.
            **params: Additional query parameters.

        Returns:
            List[Dict[str, Any]]: Query results.
        """
        if not self.http_session:
            self.connect()

        # Determine protocol based on SSL setting
        protocol = "https" if self.use_ssl else "http"
        sparql_endpoint = f"{protocol}://{self.host}:{self.port}/sparql"

        try:
            try:
                parseUpdate(query)
                data = {"update": query}
            except Exception:
                data = {"query": query}

            response = self.http_session.post(
                sparql_endpoint,
                data=data,
                headers={"Accept": "application/sparql-results+json"},
            )
            response.raise_for_status()

            # Parse SPARQL results
            result_json = response.json()

            if "results" in result_json and "bindings" in result_json["results"]:
                bindings = result_json["results"]["bindings"]
                return NeptuneSparqlConverter.convert_results(bindings)

            return []

        except Exception as e:
            logger.warning(f"Error executing SPARQL query: {e}")
            return [{"error": str(e)}]

    def _normalize_sparql_binding(
        self, binding: Dict[str, Dict[str, str]]
    ) -> Dict[str, Any]:
        """Normalize SPARQL binding to dictionary.

        Args:
            binding: SPARQL binding.

        Returns:
            Dict[str, Any]: Normalized binding.
        """
        # This method is kept for backward compatibility but delegates to the converter
        return NeptuneSparqlConverter.normalize_binding(binding)

    def _execute_cypher(self, query: str, **params) -> List[Dict[str, Any]]:
        """Execute OpenCypher query on Neptune.

        Args:
            query: OpenCypher query string.
            **params: Additional query parameters.

        Returns:
            List[Dict[str, Any]]: Query results.
        """
        if not self.http_session:
            self.connect()

        # Determine protocol based on SSL setting
        protocol = "https" if self.use_ssl else "http"
        cypher_endpoint = f"{protocol}://{self.host}:{self.port}/openCypher"

        # Prepare parameters if any
        request_params = {"query": query}

        # Add any additional parameters
        if params:
            # Neptune expects parameters as a JSON string
            request_params["parameters"] = json.dumps(params)

        try:
            response = self.http_session.post(
                cypher_endpoint,
                data=request_params,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()

            # Parse OpenCypher results
            result_json = response.json()

            # Neptune OpenCypher results format:
            # {
            #   "results": [
            #     { "column1": value1, "column2": value2, ... },
            #     ...
            #   ]
            # }

            if "results" in result_json and isinstance(result_json["results"], list):
                # Convert the results using the NeptuneCypherConverter
                results = result_json["results"]
                return NeptuneCypherConverter.convert_results(results)

            # Handle case where results might be in a different format
            return [{"result": result_json}]

        except Exception as e:
            logger.warning(f"Error executing OpenCypher query: {e}")
            return [{"error": str(e)}]

    def _aws_sigv4_auth(
        self, request: requests.PreparedRequest
    ) -> requests.PreparedRequest:
        """Sign request with AWS SigV4.

        Args:
            request: Request to sign.

        Returns:
            requests.PreparedRequest: Signed request.
        """
        # Parse URL to get service and host

        url = urlparse(request.url)
        service = "neptune-db"

        # Get credentials
        credentials = self.aws_session.get_credentials()
        if credentials is None:
            logger.error("No AWS credentials found")
            return request

        # Convert requests.PreparedRequest to botocore.awsrequest.AWSRequest
        aws_request = botocore.awsrequest.AWSRequest(
            method=request.method,
            url=request.url,
            data=request.body,
            headers=dict(request.headers),
        )

        # Sign the request
        botocore.auth.SigV4Auth(credentials, service, self.region).add_auth(aws_request)

        # Copy signed headers back to the original request
        request.headers.update(dict(aws_request.headers))

        return request
