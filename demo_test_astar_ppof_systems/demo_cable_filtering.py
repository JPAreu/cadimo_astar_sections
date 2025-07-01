#!/usr/bin/env python3
"""
Cable Filtering Demonstration

This script demonstrates how the cable filtering system works during neighbor node
evaluation in the A* pathfinding algorithm. It shows:

1. How cable types restrict which systems can be accessed
2. How edges are filtered based on system tags during graph construction
3. How neighbor evaluation only considers allowed edges
4. Step-by-step filtering process with detailed logging

Author: AI Assistant
Date: 2024-07-01
"""

import sys
import os
import json
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from cable_filter import ALLOWED, load_tagged_graph, build_adj, get_cable_info, coord_to_key, key_to_coord
    from astar_PPOF_systems import SystemFilteredGraph
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all required modules are available")
    sys.exit(1)

class CableFilteringDemo:
    """Demonstration of cable filtering during pathfinding."""
    
    def __init__(self):
        """Initialize the demo."""
        self.graph_file = "graph_LV_combined.json"
        self.test_coordinates = {
            'A1': (170.839, 12.530, 156.634),  # System A
            'A2': (182.946, 13.304, 157.295),  # System A
            'B1': (175.682, 8.418, 153.960),   # System B (gateway)
            'B3': (176.062, 2.416, 153.960),   # System B
            'B5': (170.919, 8.418, 153.960),   # System B
        }
        
    def print_header(self, title):
        """Print a formatted header."""
        print("\n" + "="*80)
        print(f"🔧 {title}")
        print("="*80)
        
    def print_section(self, title):
        """Print a formatted section header."""
        print(f"\n📋 {title}")
        print("-" * 60)
        
    def demonstrate_cable_rules(self):
        """Show the basic cable type rules."""
        self.print_section("Cable Type System Access Rules")
        
        for cable_type, allowed_systems in ALLOWED.items():
            cable_info = get_cable_info(cable_type)
            print(f"🔌 {cable_info['description']}")
            print(f"   Allowed Systems: {sorted(allowed_systems)}")
            
        print(f"\n💡 Key Insight:")
        print(f"   • Cable A: Single-system routing (System A only)")
        print(f"   • Cable B: Single-system routing (System B only)")
        print(f"   • Cable C: Cross-system routing (both A and B)")
        
    def analyze_graph_structure(self):
        """Analyze the graph structure and system distribution."""
        self.print_section("Graph Structure Analysis")
        
        # Load the tagged graph
        graph_data = load_tagged_graph(self.graph_file)
        
        print(f"📊 Graph Statistics:")
        print(f"   Total nodes: {len(graph_data['nodes'])}")
        print(f"   Total edges: {len(graph_data['edges'])}")
        
        # Analyze system distribution
        system_nodes = defaultdict(int)
        system_edges = defaultdict(int)
        
        for node_key, node_data in graph_data['nodes'].items():
            system = node_data.get('sys', 'unknown')
            system_nodes[system] += 1
            
        for edge in graph_data['edges']:
            system = edge.get('sys', 'unknown')
            system_edges[system] += 1
            
        print(f"\n🏗️  System Distribution:")
        print(f"   Nodes by system:")
        for system, count in sorted(system_nodes.items()):
            print(f"      System {system}: {count} nodes")
            
        print(f"   Edges by system:")
        for system, count in sorted(system_edges.items()):
            print(f"      System {system}: {count} edges")
            
        return graph_data
        
    def demonstrate_edge_filtering(self, graph_data):
        """Show how edges are filtered for different cable types."""
        self.print_section("Edge Filtering by Cable Type")
        
        # Test each cable type
        for cable_type in ['A', 'B', 'C']:
            cable_info = get_cable_info(cable_type)
            allowed_systems = cable_info['allowed_systems']
            
            print(f"\n🔌 {cable_info['description']}")
            print(f"   Filtering edges for systems: {sorted(allowed_systems)}")
            
            # Build filtered adjacency
            filtered_adj = build_adj(graph_data, allowed_systems)
            
            # Count filtered edges
            total_filtered_edges = sum(len(neighbors) for neighbors in filtered_adj.values()) // 2  # Divide by 2 for undirected
            
            print(f"   ✅ Filtered graph:")
            print(f"      Reachable nodes: {len(filtered_adj)}")
            print(f"      Accessible edges: {total_filtered_edges}")
            
            # Show filtering efficiency
            original_edges = len(graph_data['edges'])
            filtering_efficiency = (total_filtered_edges / original_edges) * 100
            print(f"      Filtering efficiency: {filtering_efficiency:.1f}% of original edges accessible")
            
    def demonstrate_neighbor_evaluation(self, graph_data):
        """Show detailed neighbor evaluation for a specific node."""
        self.print_section("Neighbor Evaluation During Pathfinding")
        
        # Pick a test node that has neighbors in both systems
        test_node_key = coord_to_key(self.test_coordinates['B1'])  # Gateway node
        
        print(f"🎯 Test Node: {test_node_key}")
        print(f"   Coordinate: {self.test_coordinates['B1']}")
        
        if test_node_key not in graph_data['nodes']:
            print(f"   ❌ Test node not found in graph")
            return
            
        node_system = graph_data['nodes'][test_node_key].get('sys')
        print(f"   System: {node_system}")
        
        # Find all edges from this node
        all_neighbors = []
        for edge in graph_data['edges']:
            if edge['from'] == test_node_key:
                all_neighbors.append((edge['to'], edge['sys']))
            elif edge['to'] == test_node_key:
                all_neighbors.append((edge['from'], edge['sys']))
                
        print(f"   Total neighbors: {len(all_neighbors)}")
        
        # Show neighbor distribution by system
        neighbor_systems = defaultdict(list)
        for neighbor_key, edge_system in all_neighbors:
            neighbor_systems[edge_system].append(neighbor_key)
            
        print(f"   Neighbors by system:")
        for system, neighbors in sorted(neighbor_systems.items()):
            print(f"      System {system}: {len(neighbors)} neighbors")
            
        # Now show filtering for each cable type
        print(f"\n🔍 Neighbor Filtering by Cable Type:")
        
        for cable_type in ['A', 'B', 'C']:
            cable_info = get_cable_info(cable_type)
            allowed_systems = cable_info['allowed_systems']
            
            print(f"\n   🔌 {cable_info['description']}")
            
            # Filter neighbors based on cable type
            accessible_neighbors = []
            blocked_neighbors = []
            
            for neighbor_key, edge_system in all_neighbors:
                if edge_system in allowed_systems:
                    accessible_neighbors.append((neighbor_key, edge_system))
                else:
                    blocked_neighbors.append((neighbor_key, edge_system))
                    
            print(f"      ✅ Accessible neighbors: {len(accessible_neighbors)}")
            print(f"      ❌ Blocked neighbors: {len(blocked_neighbors)}")
            
            if accessible_neighbors:
                accessible_systems = set(edge_sys for _, edge_sys in accessible_neighbors)
                print(f"      📍 Accessible systems: {sorted(accessible_systems)}")
                
            if blocked_neighbors:
                blocked_systems = set(edge_sys for _, edge_sys in blocked_neighbors)
                print(f"      🚫 Blocked systems: {sorted(blocked_systems)}")
                
    def demonstrate_pathfinding_filtering(self):
        """Show how filtering affects actual pathfinding."""
        self.print_section("Pathfinding with System Filtering")
        
        # Test cross-system routing scenario
        origin = self.test_coordinates['A2']  # System A
        destination = self.test_coordinates['B3']  # System B
        
        print(f"🎯 Cross-System Routing Test:")
        print(f"   Origin: {origin} (System A)")
        print(f"   Destination: {destination} (System B)")
        
        # Test each cable type
        for cable_type in ['A', 'B', 'C']:
            print(f"\n🔌 Testing Cable {cable_type}:")
            
            try:
                graph = SystemFilteredGraph(self.graph_file, cable_type)
                cable_info = get_cable_info(cable_type)
                
                print(f"   Cable systems: {sorted(cable_info['allowed_systems'])}")
                print(f"   Filtered nodes: {len(graph.adjacency)}")
                
                # Try pathfinding
                try:
                    path, nodes_explored = graph.find_path_direct(origin, destination)
                    print(f"   ✅ Path found: {len(path)} points, {nodes_explored} nodes explored")
                    
                    # Verify path uses only allowed systems
                    path_systems = set()
                    for coord in path:
                        coord_key = coord_to_key(coord)
                        if coord_key in graph.graph_data['nodes']:
                            system = graph.graph_data['nodes'][coord_key].get('sys')
                            path_systems.add(system)
                            
                    print(f"   🔍 Path uses systems: {sorted(path_systems)}")
                    
                    # Verify compliance
                    if path_systems.issubset(cable_info['allowed_systems']):
                        print(f"   ✅ System compliance: PASSED")
                    else:
                        forbidden_systems = path_systems - cable_info['allowed_systems']
                        print(f"   ❌ System compliance: FAILED (uses forbidden systems: {sorted(forbidden_systems)})")
                        
                except Exception as path_error:
                    print(f"   ❌ Pathfinding failed: {path_error}")
                    
            except Exception as graph_error:
                print(f"   ❌ Graph creation failed: {graph_error}")
                
    def demonstrate_filtering_step_by_step(self):
        """Show step-by-step filtering process."""
        self.print_section("Step-by-Step Filtering Process")
        
        print("🔧 Cable Filtering Algorithm Steps:")
        print()
        
        print("1️⃣ Load Tagged Graph")
        print("   • Read nodes with 'sys' tags (A or B)")
        print("   • Read edges with 'sys' tags (A or B)")
        print("   • Validate all elements have system tags")
        print()
        
        print("2️⃣ Determine Cable Capabilities")
        print("   • Cable A → Systems: {A}")
        print("   • Cable B → Systems: {B}")  
        print("   • Cable C → Systems: {A, B}")
        print()
        
        print("3️⃣ Filter Edges by System")
        print("   • For each edge in graph:")
        print("     - Check edge 'sys' tag")
        print("     - If edge.sys in allowed_systems:")
        print("       ✅ Include edge in filtered adjacency")
        print("     - Else:")
        print("       ❌ Exclude edge from filtered adjacency")
        print()
        
        print("4️⃣ Build Filtered Adjacency List")
        print("   • Only nodes with accessible edges are included")
        print("   • Bidirectional edges are added (undirected graph)")
        print("   • Duplicate edges are avoided")
        print()
        
        print("5️⃣ Pathfinding with Filtered Graph")
        print("   • A* algorithm operates on filtered adjacency")
        print("   • get_neighbors() only returns allowed neighbors")
        print("   • System compliance is enforced automatically")
        print("   • No additional system checks needed during search")
        print()
        
        print("💡 Key Benefits:")
        print("   • System filtering happens once during graph construction")
        print("   • Pathfinding algorithm remains unchanged")
        print("   • Guaranteed system compliance")
        print("   • Efficient neighbor evaluation")
        
    def run_complete_demo(self):
        """Run the complete cable filtering demonstration."""
        self.print_header("Cable Filtering System Demonstration")
        
        print("🎯 This demo shows how cable types restrict pathfinding to allowed systems")
        print("📊 Demonstrates edge filtering, neighbor evaluation, and system compliance")
        
        try:
            # Step 1: Show cable rules
            self.demonstrate_cable_rules()
            
            # Step 2: Analyze graph structure
            graph_data = self.analyze_graph_structure()
            
            # Step 3: Show edge filtering
            self.demonstrate_edge_filtering(graph_data)
            
            # Step 4: Show neighbor evaluation
            self.demonstrate_neighbor_evaluation(graph_data)
            
            # Step 5: Show pathfinding filtering
            self.demonstrate_pathfinding_filtering()
            
            # Step 6: Show step-by-step process
            self.demonstrate_filtering_step_by_step()
            
            self.print_section("Demo Completion Summary")
            print("✅ Cable filtering demonstration completed successfully!")
            print()
            print("🎯 Key Findings:")
            print("   • Cable types effectively restrict system access")
            print("   • Edge filtering happens during graph construction")
            print("   • Neighbor evaluation only considers allowed edges")
            print("   • System compliance is automatically enforced")
            print("   • Cross-system routing requires Cable C")
            
        except Exception as e:
            print(f"\n❌ Demo error: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Main function to run the cable filtering demo."""
    try:
        demo = CableFilteringDemo()
        demo.run_complete_demo()
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 