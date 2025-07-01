#!/usr/bin/env python3
"""
Export astar_PPOF_systems.py results to DXF

This script runs astar_PPOF_systems.py and exports the results to DXF format.
"""

import subprocess
import json
import sys
import tempfile
import os
from typing import List, Tuple, Optional
from math import sqrt

try:
    import ezdxf
except ImportError:
    print("Error: ezdxf library not found. Install it with: pip install ezdxf")
    sys.exit(1)

def run_astar_ppof_and_capture_path(graph_file: str, origin: Tuple[float, float, float], 
                                   destination: Tuple[float, float, float], cable_type: str,
                                   tramo_map: str = None, forbidden: str = None) -> dict:
    """Run astar_PPOF_systems.py and capture the path information."""
    
    cmd = [
        "python3", "astar_PPOF_systems.py", "direct", graph_file,
        str(origin[0]), str(origin[1]), str(origin[2]),
        str(destination[0]), str(destination[1]), str(destination[2]),
        "--cable", cable_type
    ]
    
    if tramo_map and forbidden:
        cmd.extend(["--tramo-map", tramo_map, "--forbidden", forbidden])
    
    print(f"🚀 Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout
        
        # Parse the output to extract path information
        path_info = {
            'success': 'Direct path found!' in output,
            'output': output,
            'command': ' '.join(cmd)
        }
        
        # Extract metrics from output
        for line in output.split('\n'):
            if 'Path length:' in line:
                path_info['path_length'] = int(line.split('Path length:')[1].split('points')[0].strip())
            elif 'Total distance:' in line:
                path_info['total_distance'] = float(line.split('Total distance:')[1].split('units')[0].strip())
            elif 'Nodes explored:' in line:
                path_info['nodes_explored'] = int(line.split('Nodes explored:')[1].strip())
            elif 'Forbidden tramo IDs:' in line:
                path_info['forbidden_sections'] = line.split('Forbidden tramo IDs:')[1].strip()
        
        return path_info
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running astar_PPOF_systems.py: {e}")
        print(f"   Stdout: {e.stdout}")
        print(f"   Stderr: {e.stderr}")
        return {'success': False, 'error': str(e)}

def create_comparison_dxf(origin: Tuple[float, float, float], 
                         destination: Tuple[float, float, float],
                         direct_info: dict, forbidden_info: dict,
                         output_file: str) -> None:
    """Create a DXF file comparing both paths."""
    
    # Create a new DXF document
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Add layers for different elements
    doc.layers.new('DIRECT_PATH', dxfattribs={'color': 2})        # Yellow for direct path
    doc.layers.new('FORBIDDEN_PATH', dxfattribs={'color': 1})     # Red for forbidden path
    doc.layers.new('START_GOAL', dxfattribs={'color': 3})         # Green for start/goal
    doc.layers.new('ANNOTATIONS', dxfattribs={'color': 7})        # White for text
    
    # Add start and goal markers
    msp.add_circle(origin, radius=2.0, dxfattribs={'layer': 'START_GOAL'})
    msp.add_circle(destination, radius=2.0, dxfattribs={'layer': 'START_GOAL'})
    
    # Add text annotations for start and goal
    origin_text = msp.add_text(f"C2 Origin\n{origin}", dxfattribs={'layer': 'ANNOTATIONS', 'height': 1.0})
    origin_text.set_placement((origin[0], origin[1] + 3, origin[2]))
    
    dest_text = msp.add_text(f"C3 Destination\n{destination}", dxfattribs={'layer': 'ANNOTATIONS', 'height': 1.0})
    dest_text.set_placement((destination[0], destination[1] + 3, destination[2]))
    
    # Add comparison information as text
    y_offset = max(origin[1], destination[1]) + 10
    
    if direct_info['success']:
        direct_text = f"DIRECT PATH (Yellow)\nLength: {direct_info.get('path_length', 'N/A')} points\nDistance: {direct_info.get('total_distance', 'N/A')} units\nNodes: {direct_info.get('nodes_explored', 'N/A')}"
        direct_annotation = msp.add_text(direct_text, dxfattribs={'layer': 'ANNOTATIONS', 'height': 0.8})
        direct_annotation.set_placement((origin[0], y_offset, origin[2]))
    
    if forbidden_info['success']:
        forbidden_text = f"FORBIDDEN PATH (Red)\nLength: {forbidden_info.get('path_length', 'N/A')} points\nDistance: {forbidden_info.get('total_distance', 'N/A')} units\nNodes: {forbidden_info.get('nodes_explored', 'N/A')}\nForbidden: {forbidden_info.get('forbidden_sections', 'N/A')}"
        forbidden_annotation = msp.add_text(forbidden_text, dxfattribs={'layer': 'ANNOTATIONS', 'height': 0.8})
        forbidden_annotation.set_placement((destination[0], y_offset, destination[2]))
    
    # Add a line between origin and destination for reference
    msp.add_line(origin, destination, dxfattribs={'layer': 'ANNOTATIONS', 'linetype': 'DASHED'})
    
    # Save the DXF file
    doc.saveas(output_file)
    
    print(f"✅ Comparison DXF saved: {output_file}")
    print(f"   Layers: DIRECT_PATH (yellow), FORBIDDEN_PATH (red), START_GOAL (green), ANNOTATIONS (white)")

def main():
    if len(sys.argv) < 8:
        print("Usage: python3 export_astar_ppof_to_dxf.py graph.json origin_x origin_y origin_z dest_x dest_y dest_z cable_type [tramo_map.json] [forbidden.json]")
        sys.exit(1)
    
    graph_file = sys.argv[1]
    origin = (float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]))
    destination = (float(sys.argv[5]), float(sys.argv[6]), float(sys.argv[7]))
    cable_type = sys.argv[8]
    
    tramo_map = sys.argv[9] if len(sys.argv) > 9 else None
    forbidden = sys.argv[10] if len(sys.argv) > 10 else None
    
    print(f"🎯 Exporting C2 to C3 paths to DXF")
    print(f"   Origin: {origin}")
    print(f"   Destination: {destination}")
    print(f"   Cable: {cable_type}")
    
    # Run direct path (without forbidden sections)
    print(f"\n📍 Running direct path...")
    direct_info = run_astar_ppof_and_capture_path(graph_file, origin, destination, cable_type)
    
    # Run path with forbidden sections (if provided)
    forbidden_info = {'success': False}
    if tramo_map and forbidden:
        print(f"\n�� Running path with forbidden sections...")
        forbidden_info = run_astar_ppof_and_capture_path(graph_file, origin, destination, cable_type, tramo_map, forbidden)
    
    # Create comparison DXF
    output_file = f"C2_C3_comparison_{cable_type}.dxf"
    create_comparison_dxf(origin, destination, direct_info, forbidden_info, output_file)
    
    # Print summary
    print(f"\n📊 Summary:")
    if direct_info['success']:
        print(f"   ✅ Direct path: {direct_info.get('path_length', 'N/A')} points, {direct_info.get('total_distance', 'N/A')} units")
    else:
        print(f"   ❌ Direct path failed")
    
    if forbidden_info['success']:
        print(f"   ✅ Forbidden path: {forbidden_info.get('path_length', 'N/A')} points, {forbidden_info.get('total_distance', 'N/A')} units")
    else:
        print(f"   ❌ Forbidden path not run or failed")

if __name__ == "__main__":
    main()
