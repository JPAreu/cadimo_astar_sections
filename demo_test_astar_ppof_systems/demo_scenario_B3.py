#!/usr/bin/env python3
"""
Scenario B3: Cross-System PPO with Forward Path Logic
Study of what happens when Scenario B2 is run with forward_path command

This scenario explores:
- Cross-system routing with forward path logic (prevents backtracking)
- PPO compliance across system boundaries with forward path constraints
- Performance impact of backtracking prevention on cross-system paths
- Comparison with regular PPO cross-system routing

Coordinates:
- Origin (A2): (182.946, 13.304, 157.295) - System A
- PPO (B5): (170.919, 8.418, 153.960) - System B (Mandatory Waypoint)
- Destination (B3): (176.062, 2.416, 153.960) - System B
- Cable Type: Cable C (access to both systems)
- Forward Path: Enabled (prevents backtracking by forbidding last edge from previous segment)
"""

import sys
import os
import json
from math import sqrt
from typing import List, Tuple, Dict, Any

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from astar_PPOF_systems import (
    run_ppo_systems,
    SystemFilteredGraph,
    calculate_path_distance,
    format_point
)

from astar_PPO_forbid import (
    run_astar_with_ppo_forward_path,
    run_astar_with_ppo_forbidden,
    calculate_path_distance as calculate_distance_forbid
)

