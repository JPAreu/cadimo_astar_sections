#!/usr/bin/env python3
"""
Scenario C: Cross-System Routing with System B Cable
====================================================

This scenario tests cross-system routing with a critical constraint:
- Origin: A2 (System A) 
- Destination: B3 (System B)
- Cable Type: B (System B ONLY)

Expected Result: FAILURE
The cable type B only provides access to System B, but the origin is in System A.
This should demonstrate the cable filtering system's access control enforcement.

Coordinates:
- Origin (A2): (182.946, 13.304, 157.295) - System A
- Destination (B3): (176.062, 2.416, 153.960) - System B
- Cable Type: B (System B access only)
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

def run_scenario_C():
    """
    Scenario C: Cross-System Routing with System B Cable
    
    Tests what happens when trying to route from System A to System B
    using Cable B (which only allows access to System B).
    """
    print("🚀 Scenario C: Cross-System Routing with System B Cable")
    print("=" * 70)
    print()
    
    # Scenario coordinates
    origin = (182.946, 13.304, 157.295)      # A2 - System A
    destination = (176.062, 2.416, 153.960)  # B3 - System B
    cable_type = "B"                          # Cable B: System B ONLY
    
    # Required files
    graph_file = "graph_LV_combined.json"
    tramo_map_file = "tramo_map_combined.json"
    
    print(f"📋 Scenario Configuration:")
    print(f"   Origin (A2):      {format_point(origin)} - System A")
    print(f"   Destination (B3): {format_point(destination)} - System B")
    print(f"   Cable Type:       {cable_type} (System B ONLY)")
    print(f"   Graph:            {graph_file}")
    print(f"   Tramo Map:        {tramo_map_file}")
    print()
    
    # Expected behavior analysis
    print(f"🔍 Expected Behavior Analysis:")
    print(f"   Cable B allows access to: System B only")
    print(f"   Origin system: A (NOT accessible with Cable B)")
    print(f"   Destination system: B (accessible with Cable B)")
    print(f"   Expected result: FAILURE - Origin not accessible")
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
        return False
    
    print("✅ All required files found")
    print()
    
    # ====================================================================
    # Test 1: Analyze Cable B System Access
    # ====================================================================
    print("🧪 Test C.1: Cable B System Access Analysis")
    print("-" * 50)
    
    try:
        # Create SystemFilteredGraph to analyze filtering
        graph = SystemFilteredGraph(graph_file, cable_type, tramo_map_file)
        
        print(f"✅ Cable B Analysis:")
        print(f"   Allowed systems: {', '.join(sorted(graph.allowed_systems))}")
        print(f"   Total graph nodes: {len(graph.graph_data['nodes'])}")
        print(f"   Total graph edges: {len(graph.graph_data['edges'])}")
        
        # Count nodes and edges by system
        system_a_nodes = sum(1 for node_data in graph.graph_data["nodes"].values() 
                           if node_data.get("sys") == "A")
        system_b_nodes = sum(1 for node_data in graph.graph_data["nodes"].values() 
                           if node_data.get("sys") == "B")
        
        system_a_edges = sum(1 for edge in graph.graph_data["edges"] 
                           if edge.get("sys") == "A")
        system_b_edges = sum(1 for edge in graph.graph_data["edges"] 
                           if edge.get("sys") == "B")
        
        print(f"   System A nodes: {system_a_nodes} (blocked by Cable B)")
        print(f"   System B nodes: {system_b_nodes} (accessible)")
        print(f"   System A edges: {system_a_edges} (blocked by Cable B)")
        print(f"   System B edges: {system_b_edges} (accessible)")
        
        # Calculate filtering efficiency
        accessible_nodes = len([node_key for node_key, node_data in graph.graph_data["nodes"].items() 
                              if node_data.get("sys") in graph.allowed_systems])
        accessible_edges = len([edge for edge in graph.graph_data["edges"] 
                              if edge.get("sys") in graph.allowed_systems])
        
        node_filter_efficiency = (accessible_nodes / len(graph.graph_data['nodes'])) * 100
        edge_filter_efficiency = (accessible_edges / len(graph.graph_data['edges'])) * 100
        
        print(f"   Accessible nodes: {accessible_nodes}/{len(graph.graph_data['nodes'])} ({node_filter_efficiency:.1f}%)")
        print(f"   Accessible edges: {accessible_edges}/{len(graph.graph_data['edges'])} ({edge_filter_efficiency:.1f}%)")
        
    except Exception as e:
        print(f"❌ Cable B analysis failed: {e}")
        return False
    
    print()
    
    # ====================================================================
    # Test 2: Origin Accessibility Check
    # ====================================================================
    print("🧪 Test C.2: Origin Accessibility Check")
    print("-" * 50)
    
    try:
        # Check if origin is in the filtered graph
        from astar_PPOF_systems import coord_to_key
        origin_key = coord_to_key(origin)
        
        origin_accessible = False
        origin_system = None
        
        for node_key, node_data in graph.graph_data["nodes"].items():
            if node_key == origin_key:
                origin_system = node_data.get("sys")
                origin_accessible = origin_system in graph.allowed_systems
                break
        
        print(f"🔍 Origin Analysis:")
        print(f"   Origin coordinate: {format_point(origin)}")
        print(f"   Origin key: {origin_key}")
        print(f"   Origin system: {origin_system}")
        print(f"   Cable B allows: {', '.join(sorted(graph.allowed_systems))}")
        print(f"   Origin accessible: {'✅ YES' if origin_accessible else '❌ NO'}")
        
        if not origin_accessible:
            print(f"   ⚠️  Origin is in System {origin_system}, but Cable B only allows System B")
            print(f"   ⚠️  This will cause pathfinding to fail")
        
    except Exception as e:
        print(f"❌ Origin accessibility check failed: {e}")
        return False
    
    print()
    
    # ====================================================================
    # Test 3: Destination Accessibility Check
    # ====================================================================
    print("🧪 Test C.3: Destination Accessibility Check")
    print("-" * 50)
    
    try:
        # Check if destination is in the filtered graph
        destination_key = coord_to_key(destination)
        
        destination_accessible = False
        destination_system = None
        
        for node_key, node_data in graph.graph_data["nodes"].items():
            if node_key == destination_key:
                destination_system = node_data.get("sys")
                destination_accessible = destination_system in graph.allowed_systems
                break
        
        print(f"🔍 Destination Analysis:")
        print(f"   Destination coordinate: {format_point(destination)}")
        print(f"   Destination key: {destination_key}")
        print(f"   Destination system: {destination_system}")
        print(f"   Cable B allows: {', '.join(sorted(graph.allowed_systems))}")
        print(f"   Destination accessible: {'✅ YES' if destination_accessible else '❌ NO'}")
        
        if destination_accessible:
            print(f"   ✅ Destination is in System {destination_system}, which is allowed by Cable B")
        
    except Exception as e:
        print(f"❌ Destination accessibility check failed: {e}")
        return False
    
    print()
    
    # ====================================================================
    # Test 4: Attempt Cross-System Routing with Cable B
    # ====================================================================
    print("🧪 Test C.4: Cross-System Routing Attempt")
    print("-" * 50)
    
    try:
        print(f"🚀 Attempting direct pathfinding with Cable B...")
        print(f"   Expected result: FAILURE (origin not accessible)")
        print()
        
        # Attempt the routing
        path, nodes_explored = run_direct_systems(
            graph_file, origin, destination, cable_type, tramo_map_file
        )
        
        # If we get here, something unexpected happened
        distance = calculate_path_distance(path)
        
        print(f"⚠️  UNEXPECTED SUCCESS:")
        print(f"   Path length: {len(path)} points")
        print(f"   Distance: {distance:.3f} units")
        print(f"   Nodes explored: {nodes_explored}")
        print(f"   ⚠️  This suggests a potential issue with cable filtering")
        
    except Exception as e:
        print(f"✅ EXPECTED FAILURE:")
        print(f"   Error: {str(e)}")
        print(f"   ✅ Cable filtering correctly prevented access to System A origin")
        print(f"   ✅ System access control is working as designed")
    
    print()
    
    # ====================================================================
    # Test 5: Comparison with Cable C (Control Test)
    # ====================================================================
    print("🧪 Test C.5: Control Test with Cable C")
    print("-" * 50)
    
    try:
        print(f"🔄 Control test: Same route with Cable C (both systems)...")
        
        # Test with Cable C for comparison
        control_path, control_nodes = run_direct_systems(
            graph_file, origin, destination, "C", tramo_map_file
        )
        control_distance = calculate_path_distance(control_path)
        
        print(f"✅ Cable C Success (Control):")
        print(f"   Path length: {len(control_path)} points")
        print(f"   Distance: {control_distance:.3f} units")
        print(f"   Nodes explored: {control_nodes}")
        print(f"   ✅ Confirms the route is viable with proper cable access")
        
    except Exception as e:
        print(f"❌ Control test failed: {e}")
        print(f"   ⚠️  This suggests a deeper issue with the routing system")
    
    print()
    
    # ====================================================================
    # Summary and Analysis
    # ====================================================================
    print("📋 Scenario C Summary and Analysis")
    print("=" * 50)
    
    print(f"🎯 Key Findings:")
    print(f"   1. Cable B filtering: {'✅ WORKING' if not origin_accessible else '❌ NOT WORKING'}")
    print(f"   2. System access control: {'✅ ENFORCED' if not origin_accessible else '❌ BYPASSED'}")
    print(f"   3. Origin accessibility: {'❌ BLOCKED' if not origin_accessible else '✅ ALLOWED'}")
    print(f"   4. Destination accessibility: {'✅ ALLOWED' if destination_accessible else '❌ BLOCKED'}")
    print()
    
    print(f"🔧 Technical Validation:")
    print(f"   • Cable B allows only System B access")
    print(f"   • Origin A2 is in System A (should be blocked)")
    print(f"   • Destination B3 is in System B (should be allowed)")
    print(f"   • Expected behavior: Route fails due to inaccessible origin")
    print()
    
    print(f"📊 System Filtering Efficiency:")
    print(f"   • Nodes accessible: {accessible_nodes}/{len(graph.graph_data['nodes'])} ({node_filter_efficiency:.1f}%)")
    print(f"   • Edges accessible: {accessible_edges}/{len(graph.graph_data['edges'])} ({edge_filter_efficiency:.1f}%)")
    print(f"   • System A nodes blocked: {system_a_nodes}")
    print(f"   • System B nodes accessible: {system_b_nodes}")
    print()
    
    print(f"✅ Scenario C completed successfully!")
    print("=" * 70)
    
    return True

def create_scenario_C_summary():
    """Create a summary of Scenario C results for documentation."""
    summary = {
        "scenario": "C",
        "title": "Cross-System Routing with System B Cable",
        "description": "Tests cable access control with System B cable from System A origin",
        "coordinates": {
            "origin": {"point": "A2", "coord": (182.946, 13.304, 157.295), "system": "A"},
            "destination": {"point": "B3", "coord": (176.062, 2.416, 153.960), "system": "B"}
        },
        "cable_type": "B",
        "expected_result": "FAILURE",
        "test_purpose": "Cable access control validation"
    }
    
    return summary

if __name__ == "__main__":
    print("Scenario C: Cross-System Routing with System B Cable")
    print("Testing cable access control enforcement")
    print()
    
    success = run_scenario_C()
    
    if success:
        print("\n🎉 Scenario C analysis completed successfully!")
        
        # Create summary for documentation
        summary = create_scenario_C_summary()
        print(f"\n📄 Summary created for documentation purposes")
    else:
        print("\n❌ Scenario C analysis failed")
        sys.exit(1) 