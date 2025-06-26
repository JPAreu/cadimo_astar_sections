#!/usr/bin/env python3
# astar_PPO.py
# A* pathfinding with optional PPO (Punto de Paso Obligatorio - Mandatory Waypoint)
# Uses edge splitting for exact intermediate point pathfinding
# Supports multiple PPOs in sequence

import sys
from astar_spatial_IP import OptimizedSpatialGraph3D

def run_astar(graph_path, origin, destination):
    """
    Run direct A* pathfinding from origin to destination using edge splitting
    
    Args:
        graph_path (str): Path to the graph JSON file
        origin (tuple): Origin coordinates (x, y, z)
        destination (tuple): Destination coordinates (x, y, z)
        
    Returns:
        tuple: (path, nodes_explored)
    """
    graph = OptimizedSpatialGraph3D(graph_path)
    path, nodes_explored = graph.find_path_with_edge_split(origin, destination)
    if not path:
        raise Exception("No se encontró camino entre origen y destino.")
    return path, nodes_explored

def run_astar_with_ppo(graph_path, origin, ppo, destination):
    """
    Run A* pathfinding with single mandatory waypoint (PPO) using edge splitting
    Path: origin → PPO → destination
    
    Args:
        graph_path (str): Path to the graph JSON file
        origin (tuple): Origin coordinates (x, y, z)
        ppo (tuple): Mandatory waypoint coordinates (x, y, z)
        destination (tuple): Destination coordinates (x, y, z)
        
    Returns:
        tuple: (combined_path, total_nodes_explored)
    """
    graph = OptimizedSpatialGraph3D(graph_path)

    # Parte 1: origen → PPO (usando edge splitting)
    path1, nodes1 = graph.find_path_with_edge_split(origin, ppo)
    if not path1:
        raise Exception("No se encontró camino desde origen hasta PPO")

    # Parte 2: PPO → destino (usando edge splitting)
    path2, nodes2 = graph.find_path_with_edge_split(ppo, destination)
    if not path2:
        raise Exception("No se encontró camino desde PPO hasta destino")

    # Evita duplicar PPO si es el mismo punto
    if len(path1) > 0 and len(path2) > 0 and path1[-1] == path2[0]:
        path2 = path2[1:]

    return path1 + path2, nodes1 + nodes2

def run_astar_with_multiple_ppos(graph_path, origin, ppos, destination):
    """
    Run A* pathfinding with multiple mandatory waypoints (PPOs) using edge splitting
    Path: origin → PPO_1 → PPO_2 → ... → PPO_n → destination
    
    Args:
        graph_path (str): Path to the graph JSON file
        origin (tuple): Origin coordinates (x, y, z)
        ppos (list): List of PPO coordinates [(x1,y1,z1), (x2,y2,z2), ...]
        destination (tuple): Destination coordinates (x, y, z)
        
    Returns:
        tuple: (combined_path, total_nodes_explored, segment_info)
    """
    if not ppos:
        # No PPOs, just direct pathfinding
        path, nodes_explored = run_astar(graph_path, origin, destination)
        segment_info = [{'segment': 1, 'start': origin, 'end': destination, 
                        'path_length': len(path), 'nodes_explored': nodes_explored}]
        return path, nodes_explored, segment_info
    
    graph = OptimizedSpatialGraph3D(graph_path)
    
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
        
        # Find path for this segment using edge splitting
        segment_path, nodes_explored = graph.find_path_with_edge_split(start_point, end_point)
        
        if not segment_path:
            raise Exception(f"No se encontró camino en segmento {i+1}: {format_point(start_point)} → {format_point(end_point)}")
        
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
    print("✅ Sin PPO: python astar_PPO.py <graph> x1 y1 z1 x_dest y_dest z_dest")
    print("✅ Con 1 PPO: python astar_PPO.py <graph> x1 y1 z1 x_ppo1 y_ppo1 z_ppo1 x_dest y_dest z_dest")
    print("✅ Con múltiples PPOs: python astar_PPO.py <graph> x1 y1 z1 x_ppo1 y_ppo1 z_ppo1 x_ppo2 y_ppo2 z_ppo2 ... x_dest y_dest z_dest")
    print("✅ Optimal Check: python astar_PPO.py optimal_check <graph> x1 y1 z1 x_ppo1 y_ppo1 z_ppo1 x_ppo2 y_ppo2 z_ppo2 x_dest y_dest z_dest")
    print("")
    print("Ejemplos:")
    print("  # Directo:")
    print("  python astar_PPO.py graph_LVA1.json 145.475 28.926 145.041 122.331 10.427 161.623")
    print("  # 1 PPO:")
    print("  python astar_PPO.py graph_LVA1.json 145.475 28.926 145.041 140.0 25.0 150.0 122.331 10.427 161.623")
    print("  # 2 PPOs:")
    print("  python astar_PPO.py graph_LVA1.json 145.475 28.926 145.041 140.0 25.0 150.0 135.0 27.0 145.0 122.331 10.427 161.623")
    print("  # 3 PPOs:")
    print("  python astar_PPO.py graph_LVA1.json 145.475 28.926 145.041 140.0 25.0 150.0 135.0 27.0 145.0 130.0 20.0 155.0 122.331 10.427 161.623")
    print("  # Optimal Check (compara 2 órdenes de PPOs):")
    print("  python astar_PPO.py optimal_check graph_LVA1.json 152.290 17.883 160.124 143.382 25.145 160.703 139.608 25.145 160.703 139.232 28.845 139.993")

