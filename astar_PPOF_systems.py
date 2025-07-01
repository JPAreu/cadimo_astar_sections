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

# ========================================================================
# INTEGRATED DIAGNOSTIC UTILITIES (from diagnose_endpoints.py)
# ========================================================================

def check_endpoints_across_graphs(src_coord: Tuple[float, float, float], dst_coord: Tuple[float, float, float], 
                                 graph_files: List[str]) -> Dict[str, Any]:
    """
    Check which systems the endpoints belong to across multiple graph files.
    
    Args:
        src_coord: Source coordinates
        dst_coord: Destination coordinates
        graph_files: List of graph file paths to check
        
    Returns:
        Dictionary with endpoint system information
    """
    src_key = coord_to_key(src_coord)
    dst_key = coord_to_key(dst_coord)
    
    endpoint_info = {
        "source": {"coord": src_coord, "key": src_key, "found_in": []},
        "destination": {"coord": dst_coord, "key": dst_key, "found_in": []},
        "compatible_cables": []
    }
    
    # Check each graph file
    for graph_file in graph_files:
        try:
            graph_data = load_tagged_graph(graph_file)
            
            # Check source
            if src_key in graph_data["nodes"]:
                src_sys = graph_data["nodes"][src_key].get("sys")
                endpoint_info["source"]["found_in"].append({"file": graph_file, "system": src_sys})
            
            # Check destination
            if dst_key in graph_data["nodes"]:
                dst_sys = graph_data["nodes"][dst_key].get("sys")
                endpoint_info["destination"]["found_in"].append({"file": graph_file, "system": dst_sys})
                
        except (FileNotFoundError, ValueError):
            continue  # Skip invalid/missing files
    
    # Determine compatible cables
    src_systems = {info["system"] for info in endpoint_info["source"]["found_in"]}
    dst_systems = {info["system"] for info in endpoint_info["destination"]["found_in"]}
    all_systems = src_systems.union(dst_systems)
    
    for cable, allowed_sys in ALLOWED.items():
        if all_systems.issubset(allowed_sys):
            endpoint_info["compatible_cables"].append(cable)
    
    return endpoint_info

