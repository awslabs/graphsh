"""
Fixtures for integration tests.
"""

import os
import time
import pytest
import socket
import sys
import ssl
from graphsh.cli.app import GraphShApp


def is_port_open(host, port):
    """Check if a port is open on the given host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.settimeout(1)
            s.connect((host, port))
            return True
        except (socket.timeout, ConnectionRefusedError):
            return False


@pytest.fixture(scope="session")
def neo4j_connection():
    """Create a connection to Neo4j for testing."""
    # Connection details - can be configured via environment variables
    host = os.environ.get("NEO4J_HOST", "localhost")
    port = int(os.environ.get("NEO4J_PORT", "7687"))
    username = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "password")

    # Check if Neo4j is available
    if not is_port_open(host, port):
        pytest.skip(
            f"Neo4j is not available at {host}:{port}. Skipping Neo4j integration tests."
        )

    # Create app
    app = GraphShApp()

    # Connect directly using parameters
    connected = app.connect(
        profile=None,
        db_type="neo4j",
        endpoint=f"bolt://{host}:{port}",  # Use bolt protocol for Neo4j
        auth_type="basic",
        username=username,
        password=password,
    )

    # Set language to Cypher for Neo4j
    app.set_language("cypher")

    try:
        # Load test data
        app.execute_query("MATCH (n) DETACH DELETE n")

        # Create test data - a simple social network
        app.execute_query("""
        CREATE (alice:Person {name: 'Alice', age: 30})
        CREATE (bob:Person {name: 'Bob', age: 40})
        CREATE (charlie:Person {name: 'Charlie', age: 25})
        CREATE (david:Person {name: 'David', age: 35})
        
        CREATE (alice)-[:KNOWS {since: 2010}]->(bob)
        CREATE (bob)-[:KNOWS {since: 2015}]->(charlie)
        CREATE (charlie)-[:KNOWS {since: 2020}]->(david)
        CREATE (alice)-[:KNOWS {since: 2018}]->(david)
        """)

        yield app

        # Cleanup
        app.connection.disconnect()
    except Exception as e:
        pytest.fail(f"Failed to set up Neo4j test data: {e}", e)


@pytest.fixture(scope="session")
def neptune_connection():
    """Create a connection to Neptune for testing.

    Uses the local Neptune docker container for testing.
    """
    # Connection details for Neptune docker container
    host = os.environ.get("NEPTUNE_HOST", "localhost")
    port = int(os.environ.get("NEPTUNE_PORT", "8182"))

    # Check if Neptune is available
    if not is_port_open(host, port):
        # Skip tests if Neptune is not available
        pytest.skip(
            f"Neptune is not available at {host}:{port}. Skipping Neptune integration tests."
        )

    # Create app
    app = GraphShApp()

    # Connect directly using parameters - use neptune type
    connected = app.connect(
        db_type="neptune",  # Use actual neptune type
        endpoint="https://localhost",  # Use HTTPS protocol for Neptune
        port=port,
        auth_type="none",
        ssl=True,  # SSL for Neptune
        verify_ssl=False,  # Don't verify SSL certificates for self-signed certs
    )

    if not connected:
        pytest.skip(
            f"Could not connect to Neptune at {host}:{port}. Skipping Neptune integration tests."
        )

    try:
        # Set language to Gremlin
        app.set_language("gremlin")

        # Load test data - first clear existing data
        app.execute_query("g.V().drop()")

        # Create test data - a simple product catalog
        app.execute_query("""
        g.addV('product').property('id', 'p1').property('name', 'Laptop').property('price', 1200).
          addV('product').property('id', 'p2').property('name', 'Phone').property('price', 800).
          addV('product').property('id', 'p3').property('name', 'Tablet').property('price', 500).
          addV('category').property('id', 'c1').property('name', 'Electronics').
          addV('category').property('id', 'c2').property('name', 'Computers').
          addV('category').property('id', 'c3').property('name', 'Mobile').
          addE('belongs_to').from(__.V().has('id', 'p1')).to(__.V().has('id', 'c2')).
          addE('belongs_to').from(__.V().has('id', 'p2')).to(__.V().has('id', 'c3')).
          addE('belongs_to').from(__.V().has('id', 'p3')).to(__.V().has('id', 'c3')).
          addE('subcategory_of').from(__.V().has('id', 'c2')).to(__.V().has('id', 'c1')).
          addE('subcategory_of').from(__.V().has('id', 'c3')).to(__.V().has('id', 'c1'))
        """)

        yield app

        # Cleanup
        app.connection.disconnect()
    except Exception as e:
        pytest.fail(f"Failed to set up Neptune test data: {e}")
