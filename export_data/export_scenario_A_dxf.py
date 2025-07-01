#!/usr/bin/env python3
"""
Export Scenario A paths to DXF format for AutoCAD LT compatibility.

Scenario A includes:
1. Direct path (GREEN) - A1 to A2 without restrictions
2. Algorithm path avoiding forbidden sections (RED) - A1 to A2 with forbidden A3-A4 edge
3. Algorithm path with PPO avoiding forbidden sections (MAGENTA) - A1 through A5 to A2 with forbidden A3-A4 edge
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from astar_PPOF_systems import SystemFilteredGraph
import ezdxf
from ezdxf import colors
from datetime import datetime

def export_scenario_a_to_dxf():
    """Export all three Scenario A paths to DXF format."""
    
    # Scenario A coordinates
    A1 = (170.839, 12.530, 156.634)  # Origin
    A2 = (182.946, 13.304, 157.295)  # Destination
    A3 = (177.381, 14.056, 157.295)  # Forbidden section start
    A4 = (178.482, 14.056, 157.295)  # Forbidden section end
    A5 = (196.310, 18.545, 153.799)  # PPO
    
    # Graph and tramo files
    graph_file = "graph_LV_combined.json"
    tramo_map_file = "tramo_map_combined.json"
    forbidden_file = "forbidden_scenario_A.json"
    
    print("🚀 Generating Scenario A paths for DXF export...")
    
    # 1. Direct path (GREEN) - no restrictions
    print("\n1️⃣ Computing direct path (GREEN)...")
    graph_direct = SystemFilteredGraph(graph_file, "A")
    path_direct, nodes_direct = graph_direct.find_path_direct(A1, A2)
    print(f"   ✅ Direct path: {len(path_direct)} points, {nodes_direct} nodes explored")
    
    # 2. Algorithm path avoiding forbidden sections (RED)
    print("\n2️⃣ Computing path avoiding forbidden sections (RED)...")
    graph_forbidden = SystemFilteredGraph(graph_file, "A", tramo_map_file, forbidden_file)
    path_forbidden, nodes_forbidden = graph_forbidden.find_path_direct(A1, A2)
    print(f"   ✅ Forbidden-avoiding path: {len(path_forbidden)} points, {nodes_forbidden} nodes explored")
    
    # 3. PPO path avoiding forbidden sections (MAGENTA)
    print("\n3️⃣ Computing PPO path avoiding forbidden sections (MAGENTA)...")
    path_ppo, nodes_ppo = graph_forbidden.find_path_with_ppo(A1, A5, A2)
    print(f"   ✅ PPO path: {len(path_ppo)} points, {nodes_ppo} nodes explored")
    
    # Create DXF document
    print("\n📄 Creating DXF document...")
    doc = ezdxf.new('R2010')  # AutoCAD LT compatible
    msp = doc.modelspace()
    
    # Create layers with colors
    doc.layers.new('DIRECT_PATH', dxfattribs={'color': colors.GREEN})
    doc.layers.new('FORBIDDEN_AVOID_PATH', dxfattribs={'color': colors.RED})
    doc.layers.new('PPO_PATH', dxfattribs={'color': colors.MAGENTA})
    doc.layers.new('POINTS', dxfattribs={'color': colors.BLUE})
    doc.layers.new('FORBIDDEN_SECTION', dxfattribs={'color': colors.YELLOW})
    doc.layers.new('TEXT', dxfattribs={'color': colors.WHITE})
    
    # Helper function to add polyline
    def add_path_polyline(path, layer_name, line_weight=0.25):
        if len(path) > 1:
            points_3d = [(p[0], p[1], p[2]) for p in path]
            polyline = msp.add_polyline3d(points_3d, dxfattribs={
                'layer': layer_name,
                'lineweight': int(line_weight * 100)  # Convert to AutoCAD units
            })
            return polyline
        return None
    
    # Add paths to DXF
    print("   📍 Adding direct path (GREEN)...")
    add_path_polyline(path_direct, 'DIRECT_PATH', 0.35)
    
    print("   📍 Adding forbidden-avoiding path (RED)...")
    add_path_polyline(path_forbidden, 'FORBIDDEN_AVOID_PATH', 0.35)
    
    print("   📍 Adding PPO path (MAGENTA)...")
    add_path_polyline(path_ppo, 'PPO_PATH', 0.35)
    
    # Add key points
    print("   📍 Adding key points...")
    
    # Origin and destination
    msp.add_circle((A1[0], A1[1], A1[2]), 0.5, dxfattribs={'layer': 'POINTS', 'color': colors.BLUE})
    msp.add_text('A1 (Origin)', dxfattribs={
        'layer': 'TEXT', 
        'height': 1.0,
        'insert': (A1[0]+1, A1[1]+1, A1[2])
    })
    
    msp.add_circle((A2[0], A2[1], A2[2]), 0.5, dxfattribs={'layer': 'POINTS', 'color': colors.BLUE})
    msp.add_text('A2 (Destination)', dxfattribs={
        'layer': 'TEXT', 
        'height': 1.0,
        'insert': (A2[0]+1, A2[1]+1, A2[2])
    })
    
    # PPO point
    msp.add_circle((A5[0], A5[1], A5[2]), 0.5, dxfattribs={'layer': 'POINTS', 'color': colors.CYAN})
    msp.add_text('A5 (PPO)', dxfattribs={
        'layer': 'TEXT', 
        'height': 1.0,
        'insert': (A5[0]+1, A5[1]+1, A5[2])
    })
    
    # Forbidden section
    msp.add_line((A3[0], A3[1], A3[2]), (A4[0], A4[1], A4[2]), dxfattribs={
        'layer': 'FORBIDDEN_SECTION', 
        'color': colors.YELLOW,
        'lineweight': 50  # Thick line
    })
    msp.add_text('Forbidden Section (A3-A4)', dxfattribs={
        'layer': 'TEXT', 
        'height': 1.0,
        'insert': (A3[0]+1, A3[1]-1, A3[2])
    })
    
    # Add title and legend
    title_pos = (160, 5, 150)
    msp.add_text('Scenario A - Pathfinding Comparison', dxfattribs={
        'layer': 'TEXT', 
        'height': 2.0,
        'color': colors.WHITE,
        'insert': title_pos
    })
    
    # Legend
    legend_start = (160, 0, 150)
    legend_items = [
        ('Direct Path (No Restrictions)', colors.GREEN),
        ('Path Avoiding Forbidden Sections', colors.RED),
        ('PPO Path Avoiding Forbidden Sections', colors.MAGENTA),
        ('Key Points', colors.BLUE),
        ('Forbidden Section', colors.YELLOW)
    ]
    
    for i, (text, color) in enumerate(legend_items):
        y_offset = legend_start[1] - (i * 2)
        msp.add_text(f'• {text}', dxfattribs={
            'layer': 'TEXT',
            'height': 1.0,
            'color': color,
            'insert': (legend_start[0], y_offset, legend_start[2])
        })
    
    # Add statistics
    stats_pos = (160, -15, 150)
    stats_text = [
        f'Direct Path: {len(path_direct)} points, {nodes_direct} nodes explored',
        f'Forbidden-Avoiding Path: {len(path_forbidden)} points, {nodes_forbidden} nodes explored',
        f'PPO Path: {len(path_ppo)} points, {nodes_ppo} nodes explored',
        f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    ]
    
    for i, text in enumerate(stats_text):
        y_offset = stats_pos[1] - (i * 1.5)
        msp.add_text(text, dxfattribs={
            'layer': 'TEXT',
            'height': 0.8,
            'color': colors.CYAN,
            'insert': (stats_pos[0], y_offset, stats_pos[2])
        })
    
    # Save DXF file
    output_file = f"export_data/scenario_A_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.dxf"
    os.makedirs("export_data", exist_ok=True)
    doc.saveas(output_file)
    
    print(f"\n✅ DXF export completed!")
    print(f"📁 Output file: {output_file}")
    print(f"📊 Summary:")
    print(f"   • Direct path (GREEN): {len(path_direct)} points")
    print(f"   • Forbidden-avoiding path (RED): {len(path_forbidden)} points")
    print(f"   • PPO path (MAGENTA): {len(path_ppo)} points")
    print(f"   • Compatible with AutoCAD LT")
    
    return output_file

if __name__ == "__main__":
    try:
        output_file = export_scenario_a_to_dxf()
        print(f"\n🎯 Ready for AutoCAD LT: {output_file}")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1) 