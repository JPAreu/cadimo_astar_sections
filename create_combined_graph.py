#!/usr/bin/env python3
"""
create_combined_graph.py - Combine multiple system graphs for cross-system routing

This script merges graph_LV1A.json (System A) and graph_LV1B.json (System B) 
into a single graph that Cable C can use for cross-system pathfinding.
"""

import json
import sys
from typing import Dict, Any, Set

def load_graph(filepath: str) -> Dict[str, Any]:
    """Load a graph JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Graph file not found: {filepath}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {filepath}: {e}")
        sys.exit(1)

def combine_graphs(graph_a: Dict[str, Any], graph_b: Dict[str, Any], 
                  add_connections: bool = True) -> Dict[str, Any]:
    """
    Combine two graphs into a single multi-system graph.
    
    Args:
        graph_a: First graph (System A)
        graph_b: Second graph (System B)
        add_connections: Whether to add connections between overlapping nodes
        
    Returns:
        Combined graph with both systems
    """
    print("🔧 Combining graphs...")
    
    # Initialize combined graph
    combined = {
        "nodes": {},
        "edges": []
    }
    
    # Add all nodes from both graphs
    print("📍 Adding nodes...")
    nodes_a = set(graph_a["nodes"].keys())
    nodes_b = set(graph_b["nodes"].keys())
    overlapping = nodes_a.intersection(nodes_b)
    
    # Add nodes from graph A
    for node, data in graph_a["nodes"].items():
        combined["nodes"][node] = data.copy()
    
    # Add nodes from graph B
    for node, data in graph_b["nodes"].items():
        if node in combined["nodes"]:
            # Handle overlapping nodes - keep both system tags if different
            existing_sys = combined["nodes"][node].get("sys")
            new_sys = data.get("sys")
            if existing_sys != new_sys:
                print(f"⚠️  Overlapping node with different systems: {node}")
                print(f"   System A: {existing_sys}, System B: {new_sys}")
                # For Cable C compatibility, we'll mark it as accessible to both
                combined["nodes"][node]["sys"] = existing_sys  # Keep original
                combined["nodes"][node]["alt_sys"] = new_sys   # Add alternative
        else:
            combined["nodes"][node] = data.copy()
    
    # Add all edges from both graphs
    print("🔗 Adding edges...")
    all_edges = graph_a["edges"] + graph_b["edges"]
    
    # Remove duplicate edges
    edge_set = set()
    for edge in all_edges:
        edge_key = (edge["from"], edge["to"], edge["sys"])
        if edge_key not in edge_set:
            combined["edges"].append(edge)
            edge_set.add(edge_key)
    
    # Add cross-system connections at overlapping nodes
    if add_connections and overlapping:
        print("🌉 Adding cross-system connections...")
        for node in overlapping:
            # Find edges from this node in both systems
            edges_a = [e for e in graph_a["edges"] if e["from"] == node or e["to"] == node]
            edges_b = [e for e in graph_b["edges"] if e["from"] == node or e["to"] == node]
            
            # Create cross-system edges (System A ↔ System B)
            for edge_a in edges_a:
                for edge_b in edges_b:
                    # Connect different system edges through the overlapping node
                    if edge_a["sys"] != edge_b["sys"]:
                        # Add bidirectional cross-system edge
                        cross_edge = {
                            "from": node,
                            "to": node,
                            "sys": "C",  # Cable C can use this connection
                            "type": "cross_system_connection"
                        }
                        # Only add if not already present
                        if not any(e["from"] == node and e["to"] == node and e.get("sys") == "C" 
                                 for e in combined["edges"]):
                            combined["edges"].append(cross_edge)
    
    print(f"✅ Combined graph created:")
    print(f"   Total nodes: {len(combined['nodes'])}")
    print(f"   Total edges: {len(combined['edges'])}")
    print(f"   Overlapping nodes: {len(overlapping)}")
    
    return combined

def main():
    """Main function to create combined graph."""
    print("🚀 Creating Combined Graph for Cross-System Routing")
    print("=" * 55)
    
    # Load individual graphs
    print("📂 Loading graphs...")
    graph_a = load_graph("graph_LV1A.json")
    graph_b = load_graph("graph_LV1B.json")
    
    print(f"   Graph A (System A): {len(graph_a['nodes'])} nodes, {len(graph_a['edges'])} edges")
    print(f"   Graph B (System B): {len(graph_b['nodes'])} nodes, {len(graph_b['edges'])} edges")
    print()
    
    # Combine graphs
    combined_graph = combine_graphs(graph_a, graph_b, add_connections=True)
    
    # Save combined graph
    output_file = "graph_LV_combined.json"
    print(f"💾 Saving combined graph to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_graph, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Combined graph saved successfully!")
    print()
    
    # Verify the target points exist
    print("🔍 Verifying target points...")
    b1_key = "(174.860, 15.369, 136.587)"
    p1_key = "(139.232, 28.845, 139.993)"
    
    b1_exists = b1_key in combined_graph["nodes"]
    p1_exists = p1_key in combined_graph["nodes"]
    
    print(f"   B1 {b1_key}: {'✅ Found' if b1_exists else '❌ Not found'}")
    if b1_exists:
        print(f"      System: {combined_graph['nodes'][b1_key]['sys']}")
    
    print(f"   P1 {p1_key}: {'✅ Found' if p1_exists else '❌ Not found'}")
    if p1_exists:
        print(f"      System: {combined_graph['nodes'][p1_key]['sys']}")
    
    if b1_exists and p1_exists:
        print()
        print("🎯 Ready for Cable C testing!")
        print(f"   Command: python3 astar_PPOF_systems.py direct {output_file} \\")
        print(f"            174.8600 15.3690 136.5870 139.232 28.845 139.993 --cable C")
    else:
        print("⚠️  One or both target points not found in combined graph")

if __name__ == "__main__":
    main() 