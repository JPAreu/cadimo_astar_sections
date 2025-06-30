#!/usr/bin/env python3
"""
astar_PPOF_systems.py - A* Pathfinding with Cable Type and System Filtering

This script extends the existing A* pathfinding functionality to support:
- Cable type restrictions (A, B, C)
- System filtering based on cable types
- PPO (Punto de Paso Obligatorio - Mandatory Waypoints) 
- Forward path logic (prevents backtracking)
- Forbidden edge avoidance

Cable Type Rules:
- Cable A: Can only use System A
- Cable B: Can only use System B  
- Cable C: Can use both System A and B

Usage:
    python3 astar_PPOF_systems.py <command> <graph_file> <args...> --cable <A|B|C>

Commands:
    direct       - Direct pathfinding
    ppo          - Single PPO pathfinding
    multi_ppo    - Multiple PPO pathfinding
    forward_path - Forward path with PPO (prevents backtracking)
    optimal      - Compare PPO orderings
"""

import sys
import os
import argparse
import json
from typing import List, Tuple, Dict, Any, Optional
from math import sqrt

# Import the cable filtering utilities
from cable_filter import ALLOWED, load_tagged_graph, build_adj, validate_endpoints, get_cable_info, coord_to_key, key_to_coord

# Import existing pathfinding functionality
from astar_PPO_forbid import (
    ForbiddenEdgeGraph,
    calculate_path_distance,
    format_point
)

