#!/usr/bin/env python3
"""
forbid_sections.py - Forbidden Edge Utility

Lightweight CLI utility that converts coordinate pairs into a list of tramo (section) IDs 
that the astar_ppo path-finder must avoid. Focuses solely on the "forbidden edge" use-case.

Usage:
    python forbid_sections.py --point_pairs "(x1,y1,z1)-(x2,y2,z2)" ... 
                              (--timestamp YYYYMMDD_HHMMSS | --graph graph.json --tramos tramo.json)
                              [-o OUT_DIR] [--output NAME.json] [--strict]

Author: A* PPO Pathfinding System
"""

import sys
import json
import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Set
from math import sqrt


def parse_point(point_str: str) -> Tuple[float, float, float]:
    """
    Convert "(x,y,z)" string to (float, float, float) tuple.
    
    Args:
        point_str: Coordinate string in format "(x,y,z)"
        
    Returns:
        Tuple of three floats (x, y, z)
        
    Raises:
        argparse.ArgumentTypeError: If coordinate format is invalid
    """
    try:
        # Remove parentheses and whitespace
        clean_str = point_str.strip().strip('()')
        
        # Split by comma and convert to floats
        parts = [float(x.strip()) for x in clean_str.split(',')]
        
        if len(parts) != 3:
            raise argparse.ArgumentTypeError(f"Expected 3 coordinates, got {len(parts)}: {point_str}")
        
        return tuple(parts)
    
    except (ValueError, AttributeError) as e:
        raise argparse.ArgumentTypeError(f"Invalid coordinate format '{point_str}': {e}")


def find_nearest_node(target: Tuple[float, float, float], 
                     graph_nodes: Dict[str, List[str]]) -> Tuple[str, float]:
    """
    Find the nearest graph node to the target coordinate.
    
    Args:
        target: Target coordinate (x, y, z)
        graph_nodes: Dictionary of graph nodes with canonical string keys
        
    Returns:
        Tuple of (nearest_node_key, distance)
    """
    min_distance = float('inf')
    nearest_node = None
    
    target_x, target_y, target_z = target
    
    for node_key in graph_nodes.keys():
        # Parse node coordinates from canonical string "(x, y, z)"
        try:
            clean_key = node_key.strip().strip('()')
            node_coords = [float(x.strip()) for x in clean_key.split(',')]
            node_x, node_y, node_z = node_coords
            
            # Calculate Euclidean distance
            distance = sqrt((target_x - node_x)**2 + (target_y - node_y)**2 + (target_z - node_z)**2)
            
            if distance < min_distance:
                min_distance = distance
                nearest_node = node_key
                
        except (ValueError, IndexError):
            # Skip malformed node keys
            continue
    
    if nearest_node is None:
        raise ValueError("No valid nodes found in graph")
    
    return nearest_node, min_distance


def generate_forbidden_sections(point_pairs: List[str],
                               graph_nodes: Dict[str, List[str]],
                               tramo_map: Dict[str, int],
                               strict_mode: bool = False) -> List[int]:
    """
    Convert coordinate pairs to forbidden tramo IDs.
    
    Args:
        point_pairs: List of coordinate pair strings "(x1,y1,z1)-(x2,y2,z2)"
        graph_nodes: Graph adjacency dictionary
        tramo_map: Edge-to-ID mapping dictionary
        strict_mode: If True, reject coordinates > 1mm from nearest node
        
    Returns:
        Sorted list of unique forbidden tramo IDs
    """
    forbidden_ids = set()
    strict_threshold = 0.001  # 1mm tolerance
    
    print(f"🔄 Processing {len(point_pairs)} coordinate pairs...")
    
    for i, pair_str in enumerate(point_pairs, 1):
        try:
            # Parse the pair string
            if '-' not in pair_str:
                print(f"⚠️  WARN: Pair {i} missing '-' separator: {pair_str}", file=sys.stderr)
                continue
            
            # Split on first '-' to handle negative coordinates
            parts = pair_str.split('-', 1)
            if len(parts) != 2:
                print(f"⚠️  WARN: Pair {i} malformed: {pair_str}", file=sys.stderr)
                continue
            
            # Parse coordinates
            coord1_str, coord2_str = parts
            coord1 = parse_point(coord1_str)
            coord2 = parse_point(coord2_str)
            
            # Find nearest nodes
            node1, dist1 = find_nearest_node(coord1, graph_nodes)
            node2, dist2 = find_nearest_node(coord2, graph_nodes)
            
            # Strict mode validation
            if strict_mode:
                if dist1 > strict_threshold:
                    print(f"⚠️  [STRICT] Pair {i}: Point 1 distance {dist1:.6f} > {strict_threshold:.3f}mm threshold", file=sys.stderr)
                    continue
                if dist2 > strict_threshold:
                    print(f"⚠️  [STRICT] Pair {i}: Point 2 distance {dist2:.6f} > {strict_threshold:.3f}mm threshold", file=sys.stderr)
                    continue
            
            # Check if nodes form a direct edge
            if node2 not in graph_nodes[node1]:
                print(f"⚠️  WARN: Pair {i} not a direct edge: {node1} -> {node2}", file=sys.stderr)
                continue
            
            # Create undirected edge key (alphabetically sorted)
            edge_key = "-".join(sorted([node1, node2]))
            
            # Look up tramo ID
            if edge_key not in tramo_map:
                print(f"⚠️  WARN: Pair {i} edge not found in tramo map: {edge_key}", file=sys.stderr)
                continue
            
            tramo_id = tramo_map[edge_key]
            forbidden_ids.add(tramo_id)
            
            print(f"   ✅ Pair {i}: {coord1} -> {coord2} = Tramo ID {tramo_id}")
            if dist1 > 0.0 or dist2 > 0.0:
                print(f"      Snap distances: {dist1:.6f}, {dist2:.6f}")
            
        except (argparse.ArgumentTypeError, ValueError) as e:
            print(f"⚠️  WARN: Pair {i} error: {e}", file=sys.stderr)
            continue
    
    # Convert to sorted list
    forbidden_list = sorted(list(forbidden_ids))
    print(f"✅ Generated {len(forbidden_list)} unique forbidden tramo IDs")
    
    return forbidden_list


