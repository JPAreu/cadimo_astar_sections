#!/usr/bin/env python3
"""
Export the actual forward path result from astar_PPOF_systems.py to DXF
"""

import subprocess
import sys
import tempfile
import json
from typing import List, Tuple

try:
    import ezdxf
except ImportError:
    print("Error: ezdxf library not found. Install it with: pip install ezdxf")
    sys.exit(1)

def capture_forward_path_result(graph_file: str, origin: Tuple[float, float, float], 
                               ppo: Tuple[float, float, float], destination: Tuple[float, float, float],
                               cable_type: str, tramo_map: str = None) -> List[Tuple[float, float, float]]:
    """Capture the actual path from astar_PPOF_systems.py forward_path command."""
    
    cmd = [
        "python3", "astar_PPOF_systems.py", "forward_path", graph_file,
        str(origin[0]), str(origin[1]), str(origin[2]),
        str(ppo[0]), str(ppo[1]), str(ppo[2]),
        str(destination[0]), str(destination[1]), str(destination[2]),
        "--cable", cable_type
    ]
    
    if tramo_map:
        cmd.extend(["--tramo-map", tramo_map])
    
    print(f"🚀 Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout
        
        # Parse the output to extract path coordinates
        # Look for the path details section
        path_coords = []
        in_path_section = False
        
        for line in output.split('\n'):
            if 'Path details:' in line:
                in_path_section = True
                continue
            elif in_path_section and line.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                # Extract coordinates from lines like "  1. (170.839, 12.530, 156.634) [ORIGIN]"
                try:
                    # Find the coordinates in parentheses
                    start = line.find('(')
                    end = line.find(')')
                    if start != -1 and end != -1:
                        coord_str = line[start+1:end]
                        coords = [float(x.strip()) for x in coord_str.split(',')]
                        if len(coords) == 3:
                            path_coords.append(tuple(coords))
                except:
                    continue
            elif in_path_section and line.strip() == '':
                break
        
        if path_coords:
            print(f"✅ Captured {len(path_coords)} path coordinates")
            return path_coords
        else:
            print("❌ No path coordinates found in output")
            return []
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running forward path: {e}")
        print(f"   Stdout: {e.stdout}")
        print(f"   Stderr: {e.stderr}")
        return []

def create_forward_path_dxf(path_coords: List[Tuple[float, float, float]], 
                           origin: Tuple[float, float, float], ppo: Tuple[float, float, float], 
                           destination: Tuple[float, float, float], output_file: str):
    """Create DXF file from the actual forward path coordinates."""
    
    if not path_coords:
        print("❌ No path coordinates to export")
        return
    
    # Create new DXF document
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Add layers
    doc.layers.new('FORWARD_PATH', dxfattribs={'color': 2})      # Yellow for forward path
    doc.layers.new('PPO_POINTS', dxfattribs={'color': 1})        # Red for PPO
    doc.layers.new('START_GOAL', dxfattribs={'color': 3})        # Green for start/goal
    doc.layers.new('ANNOTATIONS', dxfattribs={'color': 7})       # White for text
    doc.layers.new('SEGMENT_MARKERS', dxfattribs={'color': 5})   # Blue for segment boundaries
    
    # Draw the forward path
    for i in range(len(path_coords) - 1):
        msp.add_line(path_coords[i], path_coords[i + 1], 
                    dxfattribs={'layer': 'FORWARD_PATH'})
    
    # Mark start, PPO, and goal
    msp.add_circle(origin, radius=3.0, dxfattribs={'layer': 'START_GOAL'})
    msp.add_circle(destination, radius=3.0, dxfattribs={'layer': 'START_GOAL'})
    msp.add_circle(ppo, radius=2.5, dxfattribs={'layer': 'PPO_POINTS'})
    
    # Find PPO position in path for segment marking
    ppo_index = -1
    for i, coord in enumerate(path_coords):
        if abs(coord[0] - ppo[0]) < 0.001 and abs(coord[1] - ppo[1]) < 0.001 and abs(coord[2] - ppo[2]) < 0.001:
            ppo_index = i
            break
    
    # Add segment markers if PPO found
    if ppo_index > 0:
        # Mark segment 1 end / segment 2 start
        msp.add_circle(path_coords[ppo_index], radius=1.5, dxfattribs={'layer': 'SEGMENT_MARKERS'})
    
    # Add annotations
    y_offset = max(origin[1], ppo[1], destination[1]) + 10
    
    # Title and info
    title_text = f"FORWARD PATH A1→A5→A2\nBacktracking Prevention Enabled\nPoints: {len(path_coords)}"
    title_annotation = msp.add_text(title_text, dxfattribs={'layer': 'ANNOTATIONS', 'height': 1.5})
    title_annotation.set_placement((origin[0], y_offset, origin[2]))
    
    # Coordinate labels
    origin_text = msp.add_text(f"A1 (Origin)\n{origin}", dxfattribs={'layer': 'ANNOTATIONS', 'height': 1.0})
    origin_text.set_placement((origin[0], origin[1] + 3, origin[2]))
    
    ppo_text = msp.add_text(f"A5 (PPO)\n{ppo}", dxfattribs={'layer': 'ANNOTATIONS', 'height': 1.0})
    ppo_text.set_placement((ppo[0], ppo[1] + 3, ppo[2]))
    
    dest_text = msp.add_text(f"A2 (Destination)\n{destination}", dxfattribs={'layer': 'ANNOTATIONS', 'height': 1.0})
    dest_text.set_placement((destination[0], destination[1] + 3, destination[2]))
    
    # Segment info if PPO found
    if ppo_index > 0:
        segment_text = f"Segment 1: A1→A5 ({ppo_index+1} points)\nSegment 2: A5→A2 ({len(path_coords)-ppo_index} points)"
        segment_annotation = msp.add_text(segment_text, dxfattribs={'layer': 'ANNOTATIONS', 'height': 0.8})
        segment_annotation.set_placement((destination[0], y_offset, destination[2]))
    
    # Save DXF
    doc.saveas(output_file)
    
    print(f"✅ Forward path DXF saved: {output_file}")
    print(f"   Path points: {len(path_coords)}")
    print(f"   PPO found at index: {ppo_index if ppo_index >= 0 else 'Not found'}")
    print(f"   Layers: FORWARD_PATH (yellow), PPO_POINTS (red), START_GOAL (green), ANNOTATIONS (white)")

def main():
    # A1 → A5 → A2 forward path coordinates
    origin = (170.839, 12.530, 156.634)  # A1
    ppo = (196.310, 18.545, 153.799)     # A5
    destination = (182.946, 13.304, 157.295)  # A2
    
    print("🎯 Capturing actual forward path result from astar_PPOF_systems.py")
    
    # Capture the actual forward path
    path_coords = capture_forward_path_result(
        "graph_LV_combined.json", origin, ppo, destination, "C", "tramo_map_combined.json"
    )
    
    if path_coords:
        # Create DXF with actual forward path
        create_forward_path_dxf(path_coords, origin, ppo, destination, "A1_A5_A2_actual_forward_path.dxf")
    else:
        print("❌ Failed to capture forward path coordinates")

if __name__ == "__main__":
    main()
