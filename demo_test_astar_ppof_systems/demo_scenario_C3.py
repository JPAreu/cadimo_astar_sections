#!/usr/bin/env python3
"""
Scenario C3: PPO Impact Analysis - Adding C4 to C1→C3 Route
=========================================================

This scenario tests the impact of adding PPO C4 to the existing C1→C3 route:
- Origin: C1 (176.553, 6.028, 150.340) - System B
- PPO: C4 (169.378, 5.669, 140.678) - System to be determined
- Destination: C3 (174.860, 15.369, 136.587) - System B  
- Cable Type: C (Both systems)

This builds on Scenario C2 by introducing a mandatory waypoint to analyze:
1. System identification of C4
2. PPO routing impact on path length and complexity
3. Cross-system vs intra-system routing behavior
4. Comparison with direct C1→C3 path from Scenario C2

Expected Analysis:
- If C4 is in System B: Intra-system PPO routing
- If C4 is in System A: Cross-system PPO routing with system transitions
- Path efficiency impact of mandatory waypoint
"""

import sys
import os
import json
from math import sqrt
from typing import List, Tuple, Dict, Any
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from astar_PPOF_systems import (
    SystemFilteredGraph,
    calculate_path_distance,
    format_point
)

def run_scenario_C3():
    """
    Scenario C3: PPO Impact Analysis - Adding C4 to C1→C3 Route
    
    Tests the impact of adding PPO C4 as a mandatory waypoint to the C1→C3 route.
    """
    print("🚀 Scenario C3: PPO Impact Analysis - Adding C4 to C1→C3 Route")
    print("=" * 80)
    print()
    
    # Scenario coordinates
    origin = (176.553, 6.028, 150.340)      # C1 - System B
    ppo = (169.378, 5.669, 140.678)         # C4 - System to be determined
    destination = (174.860, 15.369, 136.587) # C3 - System B
    cable_type = "C"                          # Cable C: Both systems
    
    # Required files
    graph_file = "graph_LV_combined.json"
    tramo_map_file = "tramo_map_combined.json"
    
    print(f"📋 Scenario Configuration:")
    print(f"   Origin (C1):      {format_point(origin)}")
    print(f"   PPO (C4):         {format_point(ppo)}")
    print(f"   Destination (C3): {format_point(destination)}")
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
    # Test C3.1: System Identification and Endpoint Analysis
    # ====================================================================
    print("🔍 Test C3.1: System Identification and Endpoint Analysis")
    print("-" * 60)
    
    try:
        # Create SystemFilteredGraph to analyze endpoints
        graph = SystemFilteredGraph(graph_file, cable_type, tramo_map_file)
        
        from astar_PPOF_systems import coord_to_key
        origin_key = coord_to_key(origin)
        ppo_key = coord_to_key(ppo)
        destination_key = coord_to_key(destination)
        
        # Find systems for all points
        points = {
            'C1 (Origin)': (origin, origin_key),
            'C4 (PPO)': (ppo, ppo_key),
            'C3 (Destination)': (destination, destination_key)
        }
        
        point_systems = {}
        all_found = True
        
        for name, (coord, key) in points.items():
            found = False
            system = None
            for node_key, node_data in graph.graph_data["nodes"].items():
                if node_key == key:
                    system = node_data.get("sys")
                    found = True
                    break
            
            point_systems[name] = {'coord': coord, 'found': found, 'system': system}
            print(f"   {name}: {format_point(coord)}")
            print(f"     - Found in graph: {'✅ YES' if found else '❌ NO'}")
            print(f"     - System: {system if found else 'NOT FOUND'}")
            
            if not found:
                all_found = False
        
        print()
        
        if not all_found:
            print("❌ Some points not found in graph - cannot proceed")
            return None
        
        # Analyze routing complexity
        origin_sys = point_systems['C1 (Origin)']['system']
        ppo_sys = point_systems['C4 (PPO)']['system']
        dest_sys = point_systems['C3 (Destination)']['system']
        
        unique_systems = {origin_sys, ppo_sys, dest_sys}
        
        print(f"🔍 Routing Analysis:")
        print(f"   Systems involved: {sorted(unique_systems)}")
        print(f"   System transitions: {len(unique_systems) - 1}")
        
        if len(unique_systems) == 1:
            routing_type = f"Intra-System (System {list(unique_systems)[0]})"
            complexity = "LOW"
        elif len(unique_systems) == 2:
            routing_type = f"Cross-System ({origin_sys} ↔ {ppo_sys} ↔ {dest_sys})"
            complexity = "MEDIUM"
        else:
            routing_type = f"Multi-System ({origin_sys} → {ppo_sys} → {dest_sys})"
            complexity = "HIGH"
        
        print(f"   Routing Type: {routing_type}")
        print(f"   Complexity: {complexity}")
        print()
        
    except Exception as e:
        print(f"❌ Error in endpoint analysis: {e}")
        return None
    
    # ====================================================================
    # Test C3.2: PPO Pathfinding Execution
    # ====================================================================
    print("🧪 Test C3.2: PPO Pathfinding Execution")
    print("-" * 60)
    
    try:
        # Execute PPO pathfinding
        print(f"🔄 Finding path: C1 → C4 → C3")
        path, nodes_explored = graph.find_path_with_ppo(origin, ppo, destination)
        
        if not path:
            print("❌ No path found with PPO C4")
            return None
        
        # Calculate metrics
        path_distance = calculate_path_distance(path)
        direct_distance = sqrt(sum((destination[i] - origin[i])**2 for i in range(3)))
        efficiency = (direct_distance / path_distance) * 100 if path_distance > 0 else 0
        
        # Find PPO position in path
        ppo_index = -1
        for i, point in enumerate(path):
            if abs(point[0] - ppo[0]) < 0.001 and abs(point[1] - ppo[1]) < 0.001 and abs(point[2] - ppo[2]) < 0.001:
                ppo_index = i
                break
        
        print(f"✅ PPO path found successfully")
        print(f"   Path points: {len(path)}")
        print(f"   Nodes explored: {nodes_explored}")
        print(f"   Path distance: {path_distance:.3f} units")
        print(f"   Direct distance: {direct_distance:.3f} units")
        print(f"   Path efficiency: {efficiency:.1f}%")
        print(f"   PPO position: {ppo_index + 1}/{len(path)} ({((ppo_index + 1)/len(path)*100):.1f}%)")
        print()
        
        # Elevation analysis
        origin_elev = origin[2]
        ppo_elev = ppo[2]
        dest_elev = destination[2]
        
        elev_change_1 = ppo_elev - origin_elev
        elev_change_2 = dest_elev - ppo_elev
        total_elev_change = dest_elev - origin_elev
        
        print(f"📊 Elevation Profile:")
        print(f"   C1 elevation: {origin_elev:.3f}")
        print(f"   C4 elevation: {ppo_elev:.3f} ({elev_change_1:+.3f})")
        print(f"   C3 elevation: {dest_elev:.3f} ({elev_change_2:+.3f})")
        print(f"   Total change: {total_elev_change:+.3f}")
        print()
        
    except Exception as e:
        print(f"❌ Error in PPO pathfinding: {e}")
        return None
    
    # ====================================================================
    # Test C3.3: Comparison with Direct C1→C3 Path (Scenario C2)
    # ====================================================================
    print("📊 Test C3.3: Comparison with Direct C1→C3 Path")
    print("-" * 60)
    
    try:
        # Execute direct pathfinding for comparison
        print(f"🔄 Finding direct path: C1 → C3 (for comparison)")
        direct_path, direct_nodes = graph.find_path_direct(origin, destination)
        
        if direct_path:
            direct_path_distance = calculate_path_distance(direct_path)
            
            print(f"✅ Direct path found")
            print(f"   Direct path points: {len(direct_path)}")
            print(f"   Direct nodes explored: {direct_nodes}")
            print(f"   Direct path distance: {direct_path_distance:.3f} units")
            print()
            
            # Comparison analysis
            print(f"🔍 PPO vs Direct Comparison:")
            path_increase = ((len(path) - len(direct_path)) / len(direct_path)) * 100
            distance_increase = ((path_distance - direct_path_distance) / direct_path_distance) * 100
            nodes_increase = ((nodes_explored - direct_nodes) / direct_nodes) * 100
            
            print(f"   Path points: {len(path)} vs {len(direct_path)} ({path_increase:+.1f}%)")
            print(f"   Path distance: {path_distance:.3f} vs {direct_path_distance:.3f} ({distance_increase:+.1f}%)")
            print(f"   Nodes explored: {nodes_explored} vs {direct_nodes} ({nodes_increase:+.1f}%)")
            
            # Impact assessment
            if distance_increase < 10:
                impact = "LOW"
            elif distance_increase < 25:
                impact = "MODERATE"
            else:
                impact = "HIGH"
            
            print(f"   PPO Impact: {impact}")
            print()
            
        else:
            print("❌ Direct path not found - cannot compare")
            direct_path_distance = None
            
    except Exception as e:
        print(f"❌ Error in direct pathfinding: {e}")
        direct_path_distance = None
    
    # ====================================================================
    # Test C3.4: Results Summary and Export
    # ====================================================================
    print("📋 Test C3.4: Results Summary")
    print("-" * 60)
    
    # Create results summary
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {
        "scenario": "C3",
        "title": "PPO Impact Analysis - Adding C4 to C1→C3 Route",
        "timestamp": timestamp,
        "coordinates": {
            "origin": {"point": "C1", "coord": list(origin), "system": origin_sys},
            "ppo": {"point": "C4", "coord": list(ppo), "system": ppo_sys},
            "destination": {"point": "C3", "coord": list(destination), "system": dest_sys}
        },
        "cable_type": cable_type,
        "routing_analysis": {
            "type": routing_type,
            "complexity": complexity,
            "systems_involved": sorted(unique_systems),
            "system_transitions": len(unique_systems) - 1
        },
        "ppo_path": {
            "points": len(path),
            "nodes_explored": nodes_explored,
            "distance": round(path_distance, 3),
            "direct_distance": round(direct_distance, 3),
            "efficiency": round(efficiency, 1),
            "ppo_position": {
                "index": ppo_index,
                "percentage": round((ppo_index + 1)/len(path)*100, 1)
            }
        },
        "elevation_profile": {
            "origin_elevation": origin_elev,
            "ppo_elevation": ppo_elev,
            "destination_elevation": dest_elev,
            "changes": {
                "origin_to_ppo": round(elev_change_1, 3),
                "ppo_to_destination": round(elev_change_2, 3),
                "total": round(total_elev_change, 3)
            }
        }
    }
    
    # Add comparison data if available
    if direct_path_distance is not None:
        results["comparison"] = {
            "direct_path": {
                "points": len(direct_path),
                "nodes_explored": direct_nodes,
                "distance": round(direct_path_distance, 3)
            },
            "ppo_vs_direct": {
                "path_increase_percent": round(path_increase, 1),
                "distance_increase_percent": round(distance_increase, 1),
                "nodes_increase_percent": round(nodes_increase, 1),
                "impact_level": impact
            }
        }
    
    # Save results
    results_file = f"scenario_C3_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Results Summary:")
    print(f"   Scenario: C3 - PPO Impact Analysis")
    print(f"   PPO C4 System: {ppo_sys}")
    print(f"   Routing Type: {routing_type}")
    print(f"   PPO Path: {len(path)} points, {path_distance:.3f} units")
    if direct_path_distance is not None:
        print(f"   Direct Path: {len(direct_path)} points, {direct_path_distance:.3f} units")
        print(f"   PPO Impact: {impact} ({distance_increase:+.1f}% distance increase)")
    print(f"   Results saved: {results_file}")
    print()
    
    return results

def main():
    """Main execution function."""
    print("🔧 Scenario C3 Demo - PPO Impact Analysis")
    print("Testing the impact of adding PPO C4 to C1→C3 routing")
    print()
    
    results = run_scenario_C3()
    
    if results:
        print("🎉 Scenario C3 completed successfully!")
        print()
        print("📊 Key Findings:")
        print(f"   • PPO C4 is in System {results['coordinates']['ppo']['system']}")
        print(f"   • Routing complexity: {results['routing_analysis']['complexity']}")
        print(f"   • PPO path efficiency: {results['ppo_path']['efficiency']:.1f}%")
        if 'comparison' in results:
            print(f"   • PPO impact level: {results['comparison']['ppo_vs_direct']['impact_level']}")
            print(f"   • Distance increase: {results['comparison']['ppo_vs_direct']['distance_increase_percent']:+.1f}%")
        print()
        
        # Suggest next steps
        print("🔮 Suggested Analysis:")
        print("   • Export 3D visualization with export_scenario_C3_3D_dxf.py")
        print("   • Compare with Scenario C2 results for PPO impact assessment")
        print("   • Test forward path logic if C4 creates routing constraints")
    else:
        print("❌ Scenario C3 failed - check error messages above")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 