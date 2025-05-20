"""
Converters for Amazon Neptune data formats.

This module provides converters for Neptune's Gremlin, SPARQL, and Cypher
result formats to GraphSh models.
"""

from typing import Any, Dict, List

from graphsh.db.converters.base import BaseConverter
from graphsh.models.graph import GraphEdge, GraphNode, GraphPath


class NeptuneGremlinConverter(BaseConverter):
    """Converter for Neptune Gremlin data formats."""

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
                        NeptuneGremlinConverter._extract_value(v) for v in inner_value
                    ]
                elif value["@type"] == "g:Map":
                    if isinstance(inner_value, list):
                        # Convert list of key-value pairs to dict
                        result = {}
                        for i in range(0, len(inner_value), 2):
                            if i + 1 < len(inner_value):
                                key = NeptuneGremlinConverter._extract_value(
                                    inner_value[i]
                                )
                                val = NeptuneGremlinConverter._extract_value(
                                    inner_value[i + 1]
                                )
                                result[key] = val
                        return result
                    return {
                        k: NeptuneGremlinConverter._extract_value(v)
                        for k, v in inner_value.items()
                    }
                elif value["@type"] == "g:Vertex":
                    return NeptuneGremlinConverter.to_graph_node(inner_value)
                elif value["@type"] == "g:Edge":
                    return NeptuneGremlinConverter.to_graph_edge(inner_value)
                elif value["@type"] == "g:VertexProperty":
                    if isinstance(inner_value, dict) and "value" in inner_value:
                        return NeptuneGremlinConverter._extract_value(
                            inner_value["value"]
                        )
                    return NeptuneGremlinConverter._extract_value(inner_value)
                elif value["@type"] == "g:Property":
                    if isinstance(inner_value, dict) and "value" in inner_value:
                        return NeptuneGremlinConverter._extract_value(
                            inner_value["value"]
                        )
                    return NeptuneGremlinConverter._extract_value(inner_value)
                else:
                    return NeptuneGremlinConverter._extract_value(inner_value)
            # Handle regular dictionaries
            return {
                k: NeptuneGremlinConverter._extract_value(v) for k, v in value.items()
            }
        elif isinstance(value, list):
            return [NeptuneGremlinConverter._extract_value(v) for v in value]
        else:
            return value

    @staticmethod
    def to_graph_node(vertex_data: Dict[str, Any]) -> GraphNode:
        """Convert Neptune vertex data to GraphNode.

        Args:
            vertex_data: Neptune vertex data

        Returns:
            GraphNode: Converted node
        """
        # Extract ID - handle different formats
        if "id" in vertex_data:
            node_id = NeptuneGremlinConverter._extract_value(vertex_data["id"])
        elif "T.id" in vertex_data:
            node_id = NeptuneGremlinConverter._extract_value(vertex_data["T.id"])
        else:
            node_id = "unknown"

        # Extract labels
        labels = []
        if "label" in vertex_data:
            label = NeptuneGremlinConverter._extract_value(vertex_data["label"])
            # Handle compound labels (e.g., "Person::Actor")
            labels = label.split("::") if label else []
        elif "T.label" in vertex_data:
            label = NeptuneGremlinConverter._extract_value(vertex_data["T.label"])
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
                        properties[prop_name] = NeptuneGremlinConverter._extract_value(
                            prop_values[0]
                        )
                    else:
                        # Multiple values, extract each one
                        properties[prop_name] = [
                            NeptuneGremlinConverter._extract_value(val)
                            for val in prop_values
                        ]
                else:
                    properties[prop_name] = NeptuneGremlinConverter._extract_value(
                        prop_values
                    )

        return GraphNode(id=node_id, labels=labels, properties=properties)

    @staticmethod
    def to_graph_edge(edge_data: Dict[str, Any]) -> GraphEdge:
        """Convert Neptune edge data to GraphEdge.

        Args:
            edge_data: Neptune edge data

        Returns:
            GraphEdge: Converted edge
        """
        # Extract ID
        edge_id = NeptuneGremlinConverter._extract_value(edge_data["id"])

        # Extract source and target IDs and labels
        source_id = "unknown"
        target_id = "unknown"
        source_labels = []
        target_labels = []

        if "outV" in edge_data:
            source_id = NeptuneGremlinConverter._extract_value(edge_data["outV"])
        if "outVLabel" in edge_data:
            label = NeptuneGremlinConverter._extract_value(edge_data["outVLabel"])
            source_labels = label.split("::") if label else []

        if "inV" in edge_data:
            target_id = NeptuneGremlinConverter._extract_value(edge_data["inV"])
        if "inVLabel" in edge_data:
            label = NeptuneGremlinConverter._extract_value(edge_data["inVLabel"])
            target_labels = label.split("::") if label else []

        # Extract edge type/label
        edge_type = ""
        if "label" in edge_data:
            edge_type = NeptuneGremlinConverter._extract_value(edge_data["label"])

        # Extract properties
        properties = {}

        # Handle GraphSON format properties
        if "properties" in edge_data:
            props = edge_data["properties"]
            for prop_name, prop_values in props.items():
                if isinstance(prop_values, list):
                    # Extract the actual value from property value objects
                    if len(prop_values) == 1:
                        properties[prop_name] = NeptuneGremlinConverter._extract_value(
                            prop_values[0]
                        )
                    else:
                        # Multiple values, extract each one
                        properties[prop_name] = [
                            NeptuneGremlinConverter._extract_value(val)
                            for val in prop_values
                        ]
                else:
                    properties[prop_name] = NeptuneGremlinConverter._extract_value(
                        prop_values
                    )

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
        """Convert Neptune path data to GraphPath.

        Args:
            path_data: Neptune path data

        Returns:
            GraphPath: Converted path
        """
        nodes = []
        edges = []

        # Gremlin paths typically have objects and labels
        if "objects" in path_data and "labels" in path_data:
            objects = NeptuneGremlinConverter._extract_value(path_data["objects"])

            # Process objects in the path
            for i, obj in enumerate(objects):
                if isinstance(obj, dict):
                    # Check if it's a vertex or edge
                    if "type" in obj:
                        if obj["type"] == "vertex":
                            nodes.append(NeptuneGremlinConverter.to_graph_node(obj))
                        elif obj["type"] == "edge":
                            edges.append(NeptuneGremlinConverter.to_graph_edge(obj))
                    # Try to infer type from structure
                    elif "outV" in obj or "inV" in obj:
                        edges.append(NeptuneGremlinConverter.to_graph_edge(obj))
                    else:
                        nodes.append(NeptuneGremlinConverter.to_graph_node(obj))

        return GraphPath(nodes=nodes, edges=edges)

    @staticmethod
    def convert_value(value: Any) -> Any:
        """Convert a Neptune Gremlin value to a GraphSh model.

        Args:
            value: Neptune Gremlin value

        Returns:
            Any: Converted value
        """
        # First extract the actual value from GraphSON format
        value = NeptuneGremlinConverter._extract_value(value)
        return value

    @staticmethod
    def convert_result(result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Neptune Gremlin result to GraphSh models.

        Args:
            result: Neptune Gremlin result

        Returns:
            Dict[str, Any]: Converted result
        """
        converted = {}
        for key, value in result.items():
            converted[key] = NeptuneGremlinConverter.convert_value(value)
        return converted

    @staticmethod
    def convert_results(results: Any) -> List[Dict[str, Any]]:
        """Convert Neptune Gremlin results to GraphSh models.

        Args:
            results: Neptune Gremlin results

        Returns:
            List[Dict[str, Any]]: Converted results
        """
        results = NeptuneGremlinConverter._extract_value(results)
        return results


class NeptuneCypherConverter(BaseConverter):
    """Converter for Neptune OpenCypher data formats."""

    @staticmethod
    def _extract_value(value: Any) -> Any:
        """Extract the actual value from Neptune formatted values.

        Args:
            value: Neptune value that might contain nested structures

        Returns:
            Any: The extracted actual value
        """
        if isinstance(value, dict):
            # Handle Neptune format
            if "~entityType" in value and value["~entityType"] == "node":
                return NeptuneCypherConverter.to_graph_node(value)
            elif "~entityType" in value and value["~entityType"] == "relationship":
                return NeptuneCypherConverter.to_graph_edge(value)
            # Handle regular dictionaries
            return {
                k: NeptuneCypherConverter._extract_value(v) for k, v in value.items()
            }
        elif isinstance(value, list):
            return [NeptuneCypherConverter._extract_value(v) for v in value]
        else:
            return value

    @staticmethod
    def to_graph_node(node_data: Dict[str, Any]) -> GraphNode:
        """Convert Neptune node data to GraphNode.

        Args:
            node_data: Neptune node data

        Returns:
            GraphNode: Converted node
        """
        node_id = node_data.get("~id", "")
        labels = node_data.get("~labels", [])
        properties = node_data.get("~properties", {})

        return GraphNode(id=node_id, labels=labels, properties=properties)

    @staticmethod
    def to_graph_edge(edge_data: Dict[str, Any]) -> GraphEdge:
        """Convert Neptune edge data to GraphEdge.

        Args:
            edge_data: Neptune edge data

        Returns:
            GraphEdge: Converted edge
        """
        edge_id = edge_data.get("~id", "")
        source_id = edge_data.get("~start", "")
        target_id = edge_data.get("~end", "")
        edge_type = edge_data.get("~type", "")
        properties = edge_data.get("~properties", {})

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
        """Convert a Neptune OpenCypher value to a GraphSh model.

        Args:
            value: Neptune OpenCypher value

        Returns:
            Any: Converted value
        """
        return NeptuneCypherConverter._extract_value(value)

    @staticmethod
    def convert_result(result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Neptune OpenCypher result to GraphSh models.

        Args:
            result: Neptune OpenCypher result

        Returns:
            Dict[str, Any]: Converted result
        """
        converted = {}
        for key, value in result.items():
            converted[key] = NeptuneCypherConverter.convert_value(value)
        return converted

    @staticmethod
    def convert_results(results: Any) -> List[Any]:
        """Convert Neptune OpenCypher results to GraphSh models.

        Args:
            results: Neptune OpenCypher results

        Returns:
            List[Any]: Converted results
        """
        results = NeptuneCypherConverter._extract_value(results)
        return results


class NeptuneSparqlConverter(BaseConverter):
    """Converter for Neptune SPARQL data formats."""

    @staticmethod
    def normalize_binding(binding: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        """Normalize SPARQL binding to dictionary.

        Args:
            binding: SPARQL binding.

        Returns:
            Dict[str, Any]: Normalized binding.
        """
        result = {}

        for var, value in binding.items():
            if value["type"] == "uri":
                result[var] = value["value"]
            elif value["type"] == "literal":
                # Handle typed literals
                if "datatype" in value:
                    if value["datatype"] == "http://www.w3.org/2001/XMLSchema#integer":
                        result[var] = int(value["value"])
                    elif (
                        value["datatype"] == "http://www.w3.org/2001/XMLSchema#decimal"
                    ):
                        result[var] = float(value["value"])
                    elif (
                        value["datatype"] == "http://www.w3.org/2001/XMLSchema#boolean"
                    ):
                        result[var] = value["value"].lower() == "true"
                    else:
                        result[var] = value["value"]
                else:
                    result[var] = value["value"]
            else:
                result[var] = value["value"]

        return result

    @staticmethod
    def convert_value(value: Any) -> Any:
        """Convert a Neptune SPARQL value to a GraphSh model.

        Args:
            value: Neptune SPARQL value

        Returns:
            Any: Converted value
        """
        # SPARQL values are typically already in a simple format
        return value

    @staticmethod
    def convert_result(result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Neptune SPARQL result to GraphSh models.

        Args:
            result: Neptune SPARQL result

        Returns:
            Dict[str, Any]: Converted result
        """
        return NeptuneSparqlConverter.normalize_binding(result)

    @staticmethod
    def convert_results(
        results: List[Dict[str, Dict[str, str]]],
    ) -> List[Dict[str, Any]]:
        """Convert Neptune SPARQL results to GraphSh models.

        Args:
            results: Neptune SPARQL results

        Returns:
            List[Dict[str, Any]]: Converted results
        """
        return [
            NeptuneSparqlConverter.normalize_binding(binding) for binding in results
        ]
