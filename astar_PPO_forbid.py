#!/usr/bin/env python3
# astar_PPO_forbid.py
# A* pathfinding with optional PPO (Punto de Paso Obligatorio - Mandatory Waypoint)
# Enhanced with forbidden edge functionality
# Uses edge splitting for exact intermediate point pathfinding
# Supports multiple PPOs in sequence and forbidden edge avoidance

import sys
import json
from astar_spatial_IP import OptimizedSpatialGraph3D

class ForbiddenEdgeGraph(OptimizedSpatialGraph3D):
    """
    Extended OptimizedSpatialGraph3D with forbidden edge functionality
    """
    
    def __init__(self, graph_path, tramo_id_map_path=None, forbidden_sections_path=None):
        """
        Initialize graph with forbidden edge support
        
        Args:
            graph_path (str): Path to the graph JSON file
            tramo_id_map_path (str): Path to tramo ID mapping JSON file
            forbidden_sections_path (str): Path to forbidden sections JSON file
        """
        super().__init__(graph_path)
        
        # Initialize forbidden edge data structures
        self.tramo_id_map = {}
        self.forbidden_set = set()
        
        # Load tramo ID mapping if provided
        if tramo_id_map_path:
            self._load_tramo_id_map(tramo_id_map_path)
        
        # Load forbidden sections if provided
        if forbidden_sections_path:
            self._load_forbidden_sections(forbidden_sections_path)
    
    def _load_tramo_id_map(self, tramo_id_map_path):
        """Load tramo ID mapping from JSON file"""
        try:
            with open(tramo_id_map_path, 'r') as f:
                self.tramo_id_map = json.load(f)
            print(f"🔄 Loaded tramo ID mapping: {len(self.tramo_id_map)} edge mappings")
        except Exception as e:
            print(f"❌ Error loading tramo ID mapping: {e}")
            raise
    
    def _load_forbidden_sections(self, forbidden_sections_path):
        """Load forbidden sections from JSON file"""
        try:
            with open(forbidden_sections_path, 'r') as f:
                forbidden_list = json.load(f)
            self.forbidden_set = set(forbidden_list)
            print(f"🚫 Loaded forbidden sections: {len(self.forbidden_set)} forbidden tramo IDs")
            if self.forbidden_set:
                print(f"   Forbidden tramo IDs: {sorted(list(self.forbidden_set))}")
        except Exception as e:
            print(f"❌ Error loading forbidden sections: {e}")
            raise
    
    def is_edge_forbidden(self, nodeA, nodeB):
        """
        Check if an edge between two nodes is forbidden
        
        Args:
            nodeA (str): First node coordinate string "(x,y,z)"
            nodeB (str): Second node coordinate string "(x,y,z)"
            
        Returns:
            bool: True if edge is forbidden, False otherwise
        """
        if not self.tramo_id_map or not self.forbidden_set:
            return False
        
        # Create edge key in canonical form (sorted order)
        edge_key = "-".join(sorted([nodeA, nodeB]))
        
        # Look up tramo ID for this edge
        tramo_id = self.tramo_id_map.get(edge_key)
        
        # Return True if this tramo ID is in the forbidden set
        return tramo_id in self.forbidden_set if tramo_id is not None else False
    
    def find_path_with_edge_split_forbidden(self, start, goal):
        """
        Find path with edge splitting while avoiding forbidden edges
        This overrides the parent method to add forbidden edge checking
        
        Args:
            start (tuple): Start coordinates (x, y, z)
            goal (tuple): Goal coordinates (x, y, z)
            
        Returns:
            tuple: (path, nodes_explored)
        """
        # We'll override the graph's neighbor access to filter forbidden edges
        # Store the original graph adjacency for restoration
        original_graph_neighbors = {}
        
        # Create filtered adjacency lists for all nodes
        for node in self.graph.nodes():
            original_neighbors = list(self.graph[node])
            original_graph_neighbors[node] = original_neighbors
            
            # Filter out forbidden edges
            filtered_neighbors = []
            for neighbor in original_neighbors:
                # Convert nodes to strings for forbidden edge checking (use 3 decimal places to match tramo map format)
                node_str = f"({node[0]:.3f}, {node[1]:.3f}, {node[2]:.3f})"
                neighbor_str = f"({neighbor[0]:.3f}, {neighbor[1]:.3f}, {neighbor[2]:.3f})"
                
                if not self.is_edge_forbidden(node_str, neighbor_str):
                    filtered_neighbors.append(neighbor)
            
            # Temporarily replace the neighbors in the graph
            # Clear existing edges and add only non-forbidden ones
            edges_to_remove = [(node, neighbor) for neighbor in original_neighbors if neighbor not in filtered_neighbors]
            for edge in edges_to_remove:
                if self.graph.has_edge(edge[0], edge[1]):
                    self.graph.remove_edge(edge[0], edge[1])
        
        try:
            # Call the parent method with our filtered graph
            result = super().find_path_with_edge_split(start, goal)
        finally:
            # Restore original graph structure
            for node, original_neighbors in original_graph_neighbors.items():
                for neighbor in original_neighbors:
                    if not self.graph.has_edge(node, neighbor):
                        # Restore the edge with its original weight
                        weight = self.euclidean_distance(node, neighbor)
                        self.graph.add_edge(node, neighbor, weight=weight)
        
        return result

