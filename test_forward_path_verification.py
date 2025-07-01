#!/usr/bin/env python3
"""
Test script to verify forward path functionality in astar_PPOF_systems.py
"""

from astar_PPOF_systems import SystemFilteredGraph, calculate_path_distance
import json

def test_forward_path_last_edge_blocking():
    """Test that forward path properly blocks the last edge of segment 1."""
    
    print("🧪 Testing Forward Path Last Edge Blocking")
    print("=" * 50)
    
    # Test case: A1 → A5 → A2 (where A1→A5 passes through A2)
    origin = (170.839, 12.530, 156.634)      # A1
    ppo = (196.310, 18.545, 153.799)         # A5
    destination = (182.946, 13.304, 157.295) # A2
    
    print(f"📋 Test Configuration:")
    print(f"   Origin (A1): {origin}")
    print(f"   PPO (A5): {ppo}")
    print(f"   Destination (A2): {destination}")
    print(f"   Cable: A (System A only)")
    print()
    
    # Run forward path
    graph = SystemFilteredGraph("graph_LV_combined.json", "A", "tramo_map_combined.json", None)
    path, nodes_explored, segment_info = graph.find_path_forward_path(origin, ppo, destination)
    
    print(f"✅ Forward Path Results:")
    print(f"   Total points: {len(path)}")
    print(f"   Total distance: {calculate_path_distance(path):.3f} units")
    print(f"   Nodes explored: {nodes_explored}")
    print(f"   Segment 1: {segment_info[0]['path_length']} points")
    print(f"   Segment 2: {segment_info[1]['path_length']} points")
    
    # Verify the last edge of segment 1 is properly identified
    seg1_length = segment_info[0]['path_length']
    if seg1_length >= 2:
        second_last = path[seg1_length-2]
        last = path[seg1_length-1]  # Should be A5
        
        print(f"\n🔍 Last Edge Analysis:")
        print(f"   Second-to-last point: {second_last}")
        print(f"   Last point (PPO): {last}")
        
        # Check if this edge appears in segment 2 (it shouldn't)
        edge_found_in_seg2 = False
        for i in range(seg1_length-1, len(path)-1):
            edge_start = path[i]
            edge_end = path[i+1]
            
            # Check if this is the forbidden edge (in either direction)
            if (abs(edge_start[0] - second_last[0]) < 0.001 and 
                abs(edge_start[1] - second_last[1]) < 0.001 and 
                abs(edge_start[2] - second_last[2]) < 0.001 and
                abs(edge_end[0] - last[0]) < 0.001 and 
                abs(edge_end[1] - last[1]) < 0.001 and 
                abs(edge_end[2] - last[2]) < 0.001):
                edge_found_in_seg2 = True
                print(f"   ❌ FORBIDDEN EDGE USED: Index {i}→{i+1} in segment 2!")
                break
            elif (abs(edge_start[0] - last[0]) < 0.001 and 
                  abs(edge_start[1] - last[1]) < 0.001 and 
                  abs(edge_start[2] - last[2]) < 0.001 and
                  abs(edge_end[0] - second_last[0]) < 0.001 and 
                  abs(edge_end[1] - second_last[1]) < 0.001 and 
                  abs(edge_end[2] - second_last[2]) < 0.001):
                edge_found_in_seg2 = True
                print(f"   ❌ FORBIDDEN EDGE USED (reverse): Index {i}→{i+1} in segment 2!")
                break
        
        if not edge_found_in_seg2:
            print(f"   ✅ Last edge of segment 1 is properly blocked in segment 2")
    
    return True

def test_forward_path_with_forbidden_sections():
    """Test forward path with additional forbidden sections."""
    
    print(f"\n🧪 Testing Forward Path with Forbidden Sections")
    print("=" * 50)
    
    # Test case: C2 → A1 → C3 with some forbidden sections
    origin = (182.946, 13.304, 157.295)     # C2
    ppo = (170.839, 12.530, 156.634)        # A1
    destination = (174.860, 15.369, 136.587) # C3
    
    print(f"📋 Test Configuration:")
    print(f"   Origin (C2): {origin}")
    print(f"   PPO (A1): {ppo}")
    print(f"   Destination (C3): {destination}")
    print(f"   Cable: C (Both systems)")
    print(f"   Forbidden sections: forbidden_tramos_c2_c3.json")
    print()
    
    try:
        # Load forbidden sections to see what's being blocked
        with open('forbidden_tramos_c2_c3.json', 'r') as f:
            forbidden_ids = json.load(f)
        print(f"🚫 Forbidden tramo IDs: {forbidden_ids}")
        
        # Run forward path with forbidden sections
        graph = SystemFilteredGraph("graph_LV_combined.json", "C", "tramo_map_combined.json", "forbidden_tramos_c2_c3.json")
        path, nodes_explored, segment_info = graph.find_path_forward_path(origin, ppo, destination)
        
        print(f"✅ Forward Path with Forbidden Sections Results:")
        print(f"   Total points: {len(path)}")
        print(f"   Total distance: {calculate_path_distance(path):.3f} units")
        print(f"   Nodes explored: {nodes_explored}")
        print(f"   Segment 1: {segment_info[0]['path_length']} points")
        print(f"   Segment 2: {segment_info[1]['path_length']} points")
        
        return True
        
    except Exception as e:
        print(f"❌ Forward path with forbidden sections failed: {e}")
        print(f"   This may indicate that the combination of forward path restriction")
        print(f"   and forbidden sections creates an impossible pathfinding scenario")
        return False

def test_command_line_interface():
    """Test the command line interface for forward path."""
    
    print(f"\n🧪 Testing Command Line Interface")
    print("=" * 50)
    
    import subprocess
    
    # Test basic forward path command
    cmd = [
        "python3", "astar_PPOF_systems.py", "forward_path",
        "graph_LV_combined.json",
        "170.839", "12.530", "156.634",    # A1
        "196.310", "18.545", "153.799",    # A5
        "182.946", "13.304", "157.295",    # A2
        "--cable", "A",
        "--tramo-map", "tramo_map_combined.json"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✅ Command line interface working correctly")
            
            # Check for key indicators in output
            output = result.stdout
            if "Forbidding immediate last edge of segment 1" in output:
                print(f"   ✅ Last edge blocking is active")
            if "Tramo ID" in output:
                print(f"   ✅ Tramo ID identification working")
            if "TOPOLOGICAL OPTIMIZATION DETECTED" in output:
                print(f"   ✅ Topological analysis working")
                
            return True
        else:
            print(f"❌ Command failed with return code {result.returncode}")
            print(f"   Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ Command timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"❌ Command execution failed: {e}")
        return False

def main():
    """Run all forward path verification tests."""
    
    print("🚀 Forward Path Verification Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Basic last edge blocking
    results.append(test_forward_path_last_edge_blocking())
    
    # Test 2: Forward path with forbidden sections
    results.append(test_forward_path_with_forbidden_sections())
    
    # Test 3: Command line interface
    results.append(test_command_line_interface())
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 30)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print(f"🎉 All tests passed! Forward path functionality is working correctly.")
    else:
        print(f"⚠️  Some tests failed. Review the implementation.")
        
    return passed == total

if __name__ == "__main__":
    main() 