def diagnose_endpoints(src_coord: Tuple[float, float, float], dst_coord: Tuple[float, float, float], graph_files: List[str]) -> Dict[str, Any]:
    """Comprehensive endpoint diagnosis with recommendations."""
    
    print("🔍 Cross-System Endpoint Analysis")
    print("=" * 50)
    print(f"Source: {format_point(src_coord)}")
    print(f"Destination: {format_point(dst_coord)}")
    print(f"Graphs to check: {graph_files}")
    print()
    
    # Get endpoint information
    endpoint_info = check_endpoints_across_graphs(src_coord, dst_coord, graph_files)
    
    # Analyze source
    print("📍 Source Analysis:")
    if endpoint_info["source"]["found_in"]:
        for info in endpoint_info["source"]["found_in"]:
            print(f"   ✅ Found in {info['file']} (System {info['system']})")
    else:
        print("   ❌ Not found in any provided graphs")
    print()
    
    # Analyze destination  
    print("📍 Destination Analysis:")
    if endpoint_info["destination"]["found_in"]:
        for info in endpoint_info["destination"]["found_in"]:
            print(f"   ✅ Found in {info['file']} (System {info['system']})")
    else:
        print("   ❌ Not found in any provided graphs")
    print()
    
    # Cable compatibility analysis
    print("🔌 Cable Compatibility Analysis:")
    if endpoint_info["compatible_cables"]:
        print(f"   ✅ Compatible cable types: {endpoint_info['compatible_cables']}")
        for cable in endpoint_info["compatible_cables"]:
            systems = sorted(ALLOWED[cable])
            print(f"      Cable {cable}: Can access systems {systems}")
    else:
        print("   ❌ No cable type can connect these endpoints")
        
        # Show why each cable fails
        src_systems = {info["system"] for info in endpoint_info["source"]["found_in"]}
        dst_systems = {info["system"] for info in endpoint_info["destination"]["found_in"]}
        all_systems = src_systems.union(dst_systems)
        
        print("   🔍 Analysis per cable type:")
        for cable, allowed_systems in ALLOWED.items():
            missing_systems = all_systems - allowed_systems
            if missing_systems:
                print(f"      Cable {cable}: ❌ Cannot access system(s) {sorted(missing_systems)}")
            else:
                print(f"      Cable {cable}: ✅ Can access all required systems")
    print()
    
    # Routing recommendations
    print("💡 Routing Recommendations:")
    
    src_found = len(endpoint_info["source"]["found_in"]) > 0
    dst_found = len(endpoint_info["destination"]["found_in"]) > 0
    
    if not src_found and not dst_found:
        print("   ❌ Neither endpoint found in provided graphs")
        print("   🔧 Check coordinate precision and graph file paths")
        
    elif not src_found:
        print("   ❌ Source not found in provided graphs")
        print("   🔧 Verify source coordinates and check additional graph files")
        
    elif not dst_found:
        print("   ❌ Destination not found in provided graphs") 
        print("   🔧 Verify destination coordinates and check additional graph files")
        
    elif endpoint_info["compatible_cables"]:
        # Both found and compatible cables exist
        src_files = [info["file"] for info in endpoint_info["source"]["found_in"]]
        dst_files = [info["file"] for info in endpoint_info["destination"]["found_in"]]
        
        # Check if both points are in the same graph
        common_files = set(src_files).intersection(set(dst_files))
        
        if common_files:
            print(f"   ✅ Both endpoints found in: {list(common_files)}")
            print(f"   🚀 Use cable type(s) {endpoint_info['compatible_cables']} with any of these graphs")
            
            # Provide specific command suggestions
            if len(common_files) == 1:
                graph_file = list(common_files)[0]
                for cable in endpoint_info['compatible_cables']:
                    print(f"   💡 Try: python3 astar_PPOF_systems.py direct {graph_file} {coord_to_key(src_coord).replace('(', '').replace(')', '').replace(',', '')} {coord_to_key(dst_coord).replace('(', '').replace(')', '').replace(',', '')} --cable {cable}")
        else:
            print("   ⚠️  Endpoints in different graphs - cross-system routing required")
            print(f"   🔧 Need combined graph or multi-graph routing capability")
            print(f"   💡 Would work with cable type(s) {endpoint_info['compatible_cables']} if graphs were combined")
    else:
        print("   ❌ No cable type can connect these systems")
        print("   🔧 Consider using intermediate waypoints or different endpoints")
    
    print("=" * 50)
    return endpoint_info

