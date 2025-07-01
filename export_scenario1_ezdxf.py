#!/usr/bin/env python3
"""
Create DXF using ezdxf library to match the format of working DXF files.
This should be compatible with AutoCAD LT since other files in the project work.
"""

import json
import ezdxf
from ezdxf import colors
from ezdxf.math import Vec3

def parse_coordinate_string(coord_str: str) -> tuple:
    """Parse coordinate string to tuple."""
    clean_str = coord_str.strip().strip('()')
    parts = [float(x.strip()) for x in clean_str.split(',')]
    return tuple(parts)

def get_forbidden_sections():
    """Get forbidden section coordinates from tramo map."""
    try:
        with open('tramo_map_combined.json', 'r') as f:
            tramo_map = json.load(f)
    except FileNotFoundError:
        print("❌ Error: tramo_map_combined.json not found")
        return []

    forbidden_sections = []
    id_to_edge = {tramo_id: edge_key for edge_key, tramo_id in tramo_map.items()}
    
    for tramo_id in [4, 200]:
        if tramo_id in id_to_edge:
            edge_key = id_to_edge[tramo_id]
            nodes = edge_key.split('-')
            if len(nodes) == 2:
                node1 = parse_coordinate_string(nodes[0])
                node2 = parse_coordinate_string(nodes[1])
                forbidden_sections.append({
                    'tramo_id': tramo_id,
                    'node1': node1,
                    'node2': node2
                })
    
    return forbidden_sections

def get_algorithm_path():
    """Get path from algorithm with forbidden sections."""
    try:
        from astar_PPOF_systems import SystemFilteredGraph
        
        graph = SystemFilteredGraph(
            'graph_LV_combined.json', 
            'A',
            'tramo_map_combined.json',
            'forbidden_scenario1.json'
        )
        
        origin = (139.232, 28.845, 139.993)
        destination = (152.290, 17.883, 160.124)
        
        path, _ = graph.find_path_direct(origin, destination)
        return path
        
    except Exception as e:
        print(f"❌ Error getting path: {e}")
        return None

def get_direct_path():
    """Get direct path without forbidden sections (respecting graph connectivity)."""
    try:
        from astar_PPOF_systems import SystemFilteredGraph
        
        # Create graph WITHOUT forbidden sections for direct path
        graph = SystemFilteredGraph(
            'graph_LV_combined.json', 
            'A',
            'tramo_map_combined.json',
            None  # No forbidden sections file
        )
        
        origin = (139.232, 28.845, 139.993)
        destination = (152.290, 17.883, 160.124)
        
        path, _ = graph.find_path_direct(origin, destination)
        return path
        
    except Exception as e:
        print(f"❌ Error getting direct path: {e}")
        return None

