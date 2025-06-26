#!/usr/bin/env python3
import json
import argparse
import os
import math
import heapq
import ezdxf
import itertools
from datetime import datetime
from collections import defaultdict

def parse_point(point_str):
    """Parse a point string in format '(x,y,z)' to a tuple of floats"""
    # Remove parentheses and split by commas
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

class MandatorySectionsPathfinder:
    """A pathfinder that ensures paths go through all mandatory (preferred) sections"""
    def __init__(self, graph, positions, mandatory_sections=None, forbidden_sections=None, tramo_id_map=None):
        self.graph = graph
        self.positions = positions
        self.forbidden_sections = set(forbidden_sections or [])
        self.mandatory_sections = mandatory_sections or {}
        self.tramo_id_map = tramo_id_map or {}
        self.inverse_tramo_map = self._build_inverse_tramo_map()
        
        # Build spatial index (grid-based)
        self.grid_size = 1.0  # Grid cell size
        self.grid = {}
        self._build_spatial_index()
        
        # Statistics
        self.nodes_explored = 0
        self.sub_paths_computed = 0
    
    def _build_inverse_tramo_map(self):
        """Build a map from section ID to edge pair"""
        inverse_map = {}
        for edge, section_id in self.tramo_id_map.items():
            inverse_map[section_id] = edge
        return inverse_map
    
    def _build_spatial_index(self):
        """Build a grid-based spatial index for the graph"""
        for node_id, pos in self.positions.items():
            # Calculate the grid cell for this position
            cell_x = int(pos[0] / self.grid_size)
            cell_y = int(pos[1] / self.grid_size)
            cell_z = int(pos[2] / self.grid_size)
            cell = (cell_x, cell_y, cell_z)
            
            # Add the node to the grid cell
            if cell not in self.grid:
                self.grid[cell] = []
            self.grid[cell].append(node_id)
    
    def is_edge_forbidden(self, node1, node2):
        """Check if the edge between node1 and node2 is forbidden"""
        if not self.forbidden_sections:
            return False
            
        # Create the edge key
        edge = tuple(sorted([node1, node2]))
        edge_key = edge[0] + "-" + edge[1]
        
        # Check if the edge has a section ID and if it's forbidden
        if edge_key in self.tramo_id_map:
            section_id = self.tramo_id_map[edge_key]
            return section_id in self.forbidden_sections
        
        return False
    
    def find_optimal_path_between_key_nodes(self, start_node, goal_node):
        """
        Find the optimal path between two key nodes using A* algorithm,
        avoiding forbidden sections
        """
        self.sub_paths_computed += 1
        
        if start_node == goal_node:
            return [start_node], 0
            
        # A* algorithm
        open_set = []
        closed_set = set()
        
        # Dictionary to store g scores (cost from start to current)
        g_score = {start_node: 0}
        
        # Dictionary to store f scores (g_score + heuristic)
        f_score = {start_node: distance_3d(self.positions[start_node], self.positions[goal_node])}
        
        # Dictionary to reconstruct the path
        came_from = {}
        
        # Add start node to open set with priority f_score
        heapq.heappush(open_set, (f_score[start_node], start_node))
        
        while open_set:
            # Get the node with the lowest f_score
            _, current = heapq.heappop(open_set)
            
            # Increment nodes explored counter
            self.nodes_explored += 1
            
            if current == goal_node:
                # Reconstruct the path
                path = [current]
                path_cost = g_score[current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                return list(reversed(path)), path_cost
            
            # Add current to closed set
            closed_set.add(current)
            
            # Check all neighbors
            for neighbor in self.graph.get(current, []):
                if neighbor in closed_set:
                    continue
                
                # Skip if the edge is forbidden
                if self.is_edge_forbidden(current, neighbor):
                    continue
                
                # Calculate tentative g_score using actual distance
                tentative_g_score = g_score[current] + distance_3d(
                    self.positions[current], self.positions[neighbor]
                )
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    # This path is better than any previous one
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + distance_3d(
                        self.positions[neighbor], self.positions[goal_node]
                    )
                    
                    # Add to open set if not already there
                    if neighbor not in [node for _, node in open_set]:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        # No path found
        return None, float('inf')
    
    def extract_key_nodes(self, start_node, goal_node):
        """
        Extract all key nodes: start, goal, and endpoints of all mandatory sections
        Returns a set of node IDs and a mapping of section IDs to their endpoint nodes
        """
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
        """
        Build a meta-graph where nodes are key nodes and edges are optimal paths between them
        """
        meta_graph = defaultdict(dict)
        
        # Compute optimal paths between all pairs of key nodes
        for node1, node2 in itertools.combinations(key_nodes, 2):
            if node1 == node2:
                continue
                
            # Find the optimal path between these nodes
            path, cost = self.find_optimal_path_between_key_nodes(node1, node2)
            
            if path:
                meta_graph[node1][node2] = (path, cost)
                meta_graph[node2][node1] = (list(reversed(path)), cost)
        
        return meta_graph, section_endpoints
    
    def find_best_permutation(self, start_node, goal_node, meta_graph, section_endpoints):
        """
        Evaluate all possible permutations of visiting the mandatory sections
        to find the most efficient overall path
        """
        # Get all intermediate key nodes (all section endpoints except start/goal)
        intermediate_nodes = set()
        for node1, node2 in section_endpoints.values():
            if node1 != start_node and node1 != goal_node:
                intermediate_nodes.add(node1)
            if node2 != start_node and node2 != goal_node:
                intermediate_nodes.add(node2)
        
        # Create a lookup for section endpoints
        section_endpoint_lookup = {}
        for section_id, (node1, node2) in section_endpoints.items():
            section_endpoint_lookup[(node1, node2)] = section_id
            section_endpoint_lookup[(node2, node1)] = section_id
        
        # If no intermediate nodes, just return direct path
        if not intermediate_nodes:
            return meta_graph[start_node][goal_node][0] if goal_node in meta_graph[start_node] else None
        
        # Convert to list for permutations
        intermediate_list = list(intermediate_nodes)
        
        best_path = None
        best_cost = float('inf')
        
        # Function to check if a sequence of nodes includes all mandatory sections
        def includes_all_mandatory_sections(node_sequence):
            visited_sections = set()
            
            for i in range(len(node_sequence) - 1):
                node1, node2 = node_sequence[i], node_sequence[i+1]
                
                # Check if this edge corresponds to a mandatory section
                if (node1, node2) in section_endpoint_lookup:
                    visited_sections.add(section_endpoint_lookup[(node1, node2)])
                elif (node2, node1) in section_endpoint_lookup:
                    visited_sections.add(section_endpoint_lookup[(node2, node1)])
                
                # Also check all nodes in the path between these meta-nodes
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
            
            # Check if all mandatory sections are visited
            return len(visited_sections) == len(self.mandatory_sections)
        
        # Try all permutations of intermediate nodes
        for perm in itertools.permutations(intermediate_list):
            # Full path: start -> intermediate nodes -> goal
            node_sequence = [start_node] + list(perm) + [goal_node]
            
            # Check if this permutation is valid (has paths between all consecutive nodes)
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
                
                # Reconstruct the detailed path
                detailed_path = []
                for i in range(len(node_sequence) - 1):
                    node1, node2 = node_sequence[i], node_sequence[i+1]
                    sub_path = meta_graph[node1][node2][0]
                    
                    # Add all nodes except the last one (to avoid duplicates)
                    if i < len(node_sequence) - 2:
                        detailed_path.extend(sub_path[:-1])
                    else:
                        # For the last segment, include the goal node
                        detailed_path.extend(sub_path)
                
                best_path = detailed_path
        
        return best_path
    
    def find_path(self, start_point, goal_point):
        """
        Main entry point: find a path that includes all mandatory sections
        """
        # Find nearest nodes to start and goal points
        start_node, start_dist = find_nearest_node(start_point, self.positions)
        goal_node, goal_dist = find_nearest_node(goal_point, self.positions)
        
        print(f"Using nearest start node: {start_node} (distance: {start_dist:.3f})")
        print(f"Using nearest goal node: {goal_node} (distance: {goal_dist:.3f})")
        
        if start_node == goal_node:
            return [self.positions[start_node]]
            
        # 1. Extract key nodes
        key_nodes, section_endpoints = self.extract_key_nodes(start_node, goal_node)
        print(f"Found {len(key_nodes)} key nodes and {len(section_endpoints)} mandatory sections")
        
        # 2. Build the meta-graph
        meta_graph, section_endpoints = self.build_meta_graph(key_nodes, section_endpoints)
        print(f"Built meta-graph with {len(meta_graph)} nodes and {sum(len(neighbors) for neighbors in meta_graph.values())} edges")
        
        # 3 & 4. Evaluate permutations and find best path
        path_nodes = self.find_best_permutation(start_node, goal_node, meta_graph, section_endpoints)
        
        if not path_nodes:
            print("No valid path found that includes all mandatory sections.")
            return None
            
        # Convert node IDs to positions
        path = [self.positions[node] for node in path_nodes]
        return path

def export_path_to_dxf(path, output_file, mandatory_sections=None, section_positions=None, forbidden_sections=None):
    """
    Export the path to a DXF file, including mandatory and forbidden sections if provided
    """
    # Create a new DXF document
    doc = ezdxf.new('R2010')  # Use AutoCAD 2010 format
    
    # Add new entities to the modelspace
    msp = doc.modelspace()
    
    # Add the path as a polyline
    if path and len(path) > 1:
        # Create a 3D polyline
        points = [list(point) for point in path]  # Convert tuples to lists for ezdxf
        polyline = msp.add_polyline3d(points)
        polyline.dxf.color = 1  # Red color
        
        # Add points as small circles
        for i, point in enumerate(path):
            # Add a circle at each point
            msp.add_circle(center=point, radius=0.1)
            
            # Add text labels for start and end points
            if i == 0:
                # Add simple text at start point
                msp.add_text(
                    "START",
                    dxfattribs={
                        'height': 0.5,
                        'color': 3,  # Green
                        'insert': point
                    }
                )
            elif i == len(path) - 1:
                # Add simple text at end point
                msp.add_text(
                    "END",
                    dxfattribs={
                        'height': 0.5,
                        'color': 5,  # Blue
                        'insert': point
                    }
                )
    
    # Add mandatory sections if provided
    if mandatory_sections and section_positions:
        for section_id_str, weight in mandatory_sections.items():
            section_id = int(section_id_str)
            if section_id in section_positions:
                p1, p2 = section_positions[section_id]
                # Draw a green line for the mandatory section
                msp.add_line(p1, p2, dxfattribs={'color': 3})  # Green line
                # Add a circle at each end of the mandatory section
                msp.add_circle(center=p1, radius=0.15, dxfattribs={'color': 3})
                msp.add_circle(center=p2, radius=0.15, dxfattribs={'color': 3})
                # Add "MANDATORY" text
                midpoint = [(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2, (p1[2] + p2[2]) / 2]
                msp.add_text(
                    f"MANDATORY ({weight})",
                    dxfattribs={
                        'height': 0.3,
                        'color': 3,  # Green
                        'insert': midpoint
                    }
                )
    
    # Add forbidden sections if provided
    if forbidden_sections and section_positions:
        for section_id in forbidden_sections:
            if section_id in section_positions:
                p1, p2 = section_positions[section_id]
                # Draw a red line for the forbidden section
                msp.add_line(p1, p2, dxfattribs={'color': 2})  # Red line
                # Add a circle at each end of the forbidden section
                msp.add_circle(center=p1, radius=0.15, dxfattribs={'color': 2})
                msp.add_circle(center=p2, radius=0.15, dxfattribs={'color': 2})
                # Add "FORBIDDEN" text
                midpoint = [(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2, (p1[2] + p2[2]) / 2]
                msp.add_text(
                    "FORBIDDEN",
                    dxfattribs={
                        'height': 0.3,
                        'color': 2,  # Red
                        'insert': midpoint
                    }
                )
    
    # Ensure the directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save the document
    doc.saveas(output_file)
    print(f"Path exported to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Find path with mandatory sections")
    parser.add_argument("--graph", type=str, help="Graph JSON file (if not using timestamp)")
    parser.add_argument("--positions", type=str, help="Positions JSON file (if not using timestamp)")
    parser.add_argument("--tramos", type=str, help="Tramo ID map JSON file (if not using timestamp)")
    parser.add_argument("--timestamp", type=str, help="Timestamp of the graph pack to use")
    parser.add_argument("--start", type=str, required=True, help="Start point in format '(x,y,z)'")
    parser.add_argument("--goal", type=str, required=True, help="Goal point in format '(x,y,z)'")
    parser.add_argument("--prohibidos", type=str, help="Forbidden sections JSON file")
    parser.add_argument("--mandatory", type=str, help="Mandatory sections JSON file (same format as preferred sections)")
    parser.add_argument("--output", type=str, help="Output path JSON file")
    parser.add_argument("--export_dxf", action="store_true", help="Export path to DXF file")
    parser.add_argument("--output_dir", type=str, default="Path_Restrictions", help="Output directory")
    args = parser.parse_args()
    
    # Generate timestamp for output if not provided
    timestamp = args.timestamp or datetime.now().strftime("%m%d_%H%M")
    
    # Ensure output directory exists
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    # Determine output filename
    if args.output:
        output_file = args.output
        if not os.path.dirname(output_file):
            output_file = os.path.join(args.output_dir, output_file)
    else:
        output_file = os.path.join(args.output_dir, f"mandatory_path_result_{timestamp}.json")
    
    # Parse start and goal points
    start_point = parse_point(args.start)
    goal_point = parse_point(args.goal)
    
    # Determine the input files
    if args.timestamp:
        graph_file = os.path.join(args.output_dir, f"graph_{args.timestamp}.json")
        positions_file = os.path.join(args.output_dir, f"positions_{args.timestamp}.json")
        tramo_id_file = os.path.join(args.output_dir, f"tramo_id_map_{args.timestamp}.json")
        
        if not all([os.path.exists(f) for f in [graph_file, positions_file, tramo_id_file]]):
            print(f"Error: Could not find all files for timestamp {args.timestamp}")
            return
    else:
        graph_file = args.graph
        positions_file = args.positions
        tramo_id_file = args.tramos
        
        if not all([graph_file, positions_file, tramo_id_file]):
            print("Error: Please provide either a timestamp or all graph, positions, and tramos files")
            return
    
    print(f"Using graph: {graph_file}")
    print(f"Using positions: {positions_file}")
    print(f"Using tramo ID map: {tramo_id_file}")
    
    # Load the necessary files
    with open(graph_file, 'r') as f:
        graph = json.load(f)
    
    with open(positions_file, 'r') as f:
        positions = json.load(f)
    
    with open(tramo_id_file, 'r') as f:
        tramo_id_map = json.load(f)
    
    # Load forbidden sections if provided
    forbidden_sections = None
    if args.prohibidos:
        with open(args.prohibidos, 'r') as f:
            forbidden_sections = json.load(f)
        print(f"Using forbidden sections from: {args.prohibidos}")
    
    # Load mandatory sections if provided
    mandatory_sections = None
    if args.mandatory:
        with open(args.mandatory, 'r') as f:
            mandatory_sections = json.load(f)
        print(f"Using mandatory sections from: {args.mandatory}")
    else:
        print("Error: Mandatory sections file is required")
        return
    
    # Create the pathfinder
    pathfinder = MandatorySectionsPathfinder(
        graph, positions, mandatory_sections, forbidden_sections, tramo_id_map
    )
    
    print(f"Finding path from {start_point} to {goal_point}")
    if forbidden_sections:
        print(f"Avoiding {len(forbidden_sections)} forbidden sections")
    print(f"Including {len(mandatory_sections)} mandatory sections")
    
    # Find the path
    path = pathfinder.find_path(start_point, goal_point)
    
    if path:
        print(f"Path found with {len(path)} points")
        print(f"Nodes explored: {pathfinder.nodes_explored}")
        print(f"Sub-paths computed: {pathfinder.sub_paths_computed}")
        
        # Calculate total path distance
        total_distance = 0
        for i in range(1, len(path)):
            segment_distance = distance_3d(path[i-1], path[i])
            total_distance += segment_distance
        
        print(f"Total path distance: {total_distance:.3f}")
        
        # Save the path
        with open(output_file, 'w') as f:
            json.dump(path, f, indent=2)
        
        print(f"Path saved to {output_file}")
        
        # Export to DXF if requested
        if args.export_dxf:
            # Prepare section positions for DXF
            section_positions = {}
            
            # Collect mandatory section positions
            if mandatory_sections:
                # Map section IDs to pairs of positions
                inverse_tramo_map = pathfinder.inverse_tramo_map
                for section_id_str in mandatory_sections:
                    section_id = int(section_id_str)
                    if section_id in inverse_tramo_map:
                        edge_key = inverse_tramo_map[section_id]
                        nodes = edge_key.split('-')
                        if nodes[0] in positions and nodes[1] in positions:
                            section_positions[section_id] = (
                                positions[nodes[0]], 
                                positions[nodes[1]]
                            )
            
            # Collect forbidden section positions
            if forbidden_sections:
                # Map section IDs to pairs of positions
                inverse_tramo_map = pathfinder.inverse_tramo_map
                for section_id in forbidden_sections:
                    if section_id in inverse_tramo_map:
                        edge_key = inverse_tramo_map[section_id]
                        nodes = edge_key.split('-')
                        if nodes[0] in positions and nodes[1] in positions:
                            section_positions[section_id] = (
                                positions[nodes[0]], 
                                positions[nodes[1]]
                            )
            
            # Generate a detailed timestamp for the output DXF file
            current_time = datetime.now()
            detailed_timestamp = current_time.strftime("%Y%m%d_%H%M%S")
            
            dxf_file = os.path.join(args.output_dir, f"mandatory_path_result_{timestamp}_{detailed_timestamp}.dxf")
            export_path_to_dxf(path, dxf_file, mandatory_sections, section_positions, forbidden_sections)
    else:
        print("No path found that includes all mandatory sections.")

if __name__ == "__main__":
    main() 