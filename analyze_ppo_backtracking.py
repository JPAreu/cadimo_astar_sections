#!/usr/bin/env python3
"""
PPO Backtracking Analysis Tool
=============================

This tool analyzes PPO routing to detect:
1. Backtracking (returning to previously visited coordinates)
2. Repeated path segments (same edge traversed multiple times)
3. Circular routing patterns
4. Path efficiency compared to optimal segments

Specifically analyzes Scenario C3: C1 → C4 → C3 routing
"""

import sys
import os
import json
from math import sqrt
from typing import List, Tuple, Dict, Set
from collections import defaultdict

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

def find_repeated_coordinates(path: List[Tuple[float, float, float]], tolerance: float = 0.001) -> Dict:
    """
    Find coordinates that appear multiple times in the path.
    
    Args:
        path: List of 3D coordinates
        tolerance: Distance tolerance for considering points the same
        
    Returns:
        Dictionary with repeated coordinate analysis
    """
    coordinate_visits = defaultdict(list)
    
    # Group coordinates by position with tolerance
    for i, coord in enumerate(path):
        found_group = False
        for key_coord in coordinate_visits.keys():
            if calculate_distance(coord, key_coord) <= tolerance:
                coordinate_visits[key_coord].append(i)
                found_group = True
                break
        
        if not found_group:
            coordinate_visits[coord].append(i)
    
    # Find coordinates visited multiple times
    repeated_coords = {coord: visits for coord, visits in coordinate_visits.items() if len(visits) > 1}
    
    return {
        'total_unique_coordinates': len(coordinate_visits),
        'total_path_points': len(path),
        'repeated_coordinates': repeated_coords,
        'repetition_count': len(repeated_coords),
        'total_revisits': sum(len(visits) - 1 for visits in repeated_coords.values())
    }

def find_repeated_segments(path: List[Tuple[float, float, float]], tolerance: float = 0.001) -> Dict:
    """
    Find path segments (edges) that are traversed multiple times.
    
    Args:
        path: List of 3D coordinates
        tolerance: Distance tolerance for considering segments the same
        
    Returns:
        Dictionary with repeated segment analysis
    """
    segments = []
    segment_visits = defaultdict(list)
    
    # Create segments from consecutive path points
    for i in range(len(path) - 1):
        start = path[i]
        end = path[i + 1]
        # Normalize segment direction (smaller coordinate first)
        if start <= end:
            segment = (start, end)
        else:
            segment = (end, start)
        segments.append((segment, i))
    
    # Group similar segments
    for segment, index in segments:
        found_group = False
        for key_segment in segment_visits.keys():
            # Check if segments are the same within tolerance
            start_match = (calculate_distance(segment[0], key_segment[0]) <= tolerance and 
                          calculate_distance(segment[1], key_segment[1]) <= tolerance)
            reverse_match = (calculate_distance(segment[0], key_segment[1]) <= tolerance and 
                            calculate_distance(segment[1], key_segment[0]) <= tolerance)
            
            if start_match or reverse_match:
                segment_visits[key_segment].append(index)
                found_group = True
                break
        
        if not found_group:
            segment_visits[segment].append(index)
    
    # Find segments traversed multiple times
    repeated_segments = {segment: visits for segment, visits in segment_visits.items() if len(visits) > 1}
    
    return {
        'total_unique_segments': len(segment_visits),
        'total_path_segments': len(segments),
        'repeated_segments': repeated_segments,
        'repetition_count': len(repeated_segments),
        'total_retraversals': sum(len(visits) - 1 for visits in repeated_segments.values())
    }

def analyze_backtracking_patterns(path: List[Tuple[float, float, float]], tolerance: float = 0.001) -> Dict:
    """
    Analyze backtracking patterns in the path.
    
    Args:
        path: List of 3D coordinates
        tolerance: Distance tolerance for backtracking detection
        
    Returns:
        Dictionary with backtracking analysis
    """
    backtrack_events = []
    direction_changes = 0
    
    for i in range(2, len(path)):
        prev_coord = path[i-2]
        curr_coord = path[i-1] 
        next_coord = path[i]
        
        # Check if we're moving back towards a previous position
        dist_prev_curr = calculate_distance(prev_coord, curr_coord)
        dist_curr_next = calculate_distance(curr_coord, next_coord)
        dist_prev_next = calculate_distance(prev_coord, next_coord)
        
        # Backtracking indicator: if going back reduces distance to previous point
        if dist_prev_next < dist_prev_curr and dist_curr_next > tolerance:
            backtrack_events.append({
                'position': i,
                'from': prev_coord,
                'via': curr_coord,
                'to': next_coord,
                'backtrack_distance': dist_curr_next,
                'saved_distance': dist_prev_curr - dist_prev_next
            })
        
        # Count significant direction changes
        if i >= 3:
            # Calculate vectors
            vec1 = tuple(path[i-1][j] - path[i-2][j] for j in range(3))
            vec2 = tuple(path[i][j] - path[i-1][j] for j in range(3))
            
            # Calculate dot product to detect direction changes
            dot_product = sum(vec1[j] * vec2[j] for j in range(3))
            mag1 = sqrt(sum(v**2 for v in vec1))
            mag2 = sqrt(sum(v**2 for v in vec2))
            
            if mag1 > tolerance and mag2 > tolerance:
                cos_angle = dot_product / (mag1 * mag2)
                # Significant direction change (> 90 degrees)
                if cos_angle < 0:
                    direction_changes += 1
    
    return {
        'backtrack_events': backtrack_events,
        'backtrack_count': len(backtrack_events),
        'direction_changes': direction_changes,
        'total_backtrack_distance': sum(event['backtrack_distance'] for event in backtrack_events)
    }