def main():
    """Create DXF using ezdxf library."""
    print("🎨 Creating DXF using ezdxf library (same as working files)")
    print("=" * 60)
    
    # Get data
    forbidden_sections = get_forbidden_sections()
    if len(forbidden_sections) != 2:
        print(f"❌ Expected 2 forbidden sections, got {len(forbidden_sections)}")
        return
    
    path_points = get_algorithm_path()
    if not path_points:
        print("❌ Could not get algorithm path")
        return
    
    direct_path_points = get_direct_path()
    if not direct_path_points:
        print("❌ Could not get direct path")
        return
    
    print(f"✅ Got {len(forbidden_sections)} forbidden sections")
    print(f"✅ Got algorithm path with {len(path_points)} points")
    print(f"✅ Got direct path with {len(direct_path_points)} points")
    
    # Check if paths are different
    paths_identical = (len(path_points) == len(direct_path_points) and 
                      all(abs(p1[i] - p2[i]) < 0.001 for p1, p2 in zip(path_points, direct_path_points) for i in range(3)))
    
    if paths_identical:
        print("ℹ️  Note: Direct and algorithm paths are identical - forbidden sections don't affect optimal route")
    else:
        print("✅ Direct and algorithm paths are different - forbidden sections cause detour")
    
    # Create new DXF document (AutoCAD 2010 format like working files)
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Create layers with colors
    doc.layers.add('FORBIDDEN_SECTIONS', color=colors.YELLOW)
    doc.layers.add('ORIGIN_DEST', color=colors.CYAN) 
    doc.layers.add('DIRECT_PATH', color=colors.MAGENTA)
    doc.layers.add('ALGORITHM_PATH', color=colors.GREEN)
    doc.layers.add('LABELS', color=colors.WHITE)
    
    print("✅ Created layers")
    
    # Define points
    origin = Vec3(139.232, 28.845, 139.993)
    destination = Vec3(152.290, 17.883, 160.124)
    
    # Add forbidden sections (YELLOW)
    print("🟡 Adding forbidden sections...")
    for section in forbidden_sections:
        node1 = Vec3(section['node1'])
        node2 = Vec3(section['node2'])
        tramo_id = section['tramo_id']
        
        # Main line
        msp.add_line(node1, node2, dxfattribs={'layer': 'FORBIDDEN_SECTIONS'})
        
        # Endpoint circles
        msp.add_circle(node1, radius=0.3, dxfattribs={'layer': 'FORBIDDEN_SECTIONS'})
        msp.add_circle(node2, radius=0.3, dxfattribs={'layer': 'FORBIDDEN_SECTIONS'})
        
        # Label at midpoint
        midpoint = node1.lerp(node2, 0.5)
        midpoint = midpoint.replace(z=midpoint.z + 0.5)
        msp.add_text(f'TRAMO_{tramo_id}', height=0.8, dxfattribs={'layer': 'LABELS'}).set_placement(midpoint)
        
        # Coordinate labels
        coord1_text = f"({node1.x:.1f},{node1.y:.1f},{node1.z:.1f})"
        coord2_text = f"({node2.x:.1f},{node2.y:.1f},{node2.z:.1f})"
        
        label1_pos = node1.replace(x=node1.x + 0.5, z=node1.z - 1.0)
        label2_pos = node2.replace(x=node2.x + 0.5, z=node2.z - 1.0)
        
        msp.add_text(coord1_text, height=0.4, dxfattribs={'layer': 'LABELS'}).set_placement(label1_pos)
        msp.add_text(coord2_text, height=0.4, dxfattribs={'layer': 'LABELS'}).set_placement(label2_pos)
    
    # Add origin and destination (CYAN)
    print("🔵 Adding origin and destination...")
    
    # Origin
    msp.add_circle(origin, radius=1.5, dxfattribs={'layer': 'ORIGIN_DEST'})
    origin_label_pos = origin.replace(x=origin.x + 2.5)
    msp.add_text('ORIGIN', height=1.0, dxfattribs={'layer': 'LABELS'}).set_placement(origin_label_pos)
    
    origin_coord_pos = origin.replace(x=origin.x + 2.5, y=origin.y - 1.5)
    origin_coord_text = f"({origin.x:.1f},{origin.y:.1f},{origin.z:.1f})"
    msp.add_text(origin_coord_text, height=0.6, dxfattribs={'layer': 'LABELS'}).set_placement(origin_coord_pos)
    
    # Destination
    msp.add_circle(destination, radius=1.5, dxfattribs={'layer': 'ORIGIN_DEST'})
    dest_label_pos = destination.replace(x=destination.x + 2.5)
    msp.add_text('DESTINATION', height=1.0, dxfattribs={'layer': 'LABELS'}).set_placement(dest_label_pos)
    
    dest_coord_pos = destination.replace(x=destination.x + 2.5, y=destination.y - 1.5)
    dest_coord_text = f"({destination.x:.1f},{destination.y:.1f},{destination.z:.1f})"
    msp.add_text(dest_coord_text, height=0.6, dxfattribs={'layer': 'LABELS'}).set_placement(dest_coord_pos)
    
    # Add direct path (MAGENTA) - respecting graph connectivity
    print("🟣 Adding direct path (following graph edges)...")
    for i in range(len(direct_path_points) - 1):
        p1 = Vec3(direct_path_points[i])
        p2 = Vec3(direct_path_points[i + 1])
        msp.add_line(p1, p2, dxfattribs={'layer': 'DIRECT_PATH'})
    
    # Add direct path label at midpoint of the path
    if len(direct_path_points) >= 2:
        mid_index = len(direct_path_points) // 2
        direct_midpoint = Vec3(direct_path_points[mid_index])
        direct_midpoint = direct_midpoint.replace(z=direct_midpoint.z + 1.0)
        msp.add_text('DIRECT_PATH', height=0.8, dxfattribs={'layer': 'LABELS'}).set_placement(direct_midpoint)
    
    # Add algorithm path (GREEN)
    print("🟢 Adding algorithm path...")
    for i in range(len(path_points) - 1):
        p1 = Vec3(path_points[i])
        p2 = Vec3(path_points[i + 1])
        msp.add_line(p1, p2, dxfattribs={'layer': 'ALGORITHM_PATH'})
    
    # Add path point markers (every 3rd point)
    for i in range(0, len(path_points), 3):
        point = Vec3(path_points[i])
        msp.add_circle(point, radius=0.2, dxfattribs={'layer': 'ALGORITHM_PATH'})
        
        label_pos = point.replace(z=point.z + 0.5)
        msp.add_text(f'P{i+1}', height=0.3, dxfattribs={'layer': 'LABELS'}).set_placement(label_pos)
    
    # Save the DXF file
    output_file = 'export_data/scenario1_ezdxf.dxf'
    doc.saveas(output_file)
    
    # Get file info
    import os
    file_size = os.path.getsize(output_file)
    
    print(f"\n✅ DXF created with ezdxf library!")
    print(f"📁 File: {output_file}")
    print(f"📊 Size: {file_size} bytes")
    print(f"🔧 Format: AutoCAD 2010 (R2010) - Same as working files")
    print(f"🎨 Layers:")
    print(f"   • FORBIDDEN_SECTIONS (Yellow) - Forbidden sections with coordinates")
    print(f"   • ORIGIN_DEST (Cyan) - Start/end points with coordinates")
    print(f"   • DIRECT_PATH (Magenta) - Direct path following graph edges (no restrictions)")
    print(f"   • ALGORITHM_PATH (Green) - Calculated path avoiding forbidden sections")
    print(f"   • LABELS (White) - All text labels")
    
    # Calculate and show distances
    def calculate_path_distance(points):
        total = 0.0
        for i in range(len(points) - 1):
            p1 = Vec3(points[i])
            p2 = Vec3(points[i + 1])
            total += p1.distance(p2)
        return total
    
    direct_distance = calculate_path_distance(direct_path_points)
    algorithm_distance = calculate_path_distance(path_points)
    
    print(f"\n📏 Distance comparison:")
    print(f"   • Direct path (no restrictions): {direct_distance:.3f} units ({len(direct_path_points)} points)")
    print(f"   • Algorithm path (avoiding forbidden): {algorithm_distance:.3f} units ({len(path_points)} points)")
    if direct_distance > 0:
        detour_pct = ((algorithm_distance / direct_distance) - 1) * 100
        print(f"   • Detour: +{algorithm_distance - direct_distance:.3f} units ({detour_pct:.1f}% longer)")
    
    print(f"\n📋 This should work with AutoCAD LT (same format as your working files)")

if __name__ == "__main__":
    main() 