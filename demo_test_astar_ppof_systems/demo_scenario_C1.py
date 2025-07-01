#!/usr/bin/env python3
"""
Scenario C1: Direct Path Between C1 and C2
==========================================

This scenario demonstrates direct pathfinding between two specific coordinates:
- C1: (176.553, 6.028, 150.340) - New coordinate
- C2: (182.946, 13.304, 157.295) - Repeats from Scenario A (A2)

The goal is to find the optimal direct path and export it to DXF format.

Coordinates:
- Origin (C1): (176.553, 6.028, 150.340)
- Destination (C2): (182.946, 13.304, 157.295) - Same as A2 from Scenario A
- Cable Type: C (Both systems access)
"""

import sys
import os
import json
from math import sqrt
from typing import List, Tuple, Dict, Any

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from astar_PPOF_systems import (
    run_direct_systems,
    SystemFilteredGraph,
    calculate_path_distance,
    format_point
)

def run_scenario_C1():
    """
    Scenario C1: Direct Path Between C1 and C2
    
    Finds the optimal direct path between the specified coordinates
    and prepares data for DXF export.
    """
    print("🚀 Scenario C1: Direct Path Between C1 and C2")
    print("=" * 60)
    print()
    
    # Scenario coordinates
    origin = (176.553, 6.028, 150.340)      # C1 - New coordinate
    destination = (182.946, 13.304, 157.295)  # C2 - Same as A2 from Scenario A
    cable_type = "C"                          # Cable C: Both systems
    
    # Required files
    graph_file = "graph_LV_combined.json"
    tramo_map_file = "tramo_map_combined.json"
    
    print(f"📋 Scenario Configuration:")
    print(f"   Origin (C1):      {format_point(origin)}")
    print(f"   Destination (C2): {format_point(destination)} (Same as A2)")
    print(f"   Cable Type:       {cable_type} (Both systems)")
    print(f"   Graph:            {graph_file}")
    print(f"   Tramo Map:        {tramo_map_file}")
    print()
    
    # Verify required files exist
    missing_files = []
    for file_path in [graph_file, tramo_map_file]:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return None
    
    print("✅ All required files found")
    print()
    
    # ====================================================================
    # Test 1: Analyze Endpoint Systems
    # ====================================================================
    print("🧪 Test C1.1: Endpoint System Analysis")
    print("-" * 50)
    
    try:
        # Create SystemFilteredGraph to analyze endpoints
        graph = SystemFilteredGraph(graph_file, cable_type, tramo_map_file)
        
        from astar_PPOF_systems import coord_to_key
        origin_key = coord_to_key(origin)
        destination_key = coord_to_key(destination)
        
        # Find origin system
        origin_system = None
        origin_found = False
        for node_key, node_data in graph.graph_data["nodes"].items():
            if node_key == origin_key:
                origin_system = node_data.get("sys")
                origin_found = True
                break
        
        # Find destination system
        destination_system = None  
        destination_found = False
        for node_key, node_data in graph.graph_data["nodes"].items():
            if node_key == destination_key:
                destination_system = node_data.get("sys")
                destination_found = True
                break
        
        print(f"🔍 Endpoint Analysis:")
        print(f"   Origin (C1): {format_point(origin)}")
        print(f"   - Found in graph: {'✅ YES' if origin_found else '❌ NO'}")
        print(f"   - System: {origin_system if origin_found else 'NOT FOUND'}")
        print(f"   Destination (C2): {format_point(destination)}")
        print(f"   - Found in graph: {'✅ YES' if destination_found else '❌ NO'}")
        print(f"   - System: {destination_system if destination_found else 'NOT FOUND'}")
        print()
        
        if not origin_found:
            print(f"❌ Origin C1 not found in graph - cannot proceed")
            return None
        
        if not destination_found:
            print(f"❌ Destination C2 not found in graph - cannot proceed")
            return None
        
        # Determine routing type
        if origin_system == destination_system:
            routing_type = f"Intra-System (System {origin_system})"
        else:
            routing_type = f"Cross-System ({origin_system} → {destination_system})"
        
        print(f"📊 Routing Analysis:")
        print(f"   Routing Type: {routing_type}")
        print(f"   Cable Type: {cable_type} (allows {', '.join(sorted(graph.allowed_systems))})")
        print(f"   Expected Result: ✅ SUCCESS (both endpoints accessible)")
        
    except Exception as e:
        print(f"❌ Endpoint analysis failed: {e}")
        return None
    
    print()
    
    # ====================================================================
    # Test 2: Calculate Direct Distance
    # ====================================================================
    print("🧪 Test C1.2: Direct Distance Calculation")
    print("-" * 50)
    
    try:
        direct_distance = sqrt(
            (destination[0] - origin[0])**2 + 
            (destination[1] - origin[1])**2 + 
            (destination[2] - origin[2])**2
        )
        
        print(f"📏 Euclidean Distance Analysis:")
        print(f"   ΔX: {destination[0] - origin[0]:.3f}")
        print(f"   ΔY: {destination[1] - origin[1]:.3f}")
        print(f"   ΔZ: {destination[2] - origin[2]:.3f}")
        print(f"   Direct Distance: {direct_distance:.3f} units")
        
    except Exception as e:
        print(f"❌ Distance calculation failed: {e}")
        return None
    
    print()
    
    # ====================================================================
    # Test 3: Find Optimal Path
    # ====================================================================
    print("🧪 Test C1.3: Optimal Path Finding")
    print("-" * 50)
    
    try:
        print(f"🚀 Running direct pathfinding...")
        
        # Find the optimal path
        path, nodes_explored = run_direct_systems(
            graph_file, origin, destination, cable_type, tramo_map_file
        )
        
        # Calculate path metrics
        path_distance = calculate_path_distance(path)
        efficiency = (direct_distance / path_distance) * 100 if path_distance > 0 else 0
        
        print(f"✅ Path Found Successfully!")
        print(f"   Path Points: {len(path)}")
        print(f"   Nodes Explored: {nodes_explored}")
        print(f"   Path Distance: {path_distance:.3f} units")
        print(f"   Direct Distance: {direct_distance:.3f} units")
        print(f"   Path Efficiency: {efficiency:.1f}%")
        print(f"   Routing Type: {routing_type}")
        
        # Path analysis
        path_overhead = ((path_distance - direct_distance) / direct_distance) * 100
        print(f"   Path Overhead: {path_overhead:.1f}%")
        
        if len(path) > 0:
            print(f"   Start Point: {format_point(path[0])}")
            print(f"   End Point: {format_point(path[-1])}")
        
        # Store results for DXF export
        scenario_results = {
            "scenario": "C1",
            "title": "Direct Path Between C1 and C2",
            "origin": {"name": "C1", "coord": origin, "system": origin_system},
            "destination": {"name": "C2", "coord": destination, "system": destination_system},
            "cable_type": cable_type,
            "routing_type": routing_type,
            "path": path,
            "metrics": {
                "path_points": len(path),
                "nodes_explored": nodes_explored,
                "path_distance": path_distance,
                "direct_distance": direct_distance,
                "efficiency": efficiency,
                "overhead": path_overhead
            }
        }
        
        return scenario_results
        
    except Exception as e:
        print(f"❌ Pathfinding failed: {e}")
        return None
    
    print()

