"""Fixtures for integration tests with on-demand stack deployment."""

import os
import pytest
from graphsh.cli.app import GraphShApp

# Import stack manager only when needed (avoids boto3 import for local tests)
_stack_manager = None


def get_stack_manager():
    global _stack_manager
    if _stack_manager is None:
        from .stack_manager import StackManager

        _stack_manager = StackManager()
    return _stack_manager


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "neo4j: tests requiring Neo4j")
    config.addinivalue_line("markers", "neptune: tests requiring Neptune")
    config.addinivalue_line(
        "markers", "neptune_analytics: tests requiring Neptune Analytics"
    )


def pytest_collection_modifyitems(config, items):
    """Auto-add markers based on test file location."""
    for item in items:
        path = str(item.fspath)
        if "/neo4j/" in path:
            item.add_marker(pytest.mark.neo4j)
        elif "/neptune_analytics/" in path:
            item.add_marker(pytest.mark.neptune_analytics)
        elif "/neptune/" in path:
            item.add_marker(pytest.mark.neptune)


@pytest.fixture(scope="session")
def neo4j_stack(request):
    """Start Neo4j Docker container for session, stop after."""
    import subprocess
    import time
    import socket

    if os.environ.get("NEO4J_HOST"):
        yield {
            "Host": os.environ["NEO4J_HOST"],
            "Port": os.environ.get("NEO4J_PORT", "7687"),
        }
        return

    # Start Neo4j container
    container_name = "graphsh-neo4j-test"
    subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
    subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            container_name,
            "-p",
            "7474:7474",
            "-p",
            "7687:7687",
            "-e",
            "NEO4J_AUTH=neo4j/testpassword",
            "neo4j:community",
        ],
        check=True,
    )

    # Wait for Neo4j to be ready
    host, port = "localhost", 7687
    for _ in range(60):
        try:
            with socket.create_connection((host, port), timeout=2):
                break
        except (socket.timeout, ConnectionRefusedError, OSError):
            time.sleep(2)
    else:
        pytest.fail("Neo4j not ready after 2 minutes")

    time.sleep(5)  # Extra time for Neo4j to fully initialize

    yield {"Host": host, "Port": str(port)}

    # Cleanup
    if not os.environ.get("KEEP_CONTAINERS"):
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)


@pytest.fixture(scope="session")
def neptune_stack(request):
    """Deploy Neptune stack for session, teardown after."""
    if os.environ.get("NEPTUNE_HOST"):
        yield {
            "Host": os.environ["NEPTUNE_HOST"],
            "Port": os.environ.get("NEPTUNE_PORT", "8182"),
        }
        return

    if os.environ.get("SKIP_DEPLOY"):
        pytest.skip("SKIP_DEPLOY set and no NEPTUNE_HOST")

    mgr = get_stack_manager()
    outputs = mgr.deploy("neptune")
    yield outputs
    if not os.environ.get("KEEP_STACKS"):
        mgr.teardown("neptune")


@pytest.fixture(scope="session")
def neptune_analytics_stack(request):
    """Deploy Neptune Analytics stack for session, teardown after."""
    if os.environ.get("NEPTUNE_ANALYTICS_GRAPH_ID"):
        yield {"GraphId": os.environ["NEPTUNE_ANALYTICS_GRAPH_ID"]}
        return

    if os.environ.get("SKIP_DEPLOY"):
        pytest.skip("SKIP_DEPLOY set and no NEPTUNE_ANALYTICS_GRAPH_ID")

    mgr = get_stack_manager()
    outputs = mgr.deploy("neptune-analytics")
    yield outputs
    if not os.environ.get("KEEP_STACKS"):
        mgr.teardown("neptune-analytics")


@pytest.fixture(scope="session")
def neo4j_connection(neo4j_stack):
    """Create Neo4j connection using Docker container."""
    import time

    host = neo4j_stack["Host"]
    port = int(neo4j_stack.get("Port", "7687"))
    username = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "testpassword")

    app = GraphShApp()

    # Retry connection until Neo4j is fully ready
    for attempt in range(30):
        connected = app.connect(
            db_type="neo4j",
            endpoint=f"bolt://{host}:{port}",
            auth_type="basic",
            username=username,
            password=password,
        )
        if connected:
            break
        time.sleep(2)
    else:
        pytest.fail("Could not connect to Neo4j after 60 seconds")

    app.set_language("cypher")

    # Setup test data
    app.execute_query("MATCH (n) DETACH DELETE n")
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
    app.connection.disconnect()


@pytest.fixture(scope="session")
def neptune_connection(neptune_stack):
    """Create Neptune connection using deployed stack."""
    host = neptune_stack["Host"]
    port = neptune_stack.get("Port", "8182")

    app = GraphShApp()
    app.connect(
        db_type="neptune",
        endpoint=f"https://{host}",
        port=int(port),
        auth_type="iam",
        ssl=True,
        verify_ssl=False,
    )
    app.set_language("gremlin")

    # Setup test data
    app.execute_query("g.V().drop()")

    # Create vertices - use iterate() to execute without returning results
    app.execute_query("""
    g.addV('product').property('id', 'p1').property('name', 'Laptop').property('price', 1200).iterate()
    """)
    app.execute_query("""
    g.addV('product').property('id', 'p2').property('name', 'Phone').property('price', 800).iterate()
    """)
    app.execute_query("""
    g.addV('product').property('id', 'p3').property('name', 'Tablet').property('price', 500).iterate()
    """)
    app.execute_query("""
    g.addV('category').property('id', 'c1').property('name', 'Electronics').iterate()
    """)
    app.execute_query("""
    g.addV('category').property('id', 'c2').property('name', 'Computers').iterate()
    """)
    app.execute_query("""
    g.addV('category').property('id', 'c3').property('name', 'Mobile').iterate()
    """)

    # Create Movie nodes for Cypher tests
    app.execute_query("""
    g.addV('Movie').property('title', 'The Matrix').property('released', 1999).property('tagline', 'Welcome to the Real World').iterate()
    """)

    # Create edges between products and categories
    app.execute_query("""
    g.V().has('product', 'id', 'p1').as('p').
      V().has('category', 'id', 'c2').
      addE('belongs_to').from('p').iterate()
    """)
    app.execute_query("""
    g.V().has('product', 'id', 'p2').as('p').
      V().has('category', 'id', 'c3').
      addE('belongs_to').from('p').iterate()
    """)
    app.execute_query("""
    g.V().has('product', 'id', 'p3').as('p').
      V().has('category', 'id', 'c1').
      addE('belongs_to').from('p').iterate()
    """)

    # Create category hierarchy edges (subcategory_of)
    app.execute_query("""
    g.V().has('category', 'id', 'c2').as('c').
      V().has('category', 'id', 'c1').
      addE('subcategory_of').from('c').iterate()
    """)
    app.execute_query("""
    g.V().has('category', 'id', 'c3').as('c').
      V().has('category', 'id', 'c1').
      addE('subcategory_of').from('c').iterate()
    """)

    yield app
    app.connection.disconnect()


@pytest.fixture(scope="session")
def neptune_analytics_connection(neptune_analytics_stack):
    """Create Neptune Analytics connection using deployed stack."""
    graph_id = neptune_analytics_stack["GraphId"]
    region = os.environ.get("AWS_REGION", "us-east-1")

    app = GraphShApp()
    app.connect(
        db_type="neptune-analytics",
        graph_id=graph_id,
        region=region,
        auth_type="iam",
    )
    app.set_language("cypher")

    yield app
    app.connection.disconnect()
