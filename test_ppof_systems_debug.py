#!/usr/bin/env python3
"""
Debug astar_PPOF_systems.py forbidden functionality
"""

from astar_PPOF_systems import SystemFilteredGraph
import json

def test_systems_forbidden():
    """Test SystemFilteredGraph with forbidden sections."""
    
    print("🔧 Testing SystemFilteredGraph with forbidden sections")
    
    # Create the graph
    graph = SystemFilteredGraph(
        'graph_LV_combined.json', 
        'C', 
        'tramo_map_combined.json', 
        'forbidden_tramos_c2_c3.json'
    )
    
    # Test the temp graph creation
    temp_graph = graph._create_temp_graph()
    print(f"📊 Temp graph type: {type(temp_graph)}")
    print(f"📊 Has forbidden method: {hasattr(temp_graph, 'find_path_with_edge_split_forbidden')}")
    
    if hasattr(temp_graph, 'forbidden_set'):
        print(f"🚫 Forbidden set: {temp_graph.forbidden_set}")
    
    if hasattr(temp_graph, 'tramo_id_map'):
        print(f"🗺️  Tramo map loaded: {len(temp_graph.tramo_id_map)} mappings")
    
    # Test pathfinding
    origin = (182.946, 13.304, 157.295)
    destination = (174.860, 15.369, 136.587)
    
    print(f"\n🎯 Testing pathfinding:")
    print(f"   Origin: {origin}")
    print(f"   Destination: {destination}")
    
    try:
        path, nodes_explored = graph.find_path_direct(origin, destination)
        print(f"✅ Path found: {len(path)} points, {nodes_explored} nodes explored")
        
        # Check if path goes through forbidden sections
        print(f"\n🔍 Checking path for forbidden sections:")
        forbidden_edges_used = []
        
        for i in range(len(path) - 1):
            p1 = path[i]
            p2 = path[i + 1]
            
            # Format coordinates like tramo map
            node1_str = f"({p1[0]:.3f}, {p1[1]:.3f}, {p1[2]:.3f})"
            node2_str = f"({p2[0]:.3f}, {p2[1]:.3f}, {p2[2]:.3f})"
            
            # Check if this edge is forbidden
            if hasattr(temp_graph, 'is_edge_forbidden'):
                is_forbidden = temp_graph.is_edge_forbidden(node1_str, node2_str)
                if is_forbidden:
                    edge_key = "-".join(sorted([node1_str, node2_str]))
                    tramo_id = temp_graph.tramo_id_map.get(edge_key, "UNKNOWN")
                    forbidden_edges_used.append((edge_key, tramo_id))
                    print(f"   ❌ FORBIDDEN EDGE USED: {edge_key} (Tramo {tramo_id})")
        
        if not forbidden_edges_used:
            print(f"   ✅ No forbidden edges used in path")
        else:
            print(f"   ❌ {len(forbidden_edges_used)} forbidden edges used!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_systems_forbidden()
