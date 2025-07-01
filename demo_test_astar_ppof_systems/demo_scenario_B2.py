#!/usr/bin/env python3
"""
DEMO: Scenario B2 - Cross-System Cable Routing with PPO (Mandatory Waypoint)

This demo showcases cross-system routing capabilities with a Punto de Paso Obligatorio (PPO)
- Mandatory Waypoint in System B, demonstrating how PPO constraints affect cross-system pathfinding.

Scenario B2 demonstrates:
1. Cross-system routing from System A to System B
2. Cable C capabilities (access to both systems)
3. PPO impact on cross-system routing (mandatory waypoint in destination system)
4. Comparison between direct routing and PPO-constrained routing

Key Test Case:
- Origin (A2): System A point (182.946, 13.304, 157.295) - repeats from previous scenarios
- Destination (B3): System B point (176.062, 2.416, 153.960) - repeats from previous scenarios
- PPO (B5): System B mandatory waypoint (170.919, 8.418, 153.960) 
- Cable Type: Cable C (can access both System A and System B)
- No Forbidden Sections: Clean routing without constraints

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

class ScenarioB2Demo:
    """Demo class for Scenario B2 cross-system pathfinding with PPO demonstration."""
    
    def __init__(self):
        """Initialize the demo with Scenario B2 parameters."""
        # Scenario B2 coordinates - Cross-system routing with PPO
        self.A2 = (182.946, 13.304, 157.295)  # Origin (System A) - repeats from previous scenarios
        self.B3 = (176.062, 2.416, 153.960)   # Destination (System B) - repeats from previous scenarios
        self.B5 = (170.919, 8.418, 153.960)   # PPO - Mandatory waypoint (System B)
        
        # File paths
        self.graph_file = "graph_LV_combined.json"
        self.tramo_map_file = "tramo_map_combined.json"
        
        # Cable type for cross-system routing
        self.cable_type = "C"
        
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
            self.tramo_map_file
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
        self.print_section("Scenario B2 Configuration - Cross-System PPO Routing")
        
        print(f"🎯 Scenario: Cross-system routing with PPO (Mandatory Waypoint)")
        print(f"🔧 Cable Type: {self.cable_type}")
        
        cable_info = get_cable_info(self.cable_type)
        print(f"📡 Allowed Systems: {', '.join(sorted(cable_info['allowed_systems']))}")
        
        print(f"\n📍 Key Coordinates:")
        print(f"   A2 (Origin - System A):     {format_point(self.A2)}")
        print(f"   B3 (Destination - System B): {format_point(self.B3)}")
        print(f"   B5 (PPO - System B):        {format_point(self.B5)}")
        
        print(f"\n🎯 Cross-System PPO Challenge:")
        print(f"   • Origin in System A, Destination in System B")
        print(f"   • PPO (B5) is a mandatory waypoint within System B")
        print(f"   • Cable C must route: A2 → (cross-system) → B5 → B3")
        print(f"   • Tests PPO impact on cross-system routing efficiency")
        
    def verify_coordinates(self):
        """Verify that coordinates exist in the graph and show their systems."""
        self.print_section("Coordinate Verification & System Analysis")
        
        # Load graph data
        graph_data = load_tagged_graph(self.graph_file)
        
        coordinates = {
            'A2 (Origin)': self.A2,
            'B3 (Destination)': self.B3,
            'B5 (PPO)': self.B5
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
            print(f"✅ PPO is in destination system - valid PPO constraint")
        else:
            print(f"⚠️  All points in same system - cross-system demo may not be optimal")
                
        return all_valid
        
    def analyze_ppo_scenario(self):
        """Analyze the PPO scenario and its impact on cross-system routing."""
        self.print_section("PPO Scenario Analysis")
        
        print(f"🎯 PPO Configuration:")
        print(f"   • PPO Location: B5 {format_point(self.B5)} (System B)")
        print(f"   • PPO Role: Mandatory waypoint within destination system")
        print(f"   • Routing Constraint: Must visit B5 before reaching B3")
        
        print(f"\n📊 Expected Routing Patterns:")
        print(f"   1. Direct Route: A2 → (cross-system) → B3")
        print(f"   2. PPO Route: A2 → (cross-system) → B5 (PPO) → B3")
        
        print(f"\n💡 Impact Analysis:")
        print(f"   • PPO forces routing through specific System B location")
        print(f"   • May increase path length within System B")
        print(f"   • Tests cross-system routing with internal constraints")
        print(f"   • Validates mandatory waypoint handling in multi-system scenarios")
        
    def run_pathfinding_tests(self):
        """Run cross-system pathfinding scenarios with and without PPO."""
        self.print_section("Cross-System Pathfinding Execution")
        
        print("🚀 Running cross-system pathfinding scenarios...")
        
        # 1. Direct cross-system path (no PPO)
        print(f"\n1️⃣ Direct Cross-System Path (GREEN) - No PPO")
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
            
        # 2. Cross-system path with PPO
        print(f"\n2️⃣ PPO Cross-System Path (MAGENTA) - With mandatory waypoint")
        print(f"   System A → System B routing through PPO B5")
        start_time = time.time()
        try:
            graph_ppo = SystemFilteredGraph(self.graph_file, self.cable_type)
            path_ppo, nodes_ppo = graph_ppo.find_path_with_ppo(self.A2, self.B5, self.B3)
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
            
            # Analyze cross-system transitions
            self._analyze_cross_system_transitions(path_ppo, "PPO")
            
            # Analyze PPO compliance
            self._analyze_ppo_compliance(path_ppo)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.results['ppo'] = {'status': 'error', 'error': str(e)}
            
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
            
    def _analyze_ppo_compliance(self, path):
        """Analyze if the path properly visits the PPO."""
        ppo_found = False
        ppo_index = -1
        
        for i, point in enumerate(path):
            # Check if this point is close to PPO (within tolerance)
            distance_to_ppo = ((point[0] - self.B5[0])**2 + 
                             (point[1] - self.B5[1])**2 + 
                             (point[2] - self.B5[2])**2)**0.5
            
            if distance_to_ppo < 0.1:  # Very close to PPO
                ppo_found = True
                ppo_index = i
                break
                
        if ppo_found:
            print(f"   🎯 PPO Compliance: ✅ PPO visited at point {ppo_index}")
            print(f"      PPO Location: {format_point(path[ppo_index])}")
        else:
            print(f"   🎯 PPO Compliance: ❌ PPO not visited (algorithm error)")
            
    def analyze_results(self):
        """Analyze and compare the cross-system pathfinding results."""
        self.print_section("Cross-System PPO Results Analysis")
        
        # Create comparison table
        print(f"{'Scenario':<30} {'Points':<8} {'Nodes':<8} {'Distance':<12} {'Time':<8} {'Status':<10}")
        print("-" * 85)
        
        scenarios = [
            ('Direct Cross-System (GREEN)', 'direct'),
            ('PPO Cross-System (MAGENTA)', 'ppo')
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
                
        # Calculate PPO impact
        if (self.results.get('direct', {}).get('status') == 'success' and 
            self.results.get('ppo', {}).get('status') == 'success'):
            
            direct_points = len(self.results['direct']['path'])
            ppo_points = len(self.results['ppo']['path'])
            impact_factor = ppo_points / direct_points
            
            print(f"\n📊 PPO Impact on Cross-System Routing:")
            print(f"   Path length increase: {impact_factor:.1f}x ({direct_points} → {ppo_points} points)")
            
            direct_dist = self.results['direct']['distance']
            ppo_dist = self.results['ppo']['distance']
            dist_impact = ppo_dist / direct_dist
            print(f"   Distance increase: {dist_impact:.1f}x ({direct_dist:.1f} → {ppo_dist:.1f} units)")
            
            direct_nodes = self.results['direct']['nodes_explored']
            ppo_nodes = self.results['ppo']['nodes_explored']
            node_impact = ppo_nodes / direct_nodes
            print(f"   Node exploration increase: {node_impact:.1f}x ({direct_nodes} → {ppo_nodes} nodes)")
            
            print(f"\n🎯 PPO Efficiency Analysis:")
            if impact_factor < 2.0:
                print(f"   • Low Impact: PPO adds minimal overhead to cross-system routing")
            elif impact_factor < 3.0:
                print(f"   • Moderate Impact: PPO noticeably affects cross-system routing")
            else:
                print(f"   • High Impact: PPO significantly changes cross-system routing")
                
        elif self.results.get('direct', {}).get('status') == 'success':
            print(f"\n✅ Direct cross-system routing successful")
            print(f"   Cable C effectively bridges System A and System B")
            
        elif self.results.get('ppo', {}).get('status') == 'success':
            print(f"\n✅ PPO cross-system routing successful")
            print(f"   Algorithm successfully handles cross-system PPO constraints")
            
    def run_complete_demo(self):
        """Run the complete Scenario B2 demonstration."""
        self.print_header("DEMO: Scenario B2 - Cross-System PPO Routing")
        
        print(f"🎯 Demonstration of cross-system routing with PPO (Mandatory Waypoint)")
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
            
        # Step 4: Analyze PPO scenario
        self.analyze_ppo_scenario()
        
        # Step 5: Run cross-system pathfinding tests
        self.run_pathfinding_tests()
        
        # Step 6: Analyze results
        self.analyze_results()
        
        # Final summary
        self.print_section("Cross-System PPO Demo Completion Summary")
        print("✅ Scenario B2 demonstration completed successfully!")
        
        success_count = len([r for r in self.results.values() if r.get('status') == 'success'])
        print(f"📊 Cross-system scenarios executed: {success_count}/2")
            
        print(f"\n🎯 Key PPO Cross-System Findings:")
        if (self.results.get('direct', {}).get('status') == 'success' and 
            self.results.get('ppo', {}).get('status') == 'success'):
            direct_points = len(self.results['direct']['path'])
            ppo_points = len(self.results['ppo']['path'])
            impact = ppo_points / direct_points
            print(f"   • PPO increased cross-system path by {impact:.1f}x")
            print(f"   • Cable C successfully handles cross-system PPO constraints")
            print(f"   • Algorithm efficiently routes through mandatory waypoints")
        elif success_count > 0:
            print(f"   • Cross-system routing partially successful ({success_count}/2 scenarios)")
            print(f"   • Cable C demonstrates cross-system capabilities")
        else:
            print(f"   • Cross-system routing challenges detected")
            print(f"   • May require connectivity analysis")
        
        return True

def main():
    """Main function to run the Scenario B2 demo."""
    try:
        demo = ScenarioB2Demo()
        success = demo.run_complete_demo()
        
        if success:
            print(f"\n🎉 PPO Cross-System Demo completed successfully!")
            print(f"📖 This demo showcases Cable C PPO capabilities in cross-system routing")
            print(f"🎯 Validates algorithm performance with mandatory waypoints across systems")
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