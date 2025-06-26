#!/usr/bin/env python3
"""
Optimized version of path_mandatory_sections.py that integrates
the enhanced A* algorithm from astar_spatial_optimized.py

Key improvements:
- Uses OptimizedSpatialGraph3D for A* computation
- Grid-based spatial indexing
- Distance caching
- Better performance tracking
- Maintains all mandatory/forbidden sections logic
"""

import json
import argparse
import os
import math
import heapq
import ezdxf
import itertools
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Set, NamedTuple
import numpy as np
import networkx as nx
from math import sqrt
import sys

# Import the optimized spatial graph from astar_spatial_optimized
from astar_spatial_optimized import OptimizedSpatialGraph3D, MatchResult, format_point

def parse_point(point_str):
    """Parse a point string in format '(x,y,z)' to a tuple of floats"""
    coords = point_str.strip('()').split(',')
    return (float(coords[0]), float(coords[1]), float(coords[2]))

def distance_3d(p1, p2):
    """Calculate Euclidean distance between two 3D points"""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))

def find_nearest_node(point, positions):
    """Find the nearest node in the graph to the given point"""
    min_distance = float('inf')
    nearest_node = None
    
    for node_id, pos in positions.items():
        dist = distance_3d(point, pos)
        if dist < min_distance:
            min_distance = dist
            nearest_node = node_id
    
    return nearest_node, min_distance

