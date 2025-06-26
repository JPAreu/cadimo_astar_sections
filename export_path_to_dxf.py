#!/usr/bin/env python3
"""
Export A* Pathfinding Results to DXF

This script runs the A* pathfinding algorithm and exports the resulting path
to DXF format for visualization in CAD software.

Usage:
    python3 export_path_to_dxf.py graph.json start_x start_y start_z goal_x goal_y goal_z output.dxf [--tolerance 1.0]
"""

import sys
import argparse
import json
from typing import List, Tuple, Optional
from math import sqrt

# Import the pathfinding algorithm
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from astar_spatial_IP import OptimizedSpatialGraph3D
from astar_PPO import run_astar_with_ppo, run_astar_with_multiple_ppos

try:
    import ezdxf
except ImportError:
    print("Error: ezdxf library not found. Install it with: pip install ezdxf")
    sys.exit(1)

def create_dxf_from_path(path: List[Tuple[float, float, float]], 
                        output_file: str,
                        start_point: Tuple[float, float, float],
                        goal_point: Tuple[float, float, float],
                        match_info: dict = None,
                        ppo_points: List[Tuple[float, float, float]] = None) -> None:
    """
    Create a DXF file from the pathfinding results.
    
    Args:
        path: List of 3D coordinates forming the path
        output_file: Output DXF file path
        start_point: Original start coordinates
        goal_point: Original goal coordinates
        match_info: Information about coordinate matching
        ppo_points: List of PPO coordinates to mark with circles
    """
    # Create a new DXF document
    doc = ezdxf.new('R2010')  # Use AutoCAD 2010 format for compatibility
    msp = doc.modelspace()
    
    if not path:
        print("No path to export - creating empty DXF file")
        doc.saveas(output_file)
        return
    
    # Add layers for different elements
    doc.layers.new('PATH_LINES', dxfattribs={'color': 2})      # Yellow for path lines
    doc.layers.new('PPO_POINTS', dxfattribs={'color': 1})      # Red for PPO waypoints
    doc.layers.new('START_GOAL', dxfattribs={'color': 3})      # Green for start/goal
    
    # Draw the path as connected line segments
    print(f"Drawing path with {len(path)} points...")
    
    for i in range(len(path) - 1):
        start_3d = path[i]
        end_3d = path[i + 1]
        
        # Create 3D line
        msp.add_line(start_3d, end_3d, dxfattribs={'layer': 'PATH_LINES'})
    
    # Add circles only for PPO waypoints (if any)
    if ppo_points:
        for ppo_point in ppo_points:
            if ppo_point in path:  # Only mark PPOs that are actually in the path
                msp.add_circle(ppo_point, radius=1.5, dxfattribs={'layer': 'PPO_POINTS'})
    
    # Mark start and goal points with larger markers
    # Start point marker (green sphere representation)
    msp.add_circle(path[0], radius=2.0, dxfattribs={'layer': 'START_GOAL'})
    
    # Goal point marker (green sphere representation)
    msp.add_circle(path[-1], radius=2.0, dxfattribs={'layer': 'START_GOAL'})
    
    # Calculate total distance for reporting
    total_distance = 0
    for i in range(len(path) - 1):
        segment_distance = sqrt(sum((a - b) ** 2 for a, b in zip(path[i], path[i + 1])))
        total_distance += segment_distance
    
    # Save the DXF file
    doc.saveas(output_file)
    print(f"✅ DXF file saved: {output_file}")
    print(f"   Path points: {len(path)}")
    print(f"   Total distance: {total_distance:.3f} units")
    if ppo_points:
        print(f"   PPO waypoints marked: {len(ppo_points)}")
        print(f"   Layers created: PATH_LINES, PPO_POINTS, START_GOAL")
    else:
        print(f"   Layers created: PATH_LINES, START_GOAL")

