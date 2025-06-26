#!/usr/bin/env python3
import json
import argparse
import os
import math
import re
from datetime import datetime

def parse_point(point_str):
    """Parse a point string in format '(x,y,z)' to a tuple of floats"""
    # Remove parentheses and split by commas
    coords = point_str.strip('()').split(',')
    return (float(coords[0]), float(coords[1]), float(coords[2]))

def distance_3d(p1, p2):
    """Calculate Euclidean distance between two 3D points"""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))

def parse_node_str(node_str):
    """Parse a node string like '(x, y, z)' to a tuple of floats"""
    # Use regex to extract numbers
    matches = re.findall(r'[\d.]+', node_str)
    if len(matches) >= 3:
        return (float(matches[0]), float(matches[1]), float(matches[2]))
    return None

def find_nearest_node(point, nodes_list):
    """Find the nearest node in the graph to the given point"""
    min_distance = float('inf')
    nearest_node = None
    
    for node_str in nodes_list:
        node_coords = parse_node_str(node_str)
        if node_coords:
            dist = distance_3d(point, node_coords)
            if dist < min_distance:
                min_distance = dist
                nearest_node = node_str
    
    return nearest_node, min_distance

def create_section_between_points(p1, p2, graph, positions, tramo_id_map, section_type="mandatory", strict=False):
    """Find a section between two points and return its ID and info"""
    # Find nearest nodes to p1 and p2
    node1, dist1 = find_nearest_node(p1, positions if not isinstance(next(iter(positions), None), str) else graph)
    node2, dist2 = find_nearest_node(p2, positions if not isinstance(next(iter(positions), None), str) else graph)
    
    print(f"Nearest node to {p1}: {node1} (distance: {dist1:.3f})")
    print(f"Nearest node to {p2}: {node2} (distance: {dist2:.3f})")
    
    # Check if both points exist exactly in the graph
    if dist1 > 0.001 or dist2 > 0.001:
        print("\n⚠️ WARNING: One or both points are not exact nodes in the graph ⚠️")
        print(f"The script should only be used with points that exist exactly in the graph.")
        print(f"Please check your input points and ensure they are valid graph nodes.")
        
        if strict:
            print("Exiting due to strict mode.")
            return None
        else:
            print("Proceeding anyway, but results may not be as expected.")
    
    # Check if nodes are directly connected
    if node2 in graph.get(node1, []) or node1 in graph.get(node2, []):
        # Create the edge key (always sorted for consistency)
        try:
            # If nodes are string coordinates, convert to actual node IDs for tramo_id_map lookup
            if isinstance(node1, str) and ',' in node1 and isinstance(node2, str) and ',' in node2:
                # The key in tramo_id_map is likely node1-node2 where node1 and node2 are the strings
                edge = tuple(sorted([node1, node2]))
                edge_key = edge[0] + "-" + edge[1]
            else:
                edge = tuple(sorted([node1, node2]))
                edge_key = edge[0] + "-" + edge[1]
        except TypeError:
            print(f"Error: Could not create edge key from nodes {node1} and {node2}")
            return None
        
        if edge_key in tramo_id_map:
            section_id = tramo_id_map[edge_key]
            print(f"Found direct edge between nodes, section ID: {section_id}")
            return section_id, (p1, p2)
        else:
            print(f"Warning: Direct edge found but no section ID in tramo_id_map")
            return None
    else:
        print(f"Warning: No direct edge between {node1} and {node2} in the graph")
        return None

