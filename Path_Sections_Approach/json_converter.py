#!/usr/bin/env python3
import json
import argparse
import os
from datetime import datetime

def convert_graph(input_graph):
    """
    Convert a standard graph JSON to separate components:
    - graph.json: connectivity information
    - positions.json: 3D positions of nodes
    - tramo_id_map.json: mapping of node pairs to section IDs
    """
    # Load the input graph
    with open(input_graph, 'r') as f:
        graph_data = json.load(f)
    
    # Create the connectivity graph (adjacency list)
    graph = {}
    positions = {}
    tramo_id_map = {}
    tramo_id = 0  # Counter for section IDs
    
    # Parse the graph format where keys are coordinate strings and values are lists of coordinate lists
    for node_id_str, neighbors_coords in graph_data.items():
        # Extract position from the node ID string (removing parentheses and spaces)
        clean_id = node_id_str.strip('()')
        coords = [float(c.strip()) for c in clean_id.split(',')]
        pos = coords  # [x, y, z]
        
        # Store the position
        positions[node_id_str] = pos
        
        # Extract connections and create adjacency list
        neighbors = []
        for neighbor_coords in neighbors_coords:
            # Convert neighbor coordinates to string format for consistency
            neighbor_id = f"({neighbor_coords[0]}, {neighbor_coords[1]}, {neighbor_coords[2]})"
            neighbors.append(neighbor_id)
            
            # Create a unique section ID for each edge (if not already created)
            edge = tuple(sorted([node_id_str, neighbor_id]))
            edge_key = edge[0] + "-" + edge[1]
            if edge_key not in tramo_id_map:
                tramo_id_map[edge_key] = tramo_id
                tramo_id += 1
        
        graph[node_id_str] = neighbors
    
    return graph, positions, tramo_id_map

def main():
    parser = argparse.ArgumentParser(description="Convert graph JSON to separate components")
    parser.add_argument("--input", type=str, required=True, help="Input graph JSON file")
    parser.add_argument("--output_dir", type=str, default="Path_Restrictions", help="Output directory")
    args = parser.parse_args()
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%m%d_%H%M")
    
    # Ensure output directory exists
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    # Convert the graph
    print(f"Converting graph from {args.input}...")
    graph, positions, tramo_id_map = convert_graph(args.input)
    print(f"Graph conversion complete: {len(graph)} nodes, {len(tramo_id_map)} edges")
    
    # Save the outputs with timestamps
    graph_file = os.path.join(args.output_dir, f"graph_{timestamp}.json")
    positions_file = os.path.join(args.output_dir, f"positions_{timestamp}.json")
    tramo_id_file = os.path.join(args.output_dir, f"tramo_id_map_{timestamp}.json")
    
    with open(graph_file, 'w') as f:
        json.dump(graph, f, indent=2)
    
    with open(positions_file, 'w') as f:
        json.dump(positions, f, indent=2)
    
    with open(tramo_id_file, 'w') as f:
        json.dump(tramo_id_map, f, indent=2)
    
    print(f"Conversion complete.")
    print(f"Graph saved to: {graph_file}")
    print(f"Positions saved to: {positions_file}")
    print(f"Section IDs saved to: {tramo_id_file}")
    
    # Return the filenames for use by other scripts
    return graph_file, positions_file, tramo_id_file

if __name__ == "__main__":
    main()