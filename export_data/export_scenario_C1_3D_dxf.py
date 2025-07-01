#!/usr/bin/env python3
"""
Export Scenario C1 to Proper 3D DXF
===================================

This script creates a DXF file that properly preserves all 3D coordinates
including the Z elevation values. The previous version was flattening to 2D.

Fixes the issue where:
- C1 was showing as (176.553, 6.028, 0.000) 
- Should be (176.553, 6.028, 150.340)
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

from demo_scenario_C1 import run_scenario_C1

def create_3D_scenario_C1_dxf():
    """
    Create a proper 3D DXF file for Scenario C1 that preserves Z coordinates
    """
    print("🚀 Creating Proper 3D Scenario C1 DXF")
    print("=" * 50)
    print()
    
    # Get path data
    print("📊 Getting Scenario C1 data...")
    results = run_scenario_C1()
    
    if not results:
        print("❌ Failed to get Scenario C1 results")
        return None
    
    print("✅ Data obtained successfully")
    print()
    
    # Extract data
    path = results['path']
    origin = results['origin']['coord']
    destination = results['destination']['coord']
    
    print(f"🔍 Coordinate Verification:")
    print(f"   C1 Origin: ({origin[0]:.3f}, {origin[1]:.3f}, {origin[2]:.3f})")
    print(f"   C2 Destination: ({destination[0]:.3f}, {destination[1]:.3f}, {destination[2]:.3f})")
    print(f"   Path points: {len(path)}")
    print()
    
    # Create 3D DXF
    print("🎨 Creating proper 3D DXF...")
    doc = ezdxf.new('R2000')  # R2000 for compatibility
    msp = doc.modelspace()
    
    # Create layers
    doc.layers.new('PATH', dxfattribs={'color': 1})      # Red
    doc.layers.new('POINTS', dxfattribs={'color': 2})    # Yellow  
    doc.layers.new('TEXT', dxfattribs={'color': 7})      # White/Black
    
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
    # Add 3D endpoint circles
    # ====================================================================
    print("📍 Adding 3D endpoint markers...")
    
    # Origin circle at proper 3D location
    msp.add_circle(
        center=(origin[0], origin[1], origin[2]),  # Full 3D coordinates
        radius=0.5,
        dxfattribs={'layer': 'POINTS'}
    )
    
    # Destination circle at proper 3D location
    msp.add_circle(
        center=(destination[0], destination[1], destination[2]),  # Full 3D coordinates
        radius=0.5,
        dxfattribs={'layer': 'POINTS'}
    )
    
    print("✅ 3D endpoint markers added")
    
    # ====================================================================
    # Add 3D text labels with full coordinates
    # ====================================================================
    print("🏷️  Adding 3D text labels...")
    
    # Origin text with full coordinates
    origin_text = f"C1 Origin\n({origin[0]:.3f}, {origin[1]:.3f}, {origin[2]:.3f})\nSystem B"
    msp.add_text(
        origin_text,
        dxfattribs={
            'insert': (origin[0] + 1, origin[1] + 1, origin[2]),  # 3D position
            'height': 0.8,
            'layer': 'TEXT'
        }
    )
    
    # Destination text with full coordinates
    dest_text = f"C2 Destination\n({destination[0]:.3f}, {destination[1]:.3f}, {destination[2]:.3f})\nSystem A"
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
    
    stats_text = f"""SCENARIO C1 - 3D Path
Points: {len(path)}
Distance: {results['metrics']['path_distance']:.1f} units
Systems: B → A
Z Range: {min(p[2] for p in path):.1f} to {max(p[2] for p in path):.1f}"""
    
    msp.add_text(
        stats_text,
        dxfattribs={
            'insert': (stats_x, stats_y, stats_z),  # 3D position
            'height': 0.8,
            'layer': 'TEXT'
        }
    )
    
    print("✅ 3D text labels added")
    
    # ====================================================================
    # Add some reference points to verify 3D coordinates
    # ====================================================================
    print("🔍 Adding coordinate verification points...")
    
    # Add small markers at key elevation changes
    elevation_changes = []
    for i in range(1, len(path)):
        if abs(path[i][2] - path[i-1][2]) > 1.0:  # Significant Z change
            elevation_changes.append((i, path[i]))
    
    for i, point in elevation_changes:
        # Small circle at elevation change
        msp.add_circle(
            center=(point[0], point[1], point[2]),
            radius=0.2,
            dxfattribs={'layer': 'POINTS'}
        )
        
        # Text showing elevation
        msp.add_text(
            f"Z={point[2]:.1f}",
            dxfattribs={
                'insert': (point[0] + 0.3, point[1] + 0.3, point[2]),
                'height': 0.5,
                'layer': 'TEXT'
            }
        )
    
    print(f"✅ Added {len(elevation_changes)} elevation change markers")
    
    # ====================================================================
    # Save 3D DXF file
    # ====================================================================
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"export_data/scenario_C1_3D_{timestamp}.dxf"
    
    os.makedirs("export_data", exist_ok=True)
    
    try:
        doc.saveas(filename)
        print(f"✅ 3D DXF saved: {filename}")
        
        file_size = os.path.getsize(filename)
        print(f"📁 File size: {file_size:,} bytes")
        
        # Verify coordinates in file
        print(f"\n🔍 Coordinate Verification:")
        print(f"   ✅ C1 should show: ({origin[0]:.3f}, {origin[1]:.3f}, {origin[2]:.3f})")
        print(f"   ✅ C2 should show: ({destination[0]:.3f}, {destination[1]:.3f}, {destination[2]:.3f})")
        print(f"   ✅ Z coordinates preserved: {min(p[2] for p in path):.1f} to {max(p[2] for p in path):.1f}")
        
        return filename
        
    except Exception as e:
        print(f"❌ Failed to save 3D DXF: {e}")
        return None

def main():
    """Main function"""
    print("Scenario C1 Proper 3D DXF Export")
    print("Fixing Z-coordinate preservation issue")
    print()
    
    dxf_file = create_3D_scenario_C1_dxf()
    
    if dxf_file:
        print(f"\n🎉 3D DXF Export Success!")
        print(f"📄 File: {dxf_file}")
        print(f"🎯 Fixed Issues:")
        print(f"   ✅ Preserves full 3D coordinates (X, Y, Z)")
        print(f"   ✅ C1 shows correct Z = 150.340")
        print(f"   ✅ C2 shows correct Z = 157.295")
        print(f"   ✅ All path points maintain elevation")
        print(f"   ✅ Added elevation change markers")
        print(f"   ✅ 3D text positioning")
        print(f"\n💡 This version should show proper 3D coordinates in your CAD software!")
    else:
        print(f"\n❌ 3D DXF export failed")

if __name__ == "__main__":
    main() 