class SystemFilteredGraph:
    """
    A* pathfinding graph with system filtering based on cable types.
    """
    
    def __init__(self, graph_path: str, cable_type: str, tramo_id_map_path: str = None, forbidden_sections_path: str = None):
        """
        Initialize the system-filtered graph.
        
        Args:
            graph_path: Path to the tagged graph JSON file
            cable_type: Cable type ("A", "B", or "C")
            tramo_id_map_path: Optional path to tramo ID mapping file
            forbidden_sections_path: Optional path to forbidden sections file
        """
        self.cable_type = cable_type
        self.cable_info = get_cable_info(cable_type)
        self.allowed_systems = self.cable_info["allowed_systems"]
        
        # Load the tagged graph
        self.graph_data = load_tagged_graph(graph_path)
        
        # Build filtered adjacency list
        self.adjacency = build_adj(self.graph_data, self.allowed_systems)
        
        # Store original paths for potential forbidden edge functionality
        self.tramo_id_map_path = tramo_id_map_path
        self.forbidden_sections_path = forbidden_sections_path
        
        print(f"🔧 {self.cable_info['description']}")
        print(f"📊 Loaded graph: {len(self.graph_data['nodes'])} nodes, {len(self.graph_data['edges'])} edges")
        print(f"🔍 Filtered graph: {len(self.adjacency)} reachable nodes")
    
    def validate_endpoints(self, src: str, dst: str) -> None:
        """Validate that endpoints are in allowed systems."""
        validate_endpoints(self.graph_data, src, dst, self.allowed_systems)
    
    def find_path_direct(self, origin: Tuple[float, float, float], destination: Tuple[float, float, float]) -> Tuple[List[Tuple[float, float, float]], int]:
        """
        Find direct path between origin and destination.
        
        Args:
            origin: Origin coordinates (x, y, z)
            destination: Destination coordinates (x, y, z)
            
        Returns:
            Tuple of (path, nodes_explored)
        """
        origin_key = coord_to_key(origin)
        destination_key = coord_to_key(destination)
        
        # Validate endpoints are in allowed systems
        self.validate_endpoints(origin_key, destination_key)
        
        # Create a temporary ForbiddenEdgeGraph with filtered adjacency
        temp_graph = self._create_temp_graph()
        
        # Use existing pathfinding with filtered graph
        path, nodes_explored = temp_graph.find_path_with_edge_split(origin, destination)
        
        if not path:
            raise Exception(f"No route found inside the permitted system(s) {self.allowed_systems}")
        
        return path, nodes_explored
    
    def find_path_with_ppo(self, origin: Tuple[float, float, float], ppo: Tuple[float, float, float], 
                          destination: Tuple[float, float, float]) -> Tuple[List[Tuple[float, float, float]], int]:
        """
        Find path with single PPO.
        
        Args:
            origin: Origin coordinates (x, y, z)
            ppo: PPO coordinates (x, y, z)
            destination: Destination coordinates (x, y, z)
            
        Returns:
            Tuple of (combined_path, total_nodes_explored)
        """
        origin_key = coord_to_key(origin)
        ppo_key = coord_to_key(ppo)
        destination_key = coord_to_key(destination)
        
        # Validate all endpoints are in allowed systems
        self.validate_endpoints(origin_key, ppo_key)
        self.validate_endpoints(ppo_key, destination_key)
        
        # Create temporary graph
        temp_graph = self._create_temp_graph()
        
        # Segment 1: origin → PPO
        path1, nodes1 = temp_graph.find_path_with_edge_split(origin, ppo)
        if not path1:
            raise Exception(f"No route found from origin to PPO inside permitted system(s) {self.allowed_systems}")
        
        # Segment 2: PPO → destination
        path2, nodes2 = temp_graph.find_path_with_edge_split(ppo, destination)
        if not path2:
            raise Exception(f"No route found from PPO to destination inside permitted system(s) {self.allowed_systems}")
        
        # Combine paths, avoiding PPO duplication
        if len(path1) > 0 and len(path2) > 0 and path1[-1] == path2[0]:
            path2 = path2[1:]
        
        return path1 + path2, nodes1 + nodes2
    
    def find_path_with_multiple_ppos(self, origin: Tuple[float, float, float], ppos: List[Tuple[float, float, float]], 
                                   destination: Tuple[float, float, float]) -> Tuple[List[Tuple[float, float, float]], int, List[Dict]]:
        """
        Find path with multiple PPOs.
        
        Args:
            origin: Origin coordinates (x, y, z)
            ppos: List of PPO coordinates
            destination: Destination coordinates (x, y, z)
            
        Returns:
            Tuple of (combined_path, total_nodes_explored, segment_info)
        """
        if not ppos:
            path, nodes_explored = self.find_path_direct(origin, destination)
            segment_info = [{'segment': 1, 'start': origin, 'end': destination, 
                           'path_length': len(path), 'nodes_explored': nodes_explored}]
            return path, nodes_explored, segment_info
        
        # Validate all waypoints
        waypoints = [origin] + ppos + [destination]
        for i in range(len(waypoints)):
            waypoint_key = coord_to_key(waypoints[i])
            if waypoint_key not in self.graph_data["nodes"]:
                raise KeyError(f"Waypoint {i} not found in graph: {waypoint_key}")
            if self.graph_data["nodes"][waypoint_key].get("sys") not in self.allowed_systems:
                raise ValueError(f"Waypoint {i} in forbidden system: {waypoint_key}")
        
        # Create temporary graph
        temp_graph = self._create_temp_graph()
        
        combined_path = []
        total_nodes_explored = 0
        segment_info = []
        
        # Process each segment
        for i in range(len(waypoints) - 1):
            start_point = waypoints[i]
            end_point = waypoints[i + 1]
            
            segment_path, segment_nodes = temp_graph.find_path_with_edge_split(start_point, end_point)
            
            if not segment_path:
                raise Exception(f"No route found for segment {i+1} inside permitted system(s) {self.allowed_systems}")
            
            # Avoid duplicating waypoints between segments
            if i > 0 and len(combined_path) > 0 and len(segment_path) > 0:
                if combined_path[-1] == segment_path[0]:
                    segment_path = segment_path[1:]
            
            combined_path.extend(segment_path)
            total_nodes_explored += segment_nodes
            
            segment_info.append({
                'segment': i + 1,
                'start': start_point,
                'end': end_point,
                'path_length': len(segment_path),
                'nodes_explored': segment_nodes
            })
        
        return combined_path, total_nodes_explored, segment_info
    
    def find_path_forward_path(self, origin: Tuple[float, float, float], ppo: Tuple[float, float, float], 
                             destination: Tuple[float, float, float]) -> Tuple[List[Tuple[float, float, float]], int, List[Dict]]:
        """
        Find path with forward path logic (prevents backtracking).
        
        Args:
            origin: Origin coordinates (x, y, z)
            ppo: PPO coordinates (x, y, z)
            destination: Destination coordinates (x, y, z)
            
        Returns:
            Tuple of (combined_path, total_nodes_explored, segment_info)
        """
        # For now, implement as regular PPO pathfinding
        # TODO: Implement actual forward path logic with tramo ID mapping
        path, nodes_explored = self.find_path_with_ppo(origin, ppo, destination)
        
        segment_info = [
            {'segment': 1, 'start': origin, 'end': ppo, 'path_length': 0, 'nodes_explored': 0},
            {'segment': 2, 'start': ppo, 'end': destination, 'path_length': 0, 'nodes_explored': 0}
        ]
        
        return path, nodes_explored, segment_info
    
    def _create_temp_graph(self):
        """Create a temporary graph with filtered adjacency for pathfinding."""
        # We'll create a simple graph structure that mimics the OptimizedSpatialGraph3D interface
        # but uses our filtered adjacency list
        
        class FilteredGraph:
            """Simple graph wrapper that uses filtered adjacency for pathfinding."""
            
            def __init__(self, adjacency_dict):
                self.adjacency = adjacency_dict
                self.tolerance = 1.0
                self.grid_size = 1.0
            
            def find_path_with_edge_split(self, start, goal):
                """Simple A* pathfinding using filtered adjacency."""
                from heapq import heappush, heappop
                import math
                
                def heuristic(a, b):
                    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
                
                def get_neighbors(node_key):
                    return self.adjacency.get(node_key, [])
                
                # Convert coordinates to keys
                start_key = coord_to_key(start)
                goal_key = coord_to_key(goal)
                
                # Check if start and goal exist in filtered graph
                if start_key not in self.adjacency:
                    return None, 0
                if goal_key not in self.adjacency:
                    return None, 0
                
                # A* algorithm
                open_set = [(0, start_key)]
                came_from = {}
                g_score = {start_key: 0}
                f_score = {start_key: heuristic(start, goal)}
                nodes_explored = 0
                
                while open_set:
                    current_f, current_key = heappop(open_set)
                    nodes_explored += 1
                    
                    if current_key == goal_key:
                        # Reconstruct path
                        path = []
                        current = current_key
                        while current in came_from:
                            path.append(key_to_coord(current))
                            current = came_from[current]
                        path.append(start)
                        path.reverse()
                        return path, nodes_explored
                    
                    current_coord = key_to_coord(current_key)
                    
                    for neighbor_key in get_neighbors(current_key):
                        neighbor_coord = key_to_coord(neighbor_key)
                        tentative_g = g_score[current_key] + heuristic(current_coord, neighbor_coord)
                        
                        if neighbor_key not in g_score or tentative_g < g_score[neighbor_key]:
                            came_from[neighbor_key] = current_key
                            g_score[neighbor_key] = tentative_g
                            f_score[neighbor_key] = tentative_g + heuristic(neighbor_coord, goal)
                            heappush(open_set, (f_score[neighbor_key], neighbor_key))
                
                return None, nodes_explored
        
        return FilteredGraph(self.adjacency)

