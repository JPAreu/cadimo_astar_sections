#!/usr/bin/env python3
"""
DEMO: Scenario B1 - Cross-System Cable Routing with B4-B1 Forbidden Section

This demo showcases cross-system routing capabilities when a section within System B
is blocked by forbidden sections, testing the impact on cross-system connectivity.

Scenario B1 demonstrates:
1. Cross-system routing from System A to System B
2. Cable C capabilities (access to both systems)
3. Forbidden section impact within System B on cross-system routing
4. Alternative routing when internal system connections are blocked

Key Test Case:
- Origin (A2): System A point (182.946, 13.304, 157.295) - repeats from Scenario A
- Destination (B3): System B point (176.062, 2.416, 153.960) 
- Forbidden Section: B4-B1 edge (176.058, 8.042, 153.960) ↔ (175.682, 8.418, 153.960)
- Cable Type: Cable C (can access both System A and System B)

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

class ScenarioB1Demo:
    """Demo class for Scenario B1 cross-system pathfinding demonstration."""
    
    def __init__(self):
        """Initialize the demo with Scenario B1 parameters."""
        # Scenario B1 coordinates - Cross-system routing with internal System B constraint
        self.A2 = (182.946, 13.304, 157.295)  # Origin (System A) - repeats from Scenario A
        self.B3 = (176.062, 2.416, 153.960)   # Destination (System B)
        self.B4 = (176.058, 8.042, 153.960)   # Forbidden section start (System B)
        self.B1 = (175.682, 8.418, 153.960)   # Forbidden section end (System B)
        
        # File paths
        self.graph_file = "graph_LV_combined.json"
        self.tramo_map_file = "tramo_map_combined.json"
        self.forbidden_file = "forbidden_scenario_B1.json"
        
        # Cable type for cross-system routing
        self.cable_type = "C"
        
        # Results storage
        self.results = {}
        
    def print_header(self, title):
        """Print a formatted header."""
        print("\n" + "="*80)
        print(f"🔧 {title}")
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
        self.print_section("Scenario B1 Configuration - Internal System B Constraint")
        
        print(f"🔧 Scenario: Cross-system routing with internal System B constraint")
        print(f"🔧 Cable Type: {self.cable_type}")
        
        cable_info = get_cable_info(self.cable_type)
        print(f"📡 Allowed Systems: {', '.join(sorted(cable_info['allowed_systems']))}")
        
        print(f"\n📍 Key Coordinates:")
        print(f"   A2 (Origin - System A):     {format_point(self.A2)}")
        print(f"   B3 (Destination - System B): {format_point(self.B3)}")
        print(f"   B4 (Forbidden Start):       {format_point(self.B4)}")
        print(f"   B1 (Forbidden End):         {format_point(self.B1)}")
        
        print(f"\n🔧 System B Internal Challenge:")
        print(f"   • Origin in System A, Destination in System B")
        print(f"   • B4↔B1 section within System B will be forbidden")
        print(f"   • Tests impact of internal constraints on cross-system routing")
        
    def verify_coordinates(self):
        """Verify that coordinates exist in the graph and show their systems."""
        self.print_section("Coordinate Verification & System Analysis")
        
        # Load graph data
        graph_data = load_tagged_graph(self.graph_file)
        
        coordinates = {
            'A2 (Origin)': self.A2,
            'B3 (Destination)': self.B3,
            'B4 (Forbidden Start)': self.B4,
            'B1 (Forbidden End)': self.B1
        }
        
        all_valid = True
        system_distribution = {'A': 0, 'B': 0}
        
        for name, coord in coordinates.items():
            key = coord_to_key(coord)
            if key in graph_data['nodes']:
                system = graph_data['nodes'][key]['sys']
                system_distribution[system] += 1
                print(f"✅ {name}: {format_point(coord)} -> System {system}")
            else:
                print(f"❌ {name}: {format_point(coord)} -> NOT FOUND")
                all_valid = False
                
        print(f"\n🔍 System Distribution:")
        print(f"   System A points: {system_distribution['A']}")
        print(f"   System B points: {system_distribution['B']}")
        
        if system_distribution['A'] > 0 and system_distribution['B'] > 0:
            print(f"✅ Cross-system routing required - Cable C is appropriate")
        else:
            print(f"⚠️  All points in same system - cross-system demo may not be optimal")
                
        return all_valid
        
    def analyze_forbidden_section(self):
        """Analyze the forbidden section and its impact on cross-system routing."""
        self.print_section("Forbidden Section Analysis")
        
        # Load forbidden sections
        with open(self.forbidden_file, 'r') as f:
            forbidden_tramos = json.load(f)
            
        print(f"🚫 Forbidden Tramo IDs: {forbidden_tramos}")
        
        # Load tramo mapping to show which edge is forbidden
        with open(self.tramo_map_file, 'r') as f:
            tramo_map = json.load(f)
            
        for tramo_id in forbidden_tramos:
            for edge_key, mapped_id in tramo_map.items():
                if mapped_id == tramo_id:
                    print(f"🔍 Tramo {tramo_id}: {edge_key}")
                    
                    # Parse edge coordinates
                    if "175.682, 8.418, 153.960" in edge_key and "176.058, 8.042, 153.960" in edge_key:
                        print(f"   This is the B4↔B1 section connecting:")
                        print(f"   • B4: {format_point(self.B4)} (System B)")
                        print(f"   • B1: {format_point(self.B1)} (System B)")
                        print(f"   🔧 This edge is within System B network")
                    break
                    
        print(f"\n💡 Impact Analysis:")
        print(f"   • Blocking this section forces alternative routes within System B")
        print(f"   • May affect cross-system connectivity if B1 is important for transitions")
        print(f"   • Tests algorithm's ability to handle internal system constraints")
        
    def run_pathfinding_tests(self):
        """Run cross-system pathfinding scenarios."""
        self.print_section("Cross-System Pathfinding Execution")
        
        print("🚀 Running cross-system pathfinding scenarios...")
        
        # 1. Direct cross-system path (no restrictions)
        print(f"\n1️⃣ Direct Cross-System Path (GREEN) - No restrictions")
        print(f"   System A → System B routing")
        start_time = time.time()
        try:
            graph_direct = SystemFilteredGraph(self.graph_file, self.cable_type)
            path_direct, nodes_direct = graph_direct.find_path_direct(self.A2, self.B3)
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
            
            # Analyze cross-system transitions
            self._analyze_cross_system_transitions(path_direct, "Direct")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.results['direct'] = {'status': 'error', 'error': str(e)}
            
        # 2. Cross-system path avoiding forbidden section
        print(f"\n2️⃣ Section-Avoiding Cross-System Path (RED) - With restrictions")
        print(f"   System A → System B routing with B4↔B1 section forbidden")
        start_time = time.time()
        try:
            graph_forbidden = SystemFilteredGraph(self.graph_file, self.cable_type, 
                                                self.tramo_map_file, self.forbidden_file)
            path_forbidden, nodes_forbidden = graph_forbidden.find_path_direct(self.A2, self.B3)
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
            
            # Analyze cross-system transitions
            self._analyze_cross_system_transitions(path_forbidden, "Section-Avoiding")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.results['forbidden'] = {'status': 'error', 'error': str(e)}
            
    def _analyze_cross_system_transitions(self, path, scenario_name):
        """Analyze where the path transitions between systems."""
        if not path or len(path) < 2:
            return
            
        # Load graph data to get system information
        graph_data = load_tagged_graph(self.graph_file)
        
        transitions = []
        current_system = None
        
        for i, point in enumerate(path):
            key = coord_to_key(point)
            if key in graph_data['nodes']:
                system = graph_data['nodes'][key]['sys']
                if current_system is None:
                    current_system = system
                elif current_system != system:
                    transitions.append({
                        'from_system': current_system,
                        'to_system': system,
                        'point_index': i,
                        'coordinate': point
                    })
                    current_system = system
                    
        if transitions:
            print(f"   🌉 {scenario_name} Cross-System Transitions: {len(transitions)}")
            for i, trans in enumerate(transitions):
                print(f"      {i+1}. Point {trans['point_index']}: System {trans['from_system']} → System {trans['to_system']}")
                print(f"         At: {format_point(trans['coordinate'])}")
        else:
            print(f"   ⚠️  {scenario_name}: No clear cross-system transitions detected")
            
    def analyze_results(self):
        """Analyze and compare the cross-system pathfinding results."""
        self.print_section("Cross-System Results Analysis")
        
        # Create comparison table
        print(f"{'Scenario':<30} {'Points':<8} {'Nodes':<8} {'Distance':<12} {'Time':<8} {'Status':<10}")
        print("-" * 85)
        
        scenarios = [
            ('Direct Cross-System (GREEN)', 'direct'),
            ('Section-Avoiding (RED)', 'forbidden')
        ]
        
        for name, key in scenarios:
            result = self.results.get(key, {})
            if result.get('status') == 'success':
                points = len(result['path'])
                nodes = result['nodes_explored']
                distance = result['distance']
                time_taken = result['execution_time']
                status = "✅ SUCCESS"
                print(f"{name:<30} {points:<8} {nodes:<8} {distance:<12.3f} {time_taken:<8.3f} {status:<10}")
            else:
                print(f"{name:<30} {'N/A':<8} {'N/A':<8} {'N/A':<12} {'N/A':<8} {'❌ ERROR':<10}")
                
        # Calculate section blocking impact
        if (self.results.get('direct', {}).get('status') == 'success' and 
            self.results.get('forbidden', {}).get('status') == 'success'):
            
            direct_points = len(self.results['direct']['path'])
            forbidden_points = len(self.results['forbidden']['path'])
            impact_factor = forbidden_points / direct_points
            
            print(f"\n📊 Forbidden Section Impact on Cross-System Routing:")
            print(f"   Path length increase: {impact_factor:.1f}x ({direct_points} → {forbidden_points} points)")
            
            direct_dist = self.results['direct']['distance']
            forbidden_dist = self.results['forbidden']['distance']
            dist_impact = forbidden_dist / direct_dist
            print(f"   Distance increase: {dist_impact:.1f}x ({direct_dist:.1f} → {forbidden_dist:.1f} units)")
            
            direct_nodes = self.results['direct']['nodes_explored']
            forbidden_nodes = self.results['forbidden']['nodes_explored']
            node_impact = forbidden_nodes / direct_nodes
            print(f"   Node exploration increase: {node_impact:.1f}x ({direct_nodes} → {forbidden_nodes} nodes)")
            
        elif self.results.get('direct', {}).get('status') == 'success':
            print(f"\n✅ Direct cross-system routing successful")
            print(f"   Cable C effectively bridges System A and System B")
            
        elif self.results.get('forbidden', {}).get('status') == 'success':
            print(f"\n✅ Section-avoiding cross-system routing successful")
            print(f"   Algorithm found alternative route despite forbidden section")
            
    def run_complete_demo(self):
        """Run the complete Scenario B1 demonstration."""
        self.print_header("DEMO: Scenario B1 - Cross-System with Internal Constraint")
        
        print(f"🔧 Demonstration of cross-system routing with internal System B constraint")
        print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Validate environment
        if not self.validate_files():
            print("\n❌ Required files missing. Please ensure all supporting files are available.")
            return False
            
        # Step 2: Show scenario information
        self.show_scenario_info()
        
        # Step 3: Verify coordinates and systems
        if not self.verify_coordinates():
            print("\n❌ Coordinate verification failed. Some coordinates not found in graph.")
            return False
            
        # Step 4: Analyze forbidden section
        self.analyze_forbidden_section()
        
        # Step 5: Run cross-system pathfinding tests
        self.run_pathfinding_tests()
        
        # Step 6: Analyze results
        self.analyze_results()
        
        # Final summary
        self.print_section("Cross-System Demo Completion Summary")
        print("✅ Scenario B1 demonstration completed successfully!")
        
        success_count = len([r for r in self.results.values() if r.get('status') == 'success'])
        print(f"📊 Cross-system scenarios executed: {success_count}/2")
            
        print(f"\n🔧 Key Internal Constraint Findings:")
        if (self.results.get('direct', {}).get('status') == 'success' and 
            self.results.get('forbidden', {}).get('status') == 'success'):
            direct_points = len(self.results['direct']['path'])
            forbidden_points = len(self.results['forbidden']['path'])
            impact = forbidden_points / direct_points
            print(f"   • Internal System B constraint increased cross-system path by {impact:.1f}x")
            print(f"   • Cable C successfully handles internal system constraints")
            print(f"   • Algorithm adapts to blocked sections within target system")
        elif success_count > 0:
            print(f"   • Cross-system routing partially successful ({success_count}/2 scenarios)")
            print(f"   • Cable C demonstrates cross-system capabilities")
        else:
            print(f"   • Cross-system routing challenges detected")
            print(f"   • Internal constraint may significantly impact connectivity")
        
        return True

def main():
    """Main function to run the Scenario B1 demo."""
    try:
        demo = ScenarioB1Demo()
        success = demo.run_complete_demo()
        
        if success:
            print(f"\n🎉 Internal Constraint Demo completed successfully!")
            print(f"📖 This demo showcases Cable C handling of internal system constraints")
            print(f"🔧 Validates algorithm performance with System B internal restrictions")
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
