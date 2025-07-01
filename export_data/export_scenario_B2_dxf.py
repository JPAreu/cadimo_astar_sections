#!/usr/bin/env python3
"""
DXF Export for Scenario B2: Cross-System Routing with PPO (Mandatory Waypoint)

This script generates AutoCAD-compatible DXF files for Scenario B2, which demonstrates
cross-system cable routing with PPO (Punto de Paso Obligatorio) constraints.

Scenario B2 visualizes:
1. Direct Cross-System Path (GREEN) - A2 to B3 without constraints
2. PPO Cross-System Path (MAGENTA) - A2 to B5 (PPO) to B3 with mandatory waypoint
3. Key Points: Origin A2 (System A), Destination B3 (System B), PPO B5 (System B)
4. Cross-system gateway point identification
5. PPO compliance visualization

Author: AI Assistant  
Date: 2024-07-01
"""

import sys
import os
import json
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

class ScenarioB2DXFExporter:
    """DXF exporter for Scenario B2 cross-system PPO routing visualization."""
    
    def __init__(self):
        """Initialize the exporter with Scenario B2 parameters."""
        # Scenario B2 coordinates
        self.A2 = (182.946, 13.304, 157.295)  # Origin (System A)
        self.B3 = (176.062, 2.416, 153.960)   # Destination (System B)  
        self.B5 = (170.919, 8.418, 153.960)   # PPO - Mandatory waypoint (System B)
        
        # File paths
        self.graph_file = "graph_LV_combined.json"
        self.cable_type = "C"
        
        # Results storage
        self.paths = {}
        self.gateway_points = {}
        
    def run_pathfinding(self):
        """Execute pathfinding scenarios and store results."""
        print("🚀 Running Scenario B2 pathfinding for DXF export...")
        
        try:
            # 1. Direct cross-system path
            print("   1️⃣ Direct cross-system path (GREEN)")
            graph_direct = SystemFilteredGraph(self.graph_file, self.cable_type)
            path_direct, nodes_direct = graph_direct.find_path_direct(self.A2, self.B3)
            distance_direct = calculate_path_distance(path_direct)
            
            self.paths['direct'] = {
                'path': path_direct,
                'nodes_explored': nodes_direct,
                'distance': distance_direct,
                'color': 'GREEN',
                'description': 'Direct Cross-System Path'
            }
            
            # Find cross-system gateway point
            self.gateway_points['direct'] = self._find_gateway_point(path_direct)
            
            print(f"      ✅ Success: {len(path_direct)} points, {distance_direct:.3f} units")
            
            # 2. PPO cross-system path
            print("   2️⃣ PPO cross-system path (MAGENTA)")
            graph_ppo = SystemFilteredGraph(self.graph_file, self.cable_type)
            path_ppo, nodes_ppo = graph_ppo.find_path_with_ppo(self.A2, self.B5, self.B3)
            distance_ppo = calculate_path_distance(path_ppo)
            
            self.paths['ppo'] = {
                'path': path_ppo,
                'nodes_explored': nodes_ppo,
                'distance': distance_ppo,
                'color': 'MAGENTA',
                'description': 'PPO Cross-System Path'
            }
            
            # Find cross-system gateway point
            self.gateway_points['ppo'] = self._find_gateway_point(path_ppo)
            
            print(f"      ✅ Success: {len(path_ppo)} points, {distance_ppo:.3f} units")
            
            return True
            
        except Exception as e:
            print(f"❌ Pathfinding error: {e}")
            return False
            
    def _find_gateway_point(self, path):
        """Find the cross-system gateway point in a path."""
        if not path or len(path) < 2:
            return None
            
        # Load graph data to get system information
        graph_data = load_tagged_graph(self.graph_file)
        
        current_system = None
        for i, point in enumerate(path):
            key = coord_to_key(point)
            if key in graph_data['nodes']:
                system = graph_data['nodes'][key]['sys']
                if current_system is None:
                    current_system = system
                elif current_system != system:
                    return {
                        'point': point,
                        'index': i,
                        'from_system': current_system,
                        'to_system': system
                    }
                    
        return None
        
    def create_dxf_export(self):
        """Create DXF file with cross-system PPO routing visualization."""
        print("📐 Creating DXF export for Scenario B2...")
        
        # Create new DXF document (R2010 for AutoCAD LT compatibility)
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        # Create layers for different elements
        layers = {
            'DIRECT_PATH': {'color': colors.GREEN, 'lineweight': 35},
            'PPO_PATH': {'color': colors.MAGENTA, 'lineweight': 50},
            'KEY_POINTS': {'color': colors.RED, 'lineweight': 70},
            'GATEWAY': {'color': colors.BLUE, 'lineweight': 50},
            'PPO_MARKER': {'color': colors.CYAN, 'lineweight': 70},
            'TEXT': {'color': colors.BLACK, 'lineweight': 25},
            'LEGEND': {'color': colors.BLACK, 'lineweight': 35}
        }
        
        # Create layers
        for layer_name, props in layers.items():
            layer = doc.layers.new(layer_name)
            layer.color = props['color']
            layer.lineweight = props['lineweight']
            
        # Draw paths
        self._draw_paths(msp)
        
        # Draw key points
        self._draw_key_points(msp)
        
        # Draw gateway points
        self._draw_gateway_points(msp)
        
        # Draw PPO marker
        self._draw_ppo_marker(msp)
        
        # Add legend and statistics
        self._add_legend_and_stats(msp)
        
        # Save DXF file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_data/scenario_B2_cross_system_ppo_{timestamp}.dxf"
        
        # Ensure export directory exists
        os.makedirs("export_data", exist_ok=True)
        
        try:
            doc.saveas(filename)
            file_size = os.path.getsize(filename)
            print(f"✅ DXF exported successfully: {filename} ({file_size:,} bytes)")
            return filename
        except Exception as e:
            print(f"❌ DXF export error: {e}")
            return None
            
    def _draw_paths(self, msp):
        """Draw the routing paths."""
        for scenario, data in self.paths.items():
            path = data['path']
            layer_name = 'DIRECT_PATH' if scenario == 'direct' else 'PPO_PATH'
            
            if len(path) >= 2:
                # Convert to 3D points for polyline3d
                points_3d = [(p[0], p[1], p[2]) for p in path]
                
                # Create 3D polyline
                polyline = msp.add_polyline3d(points_3d)
                polyline.dxf.layer = layer_name
                
    def _draw_key_points(self, msp):
        """Draw key coordinate points."""
        key_points = {
            'A2 (Origin - Sys A)': self.A2,
            'B3 (Dest - Sys B)': self.B3,
            'B5 (PPO - Sys B)': self.B5
        }
        
        for label, point in key_points.items():
            # Draw circle marker
            circle = msp.add_circle((point[0], point[1], point[2]), 0.5)
            circle.dxf.layer = 'KEY_POINTS'
            
            # Add text label
            text = msp.add_text(label)
            text.set_placement((point[0] + 1.0, point[1] + 1.0, point[2]))
            text.dxf.layer = 'TEXT'
            text.dxf.height = 0.8
            
    def _draw_gateway_points(self, msp):
        """Draw cross-system gateway points."""
        for scenario, gateway in self.gateway_points.items():
            if gateway:
                point = gateway['point']
                
                # Draw larger circle for gateway
                circle = msp.add_circle((point[0], point[1], point[2]), 1.0)
                circle.dxf.layer = 'GATEWAY'
                
                # Add gateway label
                label = f"Gateway ({gateway['from_system']}→{gateway['to_system']})"
                text = msp.add_text(label)
                text.set_placement((point[0] + 1.5, point[1] - 1.5, point[2]))
                text.dxf.layer = 'TEXT'
                text.dxf.height = 0.7
                
                # Only draw once (both scenarios use same gateway)
                break
                
    def _draw_ppo_marker(self, msp):
        """Draw special PPO (mandatory waypoint) marker."""
        # Draw diamond shape around PPO point
        ppo_x, ppo_y, ppo_z = self.B5
        diamond_size = 1.2
        
        # Diamond vertices
        diamond_points = [
            (ppo_x, ppo_y + diamond_size, ppo_z),        # Top
            (ppo_x + diamond_size, ppo_y, ppo_z),        # Right
            (ppo_x, ppo_y - diamond_size, ppo_z),        # Bottom
            (ppo_x - diamond_size, ppo_y, ppo_z),        # Left
            (ppo_x, ppo_y + diamond_size, ppo_z)         # Close
        ]
        
        # Create diamond polyline
        diamond = msp.add_polyline3d(diamond_points)
        diamond.dxf.layer = 'PPO_MARKER'
        
        # Add PPO label
        text = msp.add_text("PPO (Mandatory)")
        text.set_placement((ppo_x + 2.0, ppo_y + 2.0, ppo_z))
        text.dxf.layer = 'TEXT'
        text.dxf.height = 0.9
        
    def _add_legend_and_stats(self, msp):
        """Add legend and statistics to the drawing."""
        # Find bounds for legend placement
        all_points = []
        for data in self.paths.values():
            all_points.extend(data['path'])
        all_points.extend([self.A2, self.B3, self.B5])
        
        if all_points:
            max_x = max(p[0] for p in all_points)
            max_y = max(p[1] for p in all_points)
            max_z = max(p[2] for p in all_points)
            
            # Legend position
            legend_x = max_x + 10
            legend_y = max_y - 5
            legend_z = max_z
            
            # Title
            title = msp.add_text("SCENARIO B2: Cross-System PPO Routing")
            title.set_placement((legend_x, legend_y, legend_z))
            title.dxf.layer = 'LEGEND'
            title.dxf.height = 1.5
            
            # Subtitle
            subtitle = msp.add_text("Cable C - Cross-System with Mandatory Waypoint")
            subtitle.set_placement((legend_x, legend_y - 2, legend_z))
            subtitle.dxf.layer = 'LEGEND'
            subtitle.dxf.height = 1.0
            
            # Path statistics
            y_offset = 5
            for scenario, data in self.paths.items():
                scenario_name = data['description']
                points = len(data['path'])
                nodes = data['nodes_explored']
                distance = data['distance']
                
                stats_text = f"{scenario_name}: {points} pts, {nodes} nodes, {distance:.1f} units"
                stats = msp.add_text(stats_text)
                stats.set_placement((legend_x, legend_y - y_offset, legend_z))
                stats.dxf.layer = 'LEGEND'
                stats.dxf.height = 0.8
                y_offset += 1.5
                
            # PPO impact analysis
            if 'direct' in self.paths and 'ppo' in self.paths:
                direct_points = len(self.paths['direct']['path'])
                ppo_points = len(self.paths['ppo']['path'])
                impact_factor = ppo_points / direct_points
                
                impact_text = f"PPO Impact: {impact_factor:.1f}x path increase"
                impact = msp.add_text(impact_text)
                impact.set_placement((legend_x, legend_y - y_offset, legend_z))
                impact.dxf.layer = 'LEGEND'
                impact.dxf.height = 0.8
                y_offset += 1.5
                
            # Legend items
            legend_items = [
                ("━━━ Direct Cross-System (GREEN)", colors.GREEN),
                ("━━━ PPO Cross-System (MAGENTA)", colors.MAGENTA),
                ("● Key Points (RED)", colors.RED),
                ("◯ Cross-System Gateway (BLUE)", colors.BLUE),
                ("◆ PPO Mandatory Waypoint (CYAN)", colors.CYAN)
            ]
            
            y_offset += 1
            for item_text, color in legend_items:
                item = msp.add_text(item_text)
                item.set_placement((legend_x, legend_y - y_offset, legend_z))
                item.dxf.layer = 'LEGEND'
                item.dxf.height = 0.7
                y_offset += 1.2
                
            # Timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            time_text = msp.add_text(f"Generated: {timestamp}")
            time_text.set_placement((legend_x, legend_y - y_offset - 2, legend_z))
            time_text.dxf.layer = 'LEGEND'
            time_text.dxf.height = 0.6

def main():
    """Main function to run the Scenario B2 DXF export."""
    print("🎯 Scenario B2 DXF Export - Cross-System PPO Routing")
    print("="*60)
    
    try:
        exporter = ScenarioB2DXFExporter()
        
        # Run pathfinding
        if not exporter.run_pathfinding():
            print("❌ Pathfinding failed, cannot create DXF export")
            return
            
        # Create DXF export
        filename = exporter.create_dxf_export()
        
        if filename:
            print(f"\n🎉 Scenario B2 DXF export completed successfully!")
            print(f"📁 Output file: {filename}")
            print(f"🎯 Visualizes cross-system routing with PPO (mandatory waypoint)")
            print(f"📊 Shows PPO impact on cross-system pathfinding efficiency")
        else:
            print(f"\n❌ DXF export failed")
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Export interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 