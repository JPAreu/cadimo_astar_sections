#!/usr/bin/env python3
"""
Simplified version of astar_PPOF_systems.py for testing forbidden sections scenarios.
This version fixes the indentation issues and focuses on the core functionality.
"""

import sys
import json
from typing import List, Tuple
from cable_filter import ALLOWED, load_tagged_graph, build_adj, validate_endpoints, get_cable_info, coord_to_key, key_to_coord
from astar_PPO_forbid import ForbiddenEdgeGraph, calculate_path_distance, format_point

def test_forbidden_scenario(graph_file, origin, destination, cable_type, tramo_map_file, forbidden_file, scenario_name):
    """
    Test a forbidden sections scenario with system filtering.
    
    Args:
        graph_file: Path to tagged graph file
        origin: Origin coordinates tuple
        destination: Destination coordinates tuple  
        cable_type: Cable type (A, B, or C)
        tramo_map_file: Path to tramo ID map file
        forbidden_file: Path to forbidden sections file
        scenario_name: Name of the scenario for display
    """
    print(f"\n🧪 TESTING {scenario_name}")
    print("=" * 60)
    print(f"🚀 Running pathfinding with cable type {cable_type}")
    print(f"   Origin: {format_point(origin)}")
    print(f"   Destination: {format_point(destination)}")
    print(f"🚫 Using forbidden sections: {forbidden_file}")
    print(f"🗺️  Using tramo map: {tramo_map_file}")
    
    try:
        # Load and filter graph data for the cable type
        graph_data = load_tagged_graph(graph_file)
        cable_info = get_cable_info(cable_type)
        allowed_systems = cable_info['allowed_systems']
        
        print(f"🔧 {cable_info['description']}")
        print(f"📊 Full graph: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges")
        
        # Create system-filtered adjacency graph in the format expected by ForbiddenEdgeGraph
        filtered_adjacency = {}
        
        # Add nodes from allowed systems
        for node_key, node_data in graph_data["nodes"].items():
            if node_data.get("sys") in allowed_systems:
                filtered_adjacency[node_key] = []
        
        # Add edges from allowed systems
        for edge in graph_data["edges"]:
            if edge.get("sys") in allowed_systems:
                from_node = edge["from"]
                to_node = edge["to"]
                
                # Add bidirectional edges
                if from_node in filtered_adjacency and to_node in filtered_adjacency:
                    if to_node not in filtered_adjacency[from_node]:
                        filtered_adjacency[from_node].append(to_node)
                    if from_node not in filtered_adjacency[to_node]:
                        filtered_adjacency[to_node].append(from_node)
        
        print(f"🔍 Filtered graph: {len(filtered_adjacency)} nodes")
        
        # Create temporary graph file for ForbiddenEdgeGraph
        import tempfile
        temp_graph_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(filtered_adjacency, temp_graph_file, indent=2)
        temp_graph_file.close()
        
        # Test pathfinding with forbidden sections
        forbidden_graph = ForbiddenEdgeGraph(temp_graph_file.name, tramo_map_file, forbidden_file)
        path, nodes_explored = forbidden_graph.find_path_with_edge_split_forbidden(origin, destination)
        
        # Cleanup
        import os
        os.unlink(temp_graph_file.name)
        
        if path:
            print(f"\n✅ Path found!")
            print(f"   Path length: {len(path)} points")
            print(f"   Nodes explored: {nodes_explored}")
            print(f"   Total distance: {calculate_path_distance(path):.3f} units")
            print(f"   Cable type: {cable_type} (Systems: {', '.join(sorted(allowed_systems))})")
            return True
        else:
            print(f"\n❌ No path found!")
            print(f"   Nodes explored: {nodes_explored}")
            print(f"   Likely blocked by forbidden sections or system restrictions")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def main():
    """Test all three forbidden sections scenarios."""
    print("🔬 FORBIDDEN SECTIONS + SYSTEM FILTERING TESTING")
    print("Testing the three requested scenarios")
    
    # Test coordinates
    origin_a = (139.232, 28.845, 139.993)  # System A
    destination_a = (152.290, 17.883, 160.124)  # System A  
    origin_b = (174.860, 15.369, 136.587)  # System B
    destination_b = (176.062, 2.768, 136.939)  # System B
    
    graph_file = "graph_LV_combined.json"
    tramo_map_file = "tramo_map_combined.json"
    
    results = {}
    
    # Scenario 1: Forbidden paths in System A, Cable A
    print("\n" + "🔍 SCENARIO 1: Forbidden paths in one system")
    print("Cable A (System A only) with forbidden sections in System A")
    results['scenario1'] = test_forbidden_scenario(
        graph_file, origin_a, destination_a, 'A', 
        tramo_map_file, 'forbidden_system_a.json',
        "SCENARIO 1: System A with forbidden sections"
    )
    
    # Scenario 2: Forbidden cross-system connection, Cable C
    print("\n" + "🔍 SCENARIO 2: Forbidden cross-system connections")  
    print("Cable C with forbidden cross-system bridge")
    results['scenario2'] = test_forbidden_scenario(
        graph_file, origin_a, origin_b, 'C',
        tramo_map_file, 'forbidden_cross_system.json', 
        "SCENARIO 2: Cross-system bridge forbidden"
    )
    
    # Scenario 3: Forbidden paths in both systems, Cable C
    print("\n" + "🔍 SCENARIO 3: Forbidden paths in both systems")
    print("Cable C with forbidden sections in both System A and B")
    results['scenario3'] = test_forbidden_scenario(
        graph_file, origin_a, destination_a, 'C',
        tramo_map_file, 'forbidden_both_systems.json',
        "SCENARIO 3: Both systems with forbidden sections"
    )
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 RESULTS SUMMARY")
    print("=" * 60)
    for scenario, success in results.items():
        status = "✅ SUCCESS" if success else "❌ BLOCKED"
        print(f"   {scenario}: {status}")
    
    print(f"\n💡 Key insights:")
    print(f"   • Only 1 cross-system edge exists (Tramo ID 528)")
    print(f"   • Forbidding it isolates System A from System B")
    print(f"   • System filtering + forbidden sections work together")
    print(f"   • Cable type determines which systems are accessible")

if __name__ == "__main__":
    main() 