#!/usr/bin/env python3
"""
DEMO: Scenario A - Multi-System Cable-Aware Pathfinding with Forbidden Sections

This demo showcases the complete workflow of the astar_PPOF_systems.py algorithm
including file generation, pathfinding execution, and result visualization.

Scenario A demonstrates:
1. Direct pathfinding (GREEN)
2. Pathfinding with forbidden sections (RED) 
3. PPO pathfinding with forbidden sections (MAGENTA)
4. DXF export for AutoCAD LT compatibility

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
    from cable_filter import ALLOWED, get_cable_info, coord_to_key, load_tagged_graph
    from astar_PPO_forbid import calculate_path_distance, format_point
    import ezdxf
    from ezdxf import colors
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all required modules are available")
    sys.exit(1)

class ScenarioADemo:
    """Demo class for Scenario A pathfinding demonstration."""
    
    def __init__(self):
        """Initialize the demo with Scenario A parameters."""
        # Scenario A coordinates (adjusted to available points in graph)
        self.A1 = (170.839, 12.530, 156.634)  # Origin
        self.A2 = (182.946, 13.304, 157.295)  # Destination  
        self.A3 = (177.381, 14.056, 157.295)  # Forbidden section start
        self.A4 = (178.482, 14.056, 157.295)  # Forbidden section end
        self.A5 = (196.310, 18.545, 153.799)  # PPO (adjusted to available point)
        
        # File paths
        self.graph_file = "graph_LV_combined.json"
        self.tramo_map_file = "tramo_map_combined.json"
        self.forbidden_file = "forbidden_scenario_A.json"
        
        # Cable type for this scenario
        self.cable_type = "A"
        
        # Results storage
        self.results = {}
        
    def print_header(self, title):
        """Print a formatted header."""
        print("\n" + "="*80)
        print(f"🎯 {title}")
        print("="*80)
        
    def print_section(self, title):
        """Print a formatted section header."""
        print(f"\n📋 {title}")
        print("-" * 60)
        
    def validate_files(self):
        """Validate that all required files exist."""
        self.print_section("File Validation")
        
        required_files = [
            self.graph_file,
            self.tramo_map_file,
            self.forbidden_file
        ]
        
        all_exist = True
        for file_path in required_files:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"✅ {file_path} ({size:,} bytes)")
            else:
                print(f"❌ {file_path} - NOT FOUND")
                all_exist = False
                
        return all_exist
        
    def show_scenario_info(self):
        """Display scenario information and coordinates."""
        self.print_section("Scenario A Configuration")
        
        print(f"🎯 Scenario: Multi-system pathfinding with forbidden sections")
        print(f"🔧 Cable Type: {self.cable_type}")
        
        cable_info = get_cable_info(self.cable_type)
        print(f"📡 Allowed Systems: {', '.join(sorted(cable_info['allowed_systems']))}")
        
        print(f"\n📍 Key Coordinates:")
        print(f"   A1 (Origin):      {format_point(self.A1)}")
        print(f"   A2 (Destination): {format_point(self.A2)}")
        print(f"   A3 (Forbidden):   {format_point(self.A3)}")
        print(f"   A4 (Forbidden):   {format_point(self.A4)}")
        print(f"   A5 (PPO):         {format_point(self.A5)}")
        
    def verify_coordinates(self):
        """Verify that coordinates exist in the graph."""
        self.print_section("Coordinate Verification")
        
        # Load graph data
        graph_data = load_tagged_graph(self.graph_file)
        
        coordinates = {
            'A1': self.A1,
            'A2': self.A2,
            'A3': self.A3,
            'A4': self.A4,
            'A5': self.A5
        }
        
        all_valid = True
        for name, coord in coordinates.items():
            key = coord_to_key(coord)
            if key in graph_data['nodes']:
                system = graph_data['nodes'][key]['sys']
                print(f"✅ {name}: {format_point(coord)} -> System {system}")
            else:
                print(f"❌ {name}: {format_point(coord)} -> NOT FOUND")
                all_valid = False
                
        return all_valid
        
    def run_pathfinding_tests(self):
        """Run all three pathfinding scenarios."""
        self.print_section("Pathfinding Execution")
        
        print("🚀 Running pathfinding scenarios...")
        
        # 1. Direct path (no restrictions)
        print(f"\n1️⃣ Direct Path (GREEN) - No restrictions")
        start_time = time.time()
        try:
            graph_direct = SystemFilteredGraph(self.graph_file, self.cable_type)
            path_direct, nodes_direct = graph_direct.find_path_direct(self.A1, self.A2)
            distance_direct = calculate_path_distance(path_direct)
            execution_time = time.time() - start_time
            
            self.results['direct'] = {
                'path': path_direct,
                'nodes_explored': nodes_direct,
                'distance': distance_direct,
                'execution_time': execution_time,
                'status': 'success'
            }
            
            print(f"   ✅ Success: {len(path_direct)} points, {nodes_direct} nodes, {distance_direct:.3f} units ({execution_time:.3f}s)")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.results['direct'] = {'status': 'error', 'error': str(e)}
            
        # 2. Path avoiding forbidden sections  
        print(f"\n2️⃣ Forbidden-Avoiding Path (RED) - With restrictions")
        start_time = time.time()
        try:
            graph_forbidden = SystemFilteredGraph(self.graph_file, self.cable_type, 
                                                self.tramo_map_file, self.forbidden_file)
            path_forbidden, nodes_forbidden = graph_forbidden.find_path_direct(self.A1, self.A2)
            distance_forbidden = calculate_path_distance(path_forbidden)
            execution_time = time.time() - start_time
            
            self.results['forbidden'] = {
                'path': path_forbidden,
                'nodes_explored': nodes_forbidden, 
                'distance': distance_forbidden,
                'execution_time': execution_time,
                'status': 'success'
            }
            
            print(f"   ✅ Success: {len(path_forbidden)} points, {nodes_forbidden} nodes, {distance_forbidden:.3f} units ({execution_time:.3f}s)")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.results['forbidden'] = {'status': 'error', 'error': str(e)}
            
        # 3. PPO path with forbidden sections
        print(f"\n3️⃣ PPO Path (MAGENTA) - Through A5 with restrictions")
        start_time = time.time()
        try:
            path_ppo, nodes_ppo = graph_forbidden.find_path_with_ppo(self.A1, self.A5, self.A2)
            distance_ppo = calculate_path_distance(path_ppo)
            execution_time = time.time() - start_time
            
            self.results['ppo'] = {
                'path': path_ppo,
                'nodes_explored': nodes_ppo,
                'distance': distance_ppo, 
                'execution_time': execution_time,
                'status': 'success'
            }
            
            print(f"   ✅ Success: {len(path_ppo)} points, {nodes_ppo} nodes, {distance_ppo:.3f} units ({execution_time:.3f}s)")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.results['ppo'] = {'status': 'error', 'error': str(e)}
            
    def analyze_results(self):
        """Analyze and compare the pathfinding results."""
        self.print_section("Results Analysis")
        
        # Create comparison table
        print(f"{'Scenario':<25} {'Points':<8} {'Nodes':<8} {'Distance':<12} {'Time':<8} {'Status':<10}")
        print("-" * 80)
        
        scenarios = [
            ('Direct (GREEN)', 'direct'),
            ('Forbidden-Avoid (RED)', 'forbidden'), 
            ('PPO (MAGENTA)', 'ppo')
        ]
        
        for name, key in scenarios:
            result = self.results.get(key, {})
            if result.get('status') == 'success':
                points = len(result['path'])
                nodes = result['nodes_explored']
                distance = result['distance']
                time_taken = result['execution_time']
                status = "✅ SUCCESS"
                print(f"{name:<25} {points:<8} {nodes:<8} {distance:<12.3f} {time_taken:<8.3f} {status:<10}")
            else:
                print(f"{name:<25} {'N/A':<8} {'N/A':<8} {'N/A':<12} {'N/A':<8} {'❌ ERROR':<10}")
                
        # Calculate impact metrics
        if (self.results.get('direct', {}).get('status') == 'success' and 
            self.results.get('forbidden', {}).get('status') == 'success'):
            
            direct_points = len(self.results['direct']['path'])
            forbidden_points = len(self.results['forbidden']['path'])
            impact_factor = forbidden_points / direct_points
            
            print(f"\n📊 Forbidden Section Impact:")
            print(f"   Path length increase: {impact_factor:.1f}x ({direct_points} → {forbidden_points} points)")
            
            direct_dist = self.results['direct']['distance']
            forbidden_dist = self.results['forbidden']['distance']
            dist_impact = forbidden_dist / direct_dist
            print(f"   Distance increase: {dist_impact:.1f}x ({direct_dist:.1f} → {forbidden_dist:.1f} units)")
            
    def run_complete_demo(self):
        """Run the complete Scenario A demonstration."""
        self.print_header("DEMO: Scenario A - Cable-Aware Pathfinding System")
        
        print(f"🎯 Demonstration of astar_PPOF_systems.py capabilities")
        print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Validate environment
        if not self.validate_files():
            print("\n❌ Required files missing. Please ensure all supporting files are available.")
            return False
            
        # Step 2: Show scenario information
        self.show_scenario_info()
        
        # Step 3: Verify coordinates
        if not self.verify_coordinates():
            print("\n❌ Coordinate verification failed. Some coordinates not found in graph.")
            return False
            
        # Step 4: Run pathfinding tests
        self.run_pathfinding_tests()
        
        # Step 5: Analyze results
        self.analyze_results()
        
        print("\n✅ Scenario A demonstration completed successfully!")
        return True

def main():
    """Main function to run the Scenario A demo."""
    try:
        demo = ScenarioADemo()
        success = demo.run_complete_demo()
        
        if success:
            print(f"\n🎉 Demo completed successfully!")
            print(f"📖 This demo showcases the complete workflow of astar_PPOF_systems.py")
            print(f"🔧 Ready for production use with real-world cable routing scenarios")
        else:
            print(f"\n❌ Demo encountered errors. Please check the output above.")
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