def run_astar_with_ppo_forward_path(graph_path, origin, ppo, destination, tramo_id_map_path=None, forbidden_sections_path=None):
    """
    Run A* pathfinding with forward path logic - prevents backtracking by forbidding 
    the last edge used in the previous segment
    Path: origin → PPO → destination (where PPO→destination cannot use the final edge from origin→PPO)
    
    Args:
        graph_path (str): Path to the graph JSON file
        origin (tuple): Origin coordinates (x, y, z)
        ppo (tuple): Mandatory waypoint coordinates (x, y, z)
        destination (tuple): Destination coordinates (x, y, z)
        tramo_id_map_path (str): Path to tramo ID mapping JSON file
        forbidden_sections_path (str): Path to forbidden sections JSON file
        
    Returns:
        tuple: (combined_path, total_nodes_explored, segment_info)
    """
    graph = ForbiddenEdgeGraph(graph_path, tramo_id_map_path, forbidden_sections_path)

    # Parte 1: origen → PPO
    print(f"  Segment 1: {format_point(origin)} → {format_point(ppo)}")
    if forbidden_sections_path and tramo_id_map_path:
        path1, nodes1 = graph.find_path_with_edge_split_forbidden(origin, ppo)
    else:
        path1, nodes1 = graph.find_path_with_edge_split(origin, ppo)
    
    if not path1:
        raise Exception("No se encontró camino desde origen hasta PPO (posiblemente bloqueado por secciones prohibidas)")
    
    print(f"    ✓ Found path with {len(path1)} points, {nodes1} nodes explored")
    
    # Get the last edge used in path1 to forbid it in path2
    last_edge_tramo_id = None
    if len(path1) >= 2 and tramo_id_map_path:
        # Get the last two points in path1
        second_last_point = path1[-2]
        last_point = path1[-1]  # This should be the PPO
        
        # Convert to string format for tramo lookup (use 3 decimal places to match tramo map format)
        node_str1 = f"({second_last_point[0]:.3f}, {second_last_point[1]:.3f}, {second_last_point[2]:.3f})"
        node_str2 = f"({last_point[0]:.3f}, {last_point[1]:.3f}, {last_point[2]:.3f})"
        
        # Create edge key in canonical form (sorted order)
        edge_key = "-".join(sorted([node_str1, node_str2]))
        
        # Look up tramo ID for this edge
        if edge_key in graph.tramo_id_map:
            last_edge_tramo_id = graph.tramo_id_map[edge_key]
            print(f"    📍 Last edge used: {edge_key} → Tramo ID {last_edge_tramo_id}")
    
    # Parte 2: PPO → destino (with forward path restriction)
    print(f"  Segment 2: {format_point(ppo)} → {format_point(destination)}")
    
    # Temporarily add the last edge to forbidden set for segment 2
    original_forbidden_set = graph.forbidden_set.copy()
    if last_edge_tramo_id is not None:
        graph.forbidden_set.add(last_edge_tramo_id)
        print(f"    🚫 Forward path: Temporarily forbidding tramo ID {last_edge_tramo_id} to prevent backtracking")
    
    try:
        if tramo_id_map_path:
            path2, nodes2 = graph.find_path_with_edge_split_forbidden(ppo, destination)
        else:
            path2, nodes2 = graph.find_path_with_edge_split(ppo, destination)
    finally:
        # Restore original forbidden set
        graph.forbidden_set = original_forbidden_set
    
    if not path2:
        raise Exception("No se encontró camino desde PPO hasta destino (posiblemente bloqueado por forward path restriction o secciones prohibidas)")
    
    print(f"    ✓ Found path with {len(path2)} points, {nodes2} nodes explored")
    
    # Combine paths, avoiding duplication of PPO
    if len(path1) > 0 and len(path2) > 0 and path1[-1] == path2[0]:
        combined_path = path1 + path2[1:]  # Skip first point of path2 (PPO duplicate)
    else:
        combined_path = path1 + path2
    
    total_nodes_explored = nodes1 + nodes2
    
    # Create segment info
    segment_info = [
        {'segment': 1, 'start': origin, 'end': ppo, 'path_length': len(path1), 'nodes_explored': nodes1},
        {'segment': 2, 'start': ppo, 'end': destination, 'path_length': len(path2), 'nodes_explored': nodes2}
    ]
    
    return combined_path, total_nodes_explored, segment_info

