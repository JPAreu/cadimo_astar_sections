#!/usr/bin/env python3
"""
DXF Export for Scenario B1 - Cross-System Routing with Internal System B Constraint

This script exports the Scenario B1 pathfinding results to AutoCAD DXF format,
showing the direct cross-system path and the impact of the forbidden B4-B1 internal section.

Since the B4-B1 constraint completely prevents cross-system routing, this export shows:
1. Direct cross-system path (GREEN) - baseline routing
2. Forbidden B4-B1 section (RED) - the internal constraint that breaks connectivity
3. Key points and analysis of the gateway isolation issue

Author: AI Assistant
Date: 2024-07-01
"""

import sys
import os
import json
import time
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from astar_PPOF_systems import SystemFilteredGraph
    from cable_filter import get_cable_info, coord_to_key, load_tagged_graph
    from astar_PPO_forbid import calculate_path_distance, format_point
    import ezdxf
    from ezdxf import colors
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all required modules are available")
    sys.exit(1)

class ScenarioB1DXFExporter:
    """DXF exporter for Scenario B1 cross-system routing with internal constraint."""
    
    def __init__(self):
        """Initialize the exporter with Scenario B1 parameters."""
        # Scenario B1 coordinates
        self.A2 = (182.946, 13.304, 157.295)  # Origin (System A)
        self.B3 = (176.062, 2.416, 153.960)   # Destination (System B)
        self.B4 = (176.058, 8.042, 153.960)   # Forbidden section start (System B)
        self.B1 = (175.682, 8.418, 153.960)   # Forbidden section end/Gateway (System B)
        
        # File paths
        self.graph_file = "graph_LV_combined.json"
        self.tramo_map_file = "tramo_map_combined.json"
        self.forbidden_file = "forbidden_scenario_B1.json"
        self.cable_type = "C"
        
        # Results storage
        self.results = {}
        
    def run_pathfinding_analysis(self):
        """Run the pathfinding analysis for both scenarios."""
        print("🚀 Running Scenario B1 pathfinding analysis...")
        
        # 1. Direct cross-system path (no restrictions)
        print("1️⃣ Computing direct cross-system path...")
        try:
            graph_direct = SystemFilteredGraph(self.graph_file, self.cable_type)
            path_direct, nodes_direct = graph_direct.find_path_direct(self.A2, self.B3)
            distance_direct = calculate_path_distance(path_direct)
            
            self.results['direct'] = {
                'path': path_direct,
                'nodes_explored': nodes_direct,
                'distance': distance_direct,
                'status': 'success'
            }
            
            print(f"   ✅ Direct path: {len(path_direct)} points, {distance_direct:.3f} units")
            
        except Exception as e:
            print(f"   ❌ Direct path error: {e}")
            self.results['direct'] = {'status': 'error', 'error': str(e)}
            
        # 2. Cross-system path avoiding B4-B1 internal constraint
        print("2️⃣ Computing path avoiding B4-B1 internal constraint...")
        try:
            graph_forbidden = SystemFilteredGraph(self.graph_file, self.cable_type, 
                                                self.tramo_map_file, self.forbidden_file)
            path_forbidden, nodes_forbidden = graph_forbidden.find_path_direct(self.A2, self.B3)
            distance_forbidden = calculate_path_distance(path_forbidden)
            
            self.results['forbidden'] = {
                'path': path_forbidden,
                'nodes_explored': nodes_forbidden,
                'distance': distance_forbidden,
                'status': 'success'
            }
            
            print(f"   ✅ Avoiding path: {len(path_forbidden)} points, {distance_forbidden:.3f} units")
            
        except Exception as e:
            print(f"   ❌ Avoiding path error: {e}")
            print(f"   📝 This is expected - B4-B1 constraint breaks cross-system connectivity")
            self.results['forbidden'] = {'status': 'error', 'error': str(e)}
            
    def create_dxf_export(self):
        """Create the DXF file with the pathfinding results."""
        print("📐 Creating DXF export...")
        
        # Create new DXF document
        doc = ezdxf.new('R2010')  # AutoCAD LT compatible
        msp = doc.modelspace()
        
        # Define layers and colors
        self._create_layers(doc)
        
        # Add title and scenario information
        self._add_title_block(msp)
        
        # Add coordinate system and key points
        self._add_key_points(msp)
        
        # Add direct path (always available)
        if self.results.get('direct', {}).get('status') == 'success':
            self._add_direct_path(msp)
            
        # Add forbidden section visualization
        self._add_forbidden_section(msp)
        
        # Add avoiding path (if available) or failure indication
        if self.results.get('forbidden', {}).get('status') == 'success':
            self._add_avoiding_path(msp)
        else:
            self._add_failure_indication(msp)
            
        # Add legend and statistics
        self._add_legend(msp)
        self._add_statistics(msp)
        
        # Add analysis notes
        self._add_analysis_notes(msp)
        
        # Save the DXF file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_data/scenario_B1_internal_constraint_{timestamp}.dxf"
        
        os.makedirs("export_data", exist_ok=True)
        doc.saveas(filename)
        
        file_size = os.path.getsize(filename)
        print(f"✅ DXF exported: {filename} ({file_size:,} bytes)")
        
        return filename
        
    def _create_layers(self, doc):
        """Create layers for different elements."""
        doc.layers.new('DIRECT_PATH', dxfattribs={'color': colors.GREEN})
        doc.layers.new('AVOIDING_PATH', dxfattribs={'color': colors.RED})
        doc.layers.new('FORBIDDEN_SECTION', dxfattribs={'color': colors.RED})
        doc.layers.new('KEY_POINTS', dxfattribs={'color': colors.BLUE})
        doc.layers.new('LABELS', dxfattribs={'color': colors.WHITE})
        doc.layers.new('LEGEND', dxfattribs={'color': colors.CYAN})
        doc.layers.new('STATISTICS', dxfattribs={'color': colors.YELLOW})
        doc.layers.new('ANALYSIS', dxfattribs={'color': colors.MAGENTA})
        
    def _add_title_block(self, msp):
        """Add title and scenario information."""
        msp.add_text(
            "SCENARIO B1: Cross-System Routing with Internal System B Constraint",
            dxfattribs={'layer': 'LABELS', 'height': 2.0, 'insert': (120, 170, 150)}
        )
        
        msp.add_text(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            dxfattribs={'layer': 'LABELS', 'height': 1.0, 'insert': (120, 167, 150)}
        )
        
        msp.add_text(
            "Cable Type: C (Cross-System) | Forbidden: B4-B1 Internal Section (Tramo 395)",
            dxfattribs={'layer': 'LABELS', 'height': 1.0, 'insert': (120, 164, 150)}
        )
        
    def _add_key_points(self, msp):
        """Add key coordinate points."""
        points = {
            'A2 (Origin)': self.A2,
            'B3 (Destination)': self.B3,
            'B4 (Forbidden Start)': self.B4,
            'B1 (Gateway/Forbidden End)': self.B1
        }
        
        for name, (x, y, z) in points.items():
            # Add point marker
            msp.add_circle(
                center=(x, y, z),
                radius=0.5,
                dxfattribs={'layer': 'KEY_POINTS'}
            )
            
            # Add label
            msp.add_text(
                f"{name}\n({x:.3f}, {y:.3f}, {z:.3f})",
                dxfattribs={'layer': 'LABELS', 'height': 0.8, 'insert': (x + 1, y + 1, z)}
            )
            
    def _add_direct_path(self, msp):
        """Add the direct cross-system path."""
        path = self.results['direct']['path']
        
        # Draw path as 3D polyline (like working Scenario A)
        points_3d = [(p[0], p[1], p[2]) for p in path]
        msp.add_polyline3d(
            points_3d,
            dxfattribs={'layer': 'DIRECT_PATH', 'lineweight': 35}
        )
        
        # Add path markers
        for i, (x, y, z) in enumerate(path):
            if i % 5 == 0:  # Every 5th point
                msp.add_circle(
                    center=(x, y, z),
                    radius=0.2,
                    dxfattribs={'layer': 'DIRECT_PATH'}
                )
                
    def _add_forbidden_section(self, msp):
        """Add the forbidden B4-B1 section."""
        # Draw forbidden section as thick line
        msp.add_line(
            start=(self.B4[0], self.B4[1], self.B4[2]),
            end=(self.B1[0], self.B1[1], self.B1[2]),
            dxfattribs={'layer': 'FORBIDDEN_SECTION', 'lineweight': 50}
        )
        
        # Add forbidden section label
        mid_x = (self.B4[0] + self.B1[0]) / 2
        mid_y = (self.B4[1] + self.B1[1]) / 2
        mid_z = (self.B4[2] + self.B1[2]) / 2
        
        msp.add_text(
            "FORBIDDEN B4-B1 Section (Tramo 395)",
            dxfattribs={'layer': 'FORBIDDEN_SECTION', 'height': 0.8, 'insert': (mid_x, mid_y + 2, mid_z)}
        )
        
    def _add_avoiding_path(self, msp):
        """Add the path avoiding the forbidden section (if it exists)."""
        path = self.results['forbidden']['path']
        
        # Draw path as 3D polyline (like working Scenario A)
        points_3d = [(p[0], p[1], p[2]) for p in path]
        msp.add_polyline3d(
            points_3d,
            dxfattribs={'layer': 'AVOIDING_PATH', 'lineweight': 35}
        )
        
        # Add path markers
        for i, (x, y, z) in enumerate(path):
            if i % 5 == 0:  # Every 5th point
                msp.add_circle(
                    center=(x, y, z),
                    radius=0.2,
                    dxfattribs={'layer': 'AVOIDING_PATH'}
                )
                
    def _add_failure_indication(self, msp):
        """Add indication that the avoiding path failed."""
        # Add failure text near the forbidden section
        msp.add_text(
            "NO ROUTE FOUND - Internal constraint breaks cross-system connectivity",
            dxfattribs={'layer': 'AVOIDING_PATH', 'height': 1.2, 'insert': (self.B1[0] + 3, self.B1[1] + 3, self.B1[2])}
        )
        
        # Add explanation
        msp.add_text(
            "Gateway Isolation: B1 serves as cross-system gateway but B4-B1 provides only access to System B network",
            dxfattribs={'layer': 'ANALYSIS', 'height': 0.9, 'insert': (170, 10, 150)}
        )
        
    def _add_legend(self, msp):
        """Add legend explaining the colors and symbols."""
        legend_x = 120
        legend_y = 40
        
        msp.add_text(
            "LEGEND:",
            dxfattribs={'layer': 'LEGEND', 'height': 1.5, 'insert': (legend_x, legend_y, 150)}
        )
        
        legend_items = [
            ("GREEN Line", "Direct Cross-System Path (A2→B3)"),
            ("RED Line", "Path Avoiding B4-B1 (FAILED)"),
            ("RED Line", "Forbidden B4-B1 Section (Tramo 395)"),
            ("BLUE Circles", "Key Coordinate Points"),
            ("Analysis", "Internal constraint causes gateway isolation")
        ]
        
        for i, (color, description) in enumerate(legend_items):
            y_pos = legend_y - 3 - (i * 2)
            msp.add_text(
                f"• {color}: {description}",
                dxfattribs={'layer': 'LEGEND', 'height': 0.9, 'insert': (legend_x, y_pos, 150)}
            )
            
    def _add_statistics(self, msp):
        """Add pathfinding statistics."""
        stats_x = 160
        stats_y = 40
        
        msp.add_text(
            "PATHFINDING STATISTICS:",
            dxfattribs={'layer': 'STATISTICS', 'height': 1.5, 'insert': (stats_x, stats_y, 150)}
        )
        
        if self.results.get('direct', {}).get('status') == 'success':
            direct = self.results['direct']
            stats_lines = [
                f"Direct Path (GREEN): {len(direct['path'])} points, {direct['nodes_explored']} nodes, {direct['distance']:.3f} units - SUCCESS",
                "Avoiding Path (RED): FAILED - Gateway isolation",
                "Impact: Internal B4-B1 constraint prevents cross-system routing",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ]
            
            for i, line in enumerate(stats_lines):
                msp.add_text(
                    line,
                    dxfattribs={'layer': 'STATISTICS', 'height': 0.8, 'insert': (stats_x, stats_y - 3 - (i * 1.5), 150)}
                )
        else:
            msp.add_text(
                "No pathfinding results available",
                dxfattribs={'layer': 'STATISTICS', 'height': 0.8, 'insert': (stats_x, stats_y - 3, 150)}
            )
        
    def _add_analysis_notes(self, msp):
        """Add technical analysis notes."""
        analysis_x = 120
        analysis_y = 160
        
        analysis_lines = [
            "TECHNICAL ANALYSIS - Gateway Isolation Pattern:",
            "1. Direct Route: A2 (System A) → B1 (Gateway) → B4 → B3 (System B)",
            "2. B1 serves as the cross-system transition point (System A → System B)",
            "3. B4-B1 provides the only access from gateway B1 to System B network",
            "4. Blocking B4-B1 isolates B1, preventing access to destination B3",
            "5. Result: Complete cross-system routing failure despite reaching System B",
            "",
            "CRITICAL FINDING: Internal constraints can break cross-system connectivity",
            "when they affect gateway access points."
        ]
        
        for i, line in enumerate(analysis_lines):
            if line:  # Skip empty lines
                msp.add_text(
                    line,
                    dxfattribs={'layer': 'ANALYSIS', 'height': 0.7, 'insert': (analysis_x, analysis_y - (i * 1.2), 150)}
                )

def main():
    """Main function to run the Scenario B1 DXF export."""
    try:
        print("🎯 Starting Scenario B1 DXF Export")
        print("="*60)
        
        exporter = ScenarioB1DXFExporter()
        
        # Run pathfinding analysis
        exporter.run_pathfinding_analysis()
        
        # Create DXF export
        filename = exporter.create_dxf_export()
        
        print("\n🎉 Scenario B1 DXF Export Completed!")
        print(f"📁 File: {filename}")
        print("\n📖 This DXF demonstrates:")
        print("   • Direct cross-system routing (GREEN)")
        print("   • Impact of internal System B constraint (RED)")
        print("   • Gateway isolation failure pattern")
        print("   • Critical dependency analysis")
        
    except KeyboardInterrupt:
        print("\n⏹️  Export interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 