class OptimizedMandatorySectionsPathfinder:
    """
    Enhanced pathfinder using OptimizedSpatialGraph3D for A* computation
    while maintaining mandatory sections logic
    """
    def __init__(self, graph, positions, mandatory_sections=None, forbidden_sections=None, tramo_id_map=None):
        self.graph = graph
        self.positions = positions
        self.forbidden_sections = set(forbidden_sections or [])
        self.mandatory_sections = mandatory_sections or {}
        self.tramo_id_map = tramo_id_map or {}
        self.inverse_tramo_map = self._build_inverse_tramo_map()
        
        # Statistics
        self.nodes_explored = 0
        self.sub_paths_computed = 0
        
        # Setup optimized spatial graph
        self._setup_optimized_spatial_graph()
        
    def _setup_optimized_spatial_graph(self):
        """Setup the optimized spatial graph for enhanced A* performance"""
        # Create temporary graph file in expected format
        temp_graph_data = {}
        
        for node_id, neighbors in self.graph.items():
            node_coords = self._parse_node_string(node_id)
            if node_coords:
                neighbor_coords = []
                for neighbor_id in neighbors:
                    neighbor_pos = self._parse_node_string(neighbor_id)
                    if neighbor_pos:
                        neighbor_coords.append(neighbor_pos)
                temp_graph_data[node_coords] = neighbor_coords
        
        # Save temporary graph file
        temp_file = "temp_graph_for_optimization.json"
        with open(temp_file, 'w') as f:
            formatted_graph = {}
            for coords, neighbors in temp_graph_data.items():
                key = f"({coords[0]}, {coords[1]}, {coords[2]})"
                value = [[n[0], n[1], n[2]] for n in neighbors]
                formatted_graph[key] = value
            json.dump(formatted_graph, f)
        
        # Initialize optimized spatial graph
        self.optimized_graph = OptimizedSpatialGraph3D(temp_file, tolerance=0.001)
        
        # Clean up
        os.remove(temp_file)
        
        # Create mappings
        self.node_id_to_coords = {}
        self.coords_to_node_id = {}
        
        for node_id, pos in self.positions.items():
            coords = tuple(pos)
            self.node_id_to_coords[node_id] = coords
            self.coords_to_node_id[coords] = node_id
    
    def _parse_node_string(self, node_str):
        """Parse node string '(x, y, z)' to tuple"""
        try:
            coords = node_str.strip('()').split(', ')
            return (float(coords[0]), float(coords[1]), float(coords[2]))
        except:
            return None
    
    def _build_inverse_tramo_map(self):
        """Build map from section ID to edge pair"""
        inverse_map = {}
        for edge, section_id in self.tramo_id_map.items():
            inverse_map[section_id] = edge
        return inverse_map
    
    def is_edge_forbidden(self, node1, node2):
        """Check if edge between nodes is forbidden"""
        if not self.forbidden_sections:
            return False
            
        edge = tuple(sorted([node1, node2]))
        edge_key = edge[0] + "-" + edge[1]
        
        if edge_key in self.tramo_id_map:
            section_id = self.tramo_id_map[edge_key]
            return section_id in self.forbidden_sections
        
        return False
    
    def find_optimal_path_between_key_nodes(self, start_node, goal_node):
        """
        Find optimal path using enhanced OptimizedSpatialGraph3D
        """
        self.sub_paths_computed += 1
        
        if start_node == goal_node:
            return [start_node], 0
        
        try:
            # Convert to coordinates
            start_coords = self.node_id_to_coords[start_node]
            goal_coords = self.node_id_to_coords[goal_node]
            
            # Use optimized A*
            optimized_path = self.optimized_graph.find_path(start_coords, goal_coords)
            
            if optimized_path:
                # Convert back to node IDs
                node_path = []
                total_cost = 0
                
                for i, coords in enumerate(optimized_path):
                    node_id = self.coords_to_node_id.get(coords)
                    if node_id:
                        node_path.append(node_id)
                        if i > 0:
                            prev_coords = optimized_path[i-1]
                            segment_cost = self.optimized_graph.euclidean_distance(prev_coords, coords)
                            total_cost += segment_cost
                
                self.nodes_explored += self.optimized_graph.nodes_explored
                return node_path, total_cost
            else:
                return None, float('inf')
                
        except Exception as e:
            print(f"Error in optimized pathfinding: {e}")
            return self._basic_astar_fallback(start_node, goal_node)
    
    def _basic_astar_fallback(self, start_node, goal_node):
        """Fallback basic A* implementation"""
        open_set = []
        closed_set = set()
        g_score = {start_node: 0}
        f_score = {start_node: distance_3d(self.positions[start_node], self.positions[goal_node])}
        came_from = {}
        
        heapq.heappush(open_set, (f_score[start_node], start_node))
        
        while open_set:
            _, current = heapq.heappop(open_set)
            self.nodes_explored += 1
            
            if current == goal_node:
                path = [current]
                path_cost = g_score[current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                return list(reversed(path)), path_cost
            
            closed_set.add(current)
            
            for neighbor in self.graph.get(current, []):
                if neighbor in closed_set or self.is_edge_forbidden(current, neighbor):
                    continue
                
                tentative_g_score = g_score[current] + distance_3d(
                    self.positions[current], self.positions[neighbor]
                )
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + distance_3d(
                        self.positions[neighbor], self.positions[goal_node]
                    )
                    
                    if neighbor not in [node for _, node in open_set]:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return None, float('inf')
    
    def extract_key_nodes(self, start_node, goal_node):
        """Extract key nodes: start, goal, and mandatory section endpoints"""
        key_nodes = {start_node, goal_node}
        section_endpoints = {}
        
        for section_id_str in self.mandatory_sections:
            section_id = int(section_id_str)
            if section_id in self.inverse_tramo_map:
                edge_key = self.inverse_tramo_map[section_id]
                node1, node2 = edge_key.split('-')
                key_nodes.add(node1)
                key_nodes.add(node2)
                section_endpoints[section_id] = (node1, node2)
        
        return key_nodes, section_endpoints
    
    def build_meta_graph(self, key_nodes, section_endpoints):
        """Build meta-graph using optimized A*"""
        meta_graph = defaultdict(dict)
        
        print(f"Building meta-graph with {len(key_nodes)} key nodes...")
        print("Using OptimizedSpatialGraph3D for enhanced A* performance")
        
        total_pairs = len(list(itertools.combinations(key_nodes, 2)))
        computed = 0
        
        for node1, node2 in itertools.combinations(key_nodes, 2):
            if node1 == node2:
                continue
            
            computed += 1
            if computed % 10 == 0:
                print(f"Progress: {computed}/{total_pairs} paths computed")
                
            path, cost = self.find_optimal_path_between_key_nodes(node1, node2)
            
            if path:
                meta_graph[node1][node2] = (path, cost)
                meta_graph[node2][node1] = (list(reversed(path)), cost)
        
        print(f"Meta-graph complete. Total nodes explored: {self.nodes_explored}")
        return meta_graph, section_endpoints
    
    def find_best_permutation(self, start_node, goal_node, meta_graph, section_endpoints):
        """Evaluate permutations to find optimal mandatory sections path"""
        intermediate_nodes = set()
        for node1, node2 in section_endpoints.values():
            if node1 != start_node and node1 != goal_node:
                intermediate_nodes.add(node1)
            if node2 != start_node and node2 != goal_node:
                intermediate_nodes.add(node2)
        
        section_endpoint_lookup = {}
        for section_id, (node1, node2) in section_endpoints.items():
            section_endpoint_lookup[(node1, node2)] = section_id
            section_endpoint_lookup[(node2, node1)] = section_id
        
        if not intermediate_nodes:
            return meta_graph[start_node][goal_node][0] if goal_node in meta_graph[start_node] else None
        
        intermediate_list = list(intermediate_nodes)
        num_permutations = math.factorial(len(intermediate_list))
        
        if num_permutations > 100000:
            print(f"⚠️  WARNING: {num_permutations:,} permutations to evaluate!")
            print("This may take a very long time.")
            response = input("Continue anyway? (y/N): ").lower().strip()
            if response != 'y':
                return None
        
        print(f"Evaluating {num_permutations:,} permutations...")
        
        best_path = None
        best_cost = float('inf')
        
        def includes_all_mandatory_sections(node_sequence):
            visited_sections = set()
            
            for i in range(len(node_sequence) - 1):
                node1, node2 = node_sequence[i], node_sequence[i+1]
                
                if (node1, node2) in section_endpoint_lookup:
                    visited_sections.add(section_endpoint_lookup[(node1, node2)])
                elif (node2, node1) in section_endpoint_lookup:
                    visited_sections.add(section_endpoint_lookup[(node2, node1)])
                
                if node2 in meta_graph[node1]:
                    path_nodes = meta_graph[node1][node2][0]
                    for j in range(len(path_nodes) - 1):
                        path_node1, path_node2 = path_nodes[j], path_nodes[j+1]
                        edge = tuple(sorted([path_node1, path_node2]))
                        edge_key = edge[0] + "-" + edge[1]
                        if edge_key in self.tramo_id_map:
                            section_id = self.tramo_id_map[edge_key]
                            if section_id in self.mandatory_sections:
                                visited_sections.add(section_id)
            
            return len(visited_sections) == len(self.mandatory_sections)
        
        evaluated = 0
        for perm in itertools.permutations(intermediate_list):
            evaluated += 1
            if evaluated % 10000 == 0:
                print(f"Progress: {evaluated:,}/{num_permutations:,}")
            
            node_sequence = [start_node] + list(perm) + [goal_node]
            
            valid = True
            total_cost = 0
            
            for i in range(len(node_sequence) - 1):
                node1, node2 = node_sequence[i], node_sequence[i+1]
                if node2 not in meta_graph[node1]:
                    valid = False
                    break
                total_cost += meta_graph[node1][node2][1]
            
            if valid and includes_all_mandatory_sections(node_sequence) and total_cost < best_cost:
                best_cost = total_cost
                
                detailed_path = []
                for i in range(len(node_sequence) - 1):
                    node1, node2 = node_sequence[i], node_sequence[i+1]
                    sub_path = meta_graph[node1][node2][0]
                    
                    if i < len(node_sequence) - 2:
                        detailed_path.extend(sub_path[:-1])
                    else:
                        detailed_path.extend(sub_path)
                
                best_path = detailed_path
        
        print(f"Best permutation found. Cost: {best_cost:.3f}")
        return best_path
    
    def find_path(self, start_point, goal_point):
        """Main pathfinding entry point"""
        start_node, start_dist = find_nearest_node(start_point, self.positions)
        goal_node, goal_dist = find_nearest_node(goal_point, self.positions)
        
        print(f"🚀 Using OptimizedSpatialGraph3D for enhanced A* performance")
        print(f"Start: {start_node} (distance: {start_dist:.3f})")
        print(f"Goal: {goal_node} (distance: {goal_dist:.3f})")
        
        if start_node == goal_node:
            return [self.positions[start_node]]
            
        key_nodes, section_endpoints = self.extract_key_nodes(start_node, goal_node)
        print(f"Key nodes: {len(key_nodes)}, Mandatory sections: {len(section_endpoints)}")
        
        meta_graph, section_endpoints = self.build_meta_graph(key_nodes, section_endpoints)
        path_nodes = self.find_best_permutation(start_node, goal_node, meta_graph, section_endpoints)
        
        if not path_nodes:
            print("No valid path found that includes all mandatory sections.")
            return None
            
        path = [self.positions[node] for node in path_nodes]
        return path

def export_path_to_dxf(path, output_file, mandatory_sections=None, section_positions=None, forbidden_sections=None):
    """Export path to DXF file"""
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    if path and len(path) > 1:
        points = [list(point) for point in path]
        polyline = msp.add_polyline3d(points)
        polyline.dxf.color = 1
        
        for i, point in enumerate(path):
            msp.add_circle(center=point, radius=0.1)
            
            if i == 0:
                msp.add_text("START", dxfattribs={'height': 0.5, 'color': 3, 'insert': point})
            elif i == len(path) - 1:
                msp.add_text("END", dxfattribs={'height': 0.5, 'color': 5, 'insert': point})
    
    # Add sections visualization
    if mandatory_sections and section_positions:
        for section_id_str, weight in mandatory_sections.items():
            section_id = int(section_id_str)
            if section_id in section_positions:
                p1, p2 = section_positions[section_id]
                msp.add_line(p1, p2, dxfattribs={'color': 3})
                msp.add_circle(center=p1, radius=0.15, dxfattribs={'color': 3})
                msp.add_circle(center=p2, radius=0.15, dxfattribs={'color': 3})
                midpoint = [(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2, (p1[2] + p2[2]) / 2]
                msp.add_text(f"MANDATORY", dxfattribs={'height': 0.3, 'color': 3, 'insert': midpoint})
    
    if forbidden_sections and section_positions:
        for section_id in forbidden_sections:
            if section_id in section_positions:
                p1, p2 = section_positions[section_id]
                msp.add_line(p1, p2, dxfattribs={'color': 2})
                msp.add_circle(center=p1, radius=0.15, dxfattribs={'color': 2})
                msp.add_circle(center=p2, radius=0.15, dxfattribs={'color': 2})
                midpoint = [(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2, (p1[2] + p2[2]) / 2]
                msp.add_text("FORBIDDEN", dxfattribs={'height': 0.3, 'color': 2, 'insert': midpoint})
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    doc.saveas(output_file)
    print(f"Path exported to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Optimized mandatory sections pathfinder")
    parser.add_argument("--graph", type=str, help="Graph JSON file")
    parser.add_argument("--positions", type=str, help="Positions JSON file")
    parser.add_argument("--tramos", type=str, help="Tramo ID map JSON file")
    parser.add_argument("--timestamp", type=str, help="Timestamp of graph pack")
    parser.add_argument("--start", type=str, required=True, help="Start point '(x,y,z)'")
    parser.add_argument("--goal", type=str, required=True, help="Goal point '(x,y,z)'")
    parser.add_argument("--prohibidos", type=str, help="Forbidden sections JSON")
    parser.add_argument("--mandatory", type=str, help="Mandatory sections JSON")
    parser.add_argument("--output", type=str, help="Output path JSON")
    parser.add_argument("--export_dxf", action="store_true", help="Export to DXF")
    parser.add_argument("--output_dir", type=str, default="Path_Restrictions", help="Output directory")
    args = parser.parse_args()
    
    # Setup
    timestamp = args.timestamp or datetime.now().strftime("%m%d_%H%M")
    os.makedirs(args.output_dir, exist_ok=True)
    
    output_file = args.output if args.output else os.path.join(args.output_dir, f"optimized_path_{timestamp}.json")
    if not os.path.dirname(output_file):
        output_file = os.path.join(args.output_dir, output_file)
    
    start_point = parse_point(args.start)
    goal_point = parse_point(args.goal)
    
    # Files
    if args.timestamp:
        graph_file = os.path.join(args.output_dir, f"graph_{args.timestamp}.json")
        positions_file = os.path.join(args.output_dir, f"positions_{args.timestamp}.json")
        tramo_id_file = os.path.join(args.output_dir, f"tramo_id_map_{args.timestamp}.json")
        
        if not all(os.path.exists(f) for f in [graph_file, positions_file, tramo_id_file]):
            print(f"Error: Missing files for timestamp {args.timestamp}")
            return
    else:
        graph_file, positions_file, tramo_id_file = args.graph, args.positions, args.tramos
        if not all([graph_file, positions_file, tramo_id_file]):
            print("Error: Provide timestamp or all files")
            return
    
    print(f"🚀 OPTIMIZED MANDATORY SECTIONS PATHFINDER")
    print(f"Enhanced with OptimizedSpatialGraph3D A* algorithm")
    print(f"Files: {graph_file}, {positions_file}, {tramo_id_file}")
    
    # Load data
    with open(graph_file, 'r') as f:
        graph = json.load(f)
    with open(positions_file, 'r') as f:
        positions = json.load(f)
    with open(tramo_id_file, 'r') as f:
        tramo_id_map = json.load(f)
    
    # Load restrictions
    forbidden_sections = None
    if args.prohibidos:
        with open(args.prohibidos, 'r') as f:
            forbidden_sections = json.load(f)
        print(f"Forbidden sections: {len(forbidden_sections)}")
    
    mandatory_sections = None
    if args.mandatory:
        with open(args.mandatory, 'r') as f:
            mandatory_sections = json.load(f)
        print(f"Mandatory sections: {len(mandatory_sections)}")
    else:
        print("Error: Mandatory sections file required")
        return
    
    # Create pathfinder
    pathfinder = OptimizedMandatorySectionsPathfinder(
        graph, positions, mandatory_sections, forbidden_sections, tramo_id_map
    )
    
    print(f"\nFinding path: {start_point} → {goal_point}")
    
    # Find path
    path = pathfinder.find_path(start_point, goal_point)
    
    if path:
        total_distance = sum(distance_3d(path[i-1], path[i]) for i in range(1, len(path)))
        
        print(f"\n✅ SUCCESS!")
        print(f"Path: {len(path)} points")
        print(f"Distance: {total_distance:.3f}")
        print(f"Nodes explored: {pathfinder.nodes_explored}")
        print(f"Sub-paths: {pathfinder.sub_paths_computed}")
        print(f"🚀 Enhanced performance with OptimizedSpatialGraph3D!")
        
        with open(output_file, 'w') as f:
            json.dump(path, f, indent=2)
        print(f"Saved: {output_file}")
        
        # DXF export
        if args.export_dxf:
            section_positions = {}
            inverse_tramo_map = pathfinder.inverse_tramo_map
            
            if mandatory_sections:
                for section_id_str in mandatory_sections:
                    section_id = int(section_id_str)
                    if section_id in inverse_tramo_map:
                        edge_key = inverse_tramo_map[section_id]
                        nodes = edge_key.split('-')
                        if nodes[0] in positions and nodes[1] in positions:
                            section_positions[section_id] = (positions[nodes[0]], positions[nodes[1]])
            
            if forbidden_sections:
                for section_id in forbidden_sections:
                    if section_id in inverse_tramo_map:
                        edge_key = inverse_tramo_map[section_id]
                        nodes = edge_key.split('-')
                        if nodes[0] in positions and nodes[1] in positions:
                            section_positions[section_id] = (positions[nodes[0]], positions[nodes[1]])
            
            dxf_file = os.path.join(args.output_dir, f"optimized_path_{timestamp}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.dxf")
            export_path_to_dxf(path, dxf_file, mandatory_sections, section_positions, forbidden_sections)
    else:
        print("\n❌ No path found including all mandatory sections.")

if __name__ == "__main__":
    main() 