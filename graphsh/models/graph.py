"""
Graph data models for GraphSh.

This module defines the core data models used to represent graph elements
(nodes, edges, paths, etc.) in a database-agnostic way.
"""

from typing import Any, Dict, List, Optional


class GraphNode:
    """Represents a node in a graph."""

    def __init__(
        self,
        id: str,
        labels: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a graph node.

        Args:
            id: Node identifier
            labels: List of node labels/types
            properties: Dictionary of node properties
        """
        self.id = id
        self.labels = labels or []
        self.properties = properties or {}

    def __str__(self) -> str:
        """Return string representation of the node.

        Returns:
            str: String representation in Cypher-like format
        """
        # Format labels
        labels_str = ":" + ":".join(self.labels) if self.labels else ""

        # Format properties with sorted keys for consistent output
        # Always include the ID first, then other properties
        props_items = [f'~id: "{self.id}"']  # Start with ID

        # Add other properties
        for key in sorted(self.properties.keys()):
            value = self.properties[key]
            if isinstance(value, str):
                # Quote string values
                props_items.append(f'{key}: "{value}"')
            else:
                # Numbers and other types as is
                props_items.append(f"{key}: {value}")

        props_str = "{" + ", ".join(props_items) + "}" if props_items else ""

        # Combine into node representation
        return f"({labels_str} {props_str})".replace("  ", " ")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "id": self.id,
            "labels": self.labels,
            "properties": self.properties,
        }


class GraphEdge:
    """Represents an edge/relationship in a graph."""

    def __init__(
        self,
        id: str,
        source: GraphNode,
        target: GraphNode,
        type: str = "",
        properties: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a graph edge.

        Args:
            id: Edge identifier
            source: Source node (GraphNode instance)
            target: Target node (GraphNode instance)
            type: Edge type/label
            properties: Dictionary of edge properties
        """
        self.id = id
        self.source = source
        self.target = target
        self.type = type
        self.properties = properties or {}

    def __str__(self) -> str:
        """Return string representation of the edge.

        Returns:
            str: String representation in format:
            source_node->[:edge_type (any edge properties)]->target_node
        """
        # Format edge type
        type_str = f":{self.type}" if self.type else ""

        # Format properties with sorted keys for consistent output
        props_items = []
        for key in sorted(self.properties.keys()):
            value = self.properties[key]
            if isinstance(value, str):
                # Quote string values
                props_items.append(f'{key}: "{value}"')
            else:
                # Numbers and other types as is
                props_items.append(f"{key}: {value}")

        props_str = " {" + ", ".join(props_items) + "}" if props_items else ""
        edge_str = f"[{type_str}{props_str}]"

        # Use the string representation of source and target nodes
        source_str = str(self.source)
        target_str = str(self.target)

        # Combine into complete edge representation
        return f"{source_str}->{edge_str}->{target_str}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "id": self.id,
            "source": self.source.to_dict(),
            "target": self.target.to_dict(),
            "type": self.type,
            "properties": self.properties,
        }


class GraphPath:
    """Represents a path in a graph."""

    def __init__(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
    ):
        """Initialize a graph path.

        Args:
            nodes: List of nodes in the path
            edges: List of edges in the path
        """
        self.nodes = nodes
        self.edges = edges

    def __str__(self) -> str:
        """Return string representation of the path.

        Returns:
            str: String representation in Cypher-like format
        """
        if not self.nodes:
            return "(empty path)"

        # Start with the first node
        result = str(self.nodes[0])

        # Add edges with their targets
        for i, edge in enumerate(self.edges):
            # Create a new edge with the correct source and target
            temp_edge = GraphEdge(
                id=edge.id,
                source=self.nodes[i],
                target=self.nodes[i + 1],
                type=edge.type,
                properties=edge.properties,
            )
            # Only add the edge and target node to avoid duplicating source nodes
            edge_str = str(temp_edge)
            # Extract just the edge and target part (remove the source part)
            parts = edge_str.split("->")
            if len(parts) >= 3:
                result += "->" + "->".join(parts[1:])
            else:
                # Fallback in case the splitting doesn't work as expected
                result += "->" + edge_str.split(")", 1)[1]

        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "length": len(self.edges),
        }


class GraphValue:
    """Represents a value in a graph query result."""

    def __init__(self, value: Any):
        """Initialize a graph value.

        Args:
            value: The value to wrap
        """
        self.value = value

    def __str__(self) -> str:
        """Return string representation of the value.

        Returns:
            str: String representation
        """
        if isinstance(self.value, dict):
            # Format dictionary with special handling for lists with single values
            props_items = []
            for key in sorted(self.value.keys()):
                val = self.value[key]
                if isinstance(val, list) and len(val) == 1:
                    # For lists with a single value, display just the value with quotes if it's a string
                    if isinstance(val[0], str):
                        props_items.append(f'{key}: "{val[0]}"')
                    else:
                        props_items.append(f"{key}: {val[0]}")
                elif isinstance(val, str):
                    # Quote string values
                    props_items.append(f'{key}: "{val}"')
                else:
                    # Numbers and other types as is
                    props_items.append(f"{key}: {val}")
            return "{" + ", ".join(props_items) + "}"
        elif isinstance(self.value, str):
            return f'"{self.value}"'
        elif self.value is None:
            return "null"
        else:
            return str(self.value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {"value": self.value}


def format_graph_element(element: Any) -> Any:
    """Format a graph element for display.

    Args:
        element: Element to format

    Returns:
        Any: Formatted element
    """
    if isinstance(element, (GraphNode, GraphEdge, GraphPath, GraphValue)):
        return str(element)
    elif isinstance(element, list):
        return [format_graph_element(item) for item in element]
    elif isinstance(element, dict):
        return {key: format_graph_element(value) for key, value in element.items()}
    else:
        return element


def dict_graph_element(element: Any) -> Any:
    """Format a graph element for dict.

    Args:
        element: Element to format

    Returns:
        Any: Formatted element
    """
    if isinstance(element, (GraphNode, GraphEdge, GraphPath, GraphValue)):
        return element.to_dict()
    elif isinstance(element, list):
        return [dict_graph_element(item) for item in element]
    elif isinstance(element, dict):
        return {key: dict_graph_element(value) for key, value in element.items()}
    else:
        return element
