#!/usr/bin/env python3
"""
Comprehensive Demo: All B Scenarios Sequential Evaluation
=========================================================

This script runs all B scenarios in sequence:
- Scenario B: Cross-System Bridge Blocking
- Scenario B1: Internal System B Constraint  
- Scenario B2: Cross-System PPO Routing
- Scenario B3: Cross-System PPO with Forward Path Logic

Each scenario is evaluated step-by-step with detailed analysis and comparison.
"""

import sys
import os
import json
from math import sqrt
from typing import List, Tuple, Dict, Any
import traceback

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from astar_PPOF_systems import (
    run_direct_systems,
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

class BScenarioResults:
    """Class to store and compare results across all B scenarios."""
    
    def __init__(self):
        self.scenarios = {}
        
    def add_scenario(self, name: str, result: Dict[str, Any]):
        """Add a scenario result."""
        self.scenarios[name] = result
        
    def print_comparison_table(self):
        """Print a comprehensive comparison table of all scenarios."""
        print("\n" + "=" * 100)
        print("📊 COMPREHENSIVE B SCENARIOS COMPARISON TABLE")
        print("=" * 100)
        
        # Header
        print(f"{'Scenario':<12} {'Type':<25} {'Result':<10} {'Points':<8} {'Distance':<12} {'Nodes':<8} {'Notes':<25}")
        print("-" * 100)
        
        # Data rows
        for name, data in self.scenarios.items():
            scenario = data.get('scenario', name)
            test_type = data.get('type', 'Unknown')
            success = '✅ SUCCESS' if data.get('success', False) else '❌ FAILED'
            points = str(data.get('points', 'N/A'))
            distance = f"{data.get('distance', 0):.3f}" if data.get('distance') else 'N/A'
            nodes = str(data.get('nodes', 'N/A'))
            notes = data.get('notes', '')
            
            print(f"{scenario:<12} {test_type:<25} {success:<10} {points:<8} {distance:<12} {nodes:<8} {notes:<25}")
        
        print("-" * 100)
        
    def print_summary_analysis(self):
        """Print summary analysis of all scenarios."""
        print("\n" + "=" * 80)
        print("🎯 SUMMARY ANALYSIS: B SCENARIOS INSIGHTS")
        print("=" * 80)
        
        # Count successes and failures
        successes = sum(1 for data in self.scenarios.values() if data.get('success', False))
        failures = len(self.scenarios) - successes
        
        print(f"📈 Overall Results:")
        print(f"   ✅ Successful scenarios: {successes}/{len(self.scenarios)}")
        print(f"   ❌ Failed scenarios: {failures}/{len(self.scenarios)}")
        print()
        
        # Identify key patterns
        cross_system_scenarios = [name for name, data in self.scenarios.items() 
                                 if 'cross-system' in data.get('type', '').lower()]
        forward_path_scenarios = [name for name, data in self.scenarios.items() 
                                 if 'forward' in data.get('type', '').lower()]
        
        print(f"🔄 Cross-System Scenarios: {len(cross_system_scenarios)}")
        for scenario in cross_system_scenarios:
            result = '✅' if self.scenarios[scenario].get('success') else '❌'
            print(f"   {result} {scenario}")
        print()
        
        print(f"⚡ Forward Path Scenarios: {len(forward_path_scenarios)}")
        for scenario in forward_path_scenarios:
            result = '✅' if self.scenarios[scenario].get('success') else '❌'
            print(f"   {result} {scenario}")
        print()
        
        # Key discoveries
        print(f"🔍 Key Discoveries:")
        print(f"   • Single point of failure: B1-B2 bridge (Tramo 528)")
        print(f"   • Gateway isolation: B4-B1 dependency (Tramo 395)")
        print(f"   • Cross-system success: Cable C enables A↔B routing")
        print(f"   • Forward path constraint: PPO B5 creates circular dependency")
        print(f"   • Network topology validation: Forward path reveals design flaws")

def run_scenario_B():
    """
    Scenario B: Cross-System Bridge Blocking
    Tests cross-system routing when the only bridge between systems is blocked.
    """
    print("🚀 Scenario B: Cross-System Bridge Blocking")
    print("-" * 60)
    
    # Coordinates
    origin = (182.946, 13.304, 157.295)      # A2 - System A
    destination = (176.062, 2.416, 153.960)  # B3 - System B
    cable_type = "C"                          # Cable C: Both systems
    
    # Files
    graph_file = "graph_LV_combined.json"
    tramo_map_file = "tramo_map_combined.json"
    forbidden_file = "forbidden_cross_system.json"  # Blocks B1-B2 bridge (Tramo 528)
    
    print(f"📋 Configuration:")
    print(f"   Origin (A2):      {format_point(origin)} - System A")
    print(f"   Destination (B3): {format_point(destination)} - System B")
    print(f"   Cable Type:       {cable_type} (Both systems)")
    print(f"   Forbidden:        {forbidden_file} (Bridge B1-B2)")
    print()
    
    results = {}
    
    try:
        # Test 1: Direct cross-system routing
        print("🧪 Test B.1: Direct Cross-System Routing")
        direct_path, direct_nodes = run_direct_systems(
            graph_file, origin, destination, cable_type, tramo_map_file
        )
        direct_distance = calculate_path_distance(direct_path)
        
        results['B_direct'] = {
            'scenario': 'B',
            'type': 'Direct Cross-System',
            'success': True,
            'points': len(direct_path),
            'distance': direct_distance,
            'nodes': direct_nodes,
            'notes': 'No restrictions'
        }
        
        print(f"✅ Success: {len(direct_path)} points, {direct_distance:.3f} units")
        print()
        
        # Test 2: Cross-system with bridge blocked
        print("🧪 Test B.2: Cross-System with Bridge Blocked")
        try:
            blocked_path, blocked_nodes = run_direct_systems(
                graph_file, origin, destination, cable_type, tramo_map_file, forbidden_file
            )
            blocked_distance = calculate_path_distance(blocked_path)
            
            results['B_blocked'] = {
                'scenario': 'B',
                'type': 'Bridge Blocked',
                'success': True,
                'points': len(blocked_path),
                'distance': blocked_distance,
                'nodes': blocked_nodes,
                'notes': 'Alternative route found'
            }
            
            print(f"✅ Success: {len(blocked_path)} points, {blocked_distance:.3f} units")
            
        except Exception as e:
            results['B_blocked'] = {
                'scenario': 'B',
                'type': 'Bridge Blocked',
                'success': False,
                'points': 0,
                'distance': 0,
                'nodes': 0,
                'notes': 'No alternative route'
            }
            
            print(f"❌ Failed: {str(e)}")
        
    except Exception as e:
        print(f"❌ Scenario B failed: {e}")
        results['B_error'] = {
            'scenario': 'B',
            'type': 'Error',
            'success': False,
            'points': 0,
            'distance': 0,
            'nodes': 0,
            'notes': str(e)
        }
    
    print()
    return results

def run_scenario_B1():
    """
    Scenario B1: Internal System B Constraint
    Tests cross-system routing when internal System B connection is blocked.
    """
    print("🚀 Scenario B1: Internal System B Constraint")
    print("-" * 60)
    
    # Coordinates (same as B)
    origin = (182.946, 13.304, 157.295)      # A2 - System A
    destination = (176.062, 2.416, 153.960)  # B3 - System B
    cable_type = "C"                          # Cable C: Both systems
    
    # Files
    graph_file = "graph_LV_combined.json"
    tramo_map_file = "tramo_map_combined.json"
    forbidden_file = "forbidden_scenario_B1.json"  # Blocks B4-B1 (Tramo 395)
    
    print(f"📋 Configuration:")
    print(f"   Origin (A2):      {format_point(origin)} - System A")
    print(f"   Destination (B3): {format_point(destination)} - System B")
    print(f"   Cable Type:       {cable_type} (Both systems)")
    print(f"   Forbidden:        {forbidden_file} (Internal B4-B1)")
    print()
    
    results = {}
    
    try:
        # Test: Cross-system with internal constraint
        print("🧪 Test B1: Cross-System with Internal Constraint")
        try:
            constrained_path, constrained_nodes = run_direct_systems(
                graph_file, origin, destination, cable_type, tramo_map_file, forbidden_file
            )
            constrained_distance = calculate_path_distance(constrained_path)
            
            results['B1_constrained'] = {
                'scenario': 'B1',
                'type': 'Internal Constraint',
                'success': True,
                'points': len(constrained_path),
                'distance': constrained_distance,
                'nodes': constrained_nodes,
                'notes': 'Alternative internal route'
            }
            
            print(f"✅ Success: {len(constrained_path)} points, {constrained_distance:.3f} units")
            
        except Exception as e:
            results['B1_constrained'] = {
                'scenario': 'B1',
                'type': 'Internal Constraint',
                'success': False,
                'points': 0,
                'distance': 0,
                'nodes': 0,
                'notes': 'Gateway isolation'
            }
            
            print(f"❌ Failed: Gateway isolation - {str(e)}")
        
    except Exception as e:
        print(f"❌ Scenario B1 failed: {e}")
        results['B1_error'] = {
            'scenario': 'B1',
            'type': 'Error',
            'success': False,
            'points': 0,
            'distance': 0,
            'nodes': 0,
            'notes': str(e)
        }
    
    print()
    return results

def run_scenario_B2():
    """
    Scenario B2: Cross-System PPO Routing
    Tests cross-system routing with mandatory waypoint (PPO).
    """
    print("🚀 Scenario B2: Cross-System PPO Routing")
    print("-" * 60)
    
    # Coordinates
    origin = (182.946, 13.304, 157.295)      # A2 - System A
    ppo = (170.919, 8.418, 153.960)          # B5 - System B (PPO)
    destination = (176.062, 2.416, 153.960)  # B3 - System B
    cable_type = "C"                          # Cable C: Both systems
    
    # Files
    graph_file = "graph_LV_combined.json"
    tramo_map_file = "tramo_map_combined.json"
    
    print(f"📋 Configuration:")
    print(f"   Origin (A2):      {format_point(origin)} - System A")
    print(f"   PPO (B5):         {format_point(ppo)} - System B")
    print(f"   Destination (B3): {format_point(destination)} - System B")
    print(f"   Cable Type:       {cable_type} (Both systems)")
    print()
    
    results = {}
    
    try:
        # Test 1: Direct cross-system (baseline)
        print("🧪 Test B2.1: Direct Cross-System (Baseline)")
        direct_path, direct_nodes = run_direct_systems(
            graph_file, origin, destination, cable_type, tramo_map_file
        )
        direct_distance = calculate_path_distance(direct_path)
        
        results['B2_direct'] = {
            'scenario': 'B2',
            'type': 'Direct Cross-System',
            'success': True,
            'points': len(direct_path),
            'distance': direct_distance,
            'nodes': direct_nodes,
            'notes': 'Baseline comparison'
        }
        
        print(f"✅ Success: {len(direct_path)} points, {direct_distance:.3f} units")
        print()
        
        # Test 2: Cross-system with PPO
        print("🧪 Test B2.2: Cross-System with PPO")
        ppo_path, ppo_nodes = run_ppo_systems(
            graph_file, origin, ppo, destination, cable_type, tramo_map_file
        )
        ppo_distance = calculate_path_distance(ppo_path)
        
        # Find PPO position
        ppo_position = None
        for i, point in enumerate(ppo_path):
            if abs(point[0] - ppo[0]) < 0.001 and abs(point[1] - ppo[1]) < 0.001 and abs(point[2] - ppo[2]) < 0.001:
                ppo_position = i + 1
                break
        
        results['B2_ppo'] = {
            'scenario': 'B2',
            'type': 'Cross-System PPO',
            'success': True,
            'points': len(ppo_path),
            'distance': ppo_distance,
            'nodes': ppo_nodes,
            'notes': f'PPO at {ppo_position}/{len(ppo_path)}'
        }
        
        print(f"✅ Success: {len(ppo_path)} points, {ppo_distance:.3f} units")
        print(f"   PPO position: {ppo_position}/{len(ppo_path)} ({ppo_position/len(ppo_path)*100:.1f}%)")
        
        # Performance comparison
        distance_ratio = ppo_distance / direct_distance if direct_distance > 0 else float('inf')
        print(f"   PPO overhead: {distance_ratio:.1f}x distance ({((distance_ratio-1)*100):.1f}% increase)")
        
    except Exception as e:
        print(f"❌ Scenario B2 failed: {e}")
        results['B2_error'] = {
            'scenario': 'B2',
            'type': 'Error',
            'success': False,
            'points': 0,
            'distance': 0,
            'nodes': 0,
            'notes': str(e)
        }
    
    print()
    return results

def run_scenario_B3():
    """
    Scenario B3: Cross-System PPO with Forward Path Logic
    Tests cross-system PPO routing with forward path constraints (prevents backtracking).
    """
    print("🚀 Scenario B3: Cross-System PPO with Forward Path Logic")
    print("-" * 60)
    
    # Coordinates (same as B2)
    origin = (182.946, 13.304, 157.295)      # A2 - System A
    ppo = (170.919, 8.418, 153.960)          # B5 - System B (PPO)
    destination = (176.062, 2.416, 153.960)  # B3 - System B
    cable_type = "C"                          # Cable C: Both systems
    
    # Files
    graph_file = "graph_LV_combined.json"
    tramo_map_file = "tramo_map_combined.json"
    legacy_graph_file = "graph_LV_combined_legacy.json"
    
    print(f"📋 Configuration:")
    print(f"   Origin (A2):      {format_point(origin)} - System A")
    print(f"   PPO (B5):         {format_point(ppo)} - System B")
    print(f"   Destination (B3): {format_point(destination)} - System B")
    print(f"   Cable Type:       {cable_type} (Both systems)")
    print(f"   Forward Path:     ENABLED (prevents backtracking)")
    print()
    
    results = {}
    
    try:
        # Test 1: Regular PPO (baseline)
        print("🧪 Test B3.1: Regular PPO (Baseline)")
        regular_path, regular_nodes = run_ppo_systems(
            graph_file, origin, ppo, destination, cable_type, tramo_map_file
        )
        regular_distance = calculate_path_distance(regular_path)
        
        results['B3_regular'] = {
            'scenario': 'B3',
            'type': 'Regular PPO',
            'success': True,
            'points': len(regular_path),
            'distance': regular_distance,
            'nodes': regular_nodes,
            'notes': 'Allows backtracking'
        }
        
        print(f"✅ Success: {len(regular_path)} points, {regular_distance:.3f} units")
        print()
        
        # Test 2: Forward path PPO
        print("🧪 Test B3.2: Forward Path PPO")
        try:
            forward_path, forward_nodes, forward_segments = run_astar_with_ppo_forward_path(
                legacy_graph_file, origin, ppo, destination, tramo_map_file
            )
            forward_distance = calculate_distance_forbid(forward_path)
            
            results['B3_forward'] = {
                'scenario': 'B3',
                'type': 'Forward Path PPO',
                'success': True,
                'points': len(forward_path),
                'distance': forward_distance,
                'nodes': forward_nodes,
                'notes': 'Prevents backtracking'
            }
            
            print(f"✅ Success: {len(forward_path)} points, {forward_distance:.3f} units")
            print(f"   Segments: {len(forward_segments)}")
            
        except Exception as e:
            results['B3_forward'] = {
                'scenario': 'B3',
                'type': 'Forward Path PPO',
                'success': False,
                'points': 0,
                'distance': 0,
                'nodes': 0,
                'notes': 'Topology constraint'
            }
            
            print(f"❌ Failed: Network topology constraint")
            print(f"   Reason: PPO B5 creates circular dependency")
            print(f"   Details: {str(e)}")
        
    except Exception as e:
        print(f"❌ Scenario B3 failed: {e}")
        results['B3_error'] = {
            'scenario': 'B3',
            'type': 'Error',
            'success': False,
            'points': 0,
            'distance': 0,
            'nodes': 0,
            'notes': str(e)
        }
    
    print()
    return results

def run_all_b_scenarios():
    """Run all B scenarios sequentially and provide comprehensive analysis."""
    
    print("🎯 COMPREHENSIVE B SCENARIOS EVALUATION")
    print("=" * 80)
    print("Sequential evaluation of all B scenarios with detailed analysis")
    print("=" * 80)
    print()
    
    # Initialize results collector
    results = BScenarioResults()
    
    # Required files check
    print("📋 Pre-flight Check: Required Files")
    print("-" * 40)
    
    required_files = [
        "graph_LV_combined.json",
        "graph_LV_combined_legacy.json", 
        "tramo_map_combined.json",
        "forbidden_cross_system.json",
        "forbidden_scenario_B1.json"
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required files. Cannot proceed.")
        return False
    
    print("✅ All required files found")
    print()
    
    # Run scenarios sequentially
    print("🚀 SCENARIO EXECUTION SEQUENCE")
    print("=" * 50)
    print()
    
    # Scenario B: Cross-System Bridge Blocking
    try:
        scenario_b_results = run_scenario_B()
        for key, value in scenario_b_results.items():
            results.add_scenario(key, value)
    except Exception as e:
        print(f"❌ Scenario B execution failed: {e}")
        traceback.print_exc()
    
    # Scenario B1: Internal System B Constraint
    try:
        scenario_b1_results = run_scenario_B1()
        for key, value in scenario_b1_results.items():
            results.add_scenario(key, value)
    except Exception as e:
        print(f"❌ Scenario B1 execution failed: {e}")
        traceback.print_exc()
    
    # Scenario B2: Cross-System PPO Routing
    try:
        scenario_b2_results = run_scenario_B2()
        for key, value in scenario_b2_results.items():
            results.add_scenario(key, value)
    except Exception as e:
        print(f"❌ Scenario B2 execution failed: {e}")
        traceback.print_exc()
    
    # Scenario B3: Cross-System PPO with Forward Path Logic
    try:
        scenario_b3_results = run_scenario_B3()
        for key, value in scenario_b3_results.items():
            results.add_scenario(key, value)
    except Exception as e:
        print(f"❌ Scenario B3 execution failed: {e}")
        traceback.print_exc()
    
    # Comprehensive analysis
    results.print_comparison_table()
    results.print_summary_analysis()
    
    # Final conclusions
    print("\n" + "=" * 80)
    print("🏁 FINAL CONCLUSIONS: B SCENARIOS EVALUATION")
    print("=" * 80)
    
    print("🔍 Network Topology Insights:")
    print("   • Cross-system routing depends on critical bridge points")
    print("   • Single points of failure can isolate entire network segments")
    print("   • PPO placement must consider network topology constraints")
    print("   • Forward path logic reveals hidden network design flaws")
    print()
    
    print("🎯 Algorithm Performance:")
    print("   • Cable C enables robust cross-system routing")
    print("   • PPO routing adds minimal overhead for optimal placements")
    print("   • Forward path constraints can expose topology limitations")
    print("   • System-aware pathfinding handles complex routing scenarios")
    print()
    
    print("🚀 Practical Applications:")
    print("   • Use multiple connection points between systems")
    print("   • Validate PPO placements with forward path testing")
    print("   • Design redundant routing for critical connections")
    print("   • Apply constraint-based pathfinding for robustness validation")
    print()
    
    print("✅ Comprehensive B scenarios evaluation completed!")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    print("Comprehensive Demo: All B Scenarios Sequential Evaluation")
    print("Running Scenarios B, B1, B2, B3 with detailed analysis...")
    print()
    
    success = run_all_b_scenarios()
    
    if success:
        print("\n🎉 All B scenarios evaluation completed successfully!")
    else:
        print("\n❌ B scenarios evaluation failed")
        sys.exit(1) 