def enhanced_error_handling(func):
    """Decorator to add enhanced error handling with diagnostic suggestions."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (KeyError, ValueError) as e:
            error_msg = str(e)
            print(f"\n❌ Error: {error_msg}")
            
            # Check if it's a coordinate/endpoint error
            if "not found in graph" in error_msg or "forbidden system" in error_msg:
                print("\n🔍 Running automatic diagnosis...")
                
                # Extract coordinates from function arguments
                if len(args) >= 3:
                    if hasattr(args[1], '__iter__') and len(args[1]) == 3:  # origin
                        if hasattr(args[2], '__iter__') and len(args[2]) == 3:  # destination
                            origin = args[1]
                            destination = args[2]
                            graph_file = args[0]
                            
                            # Try to find alternative graphs
                            import glob
                            graph_files = glob.glob("graph_*.json") + glob.glob("*graph*.json")
                            if graph_file not in graph_files:
                                graph_files.append(graph_file)
                            
                            print(f"🔍 Checking endpoints across available graphs...")
                            diagnose_endpoints(origin, destination, graph_files[:5])  # Limit to 5 graphs
            
            raise e
    return wrapper

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
        if hasattr(temp_graph, 'find_path_with_edge_split_forbidden'):
            # Use forbidden-aware pathfinding if available
            path, nodes_explored = temp_graph.find_path_with_edge_split_forbidden(origin, destination)
        else:
            # Fallback to regular pathfinding
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
        if hasattr(temp_graph, 'find_path_with_edge_split_forbidden'):
            path1, nodes1 = temp_graph.find_path_with_edge_split_forbidden(origin, ppo)
        else:
            path1, nodes1 = temp_graph.find_path_with_edge_split(origin, ppo)
        if not path1:
            raise Exception(f"No route found from origin to PPO inside permitted system(s) {self.allowed_systems}")
        
        # Segment 2: PPO → destination
        if hasattr(temp_graph, 'find_path_with_edge_split_forbidden'):
            path2, nodes2 = temp_graph.find_path_with_edge_split_forbidden(ppo, destination)
        else:
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
            
            if hasattr(temp_graph, 'find_path_with_edge_split_forbidden'):
                segment_path, segment_nodes = temp_graph.find_path_with_edge_split_forbidden(start_point, end_point)
            else:
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
        # If forbidden sections are specified, use the full ForbiddenEdgeGraph
        if self.tramo_id_map_path and self.forbidden_sections_path:
            # Convert our tagged graph to adjacency list format for ForbiddenEdgeGraph
            # Only include nodes/edges from allowed systems
            temp_adjacency = {}
            
            for node_key, node_data in self.graph_data["nodes"].items():
                if node_data.get("sys") in self.allowed_systems:
                    temp_adjacency[node_key] = []
            
            for edge in self.graph_data["edges"]:
                if edge.get("sys") in self.allowed_systems:
                    from_node = edge["from"]
                    to_node = edge["to"]
                    
                    # Add bidirectional edges
                    if from_node in temp_adjacency and to_node in temp_adjacency:
                        if to_node not in temp_adjacency[from_node]:
                            temp_adjacency[from_node].append(to_node)
                        if from_node not in temp_adjacency[to_node]:
                            temp_adjacency[to_node].append(from_node)
            
            # Convert to the legacy format that ForbiddenEdgeGraph expects:
            # String keys with list values (not string values)
            temp_adjacency_legacy = {}
            for node_key, neighbors in temp_adjacency.items():
                neighbor_lists = []
                for neighbor_key in neighbors:
                    neighbor_coord = key_to_coord(neighbor_key)
                    neighbor_lists.append(list(neighbor_coord))  # Convert tuple to list
                temp_adjacency_legacy[node_key] = neighbor_lists
            
            # Write temporary graph file in legacy adjacency list format
            import tempfile
            import json
            temp_graph_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            json.dump(temp_adjacency_legacy, temp_graph_file, indent=2)
            temp_graph_file.close()
            
            # Create ForbiddenEdgeGraph with system filtering + forbidden sections
            forbidden_graph = ForbiddenEdgeGraph(temp_graph_file.name, self.tramo_id_map_path, self.forbidden_sections_path)
            forbidden_graph._temp_file = temp_graph_file.name  # Store for cleanup
            return forbidden_graph
        else:
            # Use simple filtered graph without forbidden sections
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

@enhanced_error_handling
def run_direct_systems(graph_file: str, origin: Tuple[float, float, float], destination: Tuple[float, float, float], cable_type: str, tramo_map_path: str = None, forbidden_sections_path: str = None):
    """Run direct pathfinding with system filtering."""
    print(f"🚀 Running direct pathfinding with cable type {cable_type}")
    print(f"   Origin: {format_point(origin)}")
    print(f"   Destination: {format_point(destination)}")
    
    if forbidden_sections_path and tramo_map_path:
        print(f"🚫 Using forbidden sections: {forbidden_sections_path}")
        print(f"🗺️  Using tramo map: {tramo_map_path}")
    
    graph = SystemFilteredGraph(graph_file, cable_type, tramo_map_path, forbidden_sections_path)
    path, nodes_explored = graph.find_path_direct(origin, destination)
    
    print(f"\n✅ Direct path found!")
    print(f"   Path length: {len(path)} points")
    print(f"   Nodes explored: {nodes_explored}")
    print(f"   Total distance: {calculate_path_distance(path):.3f} units")
    print(f"   Cable type: {cable_type} (Systems: {', '.join(sorted(graph.allowed_systems))})")
    
    return path, nodes_explored

@enhanced_error_handling
def run_ppo_systems(graph_file: str, origin: Tuple[float, float, float], ppo: Tuple[float, float, float], 
                   destination: Tuple[float, float, float], cable_type: str, tramo_map_path: str = None, forbidden_sections_path: str = None):
    """Run PPO pathfinding with system filtering."""
    print(f"🚀 Running PPO pathfinding with cable type {cable_type}")
    print(f"   Origin: {format_point(origin)}")
    print(f"   PPO: {format_point(ppo)}")
    print(f"   Destination: {format_point(destination)}")
    
    if forbidden_sections_path and tramo_map_path:
        print(f"🚫 Using forbidden sections: {forbidden_sections_path}")
        print(f"🗺️  Using tramo map: {tramo_map_path}")
    
    graph = SystemFilteredGraph(graph_file, cable_type, tramo_map_path, forbidden_sections_path)
    path, nodes_explored = graph.find_path_with_ppo(origin, ppo, destination)
    
    print(f"\n✅ PPO path found!")
    print(f"   Path length: {len(path)} points")
    print(f"   Nodes explored: {nodes_explored}")
    print(f"   Total distance: {calculate_path_distance(path):.3f} units")
    print(f"   Cable type: {cable_type} (Systems: {', '.join(sorted(graph.allowed_systems))})")
    
    return path, nodes_explored

@enhanced_error_handling
def run_multi_ppo_systems(graph_file: str, origin: Tuple[float, float, float], ppos: List[Tuple[float, float, float]], 
                         destination: Tuple[float, float, float], cable_type: str, tramo_map_path: str = None, forbidden_sections_path: str = None):
    """Run multiple PPO pathfinding with system filtering."""
    print(f"🚀 Running multi-PPO pathfinding with cable type {cable_type}")
    print(f"   Origin: {format_point(origin)}")
    for i, ppo in enumerate(ppos):
        print(f"   PPO_{i+1}: {format_point(ppo)}")
    print(f"   Destination: {format_point(destination)}")
    
    if forbidden_sections_path and tramo_map_path:
        print(f"🚫 Using forbidden sections: {forbidden_sections_path}")
        print(f"🗺️  Using tramo map: {tramo_map_path}")
    
    graph = SystemFilteredGraph(graph_file, cable_type, tramo_map_path, forbidden_sections_path)
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

def run_diagnose_systems(src_coord: Tuple[float, float, float], dst_coord: Tuple[float, float, float], graph_files: List[str]):
    """Run endpoint diagnosis across multiple graph files."""
    print(f"🔍 Running endpoint diagnosis")
    
    if not graph_files:
        # Auto-discover graph files if none provided
        import glob
        graph_files = glob.glob("graph_*.json") + glob.glob("*graph*.json")
        if not graph_files:
            print("❌ No graph files found. Please specify graph files or ensure graph files are in current directory.")
            return
        print(f"📂 Auto-discovered {len(graph_files)} graph files: {graph_files}")
    
    endpoint_info = diagnose_endpoints(src_coord, dst_coord, graph_files)
    return endpoint_info

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
        
    diagnose <origin_x> <origin_y> <origin_z> <dest_x> <dest_y> <dest_z> [graph1] [graph2] ...
        Analyze endpoints across multiple graphs and suggest compatible cables
        (If no graphs specified, auto-discovers available graph files)

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
    
    # Diagnose endpoints across multiple graphs
    python3 astar_PPOF_systems.py diagnose 174.860 15.369 136.587 139.232 28.845 139.993 graph_LV1A.json graph_LV1B.json
    
    # Auto-diagnose with available graphs
    python3 astar_PPOF_systems.py diagnose 174.860 15.369 136.587 139.232 28.845 139.993
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
    
    # Check for diagnose command first (special handling)
    if command == 'diagnose':
        if len(sys.argv) < 8:  # script + command + 6 coordinates minimum
            print("❌ Error: diagnose command requires at least 6 coordinates (origin + destination)")
            print("Usage: python3 astar_PPOF_systems.py diagnose <src_x> <src_y> <src_z> <dst_x> <dst_y> <dst_z> [graph1] [graph2] ...")
            sys.exit(1)
        
        # Parse coordinates
        src_coord = (float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]))
        dst_coord = (float(sys.argv[5]), float(sys.argv[6]), float(sys.argv[7]))
        graph_files = sys.argv[8:] if len(sys.argv) > 8 else []
        
        # Run diagnosis
        run_diagnose_systems(src_coord, dst_coord, graph_files)
        sys.exit(0)
    
    # Parse arguments for other commands
    parser = argparse.ArgumentParser(description="A* Pathfinding with Cable Type and System Filtering")
    parser.add_argument('command', choices=['direct', 'ppo', 'multi_ppo', 'forward_path'], 
                       help='Pathfinding command')
    parser.add_argument('graph_file', help='Tagged graph JSON file')
    parser.add_argument('coordinates', nargs='+', type=float, help='Coordinates (x y z format)')
    parser.add_argument('--cable', choices=['A', 'B', 'C'], required=True,
                       help='Cable type that dictates which system(s) may be used')
    parser.add_argument('--ppo', action='append', nargs=3, type=float, metavar=('X', 'Y', 'Z'),
                       help='Add PPO coordinates for multi_ppo command')
    parser.add_argument('--tramo-map', type=str, help='Tramo ID mapping JSON file (required for forbidden sections)')
    parser.add_argument('--forbidden', type=str, help='Forbidden sections JSON file')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'direct':
            if len(args.coordinates) != 6:
                print("❌ Error: direct command requires 6 coordinates (origin_x origin_y origin_z dest_x dest_y dest_z)")
                sys.exit(1)
            
            origin = tuple(args.coordinates[:3])
            destination = tuple(args.coordinates[3:6])
            
            run_direct_systems(args.graph_file, origin, destination, args.cable, args.tramo_map, args.forbidden)
            
        elif args.command == 'ppo':
            if len(args.coordinates) != 9:
                print("❌ Error: ppo command requires 9 coordinates (origin_x origin_y origin_z ppo_x ppo_y ppo_z dest_x dest_y dest_z)")
                sys.exit(1)
            
            origin = tuple(args.coordinates[:3])
            ppo = tuple(args.coordinates[3:6])
            destination = tuple(args.coordinates[6:9])
            
            run_ppo_systems(args.graph_file, origin, ppo, destination, args.cable, args.tramo_map, args.forbidden)
            
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
            
            run_multi_ppo_systems(args.graph_file, origin, ppos, destination, args.cable, args.tramo_map, args.forbidden)
            
        elif args.command == 'forward_path':
            if len(args.coordinates) != 9:
                print("❌ Error: forward_path command requires 9 coordinates (origin_x origin_y origin_z ppo_x ppo_y ppo_z dest_x dest_y dest_z)")
                sys.exit(1)
            
            origin = tuple(args.coordinates[:3])
            ppo = tuple(args.coordinates[3:6])
            destination = tuple(args.coordinates[6:9])
            
            # For now, use regular PPO pathfinding
            run_ppo_systems(args.graph_file, origin, ppo, destination, args.cable, args.tramo_map, args.forbidden)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 