def run_astar_with_multiple_ppos_forward_path(graph_path, origin, ppos, destination, tramo_id_map_path=None, forbidden_sections_path=None):
    """
    Run A* pathfinding with multiple PPOs using forward path logic
    Each segment prevents backtracking by forbidding the last edge from the previous segment
    
    Args:
        graph_path (str): Path to the graph JSON file
        origin (tuple): Origin coordinates (x, y, z)
        ppos (list): List of PPO coordinates [(x, y, z), ...]
        destination (tuple): Destination coordinates (x, y, z)
        tramo_id_map_path (str): Path to tramo ID mapping JSON file
        forbidden_sections_path (str): Path to forbidden sections JSON file
        
    Returns:
        tuple: (combined_path, total_nodes_explored, segment_info)
    """
    graph = ForbiddenEdgeGraph(graph_path, tramo_id_map_path, forbidden_sections_path)
    
    # Build sequence: origin → PPO1 → PPO2 → ... → destination
    waypoints = [origin] + ppos + [destination]
    
    combined_path = []
    total_nodes_explored = 0
    segment_info = []
    last_edge_tramo_id = None
    
    for i in range(len(waypoints) - 1):
        start_point = waypoints[i]
        end_point = waypoints[i + 1]
        
        print(f"  Segment {i+1}: {format_point(start_point)} → {format_point(end_point)}")
        
        # For segments after the first, temporarily forbid the last edge from previous segment
        original_forbidden_set = graph.forbidden_set.copy()
        if last_edge_tramo_id is not None and i > 0:
            graph.forbidden_set.add(last_edge_tramo_id)
            print(f"    🚫 Forward path: Temporarily forbidding tramo ID {last_edge_tramo_id} to prevent backtracking")
        
        try:
            # Find path for this segment
            if tramo_id_map_path:
                segment_path, segment_nodes = graph.find_path_with_edge_split_forbidden(start_point, end_point)
            else:
                segment_path, segment_nodes = graph.find_path_with_edge_split(start_point, end_point)
        finally:
            # Restore original forbidden set
            graph.forbidden_set = original_forbidden_set
        
        if not segment_path:
            raise Exception(f"No se encontró camino para el segmento {i+1}: {format_point(start_point)} → {format_point(end_point)}")
        
        print(f"    ✓ Found path with {len(segment_path)} points, {segment_nodes} nodes explored")
        
        # Get the last edge used in this segment for next iteration
        last_edge_tramo_id = None
        if len(segment_path) >= 2 and tramo_id_map_path:
            # Get the last two points in this segment
            second_last_point = segment_path[-2]
            last_point = segment_path[-1]
            
            # Convert to string format for tramo lookup (use 3 decimal places to match tramo map format)
            node_str1 = f"({second_last_point[0]:.3f}, {second_last_point[1]:.3f}, {second_last_point[2]:.3f})"
            node_str2 = f"({last_point[0]:.3f}, {last_point[1]:.3f}, {last_point[2]:.3f})"
            
            # Create edge key in canonical form (sorted order)
            edge_key = "-".join(sorted([node_str1, node_str2]))
            
            # Look up tramo ID for this edge
            if edge_key in graph.tramo_id_map:
                last_edge_tramo_id = graph.tramo_id_map[edge_key]
                print(f"    📍 Last edge used: {edge_key} → Tramo ID {last_edge_tramo_id}")
        
        # Add segment to combined path
        if i == 0:
            combined_path.extend(segment_path)
        else:
            # Skip first point to avoid duplication with previous segment's end
            combined_path.extend(segment_path[1:])
        
        total_nodes_explored += segment_nodes
        
        # Store segment info
        segment_info.append({
            'segment': i + 1,
            'start': start_point,
            'end': end_point,
            'path_length': len(segment_path),
            'nodes_explored': segment_nodes
        })
    
    return combined_path, total_nodes_explored, segment_info

def run_astar_forbidden(graph_path, origin, destination, tramo_id_map_path=None, forbidden_sections_path=None):
    """
    Run direct A* pathfinding from origin to destination with forbidden edge avoidance
    
    Args:
        graph_path (str): Path to the graph JSON file
        origin (tuple): Origin coordinates (x, y, z)
        destination (tuple): Destination coordinates (x, y, z)
        tramo_id_map_path (str): Path to tramo ID mapping JSON file
        forbidden_sections_path (str): Path to forbidden sections JSON file
        
    Returns:
        tuple: (path, nodes_explored)
    """
    graph = ForbiddenEdgeGraph(graph_path, tramo_id_map_path, forbidden_sections_path)
    
    # Use forbidden-aware pathfinding if restrictions are provided
    if forbidden_sections_path and tramo_id_map_path:
        path, nodes_explored = graph.find_path_with_edge_split_forbidden(origin, destination)
    else:
        path, nodes_explored = graph.find_path_with_edge_split(origin, destination)
    
    if not path:
        raise Exception("No se encontró camino entre origen y destino (posiblemente bloqueado por secciones prohibidas).")
    return path, nodes_explored

def run_astar_with_ppo_forbidden(graph_path, origin, ppo, destination, tramo_id_map_path=None, forbidden_sections_path=None):
    """
    Run A* pathfinding with single mandatory waypoint (PPO) and forbidden edge avoidance
    Path: origin → PPO → destination
    
    Args:
        graph_path (str): Path to the graph JSON file
        origin (tuple): Origin coordinates (x, y, z)
        ppo (tuple): Mandatory waypoint coordinates (x, y, z)
        destination (tuple): Destination coordinates (x, y, z)
        tramo_id_map_path (str): Path to tramo ID mapping JSON file
        forbidden_sections_path (str): Path to forbidden sections JSON file
        
    Returns:
        tuple: (combined_path, total_nodes_explored)
    """
    graph = ForbiddenEdgeGraph(graph_path, tramo_id_map_path, forbidden_sections_path)

    # Parte 1: origen → PPO
    if forbidden_sections_path and tramo_id_map_path:
        path1, nodes1 = graph.find_path_with_edge_split_forbidden(origin, ppo)
    else:
        path1, nodes1 = graph.find_path_with_edge_split(origin, ppo)
    
    if not path1:
        raise Exception("No se encontró camino desde origen hasta PPO (posiblemente bloqueado por secciones prohibidas)")

    # Parte 2: PPO → destino
    if forbidden_sections_path and tramo_id_map_path:
        path2, nodes2 = graph.find_path_with_edge_split_forbidden(ppo, destination)
    else:
        path2, nodes2 = graph.find_path_with_edge_split(ppo, destination)
    
    if not path2:
        raise Exception("No se encontró camino desde PPO hasta destino (posiblemente bloqueado por secciones prohibidas)")

    # Evita duplicar PPO si es el mismo punto
    if len(path1) > 0 and len(path2) > 0 and path1[-1] == path2[0]:
        path2 = path2[1:]

    return path1 + path2, nodes1 + nodes2

