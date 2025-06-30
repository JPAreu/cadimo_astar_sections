# cable_filter.py
"""
Utility helpers that make the existing astar_PPO_forbid.py cable-aware.
Drop this file in the same folder and import where needed.
"""

import json
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Any

# ------------------------------------------------------------------------
# 1. Cable → permitted system(s) rule-set
ALLOWED = {
    "A": {"A"},      # cable type A may roam only in system A
    "B": {"B"},      # cable type B may roam only in system B
    "C": {"A", "B"}  # cable type C may roam anywhere
}

# ------------------------------------------------------------------------
def load_tagged_graph(path: str) -> Dict[str, Any]:
    """
    Load the tagged graph JSON with explicit 'sys' tags.
    
    Expected format:
    {
      "nodes": {"(x,y,z)": {"sys": "A"}, ...},
      "edges": [{"from": "(...)", "to": "(...)", "sys": "A"}, ...]
    }
    
    Args:
        path: Path to the tagged graph JSON file
        
    Returns:
        Dictionary containing nodes and edges with system tags
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            graph_data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Graph file not found: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in graph file: {e}")
    
    # Validate required structure
    if "nodes" not in graph_data or "edges" not in graph_data:
        raise ValueError("Graph file must contain 'nodes' and 'edges' keys")
    
    return graph_data

# ------------------------------------------------------------------------
def build_adj(graph_json: Dict[str, Any], allowed_systems: Set[str]) -> Dict[str, List[str]]:
    """
    Return a filtered adjacency dict containing ONLY edges whose
    'sys' label is in `allowed_systems`.
    
    Args:
        graph_json: The loaded graph data with nodes and edges
        allowed_systems: Set of allowed system identifiers
        
    Returns:
        Adjacency dictionary with only allowed edges
    """
    adj = defaultdict(list)
    
    for edge in graph_json["edges"]:
        if "sys" not in edge:
            raise ValueError(f"Edge missing 'sys' tag: {edge}")
        
        if edge["sys"] in allowed_systems:
            u, v = edge["from"], edge["to"]
            # Add both directions for undirected graph
            if v not in adj[u]:  # Avoid duplicates
                adj[u].append(v)
            if u not in adj[v]:  # Avoid duplicates
                adj[v].append(u)
    
    return dict(adj)

# ------------------------------------------------------------------------
def validate_endpoints(graph_json: Dict[str, Any], src: str, dst: str, allowed_systems: Set[str]) -> None:
    """
    Validate that both source and destination nodes are in allowed systems.
    
    Args:
        graph_json: The loaded graph data
        src: Source node coordinate string
        dst: Destination node coordinate string  
        allowed_systems: Set of allowed system identifiers
        
    Raises:
        ValueError: If either endpoint is in a forbidden system
        KeyError: If either endpoint doesn't exist in the graph
    """
    # Check if nodes exist in graph
    if src not in graph_json["nodes"]:
        raise KeyError(f"Source node not found in graph: {src}")
    if dst not in graph_json["nodes"]:
        raise KeyError(f"Destination node not found in graph: {dst}")
    
    # Check system tags
    src_sys = graph_json["nodes"][src].get("sys")
    dst_sys = graph_json["nodes"][dst].get("sys")
    
    if src_sys is None:
        raise ValueError(f"Source node missing 'sys' tag: {src}")
    if dst_sys is None:
        raise ValueError(f"Destination node missing 'sys' tag: {dst}")
    
    if src_sys not in allowed_systems:
        raise ValueError(f"Source node in forbidden system '{src_sys}': {src}")
    if dst_sys not in allowed_systems:
        raise ValueError(f"Destination node in forbidden system '{dst_sys}': {dst}")

# ------------------------------------------------------------------------
def get_cable_info(cable_type: str) -> Dict[str, Any]:
    """
    Get information about a cable type.
    
    Args:
        cable_type: Cable type identifier ("A", "B", or "C")
        
    Returns:
        Dictionary with cable information
    """
    if cable_type not in ALLOWED:
        raise ValueError(f"Unknown cable type: {cable_type}. Allowed: {list(ALLOWED.keys())}")
    
    return {
        "cable_type": cable_type,
        "allowed_systems": ALLOWED[cable_type],
        "description": f"Cable {cable_type} - Systems: {', '.join(sorted(ALLOWED[cable_type]))}"
    }

# ------------------------------------------------------------------------
def coord_to_key(coord: Tuple[float, float, float]) -> str:
    """
    Convert coordinate tuple to canonical string key.
    
    Args:
        coord: Coordinate tuple (x, y, z)
        
    Returns:
        Canonical string representation "(x, y, z)"
    """
    return f"({coord[0]}, {coord[1]}, {coord[2]})"

# ------------------------------------------------------------------------
def key_to_coord(key: str) -> Tuple[float, float, float]:
    """
    Convert canonical string key to coordinate tuple.
    
    Args:
        key: Canonical string representation "(x, y, z)"
        
    Returns:
        Coordinate tuple (x, y, z)
    """
    try:
        # Remove parentheses and split by comma
        clean_key = key.strip().strip('()')
        parts = [float(x.strip()) for x in clean_key.split(',')]
        
        if len(parts) != 3:
            raise ValueError(f"Expected 3 coordinates, got {len(parts)}")
        
        return tuple(parts)
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid coordinate key format '{key}': {e}") 