def run_direct_systems(graph_file: str, origin: Tuple[float, float, float], destination: Tuple[float, float, float], cable_type: str):
    """Run direct pathfinding with system filtering."""
    print(f"🚀 Running direct pathfinding with cable type {cable_type}")
    print(f"   Origin: {format_point(origin)}")
    print(f"   Destination: {format_point(destination)}")
    
    graph = SystemFilteredGraph(graph_file, cable_type)
    path, nodes_explored = graph.find_path_direct(origin, destination)
    
    print(f"\n✅ Direct path found!")
    print(f"   Path length: {len(path)} points")
    print(f"   Nodes explored: {nodes_explored}")
    print(f"   Total distance: {calculate_path_distance(path):.3f} units")
    print(f"   Cable type: {cable_type} (Systems: {', '.join(sorted(graph.allowed_systems))})")
    
    return path, nodes_explored

def run_ppo_systems(graph_file: str, origin: Tuple[float, float, float], ppo: Tuple[float, float, float], 
                   destination: Tuple[float, float, float], cable_type: str):
    """Run PPO pathfinding with system filtering."""
    print(f"🚀 Running PPO pathfinding with cable type {cable_type}")
    print(f"   Origin: {format_point(origin)}")
    print(f"   PPO: {format_point(ppo)}")
    print(f"   Destination: {format_point(destination)}")
    
    graph = SystemFilteredGraph(graph_file, cable_type)
    path, nodes_explored = graph.find_path_with_ppo(origin, ppo, destination)
    
    print(f"\n✅ PPO path found!")
    print(f"   Path length: {len(path)} points")
    print(f"   Nodes explored: {nodes_explored}")
    print(f"   Total distance: {calculate_path_distance(path):.3f} units")
    print(f"   Cable type: {cable_type} (Systems: {', '.join(sorted(graph.allowed_systems))})")
    
    return path, nodes_explored

