#!/usr/bin/env python3
"""
Export Scenario C1 to DXF
=========================

This script exports Scenario C1 (Direct Path Between C1 and C2) to DXF format
for visualization in AutoCAD or other CAD software.

Scenario C1:
- Origin (C1): (176.553, 6.028, 150.340)
- Destination (C2): (182.946, 13.304, 157.295) - Same as A2 from Scenario A
- Cable Type: C (Both systems)
- Path Type: Direct optimal path
"""

import sys
import os
import json
from datetime import datetime
from typing import List, Tuple, Dict, Any

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import ezdxf
    from ezdxf import colors
    from ezdxf.enums import TextEntityAlignment
except ImportError:
    print("❌ ezdxf library not found. Install with: pip install ezdxf")
    sys.exit(1)

from demo_scenario_C1 import run_scenario_C1

def create_scenario_C1_dxf():
    """
    Create DXF file for Scenario C1: Direct Path Between C1 and C2
    """
    print("🚀 Creating Scenario C1 DXF Export")
    print("=" * 50)
    print()
    
    # Run Scenario C1 to get path data
    print("📊 Running Scenario C1 analysis...")
    results = run_scenario_C1()
    
    if not results:
        print("❌ Failed to get Scenario C1 results")
        return None
    
    print()
    print("✅ Scenario C1 data obtained successfully")
    print(f"   Path Points: {results['metrics']['path_points']}")
    print(f"   Distance: {results['metrics']['path_distance']:.3f} units")
    print(f"   Routing: {results['routing_type']}")
    print()
    
    # Create DXF document
    print("🎨 Creating DXF document...")
    doc = ezdxf.new('R2010')  # AutoCAD 2010 format for compatibility
    msp = doc.modelspace()
    
    # Create layers with colors
    layers = {
        'PATH_C1_C2': {'color': colors.BLUE, 'description': 'Direct path C1 to C2'},
        'ENDPOINTS': {'color': colors.RED, 'description': 'Origin and destination points'},
        'LABELS': {'color': colors.BLACK, 'description': 'Text labels'},
        'LEGEND': {'color': colors.GREEN, 'description': 'Legend and statistics'},
        'GRID': {'color': colors.GRAY, 'description': 'Reference grid'}
    }
    
    for layer_name, props in layers.items():
        layer = doc.layers.new(layer_name)
        layer.color = props['color']
        layer.description = props['description']
    
    print("✅ DXF layers created")
    
    # Extract path data
    path = results['path']
    origin = results['origin']['coord']
    destination = results['destination']['coord']
    
    # ====================================================================
    # Draw the path
    # ====================================================================
    print("🎯 Drawing path...")
    
    if len(path) > 1:
        # Draw path as connected lines
        for i in range(len(path) - 1):
            start_point = path[i]
            end_point = path[i + 1]
            
            msp.add_line(
                start=start_point,
                end=end_point,
                dxfattribs={
                    'layer': 'PATH_C1_C2',
                    'color': colors.BLUE,
                    'lineweight': 50  # Thicker line
                }
            )
        
        print(f"✅ Drew path with {len(path)-1} segments")
    
    # ====================================================================
    # Mark endpoints
    # ====================================================================
    print("📍 Adding endpoint markers...")
    
    # Origin marker (C1)
    msp.add_circle(
        center=origin,
        radius=0.5,
        dxfattribs={
            'layer': 'ENDPOINTS',
            'color': colors.RED
        }
    )
    
    # Destination marker (C2)
    msp.add_circle(
        center=destination,
        radius=0.5,
        dxfattribs={
            'layer': 'ENDPOINTS',
            'color': colors.RED
        }
    )
    
    print("✅ Endpoint markers added")
    
    # ====================================================================
    # Add labels
    # ====================================================================
    print("🏷️  Adding labels...")
    
    # Origin label
    msp.add_text(
        f"C1 (Origin)\n{origin[0]:.3f}, {origin[1]:.3f}, {origin[2]:.3f}\nSystem: {results['origin']['system']}",
        height=0.8,
        dxfattribs={
            'layer': 'LABELS',
            'color': colors.BLACK
        }
    ).set_placement(
        (origin[0] + 1, origin[1] + 1, origin[2]),
        align=TextEntityAlignment.LEFT
    )
    
    # Destination label  
    msp.add_text(
        f"C2 (Destination)\n{destination[0]:.3f}, {destination[1]:.3f}, {destination[2]:.3f}\nSystem: {results['destination']['system']}",
        height=0.8,
        dxfattribs={
            'layer': 'LABELS',
            'color': colors.BLACK
        }
    ).set_placement(
        (destination[0] + 1, destination[1] + 1, destination[2]),
        align=TextEntityAlignment.LEFT
    )
    
    print("✅ Labels added")
    
    # ====================================================================
    # Create legend and statistics
    # ====================================================================
    print("📊 Creating legend...")
    
    # Find bounds for legend placement
    all_points = [origin, destination] + path
    min_x = min(p[0] for p in all_points)
    max_x = max(p[0] for p in all_points)
    min_y = min(p[1] for p in all_points)
    max_y = max(p[1] for p in all_points)
    
    # Place legend in top-right area
    legend_x = max_x + 5
    legend_y = max_y
    
    # Title
    msp.add_text(
        "SCENARIO C1: DIRECT PATH C1 → C2",
        height=1.2,
        dxfattribs={
            'layer': 'LEGEND',
            'color': colors.GREEN
        }
    ).set_placement(
        (legend_x, legend_y, 0),
        align=TextEntityAlignment.LEFT
    )
    
    # Statistics
    stats_text = f"""
COORDINATES:
Origin (C1): ({origin[0]:.3f}, {origin[1]:.3f}, {origin[2]:.3f}) - System {results['origin']['system']}
Destination (C2): ({destination[0]:.3f}, {destination[1]:.3f}, {destination[2]:.3f}) - System {results['destination']['system']}

ROUTING ANALYSIS:
Type: {results['routing_type']}
Cable: {results['cable_type']} (Both Systems)

PATH METRICS:
Points: {results['metrics']['path_points']}
Distance: {results['metrics']['path_distance']:.3f} units
Direct Distance: {results['metrics']['direct_distance']:.3f} units
Efficiency: {results['metrics']['efficiency']:.1f}%
Overhead: {results['metrics']['overhead']:.1f}%
Nodes Explored: {results['metrics']['nodes_explored']}

LEGEND:
━━━ Blue Line: Optimal Path C1 → C2
● Red Circle: Endpoints (C1, C2)
"""
    
    msp.add_text(
        stats_text.strip(),
        height=0.6,
        dxfattribs={
            'layer': 'LEGEND',
            'color': colors.GREEN
        }
    ).set_placement(
        (legend_x, legend_y - 2, 0),
        align=TextEntityAlignment.LEFT
    )
    
    print("✅ Legend created")
    
    # ====================================================================
    # Add reference grid (optional)
    # ====================================================================
    print("📐 Adding reference grid...")
    
    # Create a simple reference grid
    grid_spacing = 5
    grid_start_x = int(min_x // grid_spacing) * grid_spacing
    grid_end_x = int(max_x // grid_spacing + 1) * grid_spacing
    grid_start_y = int(min_y // grid_spacing) * grid_spacing
    grid_end_y = int(max_y // grid_spacing + 1) * grid_spacing
    
    # Vertical grid lines
    for x in range(grid_start_x, grid_end_x + grid_spacing, grid_spacing):
        msp.add_line(
            start=(x, grid_start_y, 0),
            end=(x, grid_end_y, 0),
            dxfattribs={
                'layer': 'GRID',
                'color': colors.GRAY,
                'linetype': 'DASHED'
            }
        )
    
    # Horizontal grid lines
    for y in range(grid_start_y, grid_end_y + grid_spacing, grid_spacing):
        msp.add_line(
            start=(grid_start_x, y, 0),
            end=(grid_end_x, y, 0),
            dxfattribs={
                'layer': 'GRID',
                'color': colors.GRAY,
                'linetype': 'DASHED'
            }
        )
    
    print("✅ Reference grid added")
    
    # ====================================================================
    # Save DXF file
    # ====================================================================
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"export_data/scenario_C1_direct_path_{timestamp}.dxf"
    
    # Ensure export directory exists
    os.makedirs("export_data", exist_ok=True)
    
    try:
        doc.saveas(filename)
        print(f"✅ DXF file saved: {filename}")
        
        # File information
        file_size = os.path.getsize(filename)
        print(f"📁 File size: {file_size:,} bytes")
        
        return filename
        
    except Exception as e:
        print(f"❌ Failed to save DXF file: {e}")
        return None

def main():
    """Main execution function"""
    print("Scenario C1 DXF Export")
    print("Direct Path Between C1 and C2")
    print()
    
    filename = create_scenario_C1_dxf()
    
    if filename:
        print(f"\n🎉 Scenario C1 DXF export completed successfully!")
        print(f"📄 File: {filename}")
        print(f"🎯 Contents:")
        print(f"   • Direct optimal path from C1 to C2")
        print(f"   • Endpoint markers and labels")
        print(f"   • Comprehensive statistics and legend")
        print(f"   • Reference grid for measurements")
        print(f"   • Color-coded layers for organization")
        print()
        print(f"💡 Usage:")
        print(f"   • Open in AutoCAD, AutoCAD LT, or compatible CAD software")
        print(f"   • Use layer controls to show/hide different elements")
        print(f"   • All dimensions are in original coordinate units")
        print(f"   • Path shows optimal routing between C1 and C2")
    else:
        print("\n❌ Scenario C1 DXF export failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 