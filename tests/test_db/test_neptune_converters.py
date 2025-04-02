"""
Tests for neptune converters.
"""

import pytest
from graphsh.db.converters.neptune import NeptuneGremlinConverter
from graphsh.models.graph import GraphNode, GraphEdge, GraphPath


def test_neptune_converter_node():
    """Test NeptuneGremlinConverter for nodes."""
    # Test converting g.V().limit(1)
    results = {
        "requestId": "aa601347-025e-43b1-9661-5696627c59a3",
        "status": {
            "message": "",
            "code": 200,
            "attributes": {"@type": "g:Map", "@value": []},
        },
        "result": {
            "data": {
                "@type": "g:List",
                "@value": [
                    {
                        "@type": "g:Vertex",
                        "@value": {
                            "id": "e3bc139b-a0c7-41ce-a9a3-082b9280612c",
                            "label": "Person::Actor",
                            "properties": {
                                "name": [
                                    {
                                        "@type": "g:VertexProperty",
                                        "@value": {
                                            "id": {
                                                "@type": "g:Int32",
                                                "@value": 1871508256,
                                            },
                                            "value": "Charlie Sheen",
                                            "label": "name",
                                        },
                                    }
                                ]
                            },
                        },
                    }
                ],
            },
            "meta": {"@type": "g:Map", "@value": []},
        },
    }

    nodes = NeptuneGremlinConverter.convert_results(results["result"]["data"])
    assert len(nodes) == 1
    node = nodes[0]

    # Test string representation
    assert (
        str(node)
        == '(:Person:Actor {~id: "e3bc139b-a0c7-41ce-a9a3-082b9280612c", name: "Charlie Sheen"})'
    )


def test_neptune_converter_empty():
    """Test NeptuneGremlinConverter for empty results."""
    results = {
        "requestId": "aa601347-025e-43b1-9661-5696627c59a3",
        "status": {
            "message": "",
            "code": 200,
            "attributes": {"@type": "g:Map", "@value": []},
        },
        "result": {
            "data": {"@type": "g:List", "@value": []},
            "meta": {"@type": "g:Map", "@value": []},
        },
    }

    nodes = NeptuneGremlinConverter.convert_results(results["result"]["data"])
    assert len(nodes) == 0


def test_neptune_converter_valuemap():
    """Test NeptuneGremlinConverter for valueMap results."""
    # Test converting g.V().limit(1).valueMap()
    results = {
        "requestId": "8b834aa1-439e-43ec-a1e5-703f9a8761b0",
        "status": {
            "message": "",
            "code": 200,
            "attributes": {"@type": "g:Map", "@value": []},
        },
        "result": {
            "data": {
                "@type": "g:List",
                "@value": [
                    {
                        "@type": "g:Map",
                        "@value": [
                            "name",
                            {"@type": "g:List", "@value": ["Charlie Sheen"]},
                        ],
                    }
                ],
            },
            "meta": {"@type": "g:Map", "@value": []},
        },
    }

    values = NeptuneGremlinConverter.convert_results(results["result"]["data"])
    assert len(values) == 1
    value_map = values[0]

    # Check the structure
    assert isinstance(value_map, dict)
    assert "name" in value_map
    assert value_map["name"] == ["Charlie Sheen"]

    # For string representation, we'll use a custom format
    formatted = (
        "{"
        + ", ".join(
            [
                f'{k}: "{v[0]}"' if isinstance(v, list) and len(v) == 1 else f"{k}: {v}"
                for k, v in value_map.items()
            ]
        )
        + "}"
    )
    assert str(formatted) == '{name: "Charlie Sheen"}'


def test_neptune_converter_properties():
    """Test NeptuneGremlinConverter for properties results."""
    results = {
        "requestId": "a892bb1b-8af7-4140-90b2-a1c71d330ea0",
        "status": {
            "message": "",
            "code": 200,
            "attributes": {"@type": "g:Map", "@value": []},
        },
        "result": {
            "data": {
                "@type": "g:List",
                "@value": [
                    {
                        "@type": "g:VertexProperty",
                        "@value": {
                            "id": {"@type": "g:Int32", "@value": 1871508256},
                            "value": "Charlie Sheen",
                            "label": "name",
                        },
                    }
                ],
            },
            "meta": {"@type": "g:Map", "@value": []},
        },
    }

    values = NeptuneGremlinConverter.convert_results(results["result"]["data"])
    assert len(values) == 1
    value_map = values[0]

    # Check the structure
    assert str(value_map) == "Charlie Sheen"


def test_neptune_converter_edges():
    """Test NeptuneGremlinConverter for edges results."""
    results = {
        "requestId": "c3f8b20a-c9a9-446d-a446-ca4f4df7d296",
        "status": {
            "message": "",
            "code": 200,
            "attributes": {"@type": "g:Map", "@value": []},
        },
        "result": {
            "data": {
                "@type": "g:List",
                "@value": [
                    {
                        "@type": "g:Edge",
                        "@value": {
                            "id": "58a08da3-8d66-4198-924b-72fabf7801fa",
                            "label": "DIRECTED",
                            "inVLabel": "Movie",
                            "outVLabel": "Person::Director",
                            "inV": "794246db-6b39-4cbd-900f-9ad722cfa4f8",
                            "outV": "8ec08c33-112a-44b4-a707-1f6b181c2deb",
                        },
                    }
                ],
            },
            "meta": {"@type": "g:Map", "@value": []},
        },
    }

    values = NeptuneGremlinConverter.convert_results(results["result"]["data"])
    assert len(values) == 1
    value_map = values[0]

    # Check the structure
    assert (
        str(value_map)
        == '(:Person:Director {~id: "8ec08c33-112a-44b4-a707-1f6b181c2deb"})->[:DIRECTED]->(:Movie {~id: "794246db-6b39-4cbd-900f-9ad722cfa4f8"})'
    )