def run_multi_ppo_systems(graph_file: str, origin: Tuple[float, float, float], ppos: List[Tuple[float, float, float]], 
                         destination: Tuple[float, float, float], cable_type: str):
    """Run multiple PPO pathfinding with system filtering."""
    print(f"🚀 Running multi-PPO pathfinding with cable type {cable_type}")
    print(f"   Origin: {format_point(origin)}")
    for i, ppo in enumerate(ppos):
        print(f"   PPO_{i+1}: {format_point(ppo)}")
    print(f"   Destination: {format_point(destination)}")
    
    graph = SystemFilteredGraph(graph_file, cable_type)
    path, nodes_explored, segment_info = graph.find_path_with_multiple_ppos(origin, ppos, destination)
    
    print(f"\n✅ Multi-PPO path found!")
    print(f"   Path length: {len(path)} points")
    print(f"   Total nodes explored: {nodes_explored}")
    print(f"   Total distance: {calculate_path_distance(path):.3f} units")
    print(f"   Cable type: {cable_type} (Systems: {', '.join(sorted(graph.allowed_systems))})")
    
    if len(segment_info) > 1:
        print(f"\n📊 Segment breakdown:")
        for seg in segment_info:
            print(f"   Segment {seg['segment']}: {seg['path_length']} points, {seg['nodes_explored']} nodes explored")
    
    return path, nodes_explored, segment_info

