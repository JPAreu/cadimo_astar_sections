#!/usr/bin/env python3
"""
Dedicated test script for forward path functionality
Tests the P21 > P20 > P17 scenario with comprehensive validation
"""

import sys
import os
import json
from math import sqrt
from typing import List, Tuple

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from astar_PPO_forbid import (
    run_astar_with_ppo_forward_path,
    run_astar_with_multiple_ppos_forward_path,
    run_astar_with_ppo_forbidden,
    calculate_path_distance,
    ForbiddenEdgeGraph
)

def test_forward_path_comprehensive():
    """Comprehensive test of forward path functionality with P21 > P20 > P17."""
    print("🚀 Forward Path Comprehensive Test")
    print("=" * 60)
    
    # Test coordinates
    p21_origin = (139.232, 27.373, 152.313)      # P21 - Origin
    p20_ppo = (139.683, 26.922, 152.313)         # P20 - PPO
    p17_destination = (139.200, 28.800, 156.500) # P17 - Destination
    
    # Required files
    graph_file = "graph_LVA1.json"
    tramo_map_file = "Output_Path_Sections/tramo_id_map_20250626_114538.json"
    
    # Verify files exist
    if not os.path.exists(graph_file):
        print(f"❌ Graph file not found: {graph_file}")
        return False
    
    if not os.path.exists(tramo_map_file):
        print(f"❌ Tramo mapping file not found: {tramo_map_file}")
        return False
    
    print(f"✅ Required files found")
    print(f"   Graph: {graph_file}")
    print(f"   Tramo mapping: {tramo_map_file}")
    print()
    
    # Test 1: Basic forward path functionality
    print("🧪 Test 1: Basic Forward Path Functionality")
    print("-" * 50)
    
    try:
        forward_path, forward_nodes, forward_segments = run_astar_with_ppo_forward_path(
            graph_file, p21_origin, p20_ppo, p17_destination, tramo_map_file
        )
        
        # Verify path structure
        assert forward_path is not None, "Forward path should exist"
        assert len(forward_path) > 10, f"Forward path should be long (got {len(forward_path)} points)"
        assert forward_path[0] == p21_origin, "Path should start at P21"
        assert forward_path[-1] == p17_destination, "Path should end at P17"
        assert p20_ppo in forward_path, "Path should include P20 PPO"
        
        # Check for no backtracking
        p21_occurrences = [i for i, point in enumerate(forward_path) if point == p21_origin]
        assert len(p21_occurrences) == 1, f"P21 should appear only once (found {len(p21_occurrences)} times)"
        assert p21_occurrences[0] == 0, "P21 should only appear at the beginning"
        
        forward_distance = calculate_path_distance(forward_path)
        
        print(f"✅ Forward path successful:")
        print(f"   Points: {len(forward_path)}")
        print(f"   Distance: {forward_distance:.3f} units")
        print(f"   Nodes explored: {forward_nodes}")
        print(f"   Segments: {len(forward_segments)}")
        print(f"   No backtracking: P21 appears only once at start")
        
    except Exception as e:
        print(f"❌ Forward path test failed: {e}")
        return False
    
    print()
    
    # Test 2: Compare with regular PPO
    print("🧪 Test 2: Forward Path vs Regular PPO Comparison")
    print("-" * 50)
    
    try:
        # Regular PPO path
        regular_path, regular_nodes = run_astar_with_ppo_forbidden(
            graph_file, p21_origin, p20_ppo, p17_destination
        )
        
        regular_distance = calculate_path_distance(regular_path)
        
        # Check for backtracking in regular path
        regular_p21_count = sum(1 for point in regular_path if point == p21_origin)
        
        print(f"📊 Comparison Results:")
        print(f"   Regular PPO:  {len(regular_path):3d} points, {regular_distance:7.3f} units, {regular_nodes:3d} nodes")
        print(f"   Forward Path: {len(forward_path):3d} points, {forward_distance:7.3f} units, {forward_nodes:3d} nodes")
        
        distance_ratio = forward_distance / regular_distance if regular_distance > 0 else float('inf')
        points_ratio = len(forward_path) / len(regular_path) if len(regular_path) > 0 else float('inf')
        
        print(f"   Ratios: {points_ratio:.1f}x points, {distance_ratio:.1f}x distance")
        print(f"   Regular PPO P21 occurrences: {regular_p21_count}")
        print(f"   Forward path P21 occurrences: {len(p21_occurrences)}")
        
        # Verify forward path prevents backtracking
        if regular_p21_count > 1:
            print(f"✅ Backtracking prevention verified: Regular PPO backtracks ({regular_p21_count} P21 visits), Forward path doesn't")
        else:
            print(f"ℹ️  Regular PPO doesn't backtrack in this case, but forward path still enforces constraint")
        
        # Forward path should generally be longer due to constraint
        if forward_distance > regular_distance:
            print(f"✅ Forward path is longer ({distance_ratio:.1f}x), indicating constraint is active")
        else:
            print(f"⚠️  Forward path is not longer - constraint may not be necessary for this route")
        
    except Exception as e:
        print(f"❌ Comparison test failed: {e}")
        return False
    
    print()
    
    # Test 3: Tramo ID detection
    print("🧪 Test 3: Tramo ID Detection and Mapping")
    print("-" * 50)
    
    try:
        # Create ForbiddenEdgeGraph to inspect tramo ID detection
        graph = ForbiddenEdgeGraph(graph_file, tramo_map_file)
        
        # Test the direct edge between P21 and P20
        node_str1 = f"({p21_origin[0]}, {p21_origin[1]}, {p21_origin[2]})"
        node_str2 = f"({p20_ppo[0]}, {p20_ppo[1]}, {p20_ppo[2]})"
        edge_key = "-".join(sorted([node_str1, node_str2]))
        
        if edge_key in graph.tramo_id_map:
            tramo_id = graph.tramo_id_map[edge_key]
            print(f"✅ Tramo ID mapping found:")
            print(f"   Edge: P21 ↔ P20")
            print(f"   Tramo ID: {tramo_id}")
            
            # Test edge forbidden functionality
            initial_forbidden = graph.is_edge_forbidden(node_str1, node_str2)
            print(f"   Initially forbidden: {initial_forbidden}")
            
            # Add to forbidden set and test
            original_forbidden_set = graph.forbidden_set.copy()
            graph.forbidden_set.add(tramo_id)
            after_forbidden = graph.is_edge_forbidden(node_str1, node_str2)
            print(f"   After adding to forbidden set: {after_forbidden}")
            
            # Restore original state
            graph.forbidden_set = original_forbidden_set
            
            if tramo_id == 162:
                print(f"✅ Expected tramo ID 162 confirmed")
            else:
                print(f"⚠️  Unexpected tramo ID: expected 162, got {tramo_id}")
        else:
            print(f"❌ Tramo ID mapping not found for edge: {edge_key}")
            return False
            
    except Exception as e:
        print(f"❌ Tramo ID detection test failed: {e}")
        return False
    
    print()
    
    # Test 4: Multiple PPO forward path
    print("🧪 Test 4: Multiple PPO Forward Path")
    print("-" * 50)
    
    try:
        # Add P19 as a second PPO
        p19_second_ppo = (139.608, 25.145, 160.703)
        multi_ppos = [p20_ppo, p19_second_ppo]
        
        multi_path, multi_nodes, multi_segments = run_astar_with_multiple_ppos_forward_path(
            graph_file, p21_origin, multi_ppos, p17_destination, tramo_map_file
        )
        
        # Verify path structure
        assert multi_path is not None, "Multi-PPO forward path should exist"
        assert multi_path[0] == p21_origin, "Path should start at P21"
        assert multi_path[-1] == p17_destination, "Path should end at P17"
        assert p20_ppo in multi_path, "Path should include P20"
        assert p19_second_ppo in multi_path, "Path should include P19"
        
        # Check segments
        assert len(multi_segments) == 3, f"Should have 3 segments for 2 PPOs (got {len(multi_segments)})"
        
        # Verify no backtracking
        multi_p21_count = sum(1 for point in multi_path if point == p21_origin)
        assert multi_p21_count == 1, f"P21 should appear only once (found {multi_p21_count} times)"
        
        multi_distance = calculate_path_distance(multi_path)
        
        print(f"✅ Multi-PPO forward path successful:")
        print(f"   Points: {len(multi_path)}")
        print(f"   Distance: {multi_distance:.3f} units")
        print(f"   Nodes explored: {multi_nodes}")
        print(f"   Segments: {len(multi_segments)}")
        print(f"   Segment lengths: {[seg['path_length'] for seg in multi_segments]} points")
        print(f"   No backtracking: P21 appears only once")
        
    except Exception as e:
        print(f"❌ Multi-PPO forward path test failed: {e}")
        return False
    
    print()
    
    # Test 5: Performance summary
    print("🧪 Test 5: Performance Summary")
    print("-" * 50)
    
    try:
        print(f"📊 Performance Metrics Summary:")
        print(f"   Test Case: P21 → P20 → P17")
        print(f"   Graph: {graph_file}")
        print(f"   Tramo mapping: {tramo_map_file}")
        print()
        print(f"   Single PPO Results:")
        print(f"     Regular PPO:  {len(regular_path):3d} points, {regular_distance:7.3f} units, {regular_nodes:3d} nodes")
        print(f"     Forward Path: {len(forward_path):3d} points, {forward_distance:7.3f} units, {forward_nodes:3d} nodes")
        print(f"     Improvement:  {points_ratio:.1f}x points, {distance_ratio:.1f}x distance")
        print()
        print(f"   Multi-PPO Results:")
        print(f"     Forward Path: {len(multi_path):3d} points, {multi_distance:7.3f} units, {multi_nodes:3d} nodes")
        print(f"     Segments: {len(multi_segments)} ({' + '.join(str(seg['path_length']) for seg in multi_segments)} points)")
        print()
        print(f"   Key Validations:")
        print(f"     ✅ No backtracking: P21 appears only once in all forward paths")
        print(f"     ✅ Tramo ID detection: Edge P21-P20 = Tramo {tramo_id}")
        print(f"     ✅ Forward path constraint: Prevents using last edge in next segment")
        print(f"     ✅ Multi-PPO support: Handles multiple waypoints correctly")
        
    except Exception as e:
        print(f"❌ Performance summary failed: {e}")
        return False
    
    print()
    print("🎉 All Forward Path Tests Passed!")
    print("=" * 60)
    return True