def run_astar_with_multiple_ppos_forbidden(graph_path, origin, ppos, destination, tramo_id_map_path=None, forbidden_sections_path=None):
    """
    Run A* pathfinding with multiple mandatory waypoints (PPOs) and forbidden edge avoidance
    Path: origin → PPO_1 → PPO_2 → ... → PPO_n → destination
    
    Args:
        graph_path (str): Path to the graph JSON file
        origin (tuple): Origin coordinates (x, y, z)
        ppos (list): List of PPO coordinates [(x1,y1,z1), (x2,y2,z2), ...]
        destination (tuple): Destination coordinates (x, y, z)
        tramo_id_map_path (str): Path to tramo ID mapping JSON file
        forbidden_sections_path (str): Path to forbidden sections JSON file
        
    Returns:
        tuple: (combined_path, total_nodes_explored, segment_info)
    """
    if not ppos:
        # No PPOs, just direct pathfinding
        path, nodes_explored = run_astar_forbidden(graph_path, origin, destination, tramo_id_map_path, forbidden_sections_path)
        segment_info = [{'segment': 1, 'start': origin, 'end': destination, 
                        'path_length': len(path), 'nodes_explored': nodes_explored}]
        return path, nodes_explored, segment_info
    
    graph = ForbiddenEdgeGraph(graph_path, tramo_id_map_path, forbidden_sections_path)
    
    # Create the complete waypoint sequence: origin → PPO_1 → PPO_2 → ... → destination
    waypoints = [origin] + ppos + [destination]
    
    combined_path = []
    total_nodes_explored = 0
    segment_info = []
    
    # Process each segment in sequence
    for i in range(len(waypoints) - 1):
        start_point = waypoints[i]
        end_point = waypoints[i + 1]
        
        print(f"  Segment {i+1}: {format_point(start_point)} → {format_point(end_point)}")
        
        # Find path for this segment with forbidden edge avoidance
        if forbidden_sections_path and tramo_id_map_path:
            segment_path, nodes_explored = graph.find_path_with_edge_split_forbidden(start_point, end_point)
        else:
            segment_path, nodes_explored = graph.find_path_with_edge_split(start_point, end_point)
        
        if not segment_path:
            raise Exception(f"No se encontró camino en segmento {i+1}: {format_point(start_point)} → {format_point(end_point)} (posiblemente bloqueado por secciones prohibidas)")
        
        # Record segment information
        segment_info.append({
            'segment': i + 1,
            'start': start_point,
            'end': end_point,
            'path_length': len(segment_path),
            'nodes_explored': nodes_explored
        })
        
        total_nodes_explored += nodes_explored
        
        # Add segment path to combined path, avoiding duplicates at waypoints
        if i == 0:
            # First segment: add all points
            combined_path.extend(segment_path)
        else:
            # Subsequent segments: skip first point (duplicate of previous segment's end)
            if len(segment_path) > 0 and len(combined_path) > 0 and segment_path[0] == combined_path[-1]:
                combined_path.extend(segment_path[1:])
            else:
                combined_path.extend(segment_path)
    
    return combined_path, total_nodes_explored, segment_info

def format_point(point):
    """Format a point for display"""
    return f"({point[0]:.3f}, {point[1]:.3f}, {point[2]:.3f})"