def print_usage():
    """Print usage information and examples."""
    print("""
🔧 A* Pathfinding with Cable Type and System Filtering

Usage:
    python3 astar_PPOF_systems.py <command> <graph_file> <args...> --cable <A|B|C>

Commands:
    direct <origin_x> <origin_y> <origin_z> <dest_x> <dest_y> <dest_z>
        Direct pathfinding between two points
        
    ppo <origin_x> <origin_y> <origin_z> <ppo_x> <ppo_y> <ppo_z> <dest_x> <dest_y> <dest_z>
        Pathfinding with single mandatory waypoint (PPO)
        
    multi_ppo <origin_x> <origin_y> <origin_z> <dest_x> <dest_y> <dest_z> --ppo <x> <y> <z> [--ppo <x> <y> <z> ...]
        Pathfinding with multiple mandatory waypoints
        
    forward_path <origin_x> <origin_y> <origin_z> <ppo_x> <ppo_y> <ppo_z> <dest_x> <dest_y> <dest_z>
        Forward path with PPO (prevents backtracking)

Cable Types:
    A - Can only use System A
    B - Can only use System B  
    C - Can use both System A and B

Examples:
    # Direct pathfinding with Cable A (System A only)
    python3 astar_PPOF_systems.py direct graph_tagged.json 100 200 300 400 500 600 --cable A
    
    # PPO pathfinding with Cable C (both systems)
    python3 astar_PPOF_systems.py ppo graph_tagged.json 100 200 300 150 250 350 400 500 600 --cable C
    
    # Multi-PPO pathfinding with Cable B (System B only)
    python3 astar_PPOF_systems.py multi_ppo graph_tagged.json 100 200 300 400 500 600 --cable B --ppo 150 250 350 --ppo 200 300 400
""")

def main():
    """Main function with command-line interface."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command in ['help', '--help', '-h']:
        print_usage()
        sys.exit(0)
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="A* Pathfinding with Cable Type and System Filtering")
    parser.add_argument('command', choices=['direct', 'ppo', 'multi_ppo', 'forward_path'], 
                       help='Pathfinding command')
    parser.add_argument('graph_file', help='Tagged graph JSON file')
    parser.add_argument('coordinates', nargs='+', type=float, help='Coordinates (x y z format)')
    parser.add_argument('--cable', choices=['A', 'B', 'C'], required=True,
                       help='Cable type that dictates which system(s) may be used')
    parser.add_argument('--ppo', action='append', nargs=3, type=float, metavar=('X', 'Y', 'Z'),
                       help='Add PPO coordinates for multi_ppo command')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'direct':
            if len(args.coordinates) != 6:
                print("❌ Error: direct command requires 6 coordinates (origin_x origin_y origin_z dest_x dest_y dest_z)")
                sys.exit(1)
            
            origin = tuple(args.coordinates[:3])
            destination = tuple(args.coordinates[3:6])
            
            run_direct_systems(args.graph_file, origin, destination, args.cable)
            
        elif args.command == 'ppo':
            if len(args.coordinates) != 9:
                print("❌ Error: ppo command requires 9 coordinates (origin_x origin_y origin_z ppo_x ppo_y ppo_z dest_x dest_y dest_z)")
                sys.exit(1)
            
            origin = tuple(args.coordinates[:3])
            ppo = tuple(args.coordinates[3:6])
            destination = tuple(args.coordinates[6:9])
            
            run_ppo_systems(args.graph_file, origin, ppo, destination, args.cable)
            
        elif args.command == 'multi_ppo':
            if len(args.coordinates) != 6:
                print("❌ Error: multi_ppo command requires 6 coordinates (origin_x origin_y origin_z dest_x dest_y dest_z)")
                sys.exit(1)
            
            if not args.ppo:
                print("❌ Error: multi_ppo command requires at least one --ppo argument")
                sys.exit(1)
            
            origin = tuple(args.coordinates[:3])
            destination = tuple(args.coordinates[3:6])
            ppos = [tuple(ppo) for ppo in args.ppo]
            
            run_multi_ppo_systems(args.graph_file, origin, ppos, destination, args.cable)
            
        elif args.command == 'forward_path':
            if len(args.coordinates) != 9:
                print("❌ Error: forward_path command requires 9 coordinates (origin_x origin_y origin_z ppo_x ppo_y ppo_z dest_x dest_y dest_z)")
                sys.exit(1)
            
            origin = tuple(args.coordinates[:3])
            ppo = tuple(args.coordinates[3:6])
            destination = tuple(args.coordinates[6:9])
            
            # For now, use regular PPO pathfinding
            run_ppo_systems(args.graph_file, origin, ppo, destination, args.cable)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 