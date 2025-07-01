#!/usr/bin/env python3
"""
Verify that the path actually starts and ends at the correct points
"""

from astar_PPOF_systems import SystemFilteredGraph

def verify_endpoints():
    """Verify the path endpoints are correct."""
    
    print("🔍 Verifying path endpoints")
    
    # Expected coordinates
    origin = (182.946, 13.304, 157.295)  # C2
    destination = (174.860, 15.369, 136.587)  # C3
    
    print(f"Expected origin (C2): {origin}")
    print(f"Expected destination (C3): {destination}")
    
    # Create the graph and find path
    graph = SystemFilteredGraph(
        'graph_LV_combined.json', 
        'C', 
        'tramo_map_combined.json', 
        'forbidden_tramos_c2_c3.json'
    )
    
    path, nodes_explored = graph.find_path_direct(origin, destination)
    
    print(f"\n📊 Path results:")
    print(f"   Path length: {len(path)} points")
    print(f"   Nodes explored: {nodes_explored}")
    
    if path:
        print(f"\n🎯 Actual path endpoints:")
        print(f"   First point (should be C2): {path[0]}")
        print(f"   Last point (should be C3): {path[-1]}")
        
        # Check if endpoints match (with small tolerance for floating point)
        def points_match(p1, p2, tolerance=0.001):
            return all(abs(a - b) < tolerance for a, b in zip(p1, p2))
        
        origin_match = points_match(path[0], origin)
        dest_match = points_match(path[-1], destination)
        
        print(f"\n✅ Endpoint verification:")
        print(f"   Origin matches: {origin_match}")
        print(f"   Destination matches: {dest_match}")
        
        if not origin_match:
            print(f"   ❌ Origin mismatch: expected {origin}, got {path[0]}")
        if not dest_match:
            print(f"   ❌ Destination mismatch: expected {destination}, got {path[-1]}")
        
        # Show first few and last few points
        print(f"\n📍 Path details:")
        print(f"   First 3 points:")
        for i, point in enumerate(path[:3]):
            print(f"      {i+1}: {point}")
        
        print(f"   Last 3 points:")
        for i, point in enumerate(path[-3:]):
            print(f"      {len(path)-2+i}: {point}")
    else:
        print("❌ No path found!")

if __name__ == "__main__":
    verify_endpoints()