def print_usage():
    """Print usage instructions"""
    print("❌ Uso incorrecto.")
    print("✅ Sin PPO: python astar_PPO_forbid.py <graph> x1 y1 z1 x_dest y_dest z_dest [--tramos <tramo_file>] [--forbidden <forbidden_file>]")
    print("✅ Con 1 PPO: python astar_PPO_forbid.py <graph> x1 y1 z1 x_ppo1 y_ppo1 z_ppo1 x_dest y_dest z_dest [--tramos <tramo_file>] [--forbidden <forbidden_file>]")
    print("✅ Con múltiples PPOs: python astar_PPO_forbid.py <graph> x1 y1 z1 x_ppo1 y_ppo1 z_ppo1 x_ppo2 y_ppo2 z_ppo2 ... x_dest y_dest z_dest [--tramos <tramo_file>] [--forbidden <forbidden_file>]")
    print("✅ Optimal Check: python astar_PPO_forbid.py optimal_check <graph> x1 y1 z1 x_ppo1 y_ppo1 z_ppo1 x_ppo2 y_ppo2 z_ppo2 x_dest y_dest z_dest [--tramos <tramo_file>] [--forbidden <forbidden_file>]")
    print("✅ Forward Path: python astar_PPO_forbid.py forward_path <graph> x1 y1 z1 x_ppo1 y_ppo1 z_ppo1 [x_ppo2 y_ppo2 z_ppo2 ...] x_dest y_dest z_dest [--tramos <tramo_file>] [--forbidden <forbidden_file>]")
    print("")
    print("Parámetros opcionales:")
    print("  --tramos <file>     : Archivo de mapeo de tramo IDs (JSON)")
    print("  --forbidden <file>  : Archivo de secciones prohibidas (JSON)")
    print("")
    print("Comandos especiales:")
    print("  optimal_check       : Compara dos órdenes de PPOs para encontrar el más óptimo")
    print("  forward_path        : Evita backtracking prohibiendo el último edge del segmento anterior")
    print("")
    print("Ejemplos:")
    print("  # Directo sin restricciones:")
    print("  python astar_PPO_forbid.py graph_LVA1.json 145.475 28.926 145.041 122.331 10.427 161.623")
    print("")
    print("  # Con secciones prohibidas:")
    print("  python astar_PPO_forbid.py graph_LVA1.json 145.475 28.926 145.041 122.331 10.427 161.623 \\")
    print("    --tramos Output_Path_Sections/tramo_id_map_20250626_114538.json \\")
    print("    --forbidden forbidden_sections_20250626_115543.json")
    print("")
    print("  # 1 PPO con restricciones:")
    print("  python astar_PPO_forbid.py graph_LVA1.json 145.475 28.926 145.041 140.0 25.0 150.0 122.331 10.427 161.623 \\")
    print("    --tramos Output_Path_Sections/tramo_id_map_20250626_114538.json \\")
    print("    --forbidden forbidden_sections_20250626_115543.json")
    print("")
    print("  # Forward path (previene backtracking):")
    print("  python astar_PPO_forbid.py forward_path graph_LVA1.json 152.290 17.883 160.124 143.382 25.145 160.703 139.232 28.845 139.993 \\")
    print("    --tramos Output_Path_Sections/tramo_id_map_20250626_114538.json \\")
    print("    --forbidden forbidden_sections_20250626_115543.json")

def run_optimal_check_forbidden(graph_path, origin, ppo1, ppo2, destination, tramo_id_map_path=None, forbidden_sections_path=None):
    """
    Compare two different PPO orderings to find the optimal path with forbidden edge avoidance.
    
    Order 1: origin → PPO_1 → PPO_2 → destination
    Order 2: origin → PPO_2 → PPO_1 → destination
    
    Args:
        graph_path (str): Path to the graph JSON file
        origin (tuple): Origin coordinates (x, y, z)
        ppo1 (tuple): First PPO coordinates (x, y, z)
        ppo2 (tuple): Second PPO coordinates (x, y, z)
        destination (tuple): Destination coordinates (x, y, z)
        tramo_id_map_path (str): Path to tramo ID mapping JSON file
        forbidden_sections_path (str): Path to forbidden sections JSON file
        
    Returns:
        dict: Comparison results with both paths and optimal choice
    """
    print(f"🔍 Optimal Check: Comparing PPO orderings (with forbidden edge avoidance)")
    print(f"Order 1: Origin → PPO_1 → PPO_2 → Destination")
    print(f"Order 2: Origin → PPO_2 → PPO_1 → Destination")
    print()
    
    # Order 1: PPO_1 → PPO_2
    print("📊 Testing Order 1: Origin → PPO_1 → PPO_2 → Destination")
    try:
        path1, nodes1, segments1 = run_astar_with_multiple_ppos_forbidden(
            graph_path, origin, [ppo1, ppo2], destination, tramo_id_map_path, forbidden_sections_path)
        distance1 = calculate_path_distance(path1)
        order1_success = True
        order1_error = None
    except Exception as e:
        path1, nodes1, segments1, distance1 = None, 0, [], float('inf')
        order1_success = False
        order1_error = str(e)
        print(f"❌ Order 1 failed: {e}")
    
    if order1_success:
        print(f"✅ Order 1: {len(path1)} points, {distance1:.3f} units, {nodes1} nodes explored")
    
    # Order 2: PPO_2 → PPO_1
    print("📊 Testing Order 2: Origin → PPO_2 → PPO_1 → Destination")
    try:
        path2, nodes2, segments2 = run_astar_with_multiple_ppos_forbidden(
            graph_path, origin, [ppo2, ppo1], destination, tramo_id_map_path, forbidden_sections_path)
        distance2 = calculate_path_distance(path2)
        order2_success = True
        order2_error = None
    except Exception as e:
        path2, nodes2, segments2, distance2 = None, 0, [], float('inf')
        order2_success = False
        order2_error = str(e)
        print(f"❌ Order 2 failed: {e}")
    
    if order2_success:
        print(f"✅ Order 2: {len(path2)} points, {distance2:.3f} units, {nodes2} nodes explored")
    
    # Determine optimal order
    print("\n" + "="*60)
    print("OPTIMAL CHECK RESULTS (WITH FORBIDDEN EDGE AVOIDANCE)")
    print("="*60)
    
    if not order1_success and not order2_success:
        optimal_order = None
        improvement = 0.0
        print("❌ Both orders failed - no valid path found (possibly blocked by forbidden sections)")
    elif not order1_success:
        optimal_order = 2
        improvement = float('inf')
        print("🎯 Order 2 is optimal (Order 1 failed)")
    elif not order2_success:
        optimal_order = 1
        improvement = float('inf')
        print("🎯 Order 1 is optimal (Order 2 failed)")
    else:
        # Both succeeded, compare distances
        if distance1 < distance2:
            optimal_order = 1
            improvement = distance2 - distance1
            improvement_pct = (improvement / distance2) * 100
            print(f"🎯 Order 1 is OPTIMAL!")
            print(f"   Improvement: {improvement:.3f} units ({improvement_pct:.1f}% shorter)")
        elif distance2 < distance1:
            optimal_order = 2
            improvement = distance1 - distance2
            improvement_pct = (improvement / distance1) * 100
            print(f"🎯 Order 2 is OPTIMAL!")
            print(f"   Improvement: {improvement:.3f} units ({improvement_pct:.1f}% shorter)")
        else:
            optimal_order = "tie"
            improvement = 0.0
            print(f"🤝 TIE! Both orders have identical distance: {distance1:.3f} units")
    
    # Summary table
    print(f"\nComparison Summary:")
    print(f"{'Order':<8} {'Path':<25} {'Distance':<12} {'Points':<8} {'Nodes':<8} {'Status':<10}")
    print(f"{'-'*8} {'-'*25} {'-'*12} {'-'*8} {'-'*8} {'-'*10}")
    
    order1_status = "✅ Success" if order1_success else "❌ Failed"
    order2_status = "✅ Success" if order2_success else "❌ Failed"
    
    print(f"{'1':<8} {'Origin→PPO_1→PPO_2→Dest':<25} {distance1 if order1_success else 'N/A':<12} {len(path1) if path1 else 'N/A':<8} {nodes1:<8} {order1_status:<10}")
    print(f"{'2':<8} {'Origin→PPO_2→PPO_1→Dest':<25} {distance2 if order2_success else 'N/A':<12} {len(path2) if path2 else 'N/A':<8} {nodes2:<8} {order2_status:<10}")
    
    print("="*60)
    
    # Return comprehensive results
    return {
        'order1': {
            'path': path1,
            'distance': distance1 if order1_success else None,
            'points': len(path1) if path1 else 0,
            'nodes_explored': nodes1,
            'segments': segments1,
            'success': order1_success,
            'error': order1_error,
            'sequence': [origin, ppo1, ppo2, destination]
        },
        'order2': {
            'path': path2,
            'distance': distance2 if order2_success else None,
            'points': len(path2) if path2 else 0,
            'nodes_explored': nodes2,
            'segments': segments2,
            'success': order2_success,
            'error': order2_error,
            'sequence': [origin, ppo2, ppo1, destination]
        },
        'optimal_order': optimal_order,
        'improvement': improvement,
        'both_valid': order1_success and order2_success
    }

