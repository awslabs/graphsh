"""
Tests for the Neptune Analytics adapter.
"""

import io
import json
import pytest
from unittest.mock import MagicMock, patch
from botocore.response import StreamingBody

from graphsh.db.adapters.neptune_analytics import NeptuneAnalyticsAdapter


@pytest.fixture
def mock_boto3_session():
    """Mock boto3 session."""
    with patch("boto3.Session") as mock_session:
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        yield mock_session, mock_client


def test_init_with_cluster_id():
    """Test initialization with cluster ID."""
    adapter = NeptuneAnalyticsAdapter(
        graph_id="my-graph-id",
        region="us-west-2"
    )
    assert adapter.graph_id == "my-graph-id"
    assert adapter.region == "us-west-2"


def test_init_with_endpoint():
    """Test initialization with ARN."""
    adapter = NeptuneAnalyticsAdapter(
        endpoint="g-12445.us-east-1.neptune-graph.amazonaws.com",
    )
    assert adapter.graph_id == "g-12445"


def test_init_without_valid_endpoint():
    """Test initialization without graph ID."""
    with pytest.raises(ValueError, match="Invalid Neptune Analytics endpoint: blah"):
        NeptuneAnalyticsAdapter(endpoint="blah")


def test_connect_success(mock_boto3_session):
    """Test successful connection."""
    mock_session, mock_client = mock_boto3_session
    mock_client.get_graph.return_value = {"graphId": "g-12445"}

    adapter = NeptuneAnalyticsAdapter(
        endpoint="g-12445.us-east-1.neptune-graph.amazonaws.com"
    )

    result = adapter.connect()

    assert result is True
    mock_session.assert_called_once_with(region_name="us-east-1")
    mock_session.return_value.client.assert_called_once_with(
        "neptune-graph", region_name="us-east-1"
    )
    mock_client.get_graph.assert_called_once_with(graphIdentifier="g-12445")


def test_connect_failure(mock_boto3_session):
    """Test connection failure."""
    mock_session, mock_client = mock_boto3_session
    from botocore.exceptions import ClientError

    mock_client.get_graph.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFoundException", "Message": "Graph not found"}},
        "GetGraph",
    )

    adapter = NeptuneAnalyticsAdapter(
        endpoint="g-12445.us-east-1.neptune-graph.amazonaws.com"
    )

    result = adapter.connect()

    assert result is False
    assert adapter.client is None


def test_execute_cypher_query(mock_boto3_session):
    """Test executing a Cypher query."""
    mock_session, mock_client = mock_boto3_session
    mock_client.get_graph.return_value = {"graphId": "g-12445"}

    results_json = {
        "results": [
            {"n": {"id": "1", "labels": ["Person"], "properties": {"name": "Alice"}}},
            {"n": {"id": "2", "labels": ["Person"], "properties": {"name": "Bob"}}},
        ]
    }
    results_encoded = json.dumps(results_json).encode()

    mock_client.execute_query.return_value = {
        "payload": StreamingBody(io.BytesIO(results_encoded), len(results_encoded))
    }

    adapter = NeptuneAnalyticsAdapter(
        endpoint="g-12445.us-east-1.neptune-graph.amazonaws.com"
    )

    adapter.connect()
    results = adapter.execute_query(
        "MATCH (n:Person) RETURN n LIMIT 2", language="cypher"
    )

    mock_client.execute_query.assert_called_once_with(
        graphIdentifier="g-12445",
        queryString="MATCH (n:Person) RETURN n LIMIT 2",
        language="OPEN_CYPHER",
        parameters={},
    )

    assert len(results) == 2
