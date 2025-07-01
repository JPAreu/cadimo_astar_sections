#!/usr/bin/env python3
"""
Comprehensive Scenario C Demo: Sequential Step Evaluation
========================================================

This demo combines all Scenario C tests into a single comprehensive evaluation:
- Scenario C1: Direct path C1 → C2 (cross-system routing)
- Scenario C2: Direct path C1 → C3 (intra-system routing)  
- Scenario C3: PPO path C1 → C4 → C3 (PPO impact analysis)

Features:
- Sequential execution with detailed comparisons
- Performance metrics and efficiency analysis
- Backtracking detection for PPO routing
- Comprehensive results export
- Visual comparison tables
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any
from math import sqrt

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from astar_PPOF_systems import (
    SystemFilteredGraph,
    calculate_path_distance,
    format_point
)

def calculate_distance(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
    """Calculate Euclidean distance between two 3D points."""
    return sqrt(sum((p2[i] - p1[i])**2 for i in range(3)))

def analyze_path_efficiency(path: List[Tuple[float, float, float]], 
                          origin: Tuple[float, float, float], 
                          destination: Tuple[float, float, float]) -> Dict:
    """Analyze path efficiency metrics."""
    if not path:
        return {'error': 'No path provided'}
    
    path_distance = calculate_path_distance(path)
    direct_distance = calculate_distance(origin, destination)
    
    return {
        'path_points': len(path),
        'path_distance': path_distance,
        'direct_distance': direct_distance,
        'efficiency': (direct_distance / path_distance * 100) if path_distance > 0 else 0,
        'overhead': path_distance - direct_distance,
        'overhead_percentage': ((path_distance - direct_distance) / direct_distance * 100) if direct_distance > 0 else 0
    }

def detect_backtracking(path: List[Tuple[float, float, float]], tolerance: float = 0.001) -> Dict:
    """Quick backtracking detection for path analysis."""
    if len(path) < 3:
        return {'has_backtracking': False, 'revisits': 0, 'retraversals': 0}
    
    # Count coordinate revisits
    unique_coords = set()
    revisits = 0
    for coord in path:
        coord_key = tuple(round(c, 3) for c in coord)  # Round for comparison
        if coord_key in unique_coords:
            revisits += 1
        else:
            unique_coords.add(coord_key)
    
    # Count segment retraversals
    segments = set()
    retraversals = 0
    for i in range(len(path) - 1):
        start = tuple(round(c, 3) for c in path[i])
        end = tuple(round(c, 3) for c in path[i + 1])
        segment = (min(start, end), max(start, end))  # Normalize direction
        if segment in segments:
            retraversals += 1
        else:
            segments.add(segment)
    
    return {
        'has_backtracking': revisits > 0 or retraversals > 0,
        'revisits': revisits,
        'retraversals': retraversals,
        'unique_coordinates': len(unique_coords),
        'unique_segments': len(segments)
    }

def run_scenario_c1(graph: SystemFilteredGraph) -> Dict:
    """
    Scenario C1: Direct path from C1 to C2 (cross-system routing)
    C1: (176.553, 6.028, 150.340) - System B
    C2: (182.946, 13.304, 157.295) - System A
    """
    print("🔍 Scenario C1: Cross-System Direct Routing")
    print("-" * 50)
    
    origin = (176.553, 6.028, 150.340)      # C1 - System B
    destination = (182.946, 13.304, 157.295) # C2 - System A
    
    print(f"Origin (C1):      {format_point(origin)} - System B")
    print(f"Destination (C2): {format_point(destination)} - System A")
    print(f"Routing Type:     Cross-System (B → A)")
    print()
    
    start_time = time.time()
    path, nodes_explored = graph.find_path_direct(origin, destination)
    execution_time = time.time() - start_time
    
    if not path:
        result = {
            'scenario': 'C1',
            'success': False,
            'error': 'No path found',
            'execution_time': execution_time
        }
        print("❌ No path found")
        return result
    
    # Analyze path
    efficiency = analyze_path_efficiency(path, origin, destination)
    backtracking = detect_backtracking(path)
    
    # Calculate elevation change
    elevation_change = destination[2] - origin[2]
    
    result = {
        'scenario': 'C1',
        'success': True,
        'coordinates': {
            'origin': list(origin),
            'destination': list(destination)
        },
        'routing_type': 'cross_system',
        'systems': 'B_to_A',
        'path_points': len(path),
        'nodes_explored': nodes_explored,
        'path_distance': efficiency['path_distance'],
        'direct_distance': efficiency['direct_distance'],
        'efficiency': efficiency['efficiency'],
        'overhead': efficiency['overhead'],
        'overhead_percentage': efficiency['overhead_percentage'],
        'elevation_change': elevation_change,
        'backtracking': backtracking,
        'execution_time': execution_time
    }
    
    print(f"✅ Path found: {len(path)} points")
    print(f"📊 Distance: {efficiency['path_distance']:.3f} units (direct: {efficiency['direct_distance']:.3f})")
    print(f"📈 Efficiency: {efficiency['efficiency']:.1f}%")
    print(f"🔍 Nodes explored: {nodes_explored}")
    print(f"⏱️  Execution time: {execution_time:.3f}s")
    print(f"📏 Elevation change: {elevation_change:+.3f} units")
    print(f"🔄 Backtracking: {'Yes' if backtracking['has_backtracking'] else 'No'}")
    print()
    
    return result

def run_scenario_c2(graph: SystemFilteredGraph) -> Dict:
    """
    Scenario C2: Direct path from C1 to C3 (intra-system routing)
    C1: (176.553, 6.028, 150.340) - System B
    C3: (174.860, 15.369, 136.587) - System B
    """
    print("🔍 Scenario C2: Intra-System Direct Routing")
    print("-" * 50)
    
    origin = (176.553, 6.028, 150.340)      # C1 - System B
    destination = (174.860, 15.369, 136.587) # C3 - System B
    
    print(f"Origin (C1):      {format_point(origin)} - System B")
    print(f"Destination (C3): {format_point(destination)} - System B")
    print(f"Routing Type:     Intra-System (B → B)")
    print()
    
    start_time = time.time()
    path, nodes_explored = graph.find_path_direct(origin, destination)
    execution_time = time.time() - start_time
    
    if not path:
        result = {
            'scenario': 'C2',
            'success': False,
            'error': 'No path found',
            'execution_time': execution_time
        }
        print("❌ No path found")
        return result
    
    # Analyze path
    efficiency = analyze_path_efficiency(path, origin, destination)
    backtracking = detect_backtracking(path)
    
    # Calculate elevation change
    elevation_change = destination[2] - origin[2]
    
    result = {
        'scenario': 'C2',
        'success': True,
        'coordinates': {
            'origin': list(origin),
            'destination': list(destination)
        },
        'routing_type': 'intra_system',
        'systems': 'B_to_B',
        'path_points': len(path),
        'nodes_explored': nodes_explored,
        'path_distance': efficiency['path_distance'],
        'direct_distance': efficiency['direct_distance'],
        'efficiency': efficiency['efficiency'],
        'overhead': efficiency['overhead'],
        'overhead_percentage': efficiency['overhead_percentage'],
        'elevation_change': elevation_change,
        'backtracking': backtracking,
        'execution_time': execution_time
    }
    
    print(f"✅ Path found: {len(path)} points")
    print(f"📊 Distance: {efficiency['path_distance']:.3f} units (direct: {efficiency['direct_distance']:.3f})")
    print(f"📈 Efficiency: {efficiency['efficiency']:.1f}%")
    print(f"🔍 Nodes explored: {nodes_explored}")
    print(f"⏱️  Execution time: {execution_time:.3f}s")
    print(f"📏 Elevation change: {elevation_change:+.3f} units")
    print(f"🔄 Backtracking: {'Yes' if backtracking['has_backtracking'] else 'No'}")
    print()
    
    return result

def run_scenario_c3(graph: SystemFilteredGraph) -> Dict:
    """
    Scenario C3: PPO path from C1 to C3 via C4 (PPO impact analysis)
    C1: (176.553, 6.028, 150.340) - System B
    C4: (169.378, 5.669, 140.678) - System B (PPO)
    C3: (174.860, 15.369, 136.587) - System B
    """
    print("🔍 Scenario C3: PPO Impact Analysis")
    print("-" * 50)
    
    origin = (176.553, 6.028, 150.340)      # C1 - System B
    ppo = (169.378, 5.669, 140.678)         # C4 - System B (PPO)
    destination = (174.860, 15.369, 136.587) # C3 - System B
    
    print(f"Origin (C1):      {format_point(origin)} - System B")
    print(f"PPO (C4):         {format_point(ppo)} - System B")
    print(f"Destination (C3): {format_point(destination)} - System B")
    print(f"Routing Type:     Intra-System with PPO (B → B via B)")
    print()
    
    start_time = time.time()
    path, nodes_explored = graph.find_path_with_ppo(origin, ppo, destination)
    execution_time = time.time() - start_time
    
    if not path:
        result = {
            'scenario': 'C3',
            'success': False,
            'error': 'No PPO path found',
            'execution_time': execution_time
        }
        print("❌ No PPO path found")
        return result
    
    # Analyze path
    total_direct_distance = calculate_distance(origin, ppo) + calculate_distance(ppo, destination)
    efficiency = analyze_path_efficiency(path, origin, destination)
    backtracking = detect_backtracking(path)
    
    # Find PPO position in path
    ppo_index = -1
    for i, point in enumerate(path):
        if calculate_distance(point, ppo) < 0.001:
            ppo_index = i
            break
    
    # Calculate segment efficiencies
    if ppo_index >= 0:
        segment1_path = path[:ppo_index + 1]
        segment2_path = path[ppo_index:]
        
        seg1_efficiency = analyze_path_efficiency(segment1_path, origin, ppo)
        seg2_efficiency = analyze_path_efficiency(segment2_path, ppo, destination)
    else:
        seg1_efficiency = {'error': 'PPO not found in path'}
        seg2_efficiency = {'error': 'PPO not found in path'}
    
    # Calculate elevation changes
    total_elevation_change = destination[2] - origin[2]
    ppo_elevation_change = ppo[2] - origin[2]
    
    result = {
        'scenario': 'C3',
        'success': True,
        'coordinates': {
            'origin': list(origin),
            'ppo': list(ppo),
            'destination': list(destination)
        },
        'routing_type': 'intra_system_ppo',
        'systems': 'B_to_B_via_B',
        'path_points': len(path),
        'nodes_explored': nodes_explored,
        'ppo_index': ppo_index,
        'ppo_position_percentage': (ppo_index / (len(path) - 1) * 100) if ppo_index >= 0 and len(path) > 1 else 0,
        'path_distance': efficiency['path_distance'],
        'direct_distance': efficiency['direct_distance'],
        'total_direct_distance': total_direct_distance,
        'efficiency': efficiency['efficiency'],
        'ppo_efficiency': (total_direct_distance / efficiency['path_distance'] * 100) if efficiency['path_distance'] > 0 else 0,
        'overhead': efficiency['overhead'],
        'overhead_percentage': efficiency['overhead_percentage'],
        'elevation_change': total_elevation_change,
        'ppo_elevation_change': ppo_elevation_change,
        'segment1': seg1_efficiency,
        'segment2': seg2_efficiency,
        'backtracking': backtracking,
        'execution_time': execution_time
    }
    
    print(f"✅ PPO path found: {len(path)} points")
    print(f"📊 Distance: {efficiency['path_distance']:.3f} units (direct: {efficiency['direct_distance']:.3f})")
    print(f"📊 PPO segments distance: {total_direct_distance:.3f} units")
    print(f"📈 Path efficiency: {efficiency['efficiency']:.1f}%")
    print(f"📈 PPO efficiency: {result['ppo_efficiency']:.1f}%")
    print(f"🎯 PPO position: {ppo_index + 1}/{len(path)} ({result['ppo_position_percentage']:.1f}%)")
    print(f"🔍 Nodes explored: {nodes_explored}")
    print(f"⏱️  Execution time: {execution_time:.3f}s")
    print(f"📏 Total elevation change: {total_elevation_change:+.3f} units")
    print(f"📏 PPO elevation change: {ppo_elevation_change:+.3f} units")
    print(f"🔄 Backtracking: {'Yes' if backtracking['has_backtracking'] else 'No'}")
    if backtracking['has_backtracking']:
        print(f"   • {backtracking['revisits']} coordinate revisits")
        print(f"   • {backtracking['retraversals']} segment retraversals")
    print()
    
    return result

def print_comparison_table(results: List[Dict]):
    """Print a comprehensive comparison table of all scenarios."""
    print("📊 Comprehensive Scenario Comparison")
    print("=" * 80)
    print()
    
    # Filter successful results
    successful_results = [r for r in results if r.get('success', False)]
    
    if not successful_results:
        print("❌ No successful scenarios to compare")
        return
    
    # Header
    print(f"{'Metric':<25} {'C1 (B→A)':<15} {'C2 (B→B)':<15} {'C3 (PPO)':<15}")
    print("-" * 75)
    
    # Extract data for comparison
    c1 = next((r for r in successful_results if r['scenario'] == 'C1'), None)
    c2 = next((r for r in successful_results if r['scenario'] == 'C2'), None)
    c3 = next((r for r in successful_results if r['scenario'] == 'C3'), None)
    
    def get_value(result, key, default='-'):
        return f"{result[key]:.1f}" if result and key in result else default
    
    def get_int_value(result, key, default='-'):
        return f"{result[key]}" if result and key in result else default
    
    def get_bool_value(result, key, default='-'):
        if result and key in result:
            return "Yes" if result[key].get('has_backtracking', False) else "No"
        return default
    
    # Comparison rows
    rows = [
        ("Routing Type", 
         c1['routing_type'].replace('_', '-') if c1 else '-',
         c2['routing_type'].replace('_', '-') if c2 else '-',
         c3['routing_type'].replace('_', '-') if c3 else '-'),
        ("Path Points", 
         get_int_value(c1, 'path_points'),
         get_int_value(c2, 'path_points'),
         get_int_value(c3, 'path_points')),
        ("Path Distance", 
         get_value(c1, 'path_distance'),
         get_value(c2, 'path_distance'),
         get_value(c3, 'path_distance')),
        ("Direct Distance", 
         get_value(c1, 'direct_distance'),
         get_value(c2, 'direct_distance'),
         get_value(c3, 'direct_distance')),
        ("Efficiency (%)", 
         get_value(c1, 'efficiency'),
         get_value(c2, 'efficiency'),
         get_value(c3, 'efficiency')),
        ("Overhead (%)", 
         get_value(c1, 'overhead_percentage'),
         get_value(c2, 'overhead_percentage'),
         get_value(c3, 'overhead_percentage')),
        ("Nodes Explored", 
         get_int_value(c1, 'nodes_explored'),
         get_int_value(c2, 'nodes_explored'),
         get_int_value(c3, 'nodes_explored')),
        ("Execution Time (s)", 
         get_value(c1, 'execution_time', '-'),
         get_value(c2, 'execution_time', '-'),
         get_value(c3, 'execution_time', '-')),
        ("Elevation Change", 
         get_value(c1, 'elevation_change'),
         get_value(c2, 'elevation_change'),
         get_value(c3, 'elevation_change')),
        ("Backtracking", 
         get_bool_value(c1, 'backtracking'),
         get_bool_value(c2, 'backtracking'),
         get_bool_value(c3, 'backtracking'))
    ]
    
    for row in rows:
        print(f"{row[0]:<25} {row[1]:<15} {row[2]:<15} {row[3]:<15}")
    
    print()

def print_performance_analysis(results: List[Dict]):
    """Print detailed performance analysis and insights."""
    print("🔍 Performance Analysis & Insights")
    print("=" * 50)
    print()
    
    successful_results = [r for r in results if r.get('success', False)]
    c1 = next((r for r in successful_results if r['scenario'] == 'C1'), None)
    c2 = next((r for r in successful_results if r['scenario'] == 'C2'), None)
    c3 = next((r for r in successful_results if r['scenario'] == 'C3'), None)
    
    # Cross-system vs Intra-system comparison
    if c1 and c2:
        print("🔄 Cross-System vs Intra-System Routing:")
        efficiency_diff = c1['efficiency'] - c2['efficiency']
        distance_diff = c1['path_distance'] - c2['path_distance']
        
        print(f"   • Cross-system (C1): {c1['efficiency']:.1f}% efficiency")
        print(f"   • Intra-system (C2):  {c2['efficiency']:.1f}% efficiency")
        print(f"   • Efficiency difference: {efficiency_diff:+.1f}%")
        print(f"   • Distance difference: {distance_diff:+.1f} units")
        
        if efficiency_diff > 0:
            print("   ✅ Cross-system routing is more efficient")
        else:
            print("   ✅ Intra-system routing is more efficient")
        print()
    
    # PPO Impact Analysis
    if c2 and c3:
        print("🎯 PPO Impact Analysis (C2 vs C3):")
        ppo_overhead = ((c3['path_distance'] - c2['path_distance']) / c2['path_distance'] * 100)
        efficiency_loss = c2['efficiency'] - c3['efficiency']
        
        print(f"   • Direct path (C2):     {c2['path_distance']:.1f} units, {c2['efficiency']:.1f}% efficiency")
        print(f"   • PPO path (C3):        {c3['path_distance']:.1f} units, {c3['efficiency']:.1f}% efficiency")
        print(f"   • PPO distance overhead: {ppo_overhead:+.1f}%")
        print(f"   • Efficiency loss:      {efficiency_loss:+.1f}%")
        
        # PPO impact rating
        if ppo_overhead < 20:
            impact_rating = "LOW"
        elif ppo_overhead < 50:
            impact_rating = "MODERATE"
        elif ppo_overhead < 100:
            impact_rating = "HIGH"
        else:
            impact_rating = "VERY HIGH"
        
        print(f"   • PPO impact rating:    {impact_rating}")
        print()
    
    # Backtracking Analysis
    backtracking_scenarios = [r for r in successful_results if r.get('backtracking', {}).get('has_backtracking', False)]
    if backtracking_scenarios:
        print("🔄 Backtracking Analysis:")
        for result in backtracking_scenarios:
            bt = result['backtracking']
            print(f"   • Scenario {result['scenario']}: {bt['revisits']} revisits, {bt['retraversals']} retraversals")
        print("   ⚠️  Backtracking indicates network topology constraints")
        print()
    else:
        print("✅ No backtracking detected in any scenario")
        print()
    
    # Performance Rankings
    print("🏆 Performance Rankings:")
    
    # Sort by efficiency
    efficiency_ranking = sorted(successful_results, key=lambda x: x['efficiency'], reverse=True)
    print("   By Efficiency:")
    for i, result in enumerate(efficiency_ranking, 1):
        print(f"   {i}. Scenario {result['scenario']}: {result['efficiency']:.1f}%")
    
    # Sort by path distance (shorter is better)
    distance_ranking = sorted(successful_results, key=lambda x: x['path_distance'])
    print("   By Path Distance:")
    for i, result in enumerate(distance_ranking, 1):
        print(f"   {i}. Scenario {result['scenario']}: {result['path_distance']:.1f} units")
    
    print()

def main():
    """Main execution function for comprehensive Scenario C demo."""
    print("🔧 Comprehensive Scenario C Demo")
    print("Sequential Step Evaluation of Cross-System and PPO Routing")
    print("=" * 70)
    print()
    
    # Configuration
    cable_type = "C"  # Both systems
    graph_file = "graph_LV_combined.json"
    tramo_map_file = "tramo_map_combined.json"
    
    print(f"📋 Configuration:")
    print(f"   Graph File:    {graph_file}")
    print(f"   Tramo Map:     {tramo_map_file}")
    print(f"   Cable Type:    {cable_type} (Both Systems)")
    print()
    
    try:
        # Initialize graph
        print("🔄 Initializing SystemFilteredGraph...")
        graph = SystemFilteredGraph(graph_file, cable_type, tramo_map_file)
        print("✅ Graph initialized successfully")
        print()
        
        # Execute scenarios sequentially
        results = []
        
        # Scenario C1: Cross-system direct routing
        print("🚀 Executing Scenario C1...")
        c1_result = run_scenario_c1(graph)
        results.append(c1_result)
        
        # Scenario C2: Intra-system direct routing
        print("🚀 Executing Scenario C2...")
        c2_result = run_scenario_c2(graph)
        results.append(c2_result)
        
        # Scenario C3: PPO routing with backtracking analysis
        print("🚀 Executing Scenario C3...")
        c3_result = run_scenario_c3(graph)
        results.append(c3_result)
        
        # Comprehensive analysis
        print_comparison_table(results)
        print_performance_analysis(results)
        
        # Save comprehensive results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"scenario_C_comprehensive_{timestamp}.json"
        
        comprehensive_results = {
            'timestamp': timestamp,
            'configuration': {
                'cable_type': cable_type,
                'graph_file': graph_file,
                'tramo_map_file': tramo_map_file
            },
            'scenarios': results,
            'summary': {
                'total_scenarios': len(results),
                'successful_scenarios': len([r for r in results if r.get('success', False)]),
                'scenarios_with_backtracking': len([r for r in results if r.get('backtracking', {}).get('has_backtracking', False)])
            }
        }
        
        with open(results_file, 'w') as f:
            json.dump(comprehensive_results, f, indent=2)
        
        print(f"📄 Comprehensive results saved to: {results_file}")
        print()
        
        # Final summary
        successful_count = len([r for r in results if r.get('success', False)])
        print("🎉 Comprehensive Demo Completed!")
        print(f"   • Total scenarios: {len(results)}")
        print(f"   • Successful: {successful_count}")
        print(f"   • Failed: {len(results) - successful_count}")
        
        if successful_count == len(results):
            print("   ✅ All scenarios executed successfully!")
            return 0
        else:
            print("   ⚠️  Some scenarios failed - check results above")
            return 1
            
    except Exception as e:
        print(f"❌ Error in comprehensive demo: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