def calculate_path_distance(path):
    """Calculate total distance of a path."""
    if not path or len(path) < 2:
        return 0.0
    
    total_distance = 0.0
    for i in range(1, len(path)):
        from math import sqrt
        dist = sqrt(sum((a - b) ** 2 for a, b in zip(path[i-1], path[i])))
        total_distance += dist
    return total_distance

def parse_arguments(args):
    """Parse command line arguments including optional flags"""
    # Find optional arguments
    tramo_id_map_path = None
    forbidden_sections_path = None
    
    # Create a copy of args to modify
    filtered_args = []
    i = 0
    while i < len(args):
        if args[i] == '--tramos' and i + 1 < len(args):
            tramo_id_map_path = args[i + 1]
            i += 2  # Skip both --tramos and the filename
        elif args[i] == '--forbidden' and i + 1 < len(args):
            forbidden_sections_path = args[i + 1]
            i += 2  # Skip both --forbidden and the filename
        else:
            filtered_args.append(args[i])
            i += 1
    
    return filtered_args, tramo_id_map_path, forbidden_sections_path

if __name__ == "__main__":
    # Parse arguments to extract optional flags
    filtered_args, tramo_id_map_path, forbidden_sections_path = parse_arguments(sys.argv)
    
    # Show forbidden edge status
    if forbidden_sections_path and tramo_id_map_path:
        print("🚫 Forbidden edge avoidance: ENABLED")
        print(f"   Tramo mapping: {tramo_id_map_path}")
        print(f"   Forbidden sections: {forbidden_sections_path}")
    else:
        print("🟢 Forbidden edge avoidance: DISABLED (no restrictions)")
    print()
    
    # Check for forward_path command
    if len(filtered_args) >= 2 and filtered_args[1] == "forward_path":
        # forward_path mode: forward_path graph_file origin(3) ppo(3) destination(3) = 11 total (single PPO)
        # OR forward_path graph_file origin(3) ppo1(3) ppo2(3) ... destination(3) (multiple PPOs)
        if len(filtered_args) < 11:
            print("❌ Error: forward_path requiere al menos 9 coordenadas (origen + 1 PPO + destino)")
            print("Uso: python astar_PPO_forbid.py forward_path <graph> x1 y1 z1 x_ppo y_ppo z_ppo x_dest y_dest z_dest [--tramos <tramo_file>] [--forbidden <forbidden_file>]")
            print("     python astar_PPO_forbid.py forward_path <graph> x1 y1 z1 x_ppo1 y_ppo1 z_ppo1 x_ppo2 y_ppo2 z_ppo2 ... x_dest y_dest z_dest [--tramos <tramo_file>] [--forbidden <forbidden_file>]")
            sys.exit(1)
        
        # Check that we have proper coordinate triplets (total args - 3) must be divisible by 3
        total_coords = len(filtered_args) - 3  # Subtract script name, command, and graph file
        if total_coords % 3 != 0:
            print("❌ Error: Las coordenadas deben ser en grupos de 3 (x, y, z)")
            sys.exit(1)

        graph_file = filtered_args[2]
        
        # Parse all coordinates in groups of 3
        coords = []
        for i in range(3, len(filtered_args), 3):
            if i + 2 < len(filtered_args):
                coord = tuple(map(float, filtered_args[i:i+3]))
                coords.append(coord)
        
        # Need at least origin, one PPO, and destination
        if len(coords) < 3:
            print("❌ Error: forward_path necesita al menos origen, 1 PPO y destino")
            sys.exit(1)
        
        origin = coords[0]
        destination = coords[-1]
        ppos = coords[1:-1]  # All coordinates between origin and destination are PPOs

        print(f"🚀 A* Forward Path - Prevents Backtracking")
        print(f"Graph: {graph_file}")
        print(f"Origin: {format_point(origin)}")
        
        if len(ppos) == 1:
            print(f"PPO: {format_point(ppos[0])}")
            print(f"Mode: Single PPO forward path")
        else:
            print(f"PPOs ({len(ppos)} waypoints):")
            for i, ppo in enumerate(ppos):
                print(f"  PPO_{i+1}: {format_point(ppo)}")
            print(f"Mode: Multi-PPO forward path")
        
        print(f"Destination: {format_point(destination)}")
        print(f"\nForward Path Logic: Each segment cannot use the last edge from the previous segment")
        print(f"Processing segments:")
        
        try:
            if len(ppos) == 1:
                # Single PPO forward path
                full_path, nodes_explored, segment_info = run_astar_with_ppo_forward_path(
                    graph_file, origin, ppos[0], destination, tramo_id_map_path, forbidden_sections_path)
            else:
                # Multiple PPO forward path
                full_path, nodes_explored, segment_info = run_astar_with_multiple_ppos_forward_path(
                    graph_file, origin, ppos, destination, tramo_id_map_path, forbidden_sections_path)
            
            print(f"\n✅ Forward path completo con {len(ppos)} PPO(s) y prevención de backtracking:")
            print(f"Total points: {len(full_path)}")
            print(f"Total nodes explored: {nodes_explored}")
            print(f"Edge splitting: Enabled (exact PPO coordinates on edges allowed)")
            print(f"Forbidden edge avoidance: {'Enabled' if forbidden_sections_path and tramo_id_map_path else 'Disabled'}")
            print(f"Forward path logic: Enabled (prevents backtracking)")
            
            # Calculate total distance
            total_distance = calculate_path_distance(full_path)
            print(f"Total distance: {total_distance:.3f}")
            
            # Show segment breakdown
            if len(segment_info) > 1:
                print(f"\nSegment breakdown:")
                for seg in segment_info:
                    print(f"  Segment {seg['segment']}: {seg['path_length']} points, {seg['nodes_explored']} nodes explored")
            
            print(f"\nPath details:")
            for i, point in enumerate(full_path):
                marker = ""
                if point == origin:
                    marker = " [ORIGIN]"
                elif point == destination:
                    marker = " [DESTINATION]"
                else:
                    # Check if this point is one of our PPOs
                    for j, ppo in enumerate(ppos):
                        if point == ppo:
                            marker = f" [PPO_{j+1}]"
                            break
                print(f"{i+1:3d}. {format_point(point)}{marker}")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        sys.exit(0)

    # Check for optimal_check command
    if len(filtered_args) >= 2 and filtered_args[1] == "optimal_check":
        # optimal_check mode: optimal_check graph_file origin(3) ppo1(3) ppo2(3) destination(3) = 15 total
        if len(filtered_args) != 15:
            print("❌ Error: optimal_check requiere exactamente 12 coordenadas (origen + 2 PPOs + destino)")
            print("Uso: python astar_PPO_forbid.py optimal_check <graph> x1 y1 z1 x_ppo1 y_ppo1 z_ppo1 x_ppo2 y_ppo2 z_ppo2 x_dest y_dest z_dest [--tramos <tramo_file>] [--forbidden <forbidden_file>]")
            sys.exit(1)
        
        graph_file = filtered_args[2]
        origin = tuple(map(float, filtered_args[3:6]))
        ppo1 = tuple(map(float, filtered_args[6:9]))
        ppo2 = tuple(map(float, filtered_args[9:12]))
        destination = tuple(map(float, filtered_args[12:15]))
        
        print(f"🚀 A* Optimal Check - PPO Order Comparison (with Forbidden Edge Avoidance)")
        print(f"Graph: {graph_file}")
        print(f"Origin: {format_point(origin)}")
        print(f"PPO_1: {format_point(ppo1)}")
        print(f"PPO_2: {format_point(ppo2)}")
        print(f"Destination: {format_point(destination)}")
        print()
        
        try:
            results = run_optimal_check_forbidden(graph_file, origin, ppo1, ppo2, destination, 
                                                tramo_id_map_path, forbidden_sections_path)
            
            # Show detailed path for optimal order
            if results['optimal_order'] == 1 and results['order1']['success']:
                print(f"\n🎯 OPTIMAL PATH DETAILS (Order 1):")
                optimal_path = results['order1']['path']
                for i, point in enumerate(optimal_path):
                    marker = ""
                    if point == origin:
                        marker = " [ORIGIN]"
                    elif point == ppo1:
                        marker = " [PPO_1]"
                    elif point == ppo2:
                        marker = " [PPO_2]"
                    elif point == destination:
                        marker = " [DESTINATION]"
                    print(f"{i+1:3d}. {format_point(point)}{marker}")
                    
            elif results['optimal_order'] == 2 and results['order2']['success']:
                print(f"\n🎯 OPTIMAL PATH DETAILS (Order 2):")
                optimal_path = results['order2']['path']
                for i, point in enumerate(optimal_path):
                    marker = ""
                    if point == origin:
                        marker = " [ORIGIN]"
                    elif point == ppo1:
                        marker = " [PPO_1]"
                    elif point == ppo2:
                        marker = " [PPO_2]"
                    elif point == destination:
                        marker = " [DESTINATION]"
                    print(f"{i+1:3d}. {format_point(point)}{marker}")
            
        except Exception as e:
            print(f"\n❌ Error during optimal check: {e}")
        
        sys.exit(0)
    
    # Regular pathfinding mode
    # Validate minimum arguments: script graph_file origin(3) destination(3) = 8 total
    if len(filtered_args) < 8:
        print_usage()
        sys.exit(1)
    
    # Check that we have proper coordinate triplets (total args - 2) must be divisible by 3
    total_coords = len(filtered_args) - 2  # Subtract script name and graph file
    if total_coords % 3 != 0:
        print("❌ Error: Las coordenadas deben ser en grupos de 3 (x, y, z)")
        print_usage()
        sys.exit(1)

    graph_file = filtered_args[1]
    
    # Parse all coordinates in groups of 3
    coords = []
    for i in range(2, len(filtered_args), 3):
        if i + 2 < len(filtered_args):
            coord = tuple(map(float, filtered_args[i:i+3]))
            coords.append(coord)
    
    # Need at least origin and destination
    if len(coords) < 2:
        print("❌ Error: Se necesitan al menos origen y destino")
        print_usage()
        sys.exit(1)
    
    origin = coords[0]
    destination = coords[-1]
    ppos = coords[1:-1]  # All coordinates between origin and destination are PPOs

    print(f"🚀 A* Pathfinding with Multiple PPOs, Edge Splitting, and Forbidden Edge Avoidance")
    print(f"Graph: {graph_file}")
    print(f"Origin: {format_point(origin)}")
    
    if len(ppos) == 0:
        print(f"Destination: {format_point(destination)}")
        print(f"Mode: Direct pathfinding (no PPOs)")
    else:
        print(f"PPOs ({len(ppos)} waypoints):")
        for i, ppo in enumerate(ppos):
            print(f"  PPO_{i+1}: {format_point(ppo)}")
        print(f"Destination: {format_point(destination)}")
        print(f"Mode: Multi-PPO pathfinding with edge splitting")
    
    print(f"\nProcessing segments:")
    
    try:
        if len(ppos) == 0:
            # Direct pathfinding
            full_path, nodes_explored = run_astar_forbidden(graph_file, origin, destination, 
                                                          tramo_id_map_path, forbidden_sections_path)
            segment_info = [{'segment': 1, 'start': origin, 'end': destination, 
                           'path_length': len(full_path), 'nodes_explored': nodes_explored}]
        else:
            # Multi-PPO pathfinding
            full_path, nodes_explored, segment_info = run_astar_with_multiple_ppos_forbidden(
                graph_file, origin, ppos, destination, tramo_id_map_path, forbidden_sections_path)
        
        print(f"\n✅ Camino completo con {len(ppos)} PPO(s) y restricciones de secciones prohibidas:")
        print(f"Total points: {len(full_path)}")
        print(f"Total nodes explored: {nodes_explored}")
        print(f"Edge splitting: Enabled (exact PPO coordinates on edges allowed)")
        print(f"Forbidden edge avoidance: {'Enabled' if forbidden_sections_path and tramo_id_map_path else 'Disabled'}")
        
        # Calculate total distance
        total_distance = 0
        for i in range(1, len(full_path)):
            from math import sqrt
            dist = sqrt(sum((a - b) ** 2 for a, b in zip(full_path[i-1], full_path[i])))
            total_distance += dist
        
        print(f"Total distance: {total_distance:.3f}")
        
        # Show segment breakdown
        if len(segment_info) > 1:
            print(f"\nSegment breakdown:")
            for seg in segment_info:
                print(f"  Segment {seg['segment']}: {seg['path_length']} points, {seg['nodes_explored']} nodes explored")
        
        print(f"\nPath details:")
        for i, point in enumerate(full_path):
            marker = ""
            if point == origin:
                marker = " [ORIGIN]"
            elif point == destination:
                marker = " [DESTINATION]"
            else:
                # Check if this point is one of our PPOs
                for j, ppo in enumerate(ppos):
                    if point == ppo:
                        marker = f" [PPO_{j+1}]"
                        break
            print(f"{i+1:3d}. {format_point(point)}{marker}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1) 