def run_pathfinding_and_export(graph_file: str,
                              start_point: Tuple[float, float, float],
                              goal_point: Tuple[float, float, float],
                              output_file: str,
                              tolerance: float = 1.0,
                              grid_size: float = 1.0,
                              edge_split: bool = False,
                              ppo_points: List[Tuple[float, float, float]] = None) -> None:
    """
    Run pathfinding and export results to DXF.
    
    Args:
        graph_file: Path to graph JSON file
        start_point: Starting coordinates
        goal_point: Goal coordinates
        output_file: Output DXF file path
        tolerance: Tolerance for coordinate matching
        grid_size: Grid size for spatial indexing
        edge_split: Enable edge splitting
        ppo_points: List of PPO (mandatory waypoint) coordinates
    """
    print(f"🚀 Running A* pathfinding...")
    print(f"   Graph: {graph_file}")
    print(f"   Start: {start_point}")
    if ppo_points:
        print(f"   PPOs: {ppo_points}")
    print(f"   Goal: {goal_point}")
    print(f"   Tolerance: {tolerance}")
    print(f"   Edge split: {'Enabled' if edge_split else 'Disabled'}")
    
    # Run pathfinding with or without PPOs
    try:
        if ppo_points:
            # PPO pathfinding
            if len(ppo_points) == 1:
                path, nodes_explored = run_astar_with_ppo(graph_file, start_point, ppo_points[0], goal_point)
            else:
                path, nodes_explored, segments = run_astar_with_multiple_ppos(graph_file, start_point, ppo_points, goal_point)
            
            # Create match_info for compatibility
            match_info = {
                'start_match': type('obj', (object,), {'matched_node': start_point, 'distance': 0.0}),
                'goal_match': type('obj', (object,), {'matched_node': goal_point, 'distance': 0.0}),
                'start_usable': True,
                'goal_usable': True,
                'both_usable': True
            }
        else:
            # Direct pathfinding (existing code)
            graph = OptimizedSpatialGraph3D(graph_file, grid_size=grid_size, tolerance=tolerance)
            
            if edge_split:
                path, nodes_explored = graph.find_path_with_edge_split(start_point, goal_point)
                if path is not None:
                    match_info = {
                        'start_match': type('obj', (object,), {'matched_node': start_point, 'distance': 0.0}),
                        'goal_match': type('obj', (object,), {'matched_node': goal_point, 'distance': 0.0}),
                        'start_usable': True,
                        'goal_usable': True,
                        'both_usable': True
                    }
                else:
                    match_info = {
                        'start_match': None,
                        'goal_match': None,
                        'start_usable': False,
                        'goal_usable': False,
                        'both_usable': False
                    }
            else:
                path, match_info = graph.find_path_with_tolerance(start_point, goal_point)
    except Exception as e:
        print(f"❌ Error during pathfinding: {e}")
        return
    
    # Display pathfinding results
    if path:
        print(f"✅ Path found!")
        if not ppo_points and match_info['start_match'] and match_info['goal_match']:
            print(f"   Start match: {match_info['start_match'].matched_node} (distance: {match_info['start_match'].distance:.3f})")
            print(f"   Goal match: {match_info['goal_match'].matched_node} (distance: {match_info['goal_match'].distance:.3f})")
        elif ppo_points:
            print(f"   PPO pathfinding with {len(ppo_points)} waypoint(s)")
        print(f"   Path length: {len(path)} points")
        
        # Calculate total distance
        total_distance = 0
        for i in range(len(path) - 1):
            segment_distance = sqrt(sum((a - b) ** 2 for a, b in zip(path[i], path[i + 1])))
            total_distance += segment_distance
        print(f"   Total distance: {total_distance:.3f} units")
    else:
        print(f"❌ No path found")
        if not ppo_points:
            print(f"   Start usable: {match_info['start_usable']}")
            print(f"   Goal usable: {match_info['goal_usable']}")
            if not match_info['start_usable']:
                print(f"   Start issue: {match_info['start_match']}")
            if not match_info['goal_usable']:
                print(f"   Goal issue: {match_info['goal_match']}")
    
    # Export to DXF
    print(f"📄 Exporting to DXF...")
    create_dxf_from_path(path, output_file, start_point, goal_point, match_info, ppo_points)

def main():
    parser = argparse.ArgumentParser(
        description="Run A* pathfinding and export results to DXF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard mode
  python3 export_path_to_dxf.py graph_LVA1.json 139.232 28.845 139.993 152.290 17.883 160.124 path_result.dxf
  
  # Edge split mode for intermediate points
  python3 export_path_to_dxf.py graph_LVA1.json 143.382 25.145 160.703 139.232 28.845 139.993 P5_to_P1.dxf --edge-split
  
  # PPO pathfinding (single waypoint)
  python3 export_path_to_dxf.py graph_LVA1.json 152.290 17.883 160.124 139.232 28.845 139.993 P2_P5_P1.dxf --ppo 143.382 25.145 160.703
  
  # PPO pathfinding (multiple waypoints)
  python3 export_path_to_dxf.py graph_LVA1.json 152.290 17.883 160.124 139.232 28.845 139.993 multi_ppo.dxf --ppo 143.382 25.145 160.703 --ppo 140.183 28.000 149.385
  
  # Custom tolerance
  python3 export_path_to_dxf.py graph.json 100 200 300 400 500 600 output.dxf --tolerance 5.0
        """
    )
    
    parser.add_argument('graph_file', help='JSON graph file path')
    parser.add_argument('start_x', type=float, help='Start X coordinate')
    parser.add_argument('start_y', type=float, help='Start Y coordinate')
    parser.add_argument('start_z', type=float, help='Start Z coordinate')
    parser.add_argument('goal_x', type=float, help='Goal X coordinate')
    parser.add_argument('goal_y', type=float, help='Goal Y coordinate')
    parser.add_argument('goal_z', type=float, help='Goal Z coordinate')
    parser.add_argument('output_dxf', help='Output DXF file path')
    parser.add_argument('--tolerance', type=float, default=1.0,
                        help='Tolerance for coordinate matching (default: 1.0)')
    parser.add_argument('--grid-size', type=float, default=1.0,
                        help='Grid cell size for spatial indexing (default: 1.0)')
    parser.add_argument('--edge-split', action='store_true',
                        help='Enable edge split for intermediate points on edges')
    parser.add_argument('--ppo', action='append', nargs=3, type=float, metavar=('X', 'Y', 'Z'),
                        help='Add PPO (mandatory waypoint) coordinates. Can be used multiple times.')
    
    args = parser.parse_args()
    
    # Parse coordinates
    start_point = (args.start_x, args.start_y, args.start_z)
    goal_point = (args.goal_x, args.goal_y, args.goal_z)
    
    # Parse PPO points
    ppo_points = None
    if args.ppo:
        ppo_points = [tuple(ppo) for ppo in args.ppo]
    
    # Run pathfinding and export
    run_pathfinding_and_export(
        args.graph_file,
        start_point,
        goal_point,
        args.output_dxf,
        args.tolerance,
        args.grid_size,
        args.edge_split,
        ppo_points
    )

if __name__ == "__main__":
    main() 