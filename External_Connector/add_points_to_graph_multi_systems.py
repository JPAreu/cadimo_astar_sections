#!/usr/bin/env python3
"""
Enhanced Graph Extension with System Awareness

This script extends add_points_to_graph_multi.py to support system-aware graph extension.
It respects system constraints when adding external points to the graph.

Usage:
    python3 add_points_to_graph_multi_systems.py input_graph.json output_graph.json 
    --points-json connection.json --external-point X Y Z [--system A|B|C]
"""

import json
import argparse
from typing import Dict, List, Tuple, Set

Point3D = Tuple[float, float, float]

def coord_to_key(coord: Point3D) -> str:
    """Convert coordinate tuple to string key with canonical formatting."""
    return f"({coord[0]:.3f}, {coord[1]:.3f}, {coord[2]:.3f})"

def key_to_coord(key: str) -> Point3D:
    """Convert string key to coordinate tuple."""
    clean_str = key.strip("()")
    parts = [float(c.strip()) for c in clean_str.split(",")]
    return tuple(parts)

def load_graph(filepath: str) -> Dict:
    """Load graph from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def save_graph(graph: Dict, filepath: str):
    """Save graph to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(graph, f, indent=2)

def determine_system_for_external_point(
    connection_data: Dict, 
    system_filter: str,
    external_point: Point3D
) -> str:
    """Determine appropriate system for external point based on connection data and filter."""
    
    # If system filter is specific (A or B), use that
    if system_filter in ["A", "B"]:
        return system_filter
    
    # For system C (all systems), determine based on connection
    # Look at the projection point and connected edges to infer system
    best_edge = connection_data.get("best_edge")
    if not best_edge:
        return "A"  # Default fallback
    
    # For now, default to A for system C
    # In a more sophisticated implementation, we could analyze the edge
    # to determine which system it belongs to
    return "A"

def add_external_points_to_graph(
    input_graph: Dict,
    connection_data: Dict,
    external_point: Point3D,
    system_filter: str = "C"
) -> Dict:
    """Add external points to graph with system awareness."""
    
    # Create a copy of the input graph
    extended_graph = {
        "nodes": input_graph.get("nodes", {}).copy(),
        "edges": input_graph.get("edges", []).copy()
    }
    
    # Determine system for external nodes
    external_system = determine_system_for_external_point(
        connection_data, system_filter, external_point
    )
    
    print(f"[GraphExtender] Assigning system '{external_system}' to external nodes")
    
    # Extract connection information
    best_edge = connection_data["best_edge"]
    projection = tuple(connection_data["projection"])
    manhattan_path = connection_data["best_manhattan_path"]
    
    # Create coordinate keys
    pe_key = coord_to_key(external_point)
    pc_key = coord_to_key(projection)
    
    # Add PE (External Point) node
    extended_graph["nodes"][pe_key] = {
        "sys": external_system,
        "cable": ["A", "B", "C"],  # External points support all cables
        "type": "external"
    }
    
    # Add PC (Projection/Connection Point) node if not already present
    if pc_key not in extended_graph["nodes"]:
        extended_graph["nodes"][pc_key] = {
            "sys": external_system,
            "cable": ["A", "B", "C"],  # Connection points support all cables
            "type": "connection"
        }
    
    # Add intermediate points from Manhattan path
    manhattan_points = manhattan_path["points"]
    intermediate_keys = []
    
    for i, point in enumerate(manhattan_points):
        point_key = coord_to_key(tuple(point))
        
        if point_key not in extended_graph["nodes"]:
            extended_graph["nodes"][point_key] = {
                "sys": external_system,
                "cable": ["A", "B", "C"],
                "type": "intermediate" if i not in [0, len(manhattan_points)-1] else "endpoint"
            }
        
        intermediate_keys.append(point_key)
    
    # Add edges for Manhattan path
    for i in range(len(intermediate_keys) - 1):
        from_key = intermediate_keys[i]
        to_key = intermediate_keys[i + 1]
        
        # Add edge in both directions
        extended_graph["edges"].append({
            "from": from_key,
            "to": to_key,
            "sys": external_system,
            "cable": ["A", "B", "C"],
            "type": "manhattan"
        })
        
        extended_graph["edges"].append({
            "from": to_key,
            "to": from_key,
            "sys": external_system,
            "cable": ["A", "B", "C"],
            "type": "manhattan"
        })
    
    # Connect projection point to original graph edges
    edge_a_key = coord_to_key(tuple(best_edge[0]))
    edge_b_key = coord_to_key(tuple(best_edge[1]))
    
    # Find the original edge system by looking at existing edges
    original_edge_system = external_system  # Default
    for edge in input_graph.get("edges", []):
        if ((edge["from"] == edge_a_key and edge["to"] == edge_b_key) or
            (edge["from"] == edge_b_key and edge["to"] == edge_a_key)):
            original_edge_system = edge.get("sys", external_system)
            break
    
    # Add connections from PC to the original edge endpoints
    for endpoint_key in [edge_a_key, edge_b_key]:
        if endpoint_key in extended_graph["nodes"]:
            # Add bidirectional edges
            extended_graph["edges"].append({
                "from": pc_key,
                "to": endpoint_key,
                "sys": original_edge_system,
                "cable": ["A", "B", "C"],
                "type": "connection"
            })
            
            extended_graph["edges"].append({
                "from": endpoint_key,
                "to": pc_key,
                "sys": original_edge_system,
                "cable": ["A", "B", "C"],
                "type": "connection"
            })
    
    return extended_graph

def main():
    parser = argparse.ArgumentParser(
        description="Add external points to graph with system awareness"
    )
    parser.add_argument("input_graph", help="Input graph JSON file")
    parser.add_argument("output_graph", help="Output graph JSON file")
    parser.add_argument("--points-json", required=True, help="Connection data JSON file")
    parser.add_argument("--external-point", nargs=3, type=float, required=True,
                        metavar=("X", "Y", "Z"), help="External point coordinates")
    parser.add_argument("--system", choices=["A", "B", "C"], default="C",
                        help="System constraint (A, B, or C for all)")
    
    args = parser.parse_args()
    
    # Load input data
    print(f"�� System Filter: {args.system}")
    print(f"📂 Loading graph: {args.input_graph}")
    print(f"📂 Loading connection data: {args.points_json}")
    
    input_graph = load_graph(args.input_graph)
    connection_data = load_graph(args.points_json)
    external_point = tuple(args.external_point)
    
    print(f"📍 External point: {external_point}")
    
    # Extend the graph
    extended_graph = add_external_points_to_graph(
        input_graph, connection_data, external_point, args.system
    )
    
    # Save result
    save_graph(extended_graph, args.output_graph)
    
    # Report results
    original_nodes = len(input_graph.get("nodes", input_graph))
    extended_nodes = len(extended_graph["nodes"])
    original_edges = len(input_graph.get("edges", []))
    extended_edges = len(extended_graph["edges"])
    
    print(f"\n✅ Graph extension completed:")
    print(f"   Nodes: {original_nodes} → {extended_nodes} (+{extended_nodes - original_nodes})")
    print(f"   Edges: {original_edges} → {extended_edges} (+{extended_edges - original_edges})")
    print(f"   Output saved: {args.output_graph}")

if __name__ == "__main__":
    main()
