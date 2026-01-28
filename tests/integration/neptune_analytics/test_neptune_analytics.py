"""Integration tests for Neptune Analytics."""

import pytest


def test_neptune_analytics_cypher_query(neptune_analytics_connection):
    """Test basic Cypher query on Neptune Analytics."""
    app = neptune_analytics_connection
    app.set_language("cypher")

    # Create test data
    app.execute_query("MATCH (n) DETACH DELETE n")
    app.execute_query("""
    CREATE (a:Person {name: 'Alice', age: 30})
    CREATE (b:Person {name: 'Bob', age: 40})
    CREATE (a)-[:KNOWS]->(b)
    """)

    # Query - Neptune Analytics returns nested results
    result = app.execute_query("MATCH (p:Person) RETURN p.name AS name ORDER BY name")
    # Handle nested result format
    if result and isinstance(result[0], dict) and "result" in result[0]:
        names = [r.get("name") for r in result[0]["result"]]
    else:
        names = [r.get("name") for r in result]
    assert "Alice" in names
    assert "Bob" in names


def test_neptune_analytics_count(neptune_analytics_connection):
    """Test count query on Neptune Analytics."""
    app = neptune_analytics_connection
    result = app.execute_query("MATCH (n) RETURN count(n) AS cnt")
    # Handle nested result format
    if result and isinstance(result[0], dict) and "result" in result[0]:
        cnt = result[0]["result"][0].get("cnt")
    else:
        cnt = result[0].get("cnt")
    assert cnt >= 0
