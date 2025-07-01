#!/usr/bin/env python3
"""
Create a combined DXF showing both direct and forbidden paths
"""

import json
import sys
import subprocess
from typing import List, Tuple
from math import sqrt

try:
    import ezdxf
except ImportError:
    print("Error: ezdxf library not found. Install it with: pip install ezdxf")
    sys.exit(1)

def get_path_from_export_script(graph_file: str, start: Tuple[float, float, float], 
                               goal: Tuple[float, float, float]) -> List[Tuple[float, float, float]]:
    """Extract path coordinates by running the export script and parsing output."""
    
    # Create a temporary DXF file
    temp_dxf = "temp_path.dxf"
    
    cmd = [
        "python3", "export_path_to_dxf.py", graph_file,
        str(start[0]), str(start[1]), str(start[2]),
        str(goal[0]), str(goal[1]), str(goal[2]),
        temp_dxf
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Parse the output to extract path information
        path_points = []
        total_distance = 0.0
        
        for line in result.stdout.split('\n'):
            if 'Path length:' in line:
                path_length = int(line.split('Path length:')[1].split('points')[0].strip())
            elif 'Total distance:' in line:
                total_distance = float(line.split('Total distance:')[1].split('units')[0].strip())
        
        # Read the DXF file to extract coordinates
        try:
            doc = ezdxf.readfile(temp_dxf)
            msp = doc.modelspace()
            
            # Extract line coordinates from PATH_LINES layer
            for entity in msp.query('LINE[layer=="PATH_LINES"]'):
                start_point = entity.dxf.start
                end_point = entity.dxf.end
                path_points.extend([
                    (start_point.x, start_point.y, start_point.z),
                    (end_point.x, end_point.y, end_point.z)
                ])
            
            # Remove duplicates while preserving order
            unique_points = []
            for point in path_points:
                if point not in unique_points:
                    unique_points.append(point)
            
            return unique_points, total_distance
            
        except Exception as e:
            print(f"Warning: Could not extract coordinates from DXF: {e}")
            return [], total_distance
            
    except subprocess.CalledProcessError as e:
        print(f"Error running export script: {e}")
        return [], 0.0

def create_combined_dxf(start: Tuple[float, float, float], goal: Tuple[float, float, float],
                       direct_graph: str, forbidden_graph: str, output_file: str):
    """Create a combined DXF with both paths."""
    
    print(f"🎯 Creating combined DXF comparison")
    print(f"   Start: C2 {start}")
    print(f"   Goal: C3 {goal}")
    
    # Get direct path
    print(f"📍 Extracting direct path...")
    direct_points, direct_distance = get_path_from_export_script(direct_graph, start, goal)
    
    # Get forbidden path
    print(f"🚫 Extracting forbidden path...")
    forbidden_points, forbidden_distance = get_path_from_export_script(forbidden_graph, start, goal)
    
    # Create new DXF document
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Add layers
    doc.layers.new('DIRECT_PATH', dxfattribs={'color': 2})      # Yellow
    doc.layers.new('FORBIDDEN_PATH', dxfattribs={'color': 1})   # Red
    doc.layers.new('START_GOAL', dxfattribs={'color': 3})       # Green
    doc.layers.new('ANNOTATIONS', dxfattribs={'color': 7})      # White
    
    # Add start and goal markers
    msp.add_circle(start, radius=3.0, dxfattribs={'layer': 'START_GOAL'})
    msp.add_circle(goal, radius=3.0, dxfattribs={'layer': 'START_GOAL'})
    
    # Draw direct path
    if len(direct_points) > 1:
        for i in range(len(direct_points) - 1):
            msp.add_line(direct_points[i], direct_points[i + 1], 
                        dxfattribs={'layer': 'DIRECT_PATH'})
    
    # Draw forbidden path
    if len(forbidden_points) > 1:
        for i in range(len(forbidden_points) - 1):
            msp.add_line(forbidden_points[i], forbidden_points[i + 1], 
                        dxfattribs={'layer': 'FORBIDDEN_PATH'})
    
    # Add annotations
    y_offset = max(start[1], goal[1]) + 15
    
    # Direct path info
    direct_text = f"DIRECT PATH (Yellow)\nPoints: {len(direct_points)}\nDistance: {direct_distance:.3f} units"
    direct_annotation = msp.add_text(direct_text, dxfattribs={'layer': 'ANNOTATIONS', 'height': 1.5})
    direct_annotation.set_placement((start[0], y_offset, start[2]))
    
    # Forbidden path info
    forbidden_text = f"FORBIDDEN PATH (Red)\nPoints: {len(forbidden_points)}\nDistance: {forbidden_distance:.3f} units"
    forbidden_annotation = msp.add_text(forbidden_text, dxfattribs={'layer': 'ANNOTATIONS', 'height': 1.5})
    forbidden_annotation.set_placement((goal[0], y_offset, goal[2]))
    
    # Comparison info
    if direct_distance > 0 and forbidden_distance > 0:
        increase = ((forbidden_distance - direct_distance) / direct_distance) * 100
        comparison_text = f"COMPARISON\nDirect: {direct_distance:.3f} units\nForbidden: {forbidden_distance:.3f} units\nIncrease: {increase:.1f}%"
        comparison_annotation = msp.add_text(comparison_text, dxfattribs={'layer': 'ANNOTATIONS', 'height': 1.2})
        comparison_annotation.set_placement(((start[0] + goal[0])/2, y_offset + 10, (start[2] + goal[2])/2))
    
    # Add reference line
    msp.add_line(start, goal, dxfattribs={'layer': 'ANNOTATIONS', 'linetype': 'DASHED'})
    
    # Save DXF
    doc.saveas(output_file)
    
    print(f"✅ Combined DXF saved: {output_file}")
    print(f"   Direct path: {len(direct_points)} points, {direct_distance:.3f} units")
    print(f"   Forbidden path: {len(forbidden_points)} points, {forbidden_distance:.3f} units")
    
    if direct_distance > 0 and forbidden_distance > 0:
        increase = ((forbidden_distance - direct_distance) / direct_distance) * 100
        print(f"   Path increase: {increase:.1f}%")

if __name__ == "__main__":
    # C2 to C3 coordinates
    start = (182.946, 13.304, 157.295)
    goal = (174.860, 15.369, 136.587)
    
    create_combined_dxf(
        start, goal,
        "graph_LV_combined_legacy.json",
        "graph_LV_combined_with_forbidden.json", 
        "C2_C3_combined_comparison.dxf"
    )