def main():
    parser = argparse.ArgumentParser(description="Generate multiple mandatory or forbidden sections for path_mandatory_sections.py")
    parser.add_argument("--point_pairs", nargs='+', required=True, 
                      help="Pairs of points in format '(x1,y1,z1)-(x2,y2,z2)' separated by spaces")
    parser.add_argument("--graph", type=str, help="Graph JSON file (if not using timestamp)")
    parser.add_argument("--positions", type=str, help="Positions JSON file (if not using timestamp)")
    parser.add_argument("--tramos", type=str, help="Tramo ID map JSON file (if not using timestamp)")
    parser.add_argument("--timestamp", type=str, help="Timestamp of the graph pack to use")
    parser.add_argument("--output", type=str, help="Output JSON file")
    parser.add_argument("--type", type=str, choices=["mandatory", "forbidden"], default="mandatory",
                      help="Type of sections to create (mandatory or forbidden)")
    parser.add_argument("--output_dir", type=str, default="Path_Restrictions", help="Output directory")
    parser.add_argument("--strict", action="store_true", help="Strict mode: exit if points are not exact nodes")
    args = parser.parse_args()
    
    # Generate timestamp for output if not provided
    timestamp = args.timestamp or datetime.now().strftime("%m%d_%H%M")
    
    # Generate detailed timestamp for file names
    current_time = datetime.now()
    detailed_timestamp = current_time.strftime("%Y%m%d_%H%M%S")
    
    # Ensure output directory exists
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    # Determine output filename
    if args.output:
        output_file = args.output
        if not os.path.dirname(output_file):
            output_file = os.path.join(args.output_dir, output_file)
    else:
        if args.type == "mandatory":
            output_file = os.path.join(args.output_dir, f"mandatory_sections_{timestamp}_{detailed_timestamp}.json")
        else:
            output_file = os.path.join(args.output_dir, f"forbidden_sections_{timestamp}_{detailed_timestamp}.json")
    
    # Determine the input files
    if args.timestamp:
        graph_file = os.path.join(args.output_dir, f"graph_{args.timestamp}.json")
        tramo_id_file = os.path.join(args.output_dir, f"tramo_id_map_{args.timestamp}.json")
        
        # Check if files exist
        if not os.path.exists(graph_file) or not os.path.exists(tramo_id_file):
            print(f"Error: Could not find basic files for timestamp {args.timestamp}")
            return
    else:
        graph_file = args.graph
        tramo_id_file = args.tramos
        
        if not graph_file or not tramo_id_file:
            print("Error: Please provide either a timestamp or graph and tramos files")
            return
    
    print(f"Using graph: {graph_file}")
    print(f"Using tramo ID map: {tramo_id_file}")
    
    # Load the necessary files
    with open(graph_file, 'r') as f:
        graph = json.load(f)
    
    with open(tramo_id_file, 'r') as f:
        tramo_id_map = json.load(f)
    
    # Get all node strings from the graph
    all_nodes = list(graph.keys())
    
    # Process each point pair
    sections = {}
    forbidden_list = []
    
    for i, pair_str in enumerate(args.point_pairs):
        print(f"\nProcessing point pair {i+1} of {len(args.point_pairs)}: {pair_str}")
        
        # Parse the points in the pair
        try:
            p1_str, p2_str = pair_str.split('-')
            p1 = parse_point(p1_str)
            p2 = parse_point(p2_str)
        except ValueError:
            print(f"Error: Invalid point pair format: {pair_str}")
            print(f"Point pairs must be in format '(x1,y1,z1)-(x2,y2,z2)'")
            continue
        
        # Find nearest nodes to p1 and p2
        node1, dist1 = find_nearest_node(p1, all_nodes)
        node2, dist2 = find_nearest_node(p2, all_nodes)
        
        print(f"Nearest node to {p1}: {node1} (distance: {dist1:.3f})")
        print(f"Nearest node to {p2}: {node2} (distance: {dist2:.3f})")
        
        # Check if both points exist exactly in the graph
        if dist1 > 0.001 or dist2 > 0.001:
            print("\n⚠️ WARNING: One or both points are not exact nodes in the graph ⚠️")
            print(f"The script should only be used with points that exist exactly in the graph.")
            print(f"Please check your input points and ensure they are valid graph nodes.")
            
            if args.strict:
                print("Exiting due to strict mode.")
                continue
            else:
                print("Proceeding anyway, but results may not be as expected.")
        
        # Check if nodes are directly connected
        if node2 in graph.get(node1, []) or node1 in graph.get(node2, []):
            # Create the edge key (always sorted for consistency)
            edge = tuple(sorted([node1, node2]))
            edge_key = edge[0] + "-" + edge[1]
            
            if edge_key in tramo_id_map:
                section_id = tramo_id_map[edge_key]
                print(f"Found direct edge between nodes, section ID: {section_id}")
                
                if args.type == "mandatory":
                    # For mandatory sections, use a dummy weight of 0.5
                    # This weight is ignored by path_mandatory_sections.py, but needed for format compatibility
                    sections[str(section_id)] = 0.5
                else:  # forbidden
                    forbidden_list.append(section_id)
            else:
                print(f"Warning: Direct edge found but no section ID in tramo_id_map")
        else:
            print(f"Warning: No direct edge between {node1} and {node2} in the graph")
    
    # Save the sections
    if args.type == "mandatory":
        if sections:
            with open(output_file, 'w') as f:
                json.dump(sections, f, indent=2)
            print(f"\nGenerated {len(sections)} mandatory sections for path_mandatory_sections.py")
            print(f"Mandatory sections saved to: {output_file}")
        else:
            print("\nNo valid mandatory sections found.")
    else:  # forbidden
        if forbidden_list:
            with open(output_file, 'w') as f:
                json.dump(forbidden_list, f, indent=2)
            print(f"\nGenerated {len(forbidden_list)} forbidden sections for path_mandatory_sections.py")
            print(f"Forbidden sections saved to: {output_file}")
        else:
            print("\nNo valid forbidden sections found.")
    
    # Print suggestion for next steps
    if sections or forbidden_list:
        section_type_param = "--mandatory" if args.type == "mandatory" else "--prohibidos"
        print("\nNext steps:")
        print(f"1. To run path finding with these sections:")
        print(f"   python3 Path_Restrictions/path_mandatory_sections.py --timestamp {timestamp} "
              f"--start \"(168.788,14.054,156.634)\" --goal \"(139.232,28.845,139.993)\" "
              f"{section_type_param} {output_file} --export_dxf")

if __name__ == "__main__":
    main() 