#!/usr/bin/env python3
"""
Convert Extended Graph to Tagged Format

This script converts the extended graph from the External Connector workflow
to the tagged format required by astar_PPOF_systems.py.

The script:
1. Loads the original tagged graph to get system assignments
2. Loads the extended graph with new nodes (PE, PI, PC)
3. Assigns system labels to new nodes based on connection logic
4. Outputs a tagged graph with the extended nodes

Usage:
    python3 convert_extended_to_tagged.py extended_graph.json tagged_extended_graph.json
"""

import json
import sys
from typing import Dict, List, Tuple, Set
from pathlib import Path

def load_adjacency_graph(path: str) -> Dict[str, List[List[float]]]:
    """Load adjacency graph format."""
    with open(path, 'r') as f:
        return json.load(f)

def load_tagged_graph(path: str) -> Dict:
    """Load tagged graph format."""
    with open(path, 'r') as f:
        return json.load(f)

def coord_to_key(coord: Tuple[float, float, float]) -> str:
    """Convert coordinate tuple to string key with 3 decimal places."""
    return f"({coord[0]:.3f}, {coord[1]:.3f}, {coord[2]:.3f})"

def key_to_coord(key: str) -> Tuple[float, float, float]:
    """Convert string key to coordinate tuple."""
    clean_key = key.strip('()').split(', ')
    return tuple(float(c) for c in clean_key)

def find_system_for_node(node_key: str, neighbors: List[List[float]], 
                        original_tagged: Dict) -> str:
    """
    Determine the system assignment for a new node based on its neighbors.
    
    Logic:
    1. If all neighbors are from the same system, assign that system
    2. If neighbors are from different systems, assign the most common system
    3. If no neighbors have system info, assign 'A' as default
    """
    neighbor_systems = []
    
    for neighbor_coord in neighbors:
        neighbor_key = coord_to_key(tuple(neighbor_coord))
        if neighbor_key in original_tagged.get("nodes", {}):
            sys = original_tagged["nodes"][neighbor_key].get("sys")
            if sys:
                neighbor_systems.append(sys)
    
    if len(neighbor_systems) == 0:
        # No system info found, default to 'A'
        return 'A'
    elif len(set(neighbor_systems)) == 1:
        # All neighbors from same system
        return neighbor_systems[0]
    else:
        # Mixed systems, assign the most common system
        from collections import Counter
        most_common = Counter(neighbor_systems).most_common(1)
        return most_common[0][0] if most_common else 'A'

def convert_extended_to_tagged(extended_path: str, original_tagged_path: str, 
                              output_path: str) -> None:
    """
    Convert extended adjacency graph to tagged format.
    
    Args:
        extended_path: Path to extended adjacency graph
        original_tagged_path: Path to original tagged graph (for system reference)
        output_path: Path for output tagged graph
    """
    print(f"🔄 Converting extended graph to tagged format...")
    print(f"   Extended graph: {extended_path}")
    print(f"   Original tagged: {original_tagged_path}")
    print(f"   Output: {output_path}")
    
    # Load graphs
    extended_graph = load_adjacency_graph(extended_path)
    original_tagged = load_tagged_graph(original_tagged_path)
    
    print(f"   Extended nodes: {len(extended_graph)}")
    print(f"   Original tagged nodes: {len(original_tagged.get('nodes', {}))}")
    
    # Initialize output structure
    output_graph = {
        "nodes": {},
        "edges": []
    }
    
    # Track processed edges to avoid duplicates
    processed_edges = set()
    
    # Process each node in the extended graph
    for node_key, neighbors in extended_graph.items():
        # Convert node_key to canonical format with 3 decimal places
        node_coord = key_to_coord(node_key)
        canonical_key = coord_to_key(node_coord)
        
        # Determine system for this node
        if canonical_key in original_tagged.get("nodes", {}):
            # Node exists in original, use its system
            sys = original_tagged["nodes"][canonical_key]["sys"]
        else:
            # New node, determine system based on neighbors
            sys = find_system_for_node(canonical_key, neighbors, original_tagged)
            print(f"   New node {canonical_key}: assigned system '{sys}'")
        
        # Add node to output using canonical key
        output_graph["nodes"][canonical_key] = {"sys": sys}
        
        # Process edges
        for neighbor_coord in neighbors:
            neighbor_canonical_key = coord_to_key(tuple(neighbor_coord))
            
            # Create edge key for duplicate detection
            edge_key = tuple(sorted([canonical_key, neighbor_canonical_key]))
            
            if edge_key not in processed_edges:
                processed_edges.add(edge_key)
                
                # Determine edge system (same logic as nodes)
                if neighbor_canonical_key in original_tagged.get("nodes", {}):
                    neighbor_sys = original_tagged["nodes"][neighbor_canonical_key]["sys"]
                else:
                    # Find the original key format for this neighbor
                    neighbor_original_key = None
                    for orig_key in extended_graph.keys():
                        if coord_to_key(key_to_coord(orig_key)) == neighbor_canonical_key:
                            neighbor_original_key = orig_key
                            break
                    
                    neighbor_neighbors = extended_graph.get(neighbor_original_key, []) if neighbor_original_key else []
                    neighbor_sys = find_system_for_node(neighbor_canonical_key, neighbor_neighbors, original_tagged)
                
                # Edge system is determined by the nodes it connects
                if sys == neighbor_sys:
                    edge_sys = sys
                else:
                    # Cross-system edge - assign the system of the first node
                    edge_sys = sys
                
                # Add edge to output using canonical keys
                output_graph["edges"].append({
                    "from": canonical_key,
                    "to": neighbor_canonical_key,
                    "sys": edge_sys
                })
    
    # Save output
    with open(output_path, 'w') as f:
        json.dump(output_graph, f, indent=2)
    
    print(f"✅ Conversion complete!")
    print(f"   Output nodes: {len(output_graph['nodes'])}")
    print(f"   Output edges: {len(output_graph['edges'])}")
    
    # Show new nodes summary
    new_nodes = []
    for node_key in output_graph["nodes"]:
        if node_key not in original_tagged.get("nodes", {}):
            new_nodes.append((node_key, output_graph["nodes"][node_key]["sys"]))
    
    if new_nodes:
        print(f"   New nodes added ({len(new_nodes)}):")
        for node_key, sys in new_nodes:
            print(f"      {node_key} -> System {sys}")

def main():
    """Main function with command line interface."""
    if len(sys.argv) != 4:
        print("Usage: python3 convert_extended_to_tagged.py <extended_graph.json> <original_tagged.json> <output_tagged.json>")
        print()
        print("Example:")
        print("  python3 convert_extended_to_tagged.py extended_graph.json ../graph_LV_combined.json tagged_extended_graph.json")
        sys.exit(1)
    
    extended_path = sys.argv[1]
    original_tagged_path = sys.argv[2]
    output_path = sys.argv[3]
    
    # Validate input files
    if not Path(extended_path).exists():
        print(f"❌ Error: Extended graph file not found: {extended_path}")
        sys.exit(1)
    
    if not Path(original_tagged_path).exists():
        print(f"❌ Error: Original tagged graph file not found: {original_tagged_path}")
        sys.exit(1)
    
    try:
        convert_extended_to_tagged(extended_path, original_tagged_path, output_path)
    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 