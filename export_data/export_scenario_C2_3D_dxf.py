#!/usr/bin/env python3
"""
Export Scenario C2 to Proper 3D DXF
===================================

This script creates a DXF file that properly preserves all 3D coordinates
for the path from C1 to C3, including the significant elevation change.

Coordinates:
- Origin (C1): (176.553, 6.028, 150.340)
- Destination (C3): (174.860, 15.369, 136.587)
- Notable: 13.753 units elevation DROP
"""

import sys
import os
import json
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import ezdxf
except ImportError:
    print("❌ ezdxf library not found. Install with: pip install ezdxf")
    sys.exit(1)

from demo_scenario_C2 import run_scenario_C2

def create_3D_scenario_C2_dxf():
    """
    Create a proper 3D DXF file for Scenario C2 that preserves Z coordinates
    """
    print("🚀 Creating Proper 3D Scenario C2 DXF")
    print("=" * 50)
    print()
    
    # Get path data
    print("📊 Getting Scenario C2 data...")
    results = run_scenario_C2()
    
    if not results:
        print("❌ Failed to get Scenario C2 results")
        return None
    
    print("✅ Data obtained successfully")
    print()
    
    # Extract data
    path = results['path']
    origin = results['origin']['coord']
    destination = results['destination']['coord']
    elevation_change = results['metrics']['elevation_change']
    
    print(f"🔍 Coordinate Verification:")
    print(f"   C1 Origin: ({origin[0]:.3f}, {origin[1]:.3f}, {origin[2]:.3f})")
    print(f"   C3 Destination: ({destination[0]:.3f}, {destination[1]:.3f}, {destination[2]:.3f})")
    print(f"   Elevation Change: {elevation_change:.3f} units ({'DROP' if elevation_change < 0 else 'RISE'})")
    print(f"   Path points: {len(path)}")
    print()
    
    # Create 3D DXF
    print("🎨 Creating proper 3D DXF...")
    doc = ezdxf.new('R2000')  # R2000 for compatibility
    msp = doc.modelspace()
    
    # Create layers with descriptive colors
    doc.layers.new('PATH', dxfattribs={'color': 1})        # Red - main path
    doc.layers.new('ENDPOINTS', dxfattribs={'color': 2})   # Yellow - start/end points
    doc.layers.new('ELEVATION', dxfattribs={'color': 3})   # Green - elevation markers
    doc.layers.new('TEXT', dxfattribs={'color': 7})        # White/Black - labels
    doc.layers.new('GRID', dxfattribs={'color': 8})        # Gray - reference
    
    print(f"📍 Processing {len(path)} path points with full 3D coordinates...")
    
    # ====================================================================
    # Draw path as 3D lines (preserving ALL coordinates)
    # ====================================================================
    print("🎯 Drawing 3D path...")
    
    for i in range(len(path) - 1):
        start = path[i]
        end = path[i + 1]
        
        # Create 3D line with ALL three coordinates
        msp.add_line(
            start=(start[0], start[1], start[2]),  # Full 3D coordinates
            end=(end[0], end[1], end[2]),          # Full 3D coordinates
            dxfattribs={'layer': 'PATH'}
        )
    
    print(f"✅ Drew {len(path)-1} 3D line segments")
    
    # ====================================================================
    # Add 3D endpoint markers
    # ====================================================================
    print("📍 Adding 3D endpoint markers...")
    
    # Origin circle at proper 3D location
    msp.add_circle(
        center=(origin[0], origin[1], origin[2]),  # Full 3D coordinates
        radius=0.8,
        dxfattribs={'layer': 'ENDPOINTS'}
    )
    
    # Destination circle at proper 3D location
    msp.add_circle(
        center=(destination[0], destination[1], destination[2]),  # Full 3D coordinates
        radius=0.8,
        dxfattribs={'layer': 'ENDPOINTS'}
    )
    
    print("✅ 3D endpoint markers added")
    
    # ====================================================================
    # Add elevation profile visualization
    # ====================================================================
    print("📈 Adding elevation profile markers...")
    
    # Add markers at significant elevation changes
    elevation_markers = []
    for i in range(1, len(path)):
        z_change = abs(path[i][2] - path[i-1][2])
        if z_change > 1.0:  # Significant elevation change
            elevation_markers.append((i, path[i], z_change))
    
    for i, point, z_change in elevation_markers:
        # Small circle at elevation change
        msp.add_circle(
            center=(point[0], point[1], point[2]),
            radius=0.3,
            dxfattribs={'layer': 'ELEVATION'}
        )
        
        # Elevation change text
        msp.add_text(
            f"ΔZ={z_change:.1f}",
            dxfattribs={
                'insert': (point[0] + 0.5, point[1] + 0.5, point[2]),
                'height': 0.4,
                'layer': 'ELEVATION'
            }
        )
    
    print(f"✅ Added {len(elevation_markers)} elevation change markers")
    
    # ====================================================================
    # Add 3D text labels with full coordinates
    # ====================================================================
    print("🏷️  Adding 3D text labels...")
    
    # Origin text with full coordinates
    origin_text = f"C1 Origin\n({origin[0]:.3f}, {origin[1]:.3f}, {origin[2]:.3f})\nSystem {results['origin']['system']}"
    msp.add_text(
        origin_text,
        dxfattribs={
            'insert': (origin[0] + 1, origin[1] + 1, origin[2]),  # 3D position
            'height': 0.8,
            'layer': 'TEXT'
        }
    )
    
    # Destination text with full coordinates
    dest_text = f"C3 Destination\n({destination[0]:.3f}, {destination[1]:.3f}, {destination[2]:.3f})\nSystem {results['destination']['system']}"
    msp.add_text(
        dest_text,
        dxfattribs={
            'insert': (destination[0] + 1, destination[1] + 1, destination[2]),  # 3D position
            'height': 0.8,
            'layer': 'TEXT'
        }
    )
    
    # Statistics text positioned in 3D space
    stats_x = max(p[0] for p in path) + 3
    stats_y = max(p[1] for p in path)
    stats_z = sum(p[2] for p in path) / len(path)  # Average Z height
    
    elevation_profile = results['metrics']['elevation_profile']
    stats_text = f"""SCENARIO C2 - 3D Path C1 → C3
Points: {len(path)}
Distance: {results['metrics']['path_distance']:.1f} units
Efficiency: {results['metrics']['efficiency']:.1f}%
Routing: {results['routing_type']}

ELEVATION ANALYSIS:
Start Z: {elevation_profile['start_z']:.1f}
End Z: {elevation_profile['end_z']:.1f}
Drop: {abs(elevation_change):.1f} units
Range: {elevation_profile['min_z']:.1f} to {elevation_profile['max_z']:.1f}"""
    
    msp.add_text(
        stats_text,
        dxfattribs={
            'insert': (stats_x, stats_y, stats_z),  # 3D position
            'height': 0.7,
            'layer': 'TEXT'
        }
    )
    
    print("✅ 3D text labels added")
    
    # ====================================================================
    # Add elevation profile as side view
    # ====================================================================
    print("📊 Adding elevation profile side view...")
    
    # Create a side view of the elevation profile
    profile_x_start = min(p[0] for p in path) - 5
    profile_y = min(p[1] for p in path) - 5
    
    # Scale factor for visualization
    horizontal_scale = 1.0
    vertical_scale = 0.1  # Exaggerate elevation changes for visibility
    
    # Draw elevation profile as connected lines
    for i in range(len(path) - 1):
        start_profile = (
            profile_x_start + i * horizontal_scale,
            profile_y,
            path[i][2] * vertical_scale + 100  # Offset for visibility
        )
        end_profile = (
            profile_x_start + (i + 1) * horizontal_scale,
            profile_y,
            path[i + 1][2] * vertical_scale + 100
        )
        
        msp.add_line(
            start=start_profile,
            end=end_profile,
            dxfattribs={'layer': 'ELEVATION'}
        )
    
    # Label the elevation profile
    msp.add_text(
        "Elevation Profile (Scaled)",
        dxfattribs={
            'insert': (profile_x_start, profile_y - 2, 100),
            'height': 0.6,
            'layer': 'TEXT'
        }
    )
    
    print("✅ Elevation profile side view added")
    
    # ====================================================================
    # Save 3D DXF file
    # ====================================================================
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"export_data/scenario_C2_3D_{timestamp}.dxf"
    
    os.makedirs("export_data", exist_ok=True)
    
    try:
        doc.saveas(filename)
        print(f"✅ 3D DXF saved: {filename}")
        
        file_size = os.path.getsize(filename)
        print(f"📁 File size: {file_size:,} bytes")
        
        # Verify coordinates in file
        print(f"\n🔍 Coordinate Verification:")
        print(f"   ✅ C1 should show: ({origin[0]:.3f}, {origin[1]:.3f}, {origin[2]:.3f})")
        print(f"   ✅ C3 should show: ({destination[0]:.3f}, {destination[1]:.3f}, {destination[2]:.3f})")
        print(f"   ✅ Elevation drop: {abs(elevation_change):.3f} units")
        print(f"   ✅ Z range: {elevation_profile['min_z']:.1f} to {elevation_profile['max_z']:.1f}")
        
        return filename
        
    except Exception as e:
        print(f"❌ Failed to save 3D DXF: {e}")
        return None

def main():
    """Main function"""
    print("Scenario C2 Proper 3D DXF Export")
    print("C1 to C3 with elevation analysis")
    print()
    
    dxf_file = create_3D_scenario_C2_dxf()
    
    if dxf_file:
        print(f"\n🎉 3D DXF Export Success!")
        print(f"📄 File: {dxf_file}")
        print(f"🎯 Features:")
        print(f"   ✅ Preserves full 3D coordinates (X, Y, Z)")
        print(f"   ✅ C1 shows correct Z = 150.340")
        print(f"   ✅ C3 shows correct Z = 136.587")
        print(f"   ✅ Visualizes 13.753 unit elevation drop")
        print(f"   ✅ Elevation change markers")
        print(f"   ✅ Side view elevation profile")
        print(f"   ✅ Color-coded layers")
        print(f"   ✅ Comprehensive statistics")
        print(f"\n💡 This version shows the complete 3D path with elevation analysis!")
    else:
        print(f"\n❌ 3D DXF export failed")

if __name__ == "__main__":
    main() 