def analyze_segment_efficiency(path: List[Tuple[float, float, float]], origin: Tuple[float, float, float], 
                             ppo: Tuple[float, float, float], destination: Tuple[float, float, float]) -> Dict:
    """
    Analyze the efficiency of each path segment.
    
    Args:
        path: Complete PPO path
        origin: Origin coordinates
        ppo: PPO coordinates  
        destination: Destination coordinates
        
    Returns:
        Dictionary with segment efficiency analysis
    """
    # Find PPO position in path
    ppo_index = -1
    for i, point in enumerate(path):
        if calculate_distance(point, ppo) < 0.001:
            ppo_index = i
            break
    
    if ppo_index == -1:
        return {'error': 'PPO not found in path'}
    
    # Split path into segments
    segment1_path = path[:ppo_index + 1]  # Origin → PPO
    segment2_path = path[ppo_index:]      # PPO → Destination
    
    # Calculate segment metrics
    segment1_distance = calculate_path_distance(segment1_path)
    segment2_distance = calculate_path_distance(segment2_path)
    direct1_distance = calculate_distance(origin, ppo)
    direct2_distance = calculate_distance(ppo, destination)
    
    return {
        'ppo_index': ppo_index,
        'segment1': {
            'path_distance': segment1_distance,
            'direct_distance': direct1_distance,
            'efficiency': (direct1_distance / segment1_distance * 100) if segment1_distance > 0 else 0,
            'points': len(segment1_path),
            'overhead': segment1_distance - direct1_distance
        },
        'segment2': {
            'path_distance': segment2_distance,
            'direct_distance': direct2_distance,
            'efficiency': (direct2_distance / segment2_distance * 100) if segment2_distance > 0 else 0,
            'points': len(segment2_path),
            'overhead': segment2_distance - direct2_distance
        },
        'overall': {
            'total_path_distance': segment1_distance + segment2_distance,
            'total_direct_distance': direct1_distance + direct2_distance,
            'efficiency': ((direct1_distance + direct2_distance) / (segment1_distance + segment2_distance) * 100) if (segment1_distance + segment2_distance) > 0 else 0
        }
    }

