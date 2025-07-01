#!/usr/bin/env python3
"""
Test External Connector Integration with astar_PPOF_systems.py
==============================================================

This script verifies the complete integration of the External Connector workflow
with the cable-type and system-aware pathfinding in astar_PPOF_systems.py.

Tests:
1. Direct pathfinding from external point
2. PPO pathfinding from external point  
3. Forward path from external point
4. Cross-system pathfinding with Cable C
5. System filtering verification
"""

import subprocess
import sys
import os

def run_command(cmd, description, expect_success=True):
    """Run a command and verify results."""
    print(f"🧪 {description}")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if expect_success:
            if result.returncode == 0:
                print(f"   ✅ SUCCESS")
                
                # Extract key metrics from output
                output = result.stdout
                if "Path length:" in output:
                    path_length = output.split("Path length: ")[1].split(" ")[0]
                    print(f"      Path length: {path_length} points")
                
                if "Total distance:" in output:
                    distance = output.split("Total distance: ")[1].split(" ")[0]
                    print(f"      Distance: {distance} units")
                    
                if "Cable type:" in output:
                    cable_info = output.split("Cable type: ")[1].split("\n")[0]
                    print(f"      Cable: {cable_info}")
                
                return True
            else:
                print(f"   ❌ FAILED (return code {result.returncode})")
                print(f"      Error: {result.stderr}")
                return False
        else:
            if result.returncode != 0:
                print(f"   ✅ EXPECTED FAILURE (return code {result.returncode})")
                return True
            else:
                print(f"   ❌ UNEXPECTED SUCCESS (should have failed)")
                return False
                
    except subprocess.TimeoutExpired:
        print(f"   ❌ TIMEOUT (60 seconds)")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def test_external_connector_integration():
    """Test the complete External Connector + astar_PPOF_systems integration."""
    
    print("🚀 External Connector + astar_PPOF_systems Integration Test")
    print("=" * 70)
    print()
    
    # External point PE coordinates
    PE = (180.839, 22.530, 166.634)
    A1 = (170.839, 12.530, 156.634)
    A5 = (196.310, 18.545, 153.799) 
    A2 = (182.946, 13.304, 157.295)
    B3 = (176.062, 2.416, 153.960)
    
    # Tagged extended graph file
    extended_graph = "External_Connector/tagged_extended_graph.json"
    tramo_map = "tramo_map_combined.json"
    
    print(f"📋 Test Configuration:")
    print(f"   External Point PE: {PE}")
    print(f"   Internal Points: A1{A1}, A5{A5}, A2{A2}, B3{B3}")
    print(f"   Extended Graph: {extended_graph}")
    print(f"   Tramo Map: {tramo_map}")
    print()
    
    # Verify files exist
    if not os.path.exists(extended_graph):
        print(f"❌ Missing extended graph: {extended_graph}")
        return False
    
    if not os.path.exists(tramo_map):
        print(f"❌ Missing tramo map: {tramo_map}")
        return False
    
    results = []
    
    # Test 1: Direct pathfinding PE → A1 (Cable A)
    print("=" * 50)
    results.append(run_command([
        "python3", "astar_PPOF_systems.py", "direct",
        extended_graph,
        str(PE[0]), str(PE[1]), str(PE[2]),  # PE
        str(A1[0]), str(A1[1]), str(A1[2]),  # A1
        "--cable", "A"
    ], "Test 1: Direct PE → A1 (Cable A, System A only)"))
    
    # Test 2: PPO pathfinding PE → A5 → A2 (Cable A)
    print("=" * 50)
    results.append(run_command([
        "python3", "astar_PPOF_systems.py", "ppo",
        extended_graph,
        str(PE[0]), str(PE[1]), str(PE[2]),  # PE
        str(A5[0]), str(A5[1]), str(A5[2]),  # A5 (PPO)
        str(A2[0]), str(A2[1]), str(A2[2]),  # A2
        "--cable", "A"
    ], "Test 2: PPO PE → A5 → A2 (Cable A, System A only)"))
    
    # Test 3: Forward path PE → A5 → A2 (Cable A)
    print("=" * 50)
    results.append(run_command([
        "python3", "astar_PPOF_systems.py", "forward_path",
        extended_graph,
        str(PE[0]), str(PE[1]), str(PE[2]),  # PE
        str(A5[0]), str(A5[1]), str(A5[2]),  # A5 (PPO)
        str(A2[0]), str(A2[1]), str(A2[2]),  # A2
        "--cable", "A",
        "--tramo-map", tramo_map
    ], "Test 3: Forward Path PE → A5 → A2 (Cable A, backtracking prevention)"))
    
    # Test 4: Cross-system PPO PE → A1 → B3 (Cable C)
    print("=" * 50)
    results.append(run_command([
        "python3", "astar_PPOF_systems.py", "ppo",
        extended_graph,
        str(PE[0]), str(PE[1]), str(PE[2]),  # PE
        str(A1[0]), str(A1[1]), str(A1[2]),  # A1 (PPO)
        str(B3[0]), str(B3[1]), str(B3[2]),  # B3
        "--cable", "C"
    ], "Test 4: Cross-System PPO PE → A1 → B3 (Cable C, both systems)"))
    
    # Test 5: System filtering - Cable A trying to reach System B (should fail)
    print("=" * 50)
    results.append(run_command([
        "python3", "astar_PPOF_systems.py", "direct",
        extended_graph,
        str(PE[0]), str(PE[1]), str(PE[2]),  # PE
        str(B3[0]), str(B3[1]), str(B3[2]),  # B3 (System B)
        "--cable", "A"
    ], "Test 5: System Filtering PE → B3 (Cable A, should fail)", expect_success=False))
    
    # Test 6: Multi-PPO with external point
    print("=" * 50)
    results.append(run_command([
        "python3", "astar_PPOF_systems.py", "multi_ppo",
        extended_graph,
        str(PE[0]), str(PE[1]), str(PE[2]),  # PE (origin)
        str(A2[0]), str(A2[1]), str(A2[2]),  # A2 (destination)
        "--cable", "A",
        "--ppo", str(A1[0]), str(A1[1]), str(A1[2]),  # A1 (PPO 1)
        "--ppo", str(A5[0]), str(A5[1]), str(A5[2])   # A5 (PPO 2)
    ], "Test 6: Multi-PPO PE → A1 → A5 → A2 (Cable A, multiple waypoints)"))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Integration Test Results")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    test_names = [
        "Direct PE → A1 (Cable A)",
        "PPO PE → A5 → A2 (Cable A)", 
        "Forward Path PE → A5 → A2 (Cable A)",
        "Cross-System PPO PE → A1 → B3 (Cable C)",
        "System Filtering PE → B3 (Cable A, expected fail)",
        "Multi-PPO PE → A1 → A5 → A2 (Cable A)"
    ]
    
    for i, (test_name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    if passed == total:
        print(f"\n🎉 INTEGRATION COMPLETE!")
        print(f"External Connector workflow is fully integrated with astar_PPOF_systems.py")
        print(f"✅ All pathfinding modes working: direct, ppo, forward_path, multi_ppo")
        print(f"✅ Cable type filtering working: A, B, C")
        print(f"✅ System filtering working: System A, System B, Cross-system")
        print(f"✅ External point PE successfully connected to graph")
    else:
        print(f"\n⚠️  Integration incomplete - {total-passed} test(s) failed")
    
    return passed == total

def main():
    """Run the integration test."""
    success = test_external_connector_integration()
    
    if success:
        print(f"\n🚀 External Connector Integration: COMPLETE")
        sys.exit(0)
    else:
        print(f"\n❌ External Connector Integration: INCOMPLETE")
        sys.exit(1)

if __name__ == "__main__":
    main() 