def run_optimal_check(graph_path, origin, ppo1, ppo2, destination):
    """
    Compare two different PPO orderings to find the optimal path.
    
    Order 1: origin → PPO_1 → PPO_2 → destination
    Order 2: origin → PPO_2 → PPO_1 → destination
    
    Args:
        graph_path (str): Path to the graph JSON file
        origin (tuple): Origin coordinates (x, y, z)
        ppo1 (tuple): First PPO coordinates (x, y, z)
        ppo2 (tuple): Second PPO coordinates (x, y, z)
        destination (tuple): Destination coordinates (x, y, z)
        
    Returns:
        dict: Comparison results with both paths and optimal choice
    """
    print(f"🔍 Optimal Check: Comparing PPO orderings")
    print(f"Order 1: Origin → PPO_1 → PPO_2 → Destination")
    print(f"Order 2: Origin → PPO_2 → PPO_1 → Destination")
    print()
    
    # Order 1: PPO_1 → PPO_2
    print("📊 Testing Order 1: Origin → PPO_1 → PPO_2 → Destination")
    try:
        path1, nodes1, segments1 = run_astar_with_multiple_ppos(graph_path, origin, [ppo1, ppo2], destination)
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
        path2, nodes2, segments2 = run_astar_with_multiple_ppos(graph_path, origin, [ppo2, ppo1], destination)
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
    print("OPTIMAL CHECK RESULTS")
    print("="*60)
    
    if not order1_success and not order2_success:
        optimal_order = None
        improvement = 0.0
        print("❌ Both orders failed - no valid path found")
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

if __name__ == "__main__":
    # Check for optimal_check command
    if len(sys.argv) >= 2 and sys.argv[1] == "optimal_check":
        # optimal_check mode: optimal_check graph_file origin(3) ppo1(3) ppo2(3) destination(3) = 15 total
        if len(sys.argv) != 15:
            print("❌ Error: optimal_check requiere exactamente 12 coordenadas (origen + 2 PPOs + destino)")
            print("Uso: python astar_PPO.py optimal_check <graph> x1 y1 z1 x_ppo1 y_ppo1 z_ppo1 x_ppo2 y_ppo2 z_ppo2 x_dest y_dest z_dest")
            sys.exit(1)
        
        graph_file = sys.argv[2]
        origin = tuple(map(float, sys.argv[3:6]))
        ppo1 = tuple(map(float, sys.argv[6:9]))
        ppo2 = tuple(map(float, sys.argv[9:12]))
        destination = tuple(map(float, sys.argv[12:15]))
        
        print(f"🚀 A* Optimal Check - PPO Order Comparison")
        print(f"Graph: {graph_file}")
        print(f"Origin: {format_point(origin)}")
        print(f"PPO_1: {format_point(ppo1)}")
        print(f"PPO_2: {format_point(ppo2)}")
        print(f"Destination: {format_point(destination)}")
        print()
        
        try:
            results = run_optimal_check(graph_file, origin, ppo1, ppo2, destination)
            
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
    if len(sys.argv) < 8:
        print_usage()
        sys.exit(1)
    
    # Check that we have proper coordinate triplets (total args - 2) must be divisible by 3
    total_coords = len(sys.argv) - 2  # Subtract script name and graph file
    if total_coords % 3 != 0:
        print("❌ Error: Las coordenadas deben ser en grupos de 3 (x, y, z)")
        print_usage()
        sys.exit(1)

    graph_file = sys.argv[1]
    
    # Parse all coordinates in groups of 3
    coords = []
    for i in range(2, len(sys.argv), 3):
        if i + 2 < len(sys.argv):
            coord = tuple(map(float, sys.argv[i:i+3]))
            coords.append(coord)
    
    # Need at least origin and destination
    if len(coords) < 2:
        print("❌ Error: Se necesitan al menos origen y destino")
        print_usage()
        sys.exit(1)
    
    origin = coords[0]
    destination = coords[-1]
    ppos = coords[1:-1]  # All coordinates between origin and destination are PPOs

    print(f"🚀 A* Pathfinding with Multiple PPOs and Edge Splitting")
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
            full_path, nodes_explored = run_astar(graph_file, origin, destination)
            segment_info = [{'segment': 1, 'start': origin, 'end': destination, 
                           'path_length': len(full_path), 'nodes_explored': nodes_explored}]
        else:
            # Multi-PPO pathfinding
            full_path, nodes_explored, segment_info = run_astar_with_multiple_ppos(
                graph_file, origin, ppos, destination)
        
        print(f"\n✅ Camino completo con {len(ppos)} PPO(s):")
        print(f"Total points: {len(full_path)}")
        print(f"Total nodes explored: {nodes_explored}")
        print(f"Edge splitting: Enabled (exact PPO coordinates on edges allowed)")
        
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