#!/usr/bin/env python3
"""
json_convert_PPO.py - Graph Preprocessing Utility

One-shot preprocessing utility that transforms a raw network-export file into 
two compact artifacts consumed by the spatially-optimized A* path-finder:

1. graph_<timestamp>.json - Clean adjacency list with canonical node strings
2. tramo_id_map_<timestamp>.json - Edge-to-ID mapping for O(1) lookups

Usage:
    python json_convert_PPO.py RAW_GRAPH.json [-o OUT_DIR]

Author: A* PPO Pathfinding System
"""

import sys
import json
import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union, Tuple, Any


def _coord_to_key(coord: Union[str, List, Tuple]) -> str:
    """
    Convert any coordinate format to canonical string key "(x, y, z)".
    
    Args:
        coord: Coordinate in various formats (string, list, tuple)
        
    Returns:
        Canonical string representation "(x, y, z)"
        
    Raises:
        ValueError: If coordinate format is invalid
    """
    if isinstance(coord, str):
        # Already a string, clean up whitespace and ensure proper format
        coord = coord.strip()
        if coord.startswith('(') and coord.endswith(')'):
            return coord
        else:
            # Try to parse as comma-separated values
            try:
                parts = [float(x.strip()) for x in coord.split(',')]
                if len(parts) == 3:
                    return f"({parts[0]}, {parts[1]}, {parts[2]})"
                else:
                    raise ValueError(f"Expected 3 coordinates, got {len(parts)}")
            except (ValueError, AttributeError):
                raise ValueError(f"Invalid coordinate string format: {coord}")
    
    elif isinstance(coord, (list, tuple)):
        if len(coord) == 3:
            try:
                x, y, z = float(coord[0]), float(coord[1]), float(coord[2])
                return f"({x}, {y}, {z})"
            except (ValueError, TypeError):
                raise ValueError(f"Invalid coordinate values: {coord}")
        else:
            raise ValueError(f"Expected 3 coordinates, got {len(coord)}: {coord}")
    
    else:
        raise ValueError(f"Unsupported coordinate type: {type(coord)} - {coord}")


def _load_raw_graph(path: Path) -> Dict[str, List[str]]:
    """
    Load and normalize raw graph JSON into canonical adjacency dictionary.
    
    Args:
        path: Path to raw graph JSON file
        
    Returns:
        Normalized adjacency dictionary with canonical string keys
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        json.JSONDecodeError: If JSON is malformed
        ValueError: If coordinate format is invalid
    """
    print(f"🔄 Loading raw graph: {path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {path}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Malformed JSON in {path}: {e}")
    
    if not isinstance(raw_data, dict):
        raise ValueError(f"Expected JSON object (dict), got {type(raw_data)}")
    
    print(f"   Raw nodes: {len(raw_data)}")
    
    # Normalize adjacency dictionary
    normalized_adj = {}
    total_edges = 0
    
    for node_key, neighbors in raw_data.items():
        try:
            # Convert node key to canonical format
            canonical_node = _coord_to_key(node_key)
            
            # Convert neighbor list to canonical format
            canonical_neighbors = []
            if isinstance(neighbors, list):
                for neighbor in neighbors:
                    canonical_neighbor = _coord_to_key(neighbor)
                    canonical_neighbors.append(canonical_neighbor)
                    total_edges += 1
            else:
                raise ValueError(f"Expected neighbor list, got {type(neighbors)} for node {node_key}")
            
            normalized_adj[canonical_node] = canonical_neighbors
            
        except ValueError as e:
            raise ValueError(f"Error processing node {node_key}: {e}")
    
    print(f"   Normalized nodes: {len(normalized_adj)}")
    print(f"   Total directed edges: {total_edges}")
    
    return normalized_adj


def _build_tramo_id_map(adj: Dict[str, List[str]]) -> Dict[str, int]:
    """
    Build edge-to-ID mapping for undirected edges.
    
    Args:
        adj: Normalized adjacency dictionary
        
    Returns:
        Dictionary mapping edge keys to integer IDs
    """
    print(f"🔄 Building tramo ID mapping...")
    
    tramo_map = {}
    next_id = 1
    
    # Process all edges, ensuring each undirected edge gets one ID
    for node, neighbors in adj.items():
        for neighbor in neighbors:
            # Create undirected edge key (alphabetically sorted)
            edge_key = "-".join(sorted([node, neighbor]))
            
            # Assign ID if not seen before
            if edge_key not in tramo_map:
                tramo_map[edge_key] = next_id
                next_id += 1
    
    print(f"   Unique undirected edges: {len(tramo_map)}")
    print(f"   Tramo IDs assigned: 1 to {next_id - 1}")
    
    return tramo_map


def main():
    """Main function with CLI parsing and orchestration."""
    parser = argparse.ArgumentParser(
        description="Convert raw graph JSON to optimized A* pathfinding artifacts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert with default output directory (current working directory)
  python json_convert_PPO.py graph_LVA1.json
  
  # Convert with custom output directory
  python json_convert_PPO.py raw_network.json -o processed_graphs/
  
  # Process and use with restriction tools
  python json_convert_PPO.py data.json -o graphs/
  python forbid_sections.py --graph graphs/graph_20250626_093015.json \\
                           --tramos graphs/tramo_id_map_20250626_093015.json
        """
    )
    
    parser.add_argument('raw_graph', type=Path,
                        help='Input raw graph JSON file')
    parser.add_argument('-o', '--out_dir', type=Path, default=Path.cwd(),
                        help='Output directory for generated artifacts (default: current directory)')
    
    args = parser.parse_args()
    
    # Validate input file
    if not args.raw_graph.exists():
        print(f"❌ Error: Input file not found: {args.raw_graph}", file=sys.stderr)
        sys.exit(1)
    
    if not args.raw_graph.is_file():
        print(f"❌ Error: Input path is not a file: {args.raw_graph}", file=sys.stderr)
        sys.exit(1)
    
    # Create output directory if needed
    try:
        args.out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"❌ Error: Cannot create output directory {args.out_dir}: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Generate timestamp suffix
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Define output file paths
    graph_file = args.out_dir / f"graph_{timestamp}.json"
    tramo_file = args.out_dir / f"tramo_id_map_{timestamp}.json"
    
    try:
        # Step 1: Load and normalize raw graph
        normalized_adj = _load_raw_graph(args.raw_graph)
        
        # Step 2: Build tramo ID mapping
        tramo_id_map = _build_tramo_id_map(normalized_adj)
        
        # Step 3: Write graph artifact
        print(f"💾 Writing graph artifact: {graph_file}")
        with open(graph_file, 'w', encoding='utf-8') as f:
            json.dump(normalized_adj, f, indent=0, separators=(',', ':'))
        
        # Step 4: Write tramo ID mapping artifact
        print(f"💾 Writing tramo ID mapping: {tramo_file}")
        with open(tramo_file, 'w', encoding='utf-8') as f:
            json.dump(tramo_id_map, f, indent=0, separators=(',', ':'))
        
        # Success - print absolute paths
        print(f"\n✅ Conversion completed successfully!")
        print(f"📁 Graph artifact: {graph_file.resolve()}")
        print(f"📁 Tramo ID mapping: {tramo_file.resolve()}")
        print(f"🔢 Processed {len(normalized_adj)} nodes and {len(tramo_id_map)} undirected edges")
        
    except (FileNotFoundError, json.JSONDecodeError, ValueError, OSError) as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 