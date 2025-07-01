#!/usr/bin/env python3
"""
Export Scenario C1 to Simple DXF
================================

This script creates a simplified, highly compatible DXF file for Scenario C1
that should work with most CAD software including older versions.

Focus on maximum compatibility:
- Simple line entities only
- Basic layers
- No complex formatting
- Standard coordinates
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
except ImportError:
    print("❌ ezdxf library not found. Install with: pip install ezdxf")
    sys.exit(1)

from demo_scenario_C1 import run_scenario_C1

def create_simple_scenario_C1_dxf():
    """
    Create a simplified, highly compatible DXF file for Scenario C1
    """
    print("🚀 Creating Simple Scenario C1 DXF Export")
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
    print()
    
    # Create DXF document with maximum compatibility
    print("🎨 Creating simple DXF document...")
    doc = ezdxf.new('R2000')  # Use R2000 for maximum compatibility
    msp = doc.modelspace()
    
    # Create simple layers
    doc.layers.new('PATH', dxfattribs={'color': 1})      # Red
    doc.layers.new('POINTS', dxfattribs={'color': 2})    # Yellow  
    doc.layers.new('TEXT', dxfattribs={'color': 7})      # White/Black
    
    print("✅ Simple DXF layers created")
    
    # Extract path data
    path = results['path']
    origin = results['origin']['coord']
    destination = results['destination']['coord']
    
    print(f"📍 Processing {len(path)} path points...")
    
    # ====================================================================
    # Draw the path as simple lines
    # ====================================================================
    print("🎯 Drawing path as simple lines...")
    
    if len(path) > 1:
        for i in range(len(path) - 1):
            start_point = path[i]
            end_point = path[i + 1]
            
            # Create simple line - convert to 2D for better compatibility
            msp.add_line(
                start=(start_point[0], start_point[1]),  # Use only X,Y coordinates
                end=(end_point[0], end_point[1]),
                dxfattribs={'layer': 'PATH'}
            )
        
        print(f"✅ Drew {len(path)-1} line segments")
    
    # ====================================================================
    # Mark endpoints with simple circles
    # ====================================================================
    print("📍 Adding simple endpoint markers...")
    
    # Origin marker (C1) - 2D circle
    msp.add_circle(
        center=(origin[0], origin[1]),  # 2D coordinates
        radius=1.0,
        dxfattribs={'layer': 'POINTS'}
    )
    
    # Destination marker (C2) - 2D circle
    msp.add_circle(
        center=(destination[0], destination[1]),  # 2D coordinates
        radius=1.0,
        dxfattribs={'layer': 'POINTS'}
    )
    
    print("✅ Simple endpoint markers added")
    
    # ====================================================================
    # Add simple text labels
    # ====================================================================
    print("🏷️  Adding simple text labels...")
    
    # Origin label
    msp.add_text(
        f"C1 Origin",
        height=1.0,
        dxfattribs={'layer': 'TEXT'}
    ).set_pos((origin[0] + 2, origin[1] + 2))
    
    # Destination label
    msp.add_text(
        f"C2 Destination", 
        height=1.0,
        dxfattribs={'layer': 'TEXT'}
    ).set_pos((destination[0] + 2, destination[1] + 2))
    
    # Simple statistics
    stats_x = max(p[0] for p in path) + 5
    stats_y = max(p[1] for p in path)
    
    msp.add_text(
        f"SCENARIO C1 - Direct Path",
        height=1.5,
        dxfattribs={'layer': 'TEXT'}
    ).set_pos((stats_x, stats_y))
    
    msp.add_text(
        f"Points: {len(path)}",
        height=1.0,
        dxfattribs={'layer': 'TEXT'}
    ).set_pos((stats_x, stats_y - 3))
    
    msp.add_text(
        f"Distance: {results['metrics']['path_distance']:.1f}",
        height=1.0,
        dxfattribs={'layer': 'TEXT'}
    ).set_pos((stats_x, stats_y - 5))
    
    msp.add_text(
        f"Systems: B to A",
        height=1.0,
        dxfattribs={'layer': 'TEXT'}
    ).set_pos((stats_x, stats_y - 7))
    
    print("✅ Simple labels added")
    
    # ====================================================================
    # Save simplified DXF file
    # ====================================================================
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"export_data/scenario_C1_simple_{timestamp}.dxf"
    
    # Ensure export directory exists
    os.makedirs("export_data", exist_ok=True)
    
    try:
        doc.saveas(filename)
        print(f"✅ Simple DXF file saved: {filename}")
        
        # File information
        file_size = os.path.getsize(filename)
        print(f"📁 File size: {file_size:,} bytes")
        
        return filename
        
    except Exception as e:
        print(f"❌ Failed to save simple DXF file: {e}")
        return None

def create_basic_text_dxf():
    """
    Create an even more basic DXF with just text output for maximum compatibility
    """
    print("\n🚀 Creating Ultra-Basic Text DXF")
    print("-" * 40)
    
    # Get results
    results = run_scenario_C1()
    if not results:
        return None
    
    # Create minimal DXF
    doc = ezdxf.new('R12')  # Use oldest format
    msp = doc.modelspace()
    
    path = results['path']
    
    # Just add the path coordinates as text
    y_pos = 0
    for i, point in enumerate(path):
        text = f"Point {i+1}: ({point[0]:.3f}, {point[1]:.3f}, {point[2]:.3f})"
        msp.add_text(text, height=0.5).set_pos((0, y_pos))
        y_pos -= 1
    
    # Save ultra-basic file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"export_data/scenario_C1_basic_{timestamp}.dxf"
    
    try:
        doc.saveas(filename)
        print(f"✅ Ultra-basic DXF saved: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Failed to save basic DXF: {e}")
        return None

def main():
    """Main execution function"""
    print("Scenario C1 Simple DXF Export")
    print("Creating maximum compatibility DXF files")
    print()
    
    # Try simple version first
    simple_file = create_simple_scenario_C1_dxf()
    
    # Try ultra-basic version
    basic_file = create_basic_text_dxf()
    
    print(f"\n🎉 DXF Export Results:")
    if simple_file:
        print(f"✅ Simple DXF: {simple_file}")
        print(f"   • 2D path visualization")
        print(f"   • Simple lines and circles")
        print(f"   • R2000 format for compatibility")
    
    if basic_file:
        print(f"✅ Basic DXF: {basic_file}")
        print(f"   • Text-only coordinate list")
        print(f"   • R12 format for maximum compatibility")
    
    if simple_file or basic_file:
        print(f"\n💡 Troubleshooting Tips:")
        print(f"   • Try the 'simple' version first")
        print(f"   • If that fails, try the 'basic' version")
        print(f"   • Make sure your CAD software supports DXF format")
        print(f"   • Try opening in different CAD applications")
        print(f"   • Check if you need to import rather than open")
    else:
        print("\n❌ All DXF exports failed")

if __name__ == "__main__":
    main() 