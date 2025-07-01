#!/usr/bin/env python3
"""
Create a modified graph with forbidden edges removed for export purposes.
"""

import json
import sys

def remove_forbidden_edges(graph_file, tramo_map_file, forbidden_file, output_file):
    """Remove forbidden edges from the graph."""
    
    # Load files
    with open(graph_file, 'r') as f:
        graph = json.load(f)
    
    with open(tramo_map_file, 'r') as f:
        tramo_map = json.load(f)
    
    with open(forbidden_file, 'r') as f:
        forbidden_ids = json.load(f)
    
    print(f"📊 Original graph: {len(graph)} nodes")
    print(f"🚫 Forbidden tramo IDs: {forbidden_ids}")
    
    # Create reverse mapping: tramo_id -> edge_key
    id_to_edge = {}
    for edge_key, tramo_id in tramo_map.items():
        id_to_edge[tramo_id] = edge_key
    
    # Find forbidden edges
    forbidden_edges = []
    for tramo_id in forbidden_ids:
        if tramo_id in id_to_edge:
            forbidden_edges.append(id_to_edge[tramo_id])
    
    print(f"🚫 Forbidden edges: {len(forbidden_edges)}")
    for edge in forbidden_edges:
        print(f"   {edge}")
    
    # Remove forbidden edges from graph
    removed_count = 0
    for edge_key in forbidden_edges:
        # Parse edge key: "(x1,y1,z1)-(x2,y2,z2)"
        parts = edge_key.split('-')
        if len(parts) == 2:
            node1_str = parts[0]
            node2_str = parts[1]
            
            # Parse coordinates from string format
            def parse_coord(coord_str):
                # Remove parentheses and split by comma
                coord_str = coord_str.strip('()')
                coords = [float(x.strip()) for x in coord_str.split(',')]
                return coords
            
            node1_coords = parse_coord(node1_str)
            node2_coords = parse_coord(node2_str)
            
            # Remove edge in both directions
            if node1_str in graph:
                # Find and remove node2_coords from node1's adjacency list
                graph[node1_str] = [adj for adj in graph[node1_str] if adj != node2_coords]
                removed_count += 1
                print(f"   Removed: {node1_str} -> {node2_coords}")
            
            if node2_str in graph:
                # Find and remove node1_coords from node2's adjacency list
                graph[node2_str] = [adj for adj in graph[node2_str] if adj != node1_coords]
                removed_count += 1
                print(f"   Removed: {node2_str} -> {node1_coords}")
    
    print(f"🔧 Removed {removed_count} edge connections")
    
    # Save modified graph
    with open(output_file, 'w') as f:
        json.dump(graph, f, indent=2)
    
    print(f"✅ Modified graph saved: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python3 create_forbidden_graph.py graph.json tramo_map.json forbidden.json output.json")
        sys.exit(1)
    
    remove_forbidden_edges(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
