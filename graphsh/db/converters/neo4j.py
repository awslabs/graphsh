"""
Converters for Neo4j data formats.

This module provides converters for Neo4j's Cypher result formats to GraphSh models.
"""

from typing import Any, Dict, List

from graphsh.db.converters.base import BaseConverter
from graphsh.models.graph import GraphEdge, GraphNode


class Neo4jCypherConverter(BaseConverter):
    """Converter for Neo4j Cypher data formats."""

    @staticmethod
    def to_graph_node(node_data: Any) -> GraphNode:
        """Convert Neo4j node data to GraphNode.

        Args:
            node_data: Neo4j node data

        Returns:
            GraphNode: Converted node
        """
        # Handle Neo4j Node objects
        if (
            hasattr(node_data, "id")
            and hasattr(node_data, "labels")
            and hasattr(node_data, "properties")
        ):
            node_id = str(node_data.id)
            labels = node_data.labels
            properties = dict(node_data.properties)
        # Handle dictionary representation
        else:
            # Check for different key formats
            if "id" in node_data:
                node_id = str(node_data["id"])
            elif "identity" in node_data:
                node_id = str(node_data["identity"])
            else:
                node_id = ""
            labels = node_data.get("labels", [])
            properties = node_data.get("properties", {})

        return GraphNode(id=node_id, labels=labels, properties=properties)

    @staticmethod
    def to_graph_edge(edge_data: Any) -> GraphEdge:
        """Convert Neo4j edge data to GraphEdge.

        Args:
            edge_data: Neo4j edge data

        Returns:
            GraphEdge: Converted edge
        """
        # Handle Neo4j Relationship objects
        if (
            hasattr(edge_data, "id")
            and hasattr(edge_data, "type")
            and hasattr(edge_data, "properties")
        ):
            edge_id = str(edge_data.id)
            edge_type = edge_data.type
            properties = dict(edge_data.properties)

            # Extract source and target nodes
            source_node = None
            target_node = None

            if hasattr(edge_data, "start_node"):
                source_node = Neo4jCypherConverter.to_graph_node(edge_data.start_node)
            if hasattr(edge_data, "end_node"):
                target_node = Neo4jCypherConverter.to_graph_node(edge_data.end_node)

            if not source_node:
                source_node = GraphNode(id="", labels=[], properties={})
            if not target_node:
                target_node = GraphNode(id="", labels=[], properties={})

        # Handle dictionary representation
        else:
            # Check for different key formats
            if "id" in edge_data:
                edge_id = str(edge_data["id"])
            elif "identity" in edge_data:
                edge_id = str(edge_data["identity"])
            else:
                edge_id = ""

            source_id = str(edge_data.get("start", ""))
            target_id = str(edge_data.get("end", ""))
            edge_type = edge_data.get("type", "")
            properties = edge_data.get("properties", {})

            # Create source and target nodes
            source_node = GraphNode(id=source_id, labels=[], properties={})
            target_node = GraphNode(id=target_id, labels=[], properties={})

        return GraphEdge(
            id=edge_id,
            source=source_node,
            target=target_node,
            type=edge_type,
            properties=properties,
        )

    @staticmethod
    def convert_value(value: Any) -> Any:
        """Convert a Neo4j value to a GraphSh model.

        Args:
            value: Neo4j value

        Returns:
            Any: Converted value
        """
        if isinstance(value, dict):
            if "identity" in value and "labels" in value:
                return Neo4jCypherConverter.to_graph_node(value)
            elif "identity" in value and "start" in value and "end" in value:
                return Neo4jCypherConverter.to_graph_edge(value)
            else:
                return {
                    k: Neo4jCypherConverter.convert_value(v) for k, v in value.items()
                }
        elif isinstance(value, list):
            return [Neo4jCypherConverter.convert_value(item) for item in value]
        else:
            return value

    @staticmethod
    def convert_result(result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Neo4j result to GraphSh models.

        Args:
            result: Neo4j result

        Returns:
            Dict[str, Any]: Converted result
        """
        converted = {}
        for key, value in result.items():
            converted[key] = Neo4jCypherConverter.convert_value(value)
        return converted

    @staticmethod
    def convert_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert Neo4j results to GraphSh models.

        Args:
            results: Neo4j results

        Returns:
            List[Dict[str, Any]]: Converted results
        """
        return [Neo4jCypherConverter.convert_result(result) for result in results]