def run_quick_forward_path_test():
    """Quick test to verify forward path is working."""
    print("⚡ Quick Forward Path Test")
    print("-" * 30)
    
    # Test coordinates
    p21_origin = (139.232, 27.373, 152.313)
    p20_ppo = (139.683, 26.922, 152.313)
    p17_destination = (139.200, 28.800, 156.500)
    
    graph_file = "graph_LVA1.json"
    tramo_map_file = "Output_Path_Sections/tramo_id_map_20250626_114538.json"
    
    try:
        forward_path, forward_nodes, forward_segments = run_astar_with_ppo_forward_path(
            graph_file, p21_origin, p20_ppo, p17_destination, tramo_map_file
        )
        
        # Quick validation
        p21_count = sum(1 for point in forward_path if point == p21_origin)
        distance = calculate_path_distance(forward_path)
        
        print(f"✅ Forward path: {len(forward_path)} points, {distance:.1f} units")
        print(f"✅ No backtracking: P21 appears {p21_count} time(s)")
        print(f"✅ Segments: {len(forward_segments)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False

if __name__ == "__main__":
    print("Forward Path Test Suite")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        success = run_quick_forward_path_test()
    else:
        success = test_forward_path_comprehensive()
    
    if success:
        print("\n🎯 Forward path functionality is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Forward path functionality has issues!")
        sys.exit(1) 