def main():
    """Main function with CLI parsing and orchestration."""
    parser = argparse.ArgumentParser(
        description="Convert coordinate pairs to forbidden tramo IDs for A* pathfinding",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using timestamp to auto-locate graph and tramo files
  python forbid_sections.py --point_pairs "(0,0,0)-(1,0,0)" "(5,5,0)-(5,6,0)" \\
                            --timestamp 20250626_093015 --strict
  
  # Using explicit file paths
  python forbid_sections.py --point_pairs "(152.290,17.883,160.124)-(143.382,25.145,160.703)" \\
                            --graph graphs/graph_20250626_093015.json \\
                            --tramos graphs/tramo_id_map_20250626_093015.json \\
                            -o Path_Restrictions/ --output forbidden_edges.json
  
  # Multiple pairs with custom output
  python forbid_sections.py --point_pairs "(0,0,0)-(1,0,0)" "(5,5,0)-(5,6,0)" "(10,10,0)-(11,10,0)" \\
                            --graph graph_20250626_114538.json \\
                            --tramos tramo_id_map_20250626_114538.json
        """
    )
    
    # Required point pairs
    parser.add_argument('--point_pairs', required=True, nargs='+',
                        help='Coordinate pairs in format "(x1,y1,z1)-(x2,y2,z2)". Quote each pair.')
    
    # File specification options (mutually exclusive)
    parser.add_argument('--timestamp', 
                       help='Timestamp to locate graph_<ts>.json and tramo_id_map_<ts>.json files')
    parser.add_argument('--graph', 
                       help='Explicit path to graph_*.json file (requires --tramos)')
    parser.add_argument('--tramos', 
                       help='Explicit path to tramo_id_map_*.json file (requires --graph)')
    
    # Optional arguments
    parser.add_argument('-o', '--out_dir', type=Path, default=Path.cwd(),
                        help='Output directory for forbidden sections file (default: current directory)')
    parser.add_argument('--output', 
                        help='Exact filename for output JSON (default: auto-generated with timestamp)')
    parser.add_argument('--strict', action='store_true',
                        help='Abort pairs when coordinates are > 1mm from nearest graph node')
    
    args = parser.parse_args()
    
    # Validate mutually exclusive arguments
    has_timestamp = bool(args.timestamp)
    has_explicit = bool(args.graph or args.tramos)
    
    if not has_timestamp and not has_explicit:
        parser.error("Must specify either --timestamp OR both --graph and --tramos")
    if has_timestamp and has_explicit:
        parser.error("Cannot use --timestamp with --graph/--tramos")
    if args.graph and not args.tramos:
        parser.error("--graph requires --tramos")
    if args.tramos and not args.graph:
        parser.error("--tramos requires --graph")
    
    # Determine file paths
    if args.timestamp:
        # Auto-locate files using timestamp
        graph_file = args.out_dir / f"graph_{args.timestamp}.json"
        tramo_file = args.out_dir / f"tramo_id_map_{args.timestamp}.json"
    else:
        # Use explicit paths
        graph_file = Path(args.graph)
        tramo_file = Path(args.tramos)
    
    # Validate input files exist
    if not graph_file.exists():
        parser.error(f"Graph file not found: {graph_file}")
    if not tramo_file.exists():
        parser.error(f"Tramo file not found: {tramo_file}")
    
    # Create output directory if needed
    try:
        args.out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        parser.error(f"Cannot create output directory {args.out_dir}: {e}")
    
    # Generate output filename
    if args.output:
        output_file = args.out_dir / args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = args.out_dir / f"forbidden_sections_{timestamp}.json"
    
    try:
        # Load graph and tramo files
        print(f"🔄 Loading graph: {graph_file}")
        with open(graph_file, 'r', encoding='utf-8') as f:
            graph_nodes = json.load(f)
        print(f"   Loaded {len(graph_nodes)} nodes")
        
        print(f"🔄 Loading tramo mapping: {tramo_file}")
        with open(tramo_file, 'r', encoding='utf-8') as f:
            tramo_map = json.load(f)
        print(f"   Loaded {len(tramo_map)} edge mappings")
        
        # Generate forbidden sections
        forbidden_ids = generate_forbidden_sections(
            args.point_pairs, 
            graph_nodes, 
            tramo_map, 
            args.strict
        )
        
        # Write output file
        print(f"💾 Writing forbidden sections: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(forbidden_ids, f, indent=0, separators=(',', ':'))
        
        # Success
        print(f"\n✅ Forbidden sections file created successfully!")
        print(f"📁 Output file: {output_file.resolve()}")
        print(f"🚫 Forbidden tramo IDs: {forbidden_ids}")
        
    except (FileNotFoundError, json.JSONDecodeError, ValueError, OSError) as e:
        parser.error(f"Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 