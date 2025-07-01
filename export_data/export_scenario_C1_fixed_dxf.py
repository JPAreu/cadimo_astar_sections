#!/usr/bin/env python3
"""
Export Scenario C1 to Fixed Simple DXF
======================================

This script creates a very simple, highly compatible DXF file for Scenario C1.
Uses only basic entities that work with all CAD software.
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

def create_fixed_scenario_C1_dxf():
    """
    Create a very simple, compatible DXF file for Scenario C1
    """
    print("🚀 Creating Fixed Simple Scenario C1 DXF")
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
    
    # Create very simple DXF
    print("🎨 Creating ultra-simple DXF...")
    doc = ezdxf.new('R2000')  # R2000 for good compatibility
    msp = doc.modelspace()
    
    # Extract data
    path = results['path']
    origin = results['origin']['coord']
    destination = results['destination']['coord']
    
    print(f"📍 Processing {len(path)} path points...")
    
    # ====================================================================
    # Draw path as simple 2D lines (ignore Z coordinate for compatibility)
    # ====================================================================
    print("🎯 Drawing path...")
    
    for i in range(len(path) - 1):
        start = path[i]
        end = path[i + 1]
        
        # Simple 2D line
        msp.add_line(
            start=(start[0], start[1]),
            end=(end[0], end[1])
        )
    
    print(f"✅ Drew {len(path)-1} line segments")
    
    # ====================================================================
    # Add endpoint circles
    # ====================================================================
    print("📍 Adding endpoint markers...")
    
    # Origin circle
    msp.add_circle(
        center=(origin[0], origin[1]),
        radius=0.5
    )
    
    # Destination circle
    msp.add_circle(
        center=(destination[0], destination[1]),
        radius=0.5
    )
    
    print("✅ Endpoint markers added")
    
    # ====================================================================
    # Add simple text with proper positioning
    # ====================================================================
    print("🏷️  Adding text labels...")
    
    # Origin text
    msp.add_text(
        "C1 Origin",
        dxfattribs={
            'insert': (origin[0] + 1, origin[1] + 1),
            'height': 0.8
        }
    )
    
    # Destination text
    msp.add_text(
        "C2 Destination",
        dxfattribs={
            'insert': (destination[0] + 1, destination[1] + 1),
            'height': 0.8
        }
    )
    
    # Statistics text
    stats_x = max(p[0] for p in path) + 3
    stats_y = max(p[1] for p in path)
    
    msp.add_text(
        "SCENARIO C1",
        dxfattribs={
            'insert': (stats_x, stats_y),
            'height': 1.0
        }
    )
    
    msp.add_text(
        f"Points: {len(path)}",
        dxfattribs={
            'insert': (stats_x, stats_y - 2),
            'height': 0.8
        }
    )
    
    msp.add_text(
        f"Distance: {results['metrics']['path_distance']:.1f}",
        dxfattribs={
            'insert': (stats_x, stats_y - 4),
            'height': 0.8
        }
    )
    
    print("✅ Text labels added")
    
    # ====================================================================
    # Save file
    # ====================================================================
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"export_data/scenario_C1_fixed_{timestamp}.dxf"
    
    os.makedirs("export_data", exist_ok=True)
    
    try:
        doc.saveas(filename)
        print(f"✅ Fixed DXF saved: {filename}")
        
        file_size = os.path.getsize(filename)
        print(f"📁 File size: {file_size:,} bytes")
        
        return filename
        
    except Exception as e:
        print(f"❌ Failed to save fixed DXF: {e}")
        return None

def create_csv_export():
    """
    Create a CSV file with the path coordinates as backup
    """
    print("\n🚀 Creating CSV Export as Backup")
    print("-" * 40)
    
    results = run_scenario_C1()
    if not results:
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"export_data/scenario_C1_path_{timestamp}.csv"
    
    try:
        with open(filename, 'w') as f:
            f.write("Point,X,Y,Z,Description\n")
            
            path = results['path']
            for i, point in enumerate(path):
                desc = ""
                if i == 0:
                    desc = "C1 Origin (System B)"
                elif i == len(path) - 1:
                    desc = "C2 Destination (System A)"
                else:
                    desc = f"Path Point {i+1}"
                
                f.write(f"{i+1},{point[0]:.3f},{point[1]:.3f},{point[2]:.3f},{desc}\n")
        
        print(f"✅ CSV export saved: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Failed to save CSV: {e}")
        return None

def main():
    """Main function"""
    print("Scenario C1 Fixed DXF Export")
    print("Ultra-simple format for maximum compatibility")
    print()
    
    # Try fixed DXF
    dxf_file = create_fixed_scenario_C1_dxf()
    
    # Create CSV backup
    csv_file = create_csv_export()
    
    print(f"\n🎉 Export Results:")
    
    if dxf_file:
        print(f"✅ Fixed DXF: {dxf_file}")
        print(f"   • Ultra-simple 2D lines only")
        print(f"   • Basic circles for endpoints")
        print(f"   • Simple text labels")
        print(f"   • R2000 format")
        print(f"   • Should work with any CAD software")
    
    if csv_file:
        print(f"✅ CSV Backup: {csv_file}")
        print(f"   • All path coordinates")
        print(f"   • Can be imported into Excel/CAD")
        print(f"   • Human-readable format")
    
    if dxf_file or csv_file:
        print(f"\n💡 Usage Tips:")
        print(f"   • Try opening the DXF file first")
        print(f"   • If DXF fails, use the CSV file")
        print(f"   • CSV can be imported into most CAD software")
        print(f"   • Check your CAD software's import options")
    else:
        print(f"\n❌ All exports failed")

if __name__ == "__main__":
    main() 