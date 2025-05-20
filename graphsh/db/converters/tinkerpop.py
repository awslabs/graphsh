"""
Converters for TinkerPop data formats.

This module provides converters for TinkerPop's Gremlin result formats to GraphSh models.
"""

from typing import Any, Dict, List

from graphsh.db.converters.base import BaseConverter
from graphsh.models.graph import GraphEdge, GraphNode, GraphPath


class TinkerpopGremlinConverter(BaseConverter):
    """Converter for TinkerPop Gremlin data formats."""

    @staticmethod
    def _extract_value(value: Any) -> Any:
        """Extract the actual value from GraphSON formatted values.

        Args:
            value: GraphSON value that might contain @type and @value

        Returns:
            Any: The extracted actual value
        """
        if isinstance(value, dict):
            # Handle GraphSON format with @type and @value
            if "@type" in value and "@value" in value:
                inner_value = value["@value"]
                # Handle specific types if needed
                if value["@type"] == "g:Int32" or value["@type"] == "g:Int64":
                    return int(inner_value)
                elif value["@type"] == "g:Float" or value["@type"] == "g:Double":
                    return float(inner_value)
                elif value["@type"] == "g:String":
                    return str(inner_value)
                elif value["@type"] == "g:List":
                    return [
                        TinkerpopGremlinConverter._extract_value(v) for v in inner_value
                    ]
                elif value["@type"] == "g:Map":
                    if isinstance(inner_value, list):
                        # Convert list of key-value pairs to dict
                        result = {}
                        for i in range(0, len(inner_value), 2):
                            if i + 1 < len(inner_value):
                                key = TinkerpopGremlinConverter._extract_value(
                                    inner_value[i]
                                )
                                val = TinkerpopGremlinConverter._extract_value(
                                    inner_value[i + 1]
                                )
                                result[key] = val
                        return result
                    return {
                        k: TinkerpopGremlinConverter._extract_value(v)
                        for k, v in inner_value.items()
                    }
                elif value["@type"] == "g:Vertex":
                    return TinkerpopGremlinConverter.to_graph_node(inner_value)
                elif value["@type"] == "g:Edge":
                    return TinkerpopGremlinConverter.to_graph_edge(inner_value)
                elif value["@type"] == "g:VertexProperty":
                    if isinstance(inner_value, dict) and "value" in inner_value:
                        return TinkerpopGremlinConverter._extract_value(
                            inner_value["value"]
                        )
                    return TinkerpopGremlinConverter._extract_value(inner_value)
                else:
                    return TinkerpopGremlinConverter._extract_value(inner_value)
            # Handle regular dictionaries
            return {
                k: TinkerpopGremlinConverter._extract_value(v) for k, v in value.items()
            }
        elif isinstance(value, list):
            return [TinkerpopGremlinConverter._extract_value(v) for v in value]
        else:
            return value

    @staticmethod
    def to_graph_node(vertex_data: Dict[str, Any]) -> GraphNode:
        """Convert TinkerPop vertex data to GraphNode.

        Args:
            vertex_data: TinkerPop vertex data

        Returns:
            GraphNode: Converted node
        """
        # Extract ID - handle different formats
        if "id" in vertex_data:
            node_id = TinkerpopGremlinConverter._extract_value(vertex_data["id"])
        elif "T.id" in vertex_data:
            node_id = TinkerpopGremlinConverter._extract_value(vertex_data["T.id"])
        else:
            node_id = "unknown"

        # Extract labels
        labels = []
        if "label" in vertex_data:
            label = TinkerpopGremlinConverter._extract_value(vertex_data["label"])
            # Handle compound labels (e.g., "Person::Actor")
            labels = label.split("::") if label else []
        elif "T.label" in vertex_data:
            label = TinkerpopGremlinConverter._extract_value(vertex_data["T.label"])
            labels = label.split("::") if label else []

        # Extract properties
        properties = {}

        # Handle GraphSON format properties
        if "properties" in vertex_data:
            props = vertex_data["properties"]
            for prop_name, prop_values in props.items():
                if isinstance(prop_values, list):
                    # Extract the actual value from property value objects
                    if len(prop_values) == 1:
                        properties[prop_name] = (
                            TinkerpopGremlinConverter._extract_value(prop_values[0])
                        )
                    else:
                        # Multiple values, extract each one
                        properties[prop_name] = [
                            TinkerpopGremlinConverter._extract_value(val)
                            for val in prop_values
                        ]
                else:
                    properties[prop_name] = TinkerpopGremlinConverter._extract_value(
                        prop_values
                    )
        else:
            # Handle regular properties
            for key, value in vertex_data.items():
                # Skip special keys
                if key in ["id", "T.id", "label", "T.label", "type", "properties"]:
                    continue

                # Handle property value lists (common in Gremlin)
                if isinstance(value, list) and len(value) == 1:
                    properties[key] = TinkerpopGremlinConverter._extract_value(value[0])
                else:
                    properties[key] = TinkerpopGremlinConverter._extract_value(value)

        return GraphNode(id=node_id, labels=labels, properties=properties)

    @staticmethod
    def to_graph_edge(edge_data: Dict[str, Any]) -> GraphEdge:
        """Convert TinkerPop edge data to GraphEdge.

        Args:
            edge_data: TinkerPop edge data

        Returns:
            GraphEdge: Converted edge
        """
        # Extract ID
        if "id" in edge_data:
            edge_id = TinkerpopGremlinConverter._extract_value(edge_data["id"])
        elif "T.id" in edge_data:
            edge_id = TinkerpopGremlinConverter._extract_value(edge_data["T.id"])
        else:
            edge_id = "unknown"

        # Extract source and target IDs and labels
        source_id = "unknown"
        target_id = "unknown"
        source_labels = []
        target_labels = []

        if "outV" in edge_data:
            source_id = TinkerpopGremlinConverter._extract_value(edge_data["outV"])
        if "outVLabel" in edge_data:
            label = TinkerpopGremlinConverter._extract_value(edge_data["outVLabel"])
            source_labels = label.split("::") if label else []

        if "inV" in edge_data:
            target_id = TinkerpopGremlinConverter._extract_value(edge_data["inV"])
        if "inVLabel" in edge_data:
            label = TinkerpopGremlinConverter._extract_value(edge_data["inVLabel"])
            target_labels = label.split("::") if label else []

        # Extract edge type/label
        edge_type = ""
        if "label" in edge_data:
            edge_type = TinkerpopGremlinConverter._extract_value(edge_data["label"])
        elif "T.label" in edge_data:
            edge_type = TinkerpopGremlinConverter._extract_value(edge_data["T.label"])

        # Extract properties
        properties = {}

        # Handle GraphSON format properties
        if "properties" in edge_data:
            props = edge_data["properties"]
            for prop_name, prop_value in props.items():
                properties[prop_name] = TinkerpopGremlinConverter._extract_value(
                    prop_value
                )
        else:
            # Handle regular properties
            for key, value in edge_data.items():
                # Skip special keys
                if key in [
                    "id",
                    "T.id",
                    "label",
                    "T.label",
                    "outV",
                    "inV",
                    "outVLabel",
                    "inVLabel",
                    "type",
                    "properties",
                ]:
                    continue

                # Handle property value lists (common in Gremlin)
                if isinstance(value, list) and len(value) == 1:
                    properties[key] = TinkerpopGremlinConverter._extract_value(value[0])
                else:
                    properties[key] = TinkerpopGremlinConverter._extract_value(value)

        # Create source and target nodes with their labels
        source_node = GraphNode(id=source_id, labels=source_labels, properties={})
        target_node = GraphNode(id=target_id, labels=target_labels, properties={})

        return GraphEdge(
            id=edge_id,
            source=source_node,
            target=target_node,
            type=edge_type,
            properties=properties,
        )

    @staticmethod
    def to_graph_path(path_data: Dict[str, Any]) -> GraphPath:
        """Convert TinkerPop path data to GraphPath.

        Args:
            path_data: TinkerPop path data

        Returns:
            GraphPath: Converted path
        """
        nodes = []
        edges = []

        # Gremlin paths typically have objects and labels
        if "objects" in path_data and "labels" in path_data:
            objects = TinkerpopGremlinConverter._extract_value(path_data["objects"])

            # Process objects in the path
            for i, obj in enumerate(objects):
                if isinstance(obj, dict):
                    # Check if it's a vertex or edge
                    if "type" in obj:
                        if obj["type"] == "vertex":
                            nodes.append(TinkerpopGremlinConverter.to_graph_node(obj))
                        elif obj["type"] == "edge":
                            edges.append(TinkerpopGremlinConverter.to_graph_edge(obj))
                    # Try to infer type from structure
                    elif "outV" in obj or "inV" in obj:
                        edges.append(TinkerpopGremlinConverter.to_graph_edge(obj))
                    else:
                        nodes.append(TinkerpopGremlinConverter.to_graph_node(obj))

        return GraphPath(nodes=nodes, edges=edges)

    @staticmethod
    def convert_value(value: Any) -> Any:
        """Convert a TinkerPop value to a GraphSh model.

        Args:
            value: TinkerPop value

        Returns:
            Any: Converted value
        """
        # First extract the actual value from GraphSON format
        value = TinkerpopGremlinConverter._extract_value(value)

        # Handle dictionaries (vertices, edges, paths)
        if isinstance(value, dict):
            # Check if it's a vertex
            if "type" in value and value["type"] == "vertex":
                return TinkerpopGremlinConverter.to_graph_node(value)
            # Check if it's an edge
            elif "type" in value and value["type"] == "edge":
                return TinkerpopGremlinConverter.to_graph_edge(value)
            # Check if it's a path
            elif "objects" in value and "labels" in value:
                return TinkerpopGremlinConverter.to_graph_path(value)
            # Try to infer type from structure
            elif "outV" in value or "inV" in value:
                return TinkerpopGremlinConverter.to_graph_edge(value)
            elif "properties" in value and ("label" in value or "T.label" in value):
                return TinkerpopGremlinConverter.to_graph_node(value)
            # Process nested dictionaries
            else:
                return {
                    k: TinkerpopGremlinConverter.convert_value(v)
                    for k, v in value.items()
                }

        # Handle lists
        elif isinstance(value, list):
            return [TinkerpopGremlinConverter.convert_value(item) for item in value]

        # Handle primitive values
        else:
            return value

    @staticmethod
    def convert_result(result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a TinkerPop result to GraphSh models.

        Args:
            result: TinkerPop result

        Returns:
            Dict[str, Any]: Converted result
        """
        converted = {}
        for key, value in result.items():
            converted[key] = TinkerpopGremlinConverter.convert_value(value)
        return converted

    @staticmethod
    def convert_results(results: Any) -> List[Dict[str, Any]]:
        """Convert TinkerPop results to GraphSh models.

        Args:
            results: TinkerPop results

        Returns:
            List[Dict[str, Any]]: Converted results
        """
        # Handle non-list inputs by wrapping them
        if not isinstance(results, list):
            # If it's a dictionary, wrap it in a list
            if isinstance(results, dict):
                return TinkerpopGremlinConverter.convert_value(results)
            # For other types, wrap the value
            return [{"result": TinkerpopGremlinConverter.convert_value(results)}]

        # Handle empty list
        if not results:
            return []

        # Handle case where results might be a list of vertices or edges directly
        if not isinstance(results[0], dict):
            converted_results = []
            for item in results:
                converted_results.append(
                    {"result": TinkerpopGremlinConverter.convert_value(item)}
                )
            return converted_results

        # Handle case where results is a list of dictionaries
        return [TinkerpopGremlinConverter.convert_result(result) for result in results]
