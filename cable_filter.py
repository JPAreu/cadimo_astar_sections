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
    
    # Enhanced error messages with system information
    endpoint_systems = {src_sys, dst_sys}
    
    # Check if source is in forbidden system
    if src_sys not in allowed_systems:
        compatible_cables = [cable for cable, systems in ALLOWED.items() if src_sys in systems]
        raise ValueError(f"Source node in forbidden system '{src_sys}' (allowed: {sorted(allowed_systems)}): {src}\n"
                        f"💡 Source system '{src_sys}' is compatible with cable types: {compatible_cables}")
    
    # Check if destination is in forbidden system  
    if dst_sys not in allowed_systems:
        compatible_cables = [cable for cable, systems in ALLOWED.items() if dst_sys in systems]
        raise ValueError(f"Destination node in forbidden system '{dst_sys}' (allowed: {sorted(allowed_systems)}): {dst}\n"
                        f"💡 Destination system '{dst_sys}' is compatible with cable types: {compatible_cables}")
    
    # Check if endpoints are in different systems and suggest cable C if needed
    if src_sys != dst_sys:
        cross_system_cables = [cable for cable, systems in ALLOWED.items() if endpoint_systems.issubset(systems)]
        if not cross_system_cables:
            raise ValueError(f"Endpoints in different systems - Source: '{src_sys}', Destination: '{dst_sys}'\n"
                           f"❌ No cable type can connect these systems. Available systems per cable:\n"
                           f"   Cable A: {sorted(ALLOWED['A'])}\n"
                           f"   Cable B: {sorted(ALLOWED['B'])}\n" 
                           f"   Cable C: {sorted(ALLOWED['C'])}")
        elif len(allowed_systems) == 1 and not endpoint_systems.issubset(allowed_systems):
            raise ValueError(f"Endpoints in different systems - Source: '{src_sys}', Destination: '{dst_sys}'\n"
                           f"❌ Current cable only allows system(s): {sorted(allowed_systems)}\n"
                           f"💡 Use cable type(s) {cross_system_cables} to connect these systems")

# ------------------------------------------------------------------------
def check_endpoints_across_graphs(src_coord: Tuple[float, float, float], dst_coord: Tuple[float, float, float], 
                                 graph_files: List[str]) -> Dict[str, Any]:
    """
    Check which systems the endpoints belong to across multiple graph files.
    
    Args:
        src_coord: Source coordinates
        dst_coord: Destination coordinates
        graph_files: List of graph file paths to check
        
    Returns:
        Dictionary with endpoint system information
    """
    src_key = coord_to_key(src_coord)
    dst_key = coord_to_key(dst_coord)
    
    endpoint_info = {
        "source": {"coord": src_coord, "key": src_key, "found_in": []},
        "destination": {"coord": dst_coord, "key": dst_key, "found_in": []},
        "compatible_cables": []
    }
    
    # Check each graph file
    for graph_file in graph_files:
        try:
            graph_data = load_tagged_graph(graph_file)
            
            # Check source
            if src_key in graph_data["nodes"]:
                src_sys = graph_data["nodes"][src_key].get("sys")
                endpoint_info["source"]["found_in"].append({"file": graph_file, "system": src_sys})
            
            # Check destination
            if dst_key in graph_data["nodes"]:
                dst_sys = graph_data["nodes"][dst_key].get("sys")
                endpoint_info["destination"]["found_in"].append({"file": graph_file, "system": dst_sys})
                
        except (FileNotFoundError, ValueError):
            continue  # Skip invalid/missing files
    
    # Determine compatible cables
    src_systems = {info["system"] for info in endpoint_info["source"]["found_in"]}
    dst_systems = {info["system"] for info in endpoint_info["destination"]["found_in"]}
    all_systems = src_systems.union(dst_systems)
    
    for cable, allowed_sys in ALLOWED.items():
        if all_systems.issubset(allowed_sys):
            endpoint_info["compatible_cables"].append(cable)
    
    return endpoint_info

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
        Canonical string representation "(x, y, z)" with 3 decimal places
    """
    return f"({coord[0]:.3f}, {coord[1]:.3f}, {coord[2]:.3f})"

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