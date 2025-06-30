#!/usr/bin/env python3
# export_forward_path.py
# Export forward path results to DXF format

import sys
import subprocess
import json
import os
from datetime import datetime
import ezdxf

def run_forward_path_and_export(graph_file, origin, ppo, destination, tramos_file, output_dxf):
    """
    Run forward_path command and export results to DXF
    """
    # Build the command
    cmd = [
        'python3', 'astar_PPO_forbid.py', 'forward_path',
        graph_file,
        str(origin[0]), str(origin[1]), str(origin[2]),
        str(ppo[0]), str(ppo[1]), str(ppo[2]),
        str(destination[0]), str(destination[1]), str(destination[2]),
        '--tramos', tramos_file
    ]
    
    print(f"🚀 Running forward path command...")
    print(f"   Command: {' '.join(cmd)}")
    
    # Run the command and capture output
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Error running forward path: {result.stderr}")
        return None
    
    # Parse the output to extract path points
    output_lines = result.stdout.split('\n')
    path_points = []
    in_path_details = False
    
    for line in output_lines:
        if 'Path details:' in line:
            in_path_details = True
            continue
        
        if in_path_details and line.strip():
            # Parse lines like "  1. (152.290, 17.883, 160.124) [ORIGIN]"
            if '. (' in line:
                try:
                    # Extract coordinates between parentheses
                    start = line.find('(')
                    end = line.find(')')
                    if start != -1 and end != -1:
                        coords_str = line[start+1:end]
                        coords = [float(x.strip()) for x in coords_str.split(',')]
                        if len(coords) == 3:
                            path_points.append(tuple(coords))
                except:
                    continue
    
    if not path_points:
        print("❌ Could not extract path points from output")
        return None
    
    print(f"✅ Extracted {len(path_points)} path points")
    
    # Create DXF file
    create_forward_path_dxf(path_points, origin, ppo, destination, output_dxf)
    
    return path_points

def create_forward_path_dxf(path_points, origin, ppo, destination, output_dxf):
    """
    Create DXF file with forward path visualization
    """
    print(f"📄 Creating DXF file: {output_dxf}")
    
    # Create new DXF document
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Create layers
    doc.layers.new('PATH_LINES', dxfattribs={'color': 1})  # Red for path
    doc.layers.new('ORIGIN_POINT', dxfattribs={'color': 2})  # Yellow for origin
    doc.layers.new('PPO_POINT', dxfattribs={'color': 3})  # Green for PPO
    doc.layers.new('DESTINATION_POINT', dxfattribs={'color': 4})  # Cyan for destination
    doc.layers.new('FORWARD_PATH_INFO', dxfattribs={'color': 7})  # White for info
    
    # Draw path lines
    for i in range(len(path_points) - 1):
        start_point = path_points[i]
        end_point = path_points[i + 1]
        
        msp.add_line(
            start_point, end_point,
            dxfattribs={'layer': 'PATH_LINES', 'color': 1}
        )
    
    # Mark special points
    # Origin
    msp.add_circle(
        origin, 0.5,
        dxfattribs={'layer': 'ORIGIN_POINT', 'color': 2}
    )
    msp.add_text(
        'ORIGIN', 
        dxfattribs={'layer': 'ORIGIN_POINT', 'color': 2, 'height': 0.5, 'insert': (origin[0], origin[1] + 1, origin[2])}
    )
    
    # PPO
    msp.add_circle(
        ppo, 0.5,
        dxfattribs={'layer': 'PPO_POINT', 'color': 3}
    )
    msp.add_text(
        'PPO', 
        dxfattribs={'layer': 'PPO_POINT', 'color': 3, 'height': 0.5, 'insert': (ppo[0], ppo[1] + 1, ppo[2])}
    )
    
    # Destination
    msp.add_circle(
        destination, 0.5,
        dxfattribs={'layer': 'DESTINATION_POINT', 'color': 4}
    )
    msp.add_text(
        'DESTINATION', 
        dxfattribs={'layer': 'DESTINATION_POINT', 'color': 4, 'height': 0.5, 'insert': (destination[0], destination[1] + 1, destination[2])}
    )
    
    # Add info text
    info_text = [
        f"Forward Path Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total Points: {len(path_points)}",
        f"Origin: P21 ({origin[0]:.3f}, {origin[1]:.3f}, {origin[2]:.3f})",
        f"PPO: P20 ({ppo[0]:.3f}, {ppo[1]:.3f}, {ppo[2]:.3f})",
        f"Destination: P17 ({destination[0]:.3f}, {destination[1]:.3f}, {destination[2]:.3f})",
        "Forward Path Logic: Prevents backtracking"
    ]
    
    # Find a good position for info text (top-left of bounding box)
    min_x = min(p[0] for p in path_points)
    max_y = max(p[1] for p in path_points)
    
    for i, text in enumerate(info_text):
        msp.add_text(
            text,
            dxfattribs={'layer': 'FORWARD_PATH_INFO', 'color': 7, 'height': 0.3, 'insert': (min_x, max_y + 2 + i * 0.5)}
        )
    
    # Save DXF file
    doc.saveas(output_dxf)
    print(f"✅ DXF file saved: {output_dxf}")
    print(f"   Layers: PATH_LINES, ORIGIN_POINT, PPO_POINT, DESTINATION_POINT, FORWARD_PATH_INFO")
    print(f"   Path points: {len(path_points)}")

if __name__ == "__main__":
    # Test coordinates from user
    origin = (139.232, 27.373, 152.313)  # P21
    ppo = (139.683, 26.922, 152.313)     # P20  
    destination = (139.200, 28.800, 156.500)  # P17
    
    graph_file = "graph_LVA1.json"
    tramos_file = "Output_Path_Sections/tramo_id_map_20250626_114538.json"
    output_dxf = "export_data/forward_path_P21_P20_P17_custom.dxf"
    
    # Ensure export directory exists
    os.makedirs("export_data", exist_ok=True)
    
    # Run forward path and export
    path_points = run_forward_path_and_export(
        graph_file, origin, ppo, destination, tramos_file, output_dxf
    )
    
    if path_points:
        print(f"\n🎯 Forward Path Export Complete!")
        print(f"   File: {output_dxf}")
        print(f"   Points: {len(path_points)}")
        print(f"   Forward path logic applied successfully") 