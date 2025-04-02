"""
Tests for graph data models.
"""

import pytest
from graphsh.models.graph import (
    GraphNode,
    GraphEdge,
    GraphPath,
    GraphValue,
    format_graph_element,
)


def test_graph_node():
    """Test GraphNode class."""
    # Test node with labels and properties
    node = GraphNode(
        id="50cae22f-d113-abc8-da8f-f6f08739cda5",
        labels=["product"],
        properties={"price": 1200, "name": "Laptop", "id": "p1"},
    )

    # Test string representation
    assert (
        str(node)
        == '(:product {~id: "50cae22f-d113-abc8-da8f-f6f08739cda5", id: "p1", name: "Laptop", price: 1200})'
    )

    # Test to_dict method
    node_dict = node.to_dict()
    assert node_dict["id"] == "50cae22f-d113-abc8-da8f-f6f08739cda5"
    assert node_dict["labels"] == ["product"]
    assert node_dict["properties"]["price"] == 1200
    assert node_dict["properties"]["name"] == "Laptop"
    assert node_dict["properties"]["id"] == "p1"

    # Test node with no labels
    node = GraphNode(
        id="123",
        labels=[],
        properties={"name": "Test"},
    )

    assert str(node) == '( {~id: "123", name: "Test"})'

    # Test node with no properties
    node = GraphNode(
        id="123",
        labels=["Person"],
        properties={},
    )

    assert str(node) == '(:Person {~id: "123"})'


def test_graph_edge():
    """Test GraphEdge class."""
    # Create source and target nodes
    source_node = GraphNode(id="node1", labels=["Person"], properties={"name": "Alice"})

    target_node = GraphNode(
        id="node2", labels=["Product"], properties={"name": "Laptop"}
    )

    # Test edge with type and properties
    edge = GraphEdge(
        id="abc123",
        source=source_node,
        target=target_node,
        type="PURCHASED",
        properties={"date": "2025-03-23", "quantity": 2},
    )

    # Test string representation with all fields
    assert (
        str(edge)
        == '(:Person {~id: "node1", name: "Alice"})->[:PURCHASED {date: "2025-03-23", quantity: 2}]->(:Product {~id: "node2", name: "Laptop"})'
    )

    # Test to_dict method
    edge_dict = edge.to_dict()
    assert edge_dict["id"] == "abc123"
    assert edge_dict["source"]["id"] == "node1"
    assert edge_dict["source"]["labels"] == ["Person"]
    assert edge_dict["source"]["properties"]["name"] == "Alice"
    assert edge_dict["target"]["id"] == "node2"
    assert edge_dict["target"]["labels"] == ["Product"]
    assert edge_dict["target"]["properties"]["name"] == "Laptop"
    assert edge_dict["type"] == "PURCHASED"
    assert edge_dict["properties"]["date"] == "2025-03-23"
    assert edge_dict["properties"]["quantity"] == 2

    # Test edge with no properties
    edge = GraphEdge(
        id="abc123",
        source=GraphNode(id="node1", labels=["User"]),
        target=GraphNode(id="node2", labels=["User"]),
        type="FOLLOWS",
        properties={},
    )

    assert str(edge) == '(:User {~id: "node1"})->[:FOLLOWS]->(:User {~id: "node2"})'

    # Test edge with no type and no labels
    edge = GraphEdge(
        id="abc123",
        source=GraphNode(id="node1"),
        target=GraphNode(id="node2"),
        type="",
        properties={"since": 2020},
    )

    assert str(edge) == '( {~id: "node1"})->[ {since: 2020}]->( {~id: "node2"})'

    # Test edge with missing source label but with target label
    edge = GraphEdge(
        id="abc123",
        source=GraphNode(id="node1"),
        target=GraphNode(id="node2", labels=["Post"]),
        type="LIKES",
        properties={},
    )

    assert str(edge) == '( {~id: "node1"})->[:LIKES]->(:Post {~id: "node2"})'


def test_graph_path():
    """Test GraphPath class."""
    # Create nodes and edges for a path
    node1 = GraphNode(
        id="1",
        labels=["Person"],
        properties={"name": "Alice"},
    )

    node2 = GraphNode(
        id="2",
        labels=["Person"],
        properties={"name": "Bob"},
    )

    node3 = GraphNode(
        id="3",
        labels=["Person"],
        properties={"name": "Charlie"},
    )

    edge1 = GraphEdge(
        id="e1",
        source=node1,
        target=node2,
        type="KNOWS",
        properties={"since": 2020},
    )

    edge2 = GraphEdge(
        id="e2",
        source=node2,
        target=node3,
        type="WORKS_WITH",
        properties={},
    )

    # Create path
    path = GraphPath(
        nodes=[node1, node2, node3],
        edges=[edge1, edge2],
    )

    # Test string representation
    expected = '(:Person {~id: "1", name: "Alice"})->[:KNOWS {since: 2020}]->(:Person {~id: "2", name: "Bob"})->[:WORKS_WITH]->(:Person {~id: "3", name: "Charlie"})'
    assert str(path) == expected

    # Test to_dict method
    path_dict = path.to_dict()
    assert len(path_dict["nodes"]) == 3
    assert len(path_dict["edges"]) == 2
    assert path_dict["length"] == 2

    # Test empty path
    empty_path = GraphPath(nodes=[], edges=[])
    assert str(empty_path) == "(empty path)"


def test_graph_value():
    """Test GraphValue class."""
    # Test string value
    value = GraphValue("test")
    assert str(value) == '"test"'

    # Test numeric value
    value = GraphValue(123)
    assert str(value) == "123"

    # Test None value
    value = GraphValue(None)
    assert str(value) == "null"

    # Test to_dict method
    value = GraphValue("test")
    assert value.to_dict() == {"value": "test"}


def test_format_graph_element():
    """Test format_graph_element function."""
    # Test formatting a node
    node = GraphNode(
        id="1",
        labels=["Person"],
        properties={"name": "Alice"},
    )
    assert format_graph_element(node) == '(:Person {~id: "1", name: "Alice"})'

    # Test formatting a list of nodes
    nodes = [
        GraphNode(id="1", labels=["Person"], properties={"name": "Alice"}),
        GraphNode(id="2", labels=["Person"], properties={"name": "Bob"}),
    ]
    formatted = format_graph_element(nodes)
    assert formatted == [
        '(:Person {~id: "1", name: "Alice"})',
        '(:Person {~id: "2", name: "Bob"})',
    ]

    # Test formatting a dictionary with nodes
    data = {
        "node1": GraphNode(id="1", labels=["Person"], properties={"name": "Alice"}),
        "node2": GraphNode(id="2", labels=["Person"], properties={"name": "Bob"}),
    }
    formatted = format_graph_element(data)
    assert formatted == {
        "node1": '(:Person {~id: "1", name: "Alice"})',
        "node2": '(:Person {~id: "2", name: "Bob"})',
    }

    # Test formatting a primitive value
    assert format_graph_element(123) == 123
    assert format_graph_element("test") == "test"