def analyze_ppo_c4_backtracking():
    """Main analysis function for PPO C4 backtracking detection."""
    
    print("🔍 PPO C4 Backtracking Analysis")
    print("=" * 60)
    print()
    
    # Scenario C3 coordinates
    origin = (176.553, 6.028, 150.340)      # C1 - System B
    ppo = (169.378, 5.669, 140.678)         # C4 - System B
    destination = (174.860, 15.369, 136.587) # C3 - System B
    cable_type = "C"
    
    # Required files
    graph_file = "graph_LV_combined.json"
    tramo_map_file = "tramo_map_combined.json"
    
    print(f"📋 Configuration:")
    print(f"   Origin (C1):      {format_point(origin)}")
    print(f"   PPO (C4):         {format_point(ppo)}")
    print(f"   Destination (C3): {format_point(destination)}")
    print(f"   Cable Type:       {cable_type}")
    print()
    
    try:
        # Create SystemFilteredGraph and find PPO path
        graph = SystemFilteredGraph(graph_file, cable_type, tramo_map_file)
        
        print("🔄 Computing PPO path...")
        ppo_path, ppo_nodes = graph.find_path_with_ppo(origin, ppo, destination)
        
        if not ppo_path:
            print("❌ PPO path not found")
            return None
        
        print(f"✅ PPO path computed: {len(ppo_path)} points")
        print()
        
        # ================================================================
        # Analysis 1: Repeated Coordinates
        # ================================================================
        print("🔍 Analysis 1: Repeated Coordinates")
        print("-" * 40)
        
        coord_analysis = find_repeated_coordinates(ppo_path)
        
        print(f"Total path points: {coord_analysis['total_path_points']}")
        print(f"Unique coordinates: {coord_analysis['total_unique_coordinates']}")
        print(f"Repeated coordinates: {coord_analysis['repetition_count']}")
        print(f"Total revisits: {coord_analysis['total_revisits']}")
        
        if coord_analysis['repeated_coordinates']:
            print(f"\n📍 Repeated Coordinate Details:")
            for i, (coord, visits) in enumerate(list(coord_analysis['repeated_coordinates'].items())[:5]):  # Show first 5
                print(f"   {i+1}. {format_point(coord)} - visited at positions: {visits}")
                if i >= 4 and len(coord_analysis['repeated_coordinates']) > 5:
                    print(f"   ... and {len(coord_analysis['repeated_coordinates']) - 5} more")
                    break
        else:
            print("✅ No repeated coordinates found - no backtracking to exact positions")
        
        print()
        
        # ================================================================
        # Analysis 2: Repeated Segments
        # ================================================================
        print("🔍 Analysis 2: Repeated Path Segments")
        print("-" * 40)
        
        segment_analysis = find_repeated_segments(ppo_path)
        
        print(f"Total path segments: {segment_analysis['total_path_segments']}")
        print(f"Unique segments: {segment_analysis['total_unique_segments']}")
        print(f"Repeated segments: {segment_analysis['repetition_count']}")
        print(f"Total retraversals: {segment_analysis['total_retraversals']}")
        
        if segment_analysis['repeated_segments']:
            print(f"\n🔄 Repeated Segment Details:")
            for i, (segment, visits) in enumerate(list(segment_analysis['repeated_segments'].items())[:3]):  # Show first 3
                start, end = segment
                print(f"   {i+1}. {format_point(start)} ↔ {format_point(end)}")
                print(f"      Traversed at segment positions: {visits}")
                if i >= 2 and len(segment_analysis['repeated_segments']) > 3:
                    print(f"   ... and {len(segment_analysis['repeated_segments']) - 3} more")
                    break
        else:
            print("✅ No repeated segments found - no edge retraversal")
        
        print()
        
        # ================================================================
        # Analysis 3: Backtracking Patterns
        # ================================================================
        print("🔍 Analysis 3: Backtracking Patterns")
        print("-" * 40)
        
        backtrack_analysis = analyze_backtracking_patterns(ppo_path)
        
        print(f"Backtrack events: {backtrack_analysis['backtrack_count']}")
        print(f"Direction changes (>90°): {backtrack_analysis['direction_changes']}")
        print(f"Total backtrack distance: {backtrack_analysis['total_backtrack_distance']:.3f} units")
        
        if backtrack_analysis['backtrack_events']:
            print(f"\n↩️  Backtrack Event Details:")
            for i, event in enumerate(backtrack_analysis['backtrack_events'][:3]):  # Show first 3
                print(f"   {i+1}. Position {event['position']}: {format_point(event['via'])}")
                print(f"      Backtrack distance: {event['backtrack_distance']:.3f} units")
                print(f"      Distance saved: {event['saved_distance']:.3f} units")
                if i >= 2 and len(backtrack_analysis['backtrack_events']) > 3:
                    print(f"   ... and {len(backtrack_analysis['backtrack_events']) - 3} more")
                    break
        else:
            print("✅ No significant backtracking patterns detected")
        
        print()
        
        # ================================================================
        # Analysis 4: Segment Efficiency
        # ================================================================
        print("🔍 Analysis 4: Segment Efficiency Analysis")
        print("-" * 40)
        
        efficiency_analysis = analyze_segment_efficiency(ppo_path, origin, ppo, destination)
        
        if 'error' in efficiency_analysis:
            print(f"❌ {efficiency_analysis['error']}")
        else:
            print(f"PPO found at position: {efficiency_analysis['ppo_index'] + 1}/{len(ppo_path)}")
            print()
            
            # Segment 1: Origin → PPO
            seg1 = efficiency_analysis['segment1']
            print(f"📊 Segment 1 (C1 → C4):")
            print(f"   Path distance: {seg1['path_distance']:.3f} units")
            print(f"   Direct distance: {seg1['direct_distance']:.3f} units")
            print(f"   Efficiency: {seg1['efficiency']:.1f}%")
            print(f"   Overhead: {seg1['overhead']:.3f} units")
            print(f"   Points: {seg1['points']}")
            print()
            
            # Segment 2: PPO → Destination  
            seg2 = efficiency_analysis['segment2']
            print(f"📊 Segment 2 (C4 → C3):")
            print(f"   Path distance: {seg2['path_distance']:.3f} units")
            print(f"   Direct distance: {seg2['direct_distance']:.3f} units")
            print(f"   Efficiency: {seg2['efficiency']:.1f}%")
            print(f"   Overhead: {seg2['overhead']:.3f} units")
            print(f"   Points: {seg2['points']}")
            print()
            
            # Overall efficiency
            overall = efficiency_analysis['overall']
            print(f"📊 Overall PPO Routing:")
            print(f"   Total path distance: {overall['total_path_distance']:.3f} units")
            print(f"   Total direct distance: {overall['total_direct_distance']:.3f} units")
            print(f"   Overall efficiency: {overall['efficiency']:.1f}%")
        
        print()
        
        # ================================================================
        # Summary and Conclusions
        # ================================================================
        print("📋 Summary and Conclusions")
        print("-" * 40)
        
        has_backtracking = (coord_analysis['total_revisits'] > 0 or 
                           segment_analysis['total_retraversals'] > 0 or
                           backtrack_analysis['backtrack_count'] > 0)
        
        if has_backtracking:
            print("❌ BACKTRACKING DETECTED:")
            if coord_analysis['total_revisits'] > 0:
                print(f"   • {coord_analysis['total_revisits']} coordinate revisits")
            if segment_analysis['total_retraversals'] > 0:
                print(f"   • {segment_analysis['total_retraversals']} segment retraversals")
            if backtrack_analysis['backtrack_count'] > 0:
                print(f"   • {backtrack_analysis['backtrack_count']} backtrack events")
        else:
            print("✅ NO BACKTRACKING DETECTED:")
            print("   • No repeated coordinates")
            print("   • No repeated segments")
            print("   • No backtracking patterns")
        
        print()
        print("🎯 Path Characteristics:")
        efficiency_pct = efficiency_analysis['overall']['efficiency'] if 'overall' in efficiency_analysis else 0
        if efficiency_pct > 80:
            efficiency_rating = "EXCELLENT"
        elif efficiency_pct > 60:
            efficiency_rating = "GOOD"
        elif efficiency_pct > 40:
            efficiency_rating = "MODERATE"
        else:
            efficiency_rating = "POOR"
            
        print(f"   • Overall efficiency: {efficiency_pct:.1f}% ({efficiency_rating})")
        print(f"   • Direction changes: {backtrack_analysis['direction_changes']} (complexity indicator)")
        print(f"   • Path straightness: {'HIGH' if backtrack_analysis['direction_changes'] < 10 else 'MODERATE' if backtrack_analysis['direction_changes'] < 20 else 'LOW'}")
        
        # Save analysis results (convert tuples to lists for JSON serialization)
        results = {
            'scenario': 'C3_backtracking_analysis',
            'coordinates': {
                'origin': list(origin),
                'ppo': list(ppo),
                'destination': list(destination)
            },
            'path_length': len(ppo_path),
            'repeated_coordinates': {
                'total_unique_coordinates': coord_analysis['total_unique_coordinates'],
                'total_path_points': coord_analysis['total_path_points'],
                'repetition_count': coord_analysis['repetition_count'],
                'total_revisits': coord_analysis['total_revisits']
            },
            'repeated_segments': {
                'total_unique_segments': segment_analysis['total_unique_segments'],
                'total_path_segments': segment_analysis['total_path_segments'],
                'repetition_count': segment_analysis['repetition_count'],
                'total_retraversals': segment_analysis['total_retraversals']
            },
            'backtracking_patterns': {
                'backtrack_count': backtrack_analysis['backtrack_count'],
                'direction_changes': backtrack_analysis['direction_changes'],
                'total_backtrack_distance': backtrack_analysis['total_backtrack_distance']
            },
            'segment_efficiency': efficiency_analysis,
            'has_backtracking': has_backtracking,
            'efficiency_rating': efficiency_rating
        }
        
        with open('ppo_c4_backtracking_analysis.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print()
        print(f"📄 Detailed analysis saved to: ppo_c4_backtracking_analysis.json")
        
        return results
        
    except Exception as e:
        print(f"❌ Error in analysis: {e}")
        return None

def main():
    """Main execution function."""
    print("🔧 PPO C4 Backtracking Analysis Tool")
    print("Analyzing path efficiency and backtracking patterns")
    print()
    
    results = analyze_ppo_c4_backtracking()
    
    if results:
        print("\n🎉 Analysis completed successfully!")
        
        if results['has_backtracking']:
            print("\n⚠️  BACKTRACKING FOUND - Path contains inefficiencies")
        else:
            print("\n✅ NO BACKTRACKING - Path is efficient (no repeated segments)")
            
        return 0
    else:
        print("\n❌ Analysis failed - check error messages above")
        return 1

if __name__ == "__main__":
    exit(main()) 