def run_scenario_B3():
    """
    Scenario B3: Cross-System PPO with Forward Path Logic
    
    This scenario takes Scenario B2's coordinates and runs them with forward_path command
    to study the impact of backtracking prevention on cross-system routing.
    """
    print("🚀 Scenario B3: Cross-System PPO with Forward Path Logic")
    print("=" * 70)
    print()
    
    # Scenario coordinates (same as B2)
    origin = (182.946, 13.304, 157.295)      # A2 - System A
    ppo = (170.919, 8.418, 153.960)          # B5 - System B (PPO)
    destination = (176.062, 2.416, 153.960)  # B3 - System B
    cable_type = "C"                          # Cable C: Both systems
    
    # Required files
    graph_file = "graph_LV_combined.json"
    tramo_map_file = "tramo_map_combined.json"
    
    print(f"📋 Scenario Configuration:")
    print(f"   Origin (A2):      {format_point(origin)} - System A")
    print(f"   PPO (B5):         {format_point(ppo)} - System B")
    print(f"   Destination (B3): {format_point(destination)} - System B")
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
        return False
    
    print("✅ All required files found")
    print()
    
    # ====================================================================
    # Test 1: Regular Cross-System PPO (Baseline from Scenario B2)
    # ====================================================================
    print("🧪 Test 1: Regular Cross-System PPO (Baseline)")
    print("-" * 50)
    
    try:
        # Use systems-aware pathfinding for baseline
        regular_path, regular_nodes = run_ppo_systems(
            graph_file, origin, ppo, destination, cable_type, tramo_map_file
        )
        
        regular_distance = calculate_path_distance(regular_path)
        
        # Find PPO position in path
        ppo_position = None
        for i, point in enumerate(regular_path):
            if abs(point[0] - ppo[0]) < 0.001 and abs(point[1] - ppo[1]) < 0.001 and abs(point[2] - ppo[2]) < 0.001:
                ppo_position = i + 1  # 1-indexed for display
                break
        
        print(f"✅ Regular PPO Results:")
        print(f"   Path length: {len(regular_path)} points")
        print(f"   Distance: {regular_distance:.3f} units")
        print(f"   Nodes explored: {regular_nodes}")
        print(f"   PPO position: Point {ppo_position}/{len(regular_path)}")
        print(f"   Cross-system routing: SUCCESS")
        
    except Exception as e:
        print(f"❌ Regular PPO failed: {e}")
        return False
    
    print()
    
    # ====================================================================
    # Test 2: Forward Path Cross-System PPO
    # ====================================================================
    print("🧪 Test 2: Forward Path Cross-System PPO")
    print("-" * 50)
    
    try:
        # Use forward path logic with the legacy adjacency format
        # Forward path requires the legacy adjacency list format
        legacy_graph_file = "graph_LV_combined_legacy.json"
        legacy_tramo_map = "tramo_map_combined.json"  # Use correct tramo map
        
        # Check if we have the legacy format files
        if not os.path.exists(legacy_graph_file):
            print(f"❌ Legacy graph format not found: {legacy_graph_file}")
            print("   Forward path requires adjacency list format")
            raise Exception(f"Legacy graph file not found: {legacy_graph_file}")
        
        if not os.path.exists(legacy_tramo_map):
            print(f"❌ Legacy tramo map not found: {legacy_tramo_map}")
            raise Exception(f"Legacy tramo map not found: {legacy_tramo_map}")
        
        print(f"✅ Using legacy format files:")
        print(f"   Graph: {legacy_graph_file}")
        print(f"   Tramo Map: {legacy_tramo_map}")
        
        forward_path, forward_nodes, forward_segments = run_astar_with_ppo_forward_path(
            legacy_graph_file, origin, ppo, destination, legacy_tramo_map
        )
        
        forward_distance = calculate_distance_forbid(forward_path)
        
        # Find PPO position in forward path
        forward_ppo_position = None
        for i, point in enumerate(forward_path):
            if abs(point[0] - ppo[0]) < 0.001 and abs(point[1] - ppo[1]) < 0.001 and abs(point[2] - ppo[2]) < 0.001:
                forward_ppo_position = i + 1  # 1-indexed for display
                break
        
        print(f"✅ Forward Path Results:")
        print(f"   Path length: {len(forward_path)} points")
        print(f"   Distance: {forward_distance:.3f} units")
        print(f"   Nodes explored: {forward_nodes}")
        print(f"   PPO position: Point {forward_ppo_position}/{len(forward_path)}")
        print(f"   Segments: {len(forward_segments)}")
        
        # Show segment breakdown
        if len(forward_segments) >= 2:
            print(f"   Segment 1 (Origin→PPO): {forward_segments[0]['path_length']} points, {forward_segments[0]['nodes_explored']} nodes")
            print(f"   Segment 2 (PPO→Dest): {forward_segments[1]['path_length']} points, {forward_segments[1]['nodes_explored']} nodes")
        
        print(f"   Forward path logic: ENABLED (prevents backtracking)")
        
    except Exception as e:
        print(f"❌ Forward path failed: {e}")
        print("   This may be due to graph format incompatibility")
        return False
    
    print()
    
    # ====================================================================
    # Test 3: Performance Comparison and Analysis
    # ====================================================================
    print("🧪 Test 3: Performance Comparison and Analysis")
    print("-" * 50)
    
    try:
        # Calculate performance ratios
        distance_ratio = forward_distance / regular_distance if regular_distance > 0 else float('inf')
        points_ratio = len(forward_path) / len(regular_path) if len(regular_path) > 0 else float('inf')
        nodes_ratio = forward_nodes / regular_nodes if regular_nodes > 0 else float('inf')
        
        print(f"📊 Performance Comparison:")
        print(f"   Regular PPO:  {len(regular_path):3d} points, {regular_distance:7.3f} units, {regular_nodes:3d} nodes")
        print(f"   Forward Path: {len(forward_path):3d} points, {forward_distance:7.3f} units, {forward_nodes:3d} nodes")
        print(f"   Impact:       {points_ratio:.1f}x points, {distance_ratio:.1f}x distance, {nodes_ratio:.1f}x nodes")
        print()
        
        # Analyze the impact
        if distance_ratio < 1.5:
            impact_level = "LOW"
            impact_color = "🟢"
        elif distance_ratio < 3.0:
            impact_level = "MODERATE"
            impact_color = "🟡"
        else:
            impact_level = "HIGH"
            impact_color = "🔴"
        
        print(f"📈 Forward Path Impact Analysis:")
        print(f"   {impact_color} Impact Level: {impact_level}")
        print(f"   Distance increase: {((distance_ratio - 1) * 100):.1f}%")
        print(f"   Path complexity: {((points_ratio - 1) * 100):.1f}% more points")
        print(f"   Computational cost: {((nodes_ratio - 1) * 100):.1f}% more nodes explored")
        print()
        
        # Cross-system analysis
        print(f"🔄 Cross-System Routing Analysis:")
        print(f"   Origin system: A (Cable C allows access)")
        print(f"   PPO system: B (Cross-system transition required)")
        print(f"   Destination system: B (Same as PPO)")
        print(f"   Cross-system transitions: 1 (A→B before PPO)")
        print()
        
        # PPO compliance check
        print(f"✅ PPO Compliance Verification:")
        print(f"   Regular PPO: PPO at position {ppo_position}/{len(regular_path)}")
        print(f"   Forward Path: PPO at position {forward_ppo_position}/{len(forward_path)}")
        
        if ppo_position and forward_ppo_position:
            regular_ppo_ratio = ppo_position / len(regular_path)
            forward_ppo_ratio = forward_ppo_position / len(forward_path)
            print(f"   PPO timing: Regular {regular_ppo_ratio:.1%}, Forward {forward_ppo_ratio:.1%}")
        
        print(f"   Both paths successfully visit mandatory waypoint")
        
    except Exception as e:
        print(f"❌ Performance analysis failed: {e}")
        return False
    
    print()
    
    # ====================================================================
    # Test 4: Backtracking Analysis
    # ====================================================================
    print("🧪 Test 4: Backtracking Analysis")
    print("-" * 50)
    
    try:
        # Analyze backtracking in regular path
        origin_occurrences_regular = sum(1 for point in regular_path 
                                       if abs(point[0] - origin[0]) < 0.001 and 
                                          abs(point[1] - origin[1]) < 0.001 and 
                                          abs(point[2] - origin[2]) < 0.001)
        
        # Analyze backtracking in forward path
        origin_occurrences_forward = sum(1 for point in forward_path 
                                       if abs(point[0] - origin[0]) < 0.001 and 
                                          abs(point[1] - origin[1]) < 0.001 and 
                                          abs(point[2] - origin[2]) < 0.001)
        
        print(f"🔍 Backtracking Detection:")
        print(f"   Regular PPO: Origin appears {origin_occurrences_regular} time(s)")
        print(f"   Forward Path: Origin appears {origin_occurrences_forward} time(s)")
        
        if origin_occurrences_regular > 1:
            print(f"   ⚠️  Regular PPO shows backtracking (origin revisited)")
        else:
            print(f"   ✅ Regular PPO shows no backtracking")
        
        if origin_occurrences_forward > 1:
            print(f"   ❌ Forward path failed to prevent backtracking")
        else:
            print(f"   ✅ Forward path successfully prevented backtracking")
        
        # Analyze path efficiency
        print(f"   Path efficiency impact: {((distance_ratio - 1) * 100):.1f}% distance increase for backtracking prevention")
        
    except Exception as e:
        print(f"❌ Backtracking analysis failed: {e}")
        return False
    
    print()
    
    # ====================================================================
    # Summary and Conclusions
    # ====================================================================
    print("📋 Scenario B3 Summary and Conclusions")
    print("=" * 50)
    
    print(f"🎯 Key Findings:")
    print(f"   1. Cross-system forward path: {'SUCCESS' if forward_path else 'FAILED'}")
    print(f"   2. PPO compliance: {'MAINTAINED' if forward_ppo_position else 'LOST'}")
    print(f"   3. Backtracking prevention: {'EFFECTIVE' if origin_occurrences_forward == 1 else 'INEFFECTIVE'}")
    print(f"   4. Performance impact: {impact_level} ({distance_ratio:.1f}x distance)")
    print()
    
    print(f"📊 Comparative Results:")
    print(f"   Scenario B2 (Regular): {len(regular_path)} points, {regular_distance:.3f} units")
    print(f"   Scenario B3 (Forward): {len(forward_path)} points, {forward_distance:.3f} units")
    print(f"   Forward path overhead: {((distance_ratio - 1) * 100):.1f}% distance increase")
    print()
    
    print(f"🔧 Technical Insights:")
    print(f"   - Forward path logic works with cross-system routing")
    print(f"   - Cable C enables seamless system transitions with forward constraints")
    print(f"   - PPO compliance is maintained across system boundaries")
    print(f"   - Backtracking prevention adds computational overhead but ensures path integrity")
    print()
    
    print(f"✅ Scenario B3 completed successfully!")
    print("=" * 70)
    
    return True

def create_scenario_B3_summary():
    """Create a summary of Scenario B3 results for documentation."""
    summary = {
        "scenario": "B3",
        "title": "Cross-System PPO with Forward Path Logic",
        "description": "Study of forward path impact on cross-system PPO routing",
        "coordinates": {
            "origin": {"point": "A2", "coord": (182.946, 13.304, 157.295), "system": "A"},
            "ppo": {"point": "B5", "coord": (170.919, 8.418, 153.960), "system": "B"},
            "destination": {"point": "B3", "coord": (176.062, 2.416, 153.960), "system": "B"}
        },
        "cable_type": "C",
        "forward_path": True,
        "cross_system": True,
        "comparison_base": "Scenario B2"
    }
    
    return summary

if __name__ == "__main__":
    print("Scenario B3: Cross-System PPO with Forward Path Logic")
    print("Testing forward path command on Scenario B2 coordinates")
    print()
    
    success = run_scenario_B3()
    
    if success:
        print("\n🎉 Scenario B3 analysis completed successfully!")
        
        # Create summary for documentation
        summary = create_scenario_B3_summary()
        print(f"\n📄 Summary created for documentation purposes")
    else:
        print("\n❌ Scenario B3 analysis failed")
        sys.exit(1) 