def create_scenario_C1_summary(results):
    """Create a summary of Scenario C1 results for documentation."""
    if not results:
        return None
    
    summary = {
        "scenario": "C1",
        "title": "Direct Path Between C1 and C2",
        "description": "Optimal pathfinding between C1 and C2 coordinates",
        "coordinates": {
            "origin": {"point": "C1", "coord": results["origin"]["coord"], "system": results["origin"]["system"]},
            "destination": {"point": "C2", "coord": results["destination"]["coord"], "system": results["destination"]["system"]}
        },
        "cable_type": results["cable_type"],
        "routing_type": results["routing_type"],
        "results": {
            "success": True,
            "path_points": results["metrics"]["path_points"],
            "path_distance": results["metrics"]["path_distance"],
            "efficiency": results["metrics"]["efficiency"]
        }
    }
    
    return summary

if __name__ == "__main__":
    print("Scenario C1: Direct Path Between C1 and C2")
    print("Finding optimal path for DXF export")
    print()
    
    results = run_scenario_C1()
    
    if results:
        print("\n🎉 Scenario C1 completed successfully!")
        print(f"✅ Path found: {results['metrics']['path_points']} points")
        print(f"✅ Distance: {results['metrics']['path_distance']:.3f} units")
        print(f"✅ Efficiency: {results['metrics']['efficiency']:.1f}%")
        print(f"✅ Ready for DXF export")
        
        # Create summary for documentation
        summary = create_scenario_C1_summary(results)
        print(f"\n📄 Summary created for documentation")
        
        # Save results for DXF export
        results_file = "scenario_C1_results.json"
        try:
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"💾 Results saved to {results_file}")
        except Exception as e:
            print(f"⚠️  Could not save results: {e}")
    else:
        print("\n❌ Scenario C1 failed")
        sys.exit(1) 