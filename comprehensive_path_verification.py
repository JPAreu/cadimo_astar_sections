#!/usr/bin/env python3
"""
Comprehensive path verification for forward path algorithm
"""

from astar_PPOF_systems import SystemFilteredGraph

def analyze_forward_path():
    """Analyze the forward path in detail"""
    
    print("🔍 Comprehensive Forward Path Analysis")
    print("=" * 50)
    
    # Run the algorithm
    graph = SystemFilteredGraph("graph_LV_combined.json", "A", "tramo_map_combined.json", None)
    
    origin = (170.839, 12.530, 156.634)  # A1
    ppo = (196.310, 18.545, 153.799)     # A5
    destination = (182.946, 13.304, 157.295)  # A2
    
    path, nodes_explored, segment_info = graph.find_path_forward_path(origin, ppo, destination)
    
    print(f"📊 Path Results:")
    print(f"   Total points: {len(path)}")
    print(f"   Total distance: {sum(((path[i+1][0]-path[i][0])**2 + (path[i+1][1]-path[i][1])**2 + (path[i+1][2]-path[i][2])**2)**0.5 for i in range(len(path)-1)):.3f} units")
    print(f"   Nodes explored: {nodes_explored}")
    
    # Analyze waypoint occurrences
    waypoints = {
        'A1': origin,
        'A5': ppo, 
        'A2': destination
    }
    
    tolerance = 0.1
    occurrences = {name: [] for name in waypoints.keys()}
    
    for i, point in enumerate(path):
        for name, waypoint in waypoints.items():
            distance = ((point[0] - waypoint[0])**2 + 
                       (point[1] - waypoint[1])**2 + 
                       (point[2] - waypoint[2])**2)**0.5
            if distance <= tolerance:
                occurrences[name].append(i)
    
    print(f"\n🎯 Waypoint Occurrences:")
    for name, indices in occurrences.items():
        print(f"   {name}: {len(indices)} times at indices {indices}")
    
    # Analyze segments
    print(f"\n📏 Segment Analysis:")
    seg1_length = segment_info[0]['path_length']
    seg2_length = segment_info[1]['path_length']
    
    print(f"   Segment 1: Points 0-{seg1_length-1} ({seg1_length} points)")
    print(f"   Segment 2: Points {seg1_length-1}-{len(path)-1} ({seg2_length} points)")
    
    # Check segment 1 waypoints
    seg1_waypoints = {}
    for i in range(seg1_length):
        point = path[i]
        for name, waypoint in waypoints.items():
            distance = ((point[0] - waypoint[0])**2 + 
                       (point[1] - waypoint[1])**2 + 
                       (point[2] - waypoint[2])**2)**0.5
            if distance <= tolerance:
                if name not in seg1_waypoints:
                    seg1_waypoints[name] = []
                seg1_waypoints[name].append(i)
    
    print(f"   Segment 1 waypoints: {seg1_waypoints}")
        
    # Check segment 2 waypoints
    seg2_waypoints = {}
    for i in range(seg1_length-1, len(path)):
        point = path[i]
        for name, waypoint in waypoints.items():
            distance = ((point[0] - waypoint[0])**2 + 
                       (point[1] - waypoint[1])**2 + 
                       (point[2] - waypoint[2])**2)**0.5
            if distance <= tolerance:
                if name not in seg2_waypoints:
                    seg2_waypoints[name] = []
                seg2_waypoints[name].append(i)
    
    print(f"   Segment 2 waypoints: {seg2_waypoints}")
    
    # Identify the problem
    print(f"\n🚨 Problem Analysis:")
    
    # Check if A2 appears in segment 1
    if 'A2' in seg1_waypoints:
        print(f"   ❌ PROBLEM: A2 appears in segment 1 at indices {seg1_waypoints['A2']}")
        print(f"      This means the shortest path A1→A5 passes through A2!")
        print(f"      When we then do A5→A2, we're going back to a point we already visited.")
    
    # Check if A1 appears in segment 2
    if 'A1' in seg2_waypoints:
        print(f"   ❌ PROBLEM: A1 appears in segment 2 at indices {seg2_waypoints['A1']}")
        print(f"      This means the path A5→A2 goes back to the origin!")
    
    # Show path sequence
    print(f"\n🛤️  Path Sequence:")
    key_points = []
    for i, point in enumerate(path):
        for name, waypoint in waypoints.items():
            distance = ((point[0] - waypoint[0])**2 + 
                       (point[1] - waypoint[1])**2 + 
                       (point[2] - waypoint[2])**2)**0.5
            if distance <= tolerance:
                key_points.append((i, name, point))
    
    for i, (index, name, point) in enumerate(key_points):
        segment = "Seg1" if index < seg1_length else "Seg2"
        print(f"   {i+1}. Index {index:3d} ({segment}): {name} at {point}")
    
    # Check the forbidden edge
    print(f"\n🚫 Forbidden Edge Analysis:")
    if len(path) >= 2:
        # The last edge of segment 1
        second_last = path[seg1_length-2]
        last = path[seg1_length-1]  # This should be A5
        print(f"   Last edge of segment 1: {second_last} → {last}")
        
        # Check if this edge appears in segment 2
        for i in range(seg1_length-1, len(path)-1):
            edge_start = path[i]
            edge_end = path[i+1]
            
            # Check if this is the forbidden edge (in either direction)
            if (abs(edge_start[0] - second_last[0]) < 0.001 and 
                abs(edge_start[1] - second_last[1]) < 0.001 and 
                abs(edge_start[2] - second_last[2]) < 0.001 and
                abs(edge_end[0] - last[0]) < 0.001 and 
                abs(edge_end[1] - last[1]) < 0.001 and 
                abs(edge_end[2] - last[2]) < 0.001):
                print(f"   ❌ FORBIDDEN EDGE USED: Index {i}→{i+1} in segment 2!")
                break
            elif (abs(edge_start[0] - last[0]) < 0.001 and 
                  abs(edge_start[1] - last[1]) < 0.001 and 
                  abs(edge_start[2] - last[2]) < 0.001 and
                  abs(edge_end[0] - second_last[0]) < 0.001 and 
                  abs(edge_end[1] - second_last[1]) < 0.001 and 
                  abs(edge_end[2] - second_last[2]) < 0.001):
                print(f"   ❌ FORBIDDEN EDGE USED (reverse): Index {i}→{i+1} in segment 2!")
                break
        else:
            print(f"   ✅ Forbidden edge not used in segment 2")
    
    return path, segment_info, occurrences

if __name__ == "__main__":
    analyze_forward_path()
