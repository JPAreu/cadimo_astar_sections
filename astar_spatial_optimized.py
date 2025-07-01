import json
import numpy as np
import networkx as nx
from math import sqrt
from typing import Dict, List, Tuple, Optional, Set, NamedTuple
import sys
from collections import defaultdict
import heapq
import array

class MatchResult(NamedTuple):
    """
    Result of a coordinate matching operation with tolerance assessment.
    
    Attributes:
        matched_node: The closest node found in the graph
        distance: Distance from query point to matched node
        within_tolerance: Whether the match is within acceptable tolerance
        quality: Quality rating of the match ('EXCELLENT', 'VERY_GOOD', 'GOOD', 'POOR')
    """
    matched_node: Optional[Tuple[float, float, float]]
    distance: float
    within_tolerance: bool
    quality: str

class OptimizedSpatialGraph3D:
    def __init__(self, graph_json_path: str, grid_size: float = 1.0, tolerance: float = 1.0):
        """
        Initialize the 3D spatial graph with grid-based indexing and tolerance system.
        
        The graph uses spatial partitioning for efficient neighbor lookup and includes
        tolerance-based coordinate matching for real-world precision requirements.
        
        Args:
            graph_json_path (str): Path to the JSON file containing the graph structure
            grid_size (float): Size of grid cells for spatial partitioning (default: 1.0)
            tolerance (float): Maximum distance for coordinate matching (default: 1.0)
        """
        # Core graph data structures
        self.graph_data = None
        self.graph = nx.Graph()  # Use undirected graph for bidirectional pathfinding
        self.grid_index = {}  # Maps grid cell coordinates to lists of nodes
        
        # Configuration parameters
        self.grid_size = grid_size
        self.tolerance = tolerance
        
        # Performance tracking
        self.nodes_explored = 0  # Counter for explored nodes during pathfinding
        
        # Pre-allocate optimization structures for faster access
        self._neighboring_offsets = self._precompute_neighbor_offsets()
        self._cell_cache = {}  # Cache for grid cell calculations
        self._distance_cache = {}  # Cache for Euclidean distance calculations
        self._point_array = None  # NumPy array of all points for vectorized operations
        
        # Initialize the complete graph system
        self._initialize_graph_system(graph_json_path)
        
    def _initialize_graph_system(self, graph_json_path: str) -> None:
        """
        Initialize the complete graph system including loading, building, and indexing.
        
        Args:
            graph_json_path (str): Path to the graph JSON file
        """
        print(f"Initializing spatial graph with tolerance: {self.tolerance} units")
        self.load_graph(graph_json_path)
        self.build_graph()
        self.build_spatial_index()
        self.analyze_grid_structure()
        
    def _precompute_neighbor_offsets(self):
        """Pre-compute the offsets for neighboring cells."""
        offsets = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                for dz in [-1, 0, 1]:
                    if dx == 0 and dy == 0 and dz == 0:
                        continue
                    offsets.append((dx, dy, dz))
        return tuple(offsets)  # Make immutable for faster lookup
        
    def load_graph(self, json_path: str) -> None:
        """Load graph from JSON file."""
        try:
            with open(json_path, 'r') as file:
                json_data = json.load(file)
            
            # Convert string keys to tuples and list values to tuples
            self.graph_data = {}
            for key, value in json_data.items():
                # Remove parentheses and convert to tuple of floats
                key = tuple(float(coord) for coord in key.strip('()').split(', '))
                # Convert each neighbor (which is a list) to a tuple
                neighbors = [tuple(float(c) for c in coord) for coord in value]
                self.graph_data[key] = neighbors
                
        except Exception as e:
            print(f"Error loading graph from JSON: {e}")
            sys.exit(1)
    
    def build_graph(self) -> None:
        """
        Build NetworkX undirected graph with nodes and weighted edges.
        
        Uses undirected graph to allow bidirectional traversal, which is essential
        for pathfinding in spatial networks where movement should be possible
        in both directions along connections.
        """
        # Store all points in a numpy array for faster access
        self._point_array = np.array(list(self.graph_data.keys()))
        
        # Add nodes
        for point in self.graph_data.keys():
            self.graph.add_node(point, pos=point)
        
        # Add undirected edges with weights
        # Note: NetworkX.Graph automatically handles bidirectionality
        edge_count = 0
        for source, targets in self.graph_data.items():
            for target in targets:
                if not self.graph.has_edge(source, target):  # Avoid duplicate edges
                    weight = self.euclidean_distance(source, target)
                    self.graph.add_edge(source, target, weight=weight)
                    edge_count += 1
                    
        print(f"Built undirected graph with {len(self.graph.nodes)} nodes and {edge_count} unique edges")
    
    def get_grid_cell(self, point: Tuple[float, float, float]) -> Tuple[int, int, int]:
        """Convert a point to its grid cell coordinates with caching."""
        # Check cache first
        if point in self._cell_cache:
            return self._cell_cache[point]
        
        # Calculate and cache result
        cell = (int(point[0] // self.grid_size), 
                int(point[1] // self.grid_size), 
                int(point[2] // self.grid_size))
        self._cell_cache[point] = cell
        return cell
    
    def build_spatial_index(self) -> None:
        """Build spatial index using grid cells."""
        # Use defaultdict to avoid unnecessary if checks
        grid_index = defaultdict(list)
        
        for point in self.graph_data.keys():
            cell = self.get_grid_cell(point)
            grid_index[cell].append(point)
            
        # Convert back to regular dict for faster lookups
        self.grid_index = dict(grid_index)
    
    def get_neighboring_cells(self, cell: Tuple[int, int, int]) -> List[Tuple[int, int, int]]:
        """Get neighboring grid cells (including diagonals) using pre-computed offsets."""
        return [(cell[0] + dx, cell[1] + dy, cell[2] + dz) 
                for dx, dy, dz in self._neighboring_offsets]
    
    def assess_match_quality(self, distance: float) -> str:
        """
        Assess the quality of a coordinate match based on distance.
        
        Quality levels based on distance thresholds:
        - EXCELLENT: ≤ 0.1 units (essentially exact match)
        - VERY_GOOD: ≤ 0.5 units (very close match)
        - GOOD: ≤ 1.0 units (acceptable match within standard tolerance)
        - POOR: > 1.0 units (outside standard tolerance)
        
        Args:
            distance (float): Distance between query point and matched node
            
        Returns:
            str: Quality assessment string
        """
        if distance <= 0.1:
            return "EXCELLENT"
        elif distance <= 0.5:
            return "VERY_GOOD"
        elif distance <= 1.0:
            return "GOOD"
        else:
            return "POOR"
    
    def find_nearest_node_with_tolerance(self, query_point: Tuple[float, float, float]) -> MatchResult:
        """
        Find nearest node to query point with tolerance-based matching and quality assessment.
        
        This enhanced version includes tolerance checking and quality assessment
        for practical coordinate matching scenarios where exact matches are rare.
        
        Args:
            query_point (Tuple[float, float, float]): The 3D coordinate to find nearest node for
            
        Returns:
            MatchResult: Contains match details, distance, tolerance status, and quality
        """
        cell = self.get_grid_cell(query_point)
        
        nearest_node = None
        min_distance = float('inf')
        
        # Search current grid cell first for efficiency
        if cell in self.grid_index:
            for node in self.grid_index[cell]:
                dist = self.euclidean_distance(query_point, node)
                if dist < min_distance:
                    min_distance = dist
                    nearest_node = node
                    
            # Early termination for very close matches (optimization)
            if nearest_node is not None and min_distance < self.grid_size * 0.5:
                quality = self.assess_match_quality(min_distance)
                within_tolerance = min_distance <= self.tolerance
                return MatchResult(nearest_node, min_distance, within_tolerance, quality)
        
        # Expand search to neighboring cells if needed
        for neighbor_cell in self.get_neighboring_cells(cell):
            if neighbor_cell in self.grid_index:
                for node in self.grid_index[neighbor_cell]:
                    dist = self.euclidean_distance(query_point, node)
                    if dist < min_distance:
                        min_distance = dist
                        nearest_node = node
        
        # Prepare comprehensive match result
        if nearest_node is not None:
            quality = self.assess_match_quality(min_distance)
            within_tolerance = min_distance <= self.tolerance
            return MatchResult(nearest_node, min_distance, within_tolerance, quality)
        else:
            return MatchResult(None, float('inf'), False, "NOT_FOUND")
    
    def find_nearest_node(self, query_point: Tuple[float, float, float]) -> Optional[Tuple[Tuple[float, float, float], float]]:
        """
        Legacy nearest node finder for backward compatibility.
        
        Args:
            query_point: The point to find nearest node for
            
        Returns:
            Tuple of (nearest_node, distance) or None if no node found
        """
        result = self.find_nearest_node_with_tolerance(query_point)
        if result.matched_node is not None:
            return (result.matched_node, result.distance)
        return None
    
    def euclidean_distance(self, point1: Tuple[float, float, float], 
                          point2: Tuple[float, float, float]) -> float:
        """Calculate Euclidean distance between two 3D points with caching."""
        # Create cache key (use frozenset to make it order-independent)
        key = (point1, point2) if point1 < point2 else (point2, point1)
        
        # Check cache
        if key in self._distance_cache:
            return self._distance_cache[key]
        
        # Calculate the distance (use sum of squares which is faster than sqrt for comparison)
        distance = sqrt(sum((a - b) ** 2 for a, b in zip(point1, point2)))
        
        # Cache the result
        self._distance_cache[key] = distance
        return distance
    
    def astar_path_with_visited(self, start_node: Tuple[float, float, float], 
                              goal_node: Tuple[float, float, float]) -> Tuple[List[Tuple[float, float, float]], int]:
        """
        Optimized A* implementation that tracks visited nodes.
        
        Args:
            start_node: Starting node coordinates
            goal_node: Goal node coordinates
            
        Returns:
            Tuple of (path, number of nodes visited)
        """
        if start_node not in self.graph or goal_node not in self.graph:
            return None, 0
        
        # Precompute distance to goal for better heuristic
        goal_cell = self.get_grid_cell(goal_node)
            
        # Use a set for visited nodes (faster membership checks)
        visited = set()
        
        # Initialize priority queue with start node
        queue = [(self.euclidean_distance(start_node, goal_node), 0, start_node, [start_node])]
        heapq.heapify(queue)
        
        # Use dictionaries for g_scores and f_scores
        g_scores = {start_node: 0}
        
        # Process until queue is empty
        while queue:
            _, current_g, current, path = heapq.heappop(queue)
            
            # Found goal
            if current == goal_node:
                return path, len(visited)
                
            # Skip already visited nodes
            if current in visited:
                continue
                
            # Mark as visited
            visited.add(current)
            
            # Get neighbors from graph adjacency list (faster than iterating)
            for neighbor in self.graph[current]:
                if neighbor in visited:
                    continue
                    
                # Calculate tentative g score
                tentative_g = current_g + self.euclidean_distance(current, neighbor)
                
                # Only process if we found a better path
                if neighbor not in g_scores or tentative_g < g_scores[neighbor]:
                    g_scores[neighbor] = tentative_g
                    
                    # Calculate f_score using straight-line distance (simpler and faster)
                    f_score = tentative_g + self.euclidean_distance(neighbor, goal_node)
                    
                    # Create new path
                    new_path = path + [neighbor]
                    
                    # Add to queue
                    heapq.heappush(queue, (f_score, tentative_g, neighbor, new_path))
        
        # No path found
        return None, len(visited)

    def find_path_with_tolerance(self, start_point: Tuple[float, float, float], 
                               goal_point: Tuple[float, float, float]) -> Tuple[Optional[List[Tuple[float, float, float]]], Dict]:
        """
        Find path between two points using tolerance-based coordinate matching.
        
        This enhanced pathfinding method includes:
        - Tolerance-based coordinate matching for real-world precision
        - Quality assessment for both start and goal points
        - Detailed matching information for debugging and validation
        
        Args:
            start_point (Tuple[float, float, float]): Starting coordinates (may not be exact graph nodes)
            goal_point (Tuple[float, float, float]): Goal coordinates (may not be exact graph nodes)
            
        Returns:
            Tuple[Optional[List], Dict]: (path_list, match_info_dict)
            - path_list: List of coordinates forming the path, or None if no path exists
            - match_info_dict: Details about coordinate matching quality and status
        """
        # Reset performance counters
        self.nodes_explored = 0
        
        # Find nearest graph nodes with tolerance checking
        start_match = self.find_nearest_node_with_tolerance(start_point)
        goal_match = self.find_nearest_node_with_tolerance(goal_point)
        
        # Prepare comprehensive match information for analysis
        match_info = {
            'start_query': start_point,
            'goal_query': goal_point,
            'start_match': start_match,
            'goal_match': goal_match,
            'start_usable': start_match.within_tolerance,
            'goal_usable': goal_match.within_tolerance,
            'both_usable': start_match.within_tolerance and goal_match.within_tolerance,
            'tolerance_used': self.tolerance
        }
        
        # Check if start point has acceptable match
        if not start_match.within_tolerance:
            print(f"Start point {format_point(start_point)} has no acceptable match within tolerance {self.tolerance}")
            if start_match.matched_node:
                print(f"Closest match: {format_point(start_match.matched_node)} at distance {start_match.distance:.3f} (Quality: {start_match.quality})")
            return None, match_info
            
        # Check if goal point has acceptable match
        if not goal_match.within_tolerance:
            print(f"Goal point {format_point(goal_point)} has no acceptable match within tolerance {self.tolerance}")
            if goal_match.matched_node:
                print(f"Closest match: {format_point(goal_match.matched_node)} at distance {goal_match.distance:.3f} (Quality: {goal_match.quality})")
            return None, match_info
        
        # Report successful matches with quality assessment
        print(f"Start point match: {format_point(start_match.matched_node)} (distance: {start_match.distance:.3f}, quality: {start_match.quality})")
        print(f"Goal point match: {format_point(goal_match.matched_node)} (distance: {goal_match.distance:.3f}, quality: {goal_match.quality})")
        
        # Execute A* pathfinding between matched nodes
        path, nodes_visited = self.astar_path_with_visited(start_match.matched_node, goal_match.matched_node)
        self.nodes_explored = nodes_visited
        
        if path is None:
            print("No path found between matched start and goal nodes.")
            
        return path, match_info

    def find_path(self, start_point: Tuple[float, float, float], 
                  goal_point: Tuple[float, float, float]) -> Optional[List[Tuple[float, float, float]]]:
        """
        Legacy pathfinding method for backward compatibility.
        
        Uses the enhanced tolerance-based pathfinding internally but returns
        only the path for compatibility with existing code.
        
        Args:
            start_point: Starting coordinates
            goal_point: Goal coordinates
            
        Returns:
            List of coordinates forming the path, or None if no path exists
        """
        path, _ = self.find_path_with_tolerance(start_point, goal_point)
        return path

    def analyze_grid_structure(self) -> None:
        """Analyze the structure of the spatial grid."""
        # Count points per cell
        points_per_cell = {cell: len(points) for cell, points in self.grid_index.items()}
        
        # Get grid dimensions
        x_coords = [cell[0] for cell in self.grid_index.keys()]
        y_coords = [cell[1] for cell in self.grid_index.keys()]
        z_coords = [cell[2] for cell in self.grid_index.keys()]
        
        grid_dims = {
            'x': (min(x_coords), max(x_coords)),
            'y': (min(y_coords), max(y_coords)),
            'z': (min(z_coords), max(z_coords))
        }
        
        # Analyze point distribution
        cell_counts = defaultdict(int)
        for count in points_per_cell.values():
            cell_counts[count] += 1
        
        print("\nGrid Analysis:")
        print(f"Grid size: {self.grid_size}")
        print(f"Total cells: {len(self.grid_index)}")
        print(f"Total points: {sum(len(points) for points in self.grid_index.values())}")
        
        print("\nGrid dimensions:")
        for dim, (min_val, max_val) in grid_dims.items():
            print(f"{dim}: [{min_val}, {max_val}] ({max_val - min_val + 1} cells)")
        
        print("\nPoints per cell distribution:")
        for count in sorted(cell_counts.keys()):
            print(f"{count} point(s): {cell_counts[count]} cell(s)")


def format_point(point: Tuple[float, float, float]) -> str:
    """Format a point nicely for printing."""
    return f"({point[0]:.3f}, {point[1]:.3f}, {point[2]:.3f})"

def print_path_info(path: List[Tuple[float, float, float]], nodes_explored: int) -> None:
    """Print detailed information about the path."""
    if not path:
        print("No path found.")
        return
    
    print("\n" + "="*50)
    print(f"RESULT SUMMARY:")
    print(f"Total path length: {len(path)} points")
    print(f"NODES EXPLORED: {nodes_explored}")
    print("="*50)
    
    total_distance = 0
    
    for i, point in enumerate(path):
        print(f"{i+1}. {format_point(point)}")
        
        if i > 0:
            prev_point = path[i-1]
            segment_distance = sqrt(sum((a - b) ** 2 for a, b in zip(prev_point, point)))
            total_distance += segment_distance
            print(f"   Distance from previous point: {segment_distance:.3f}")
    
    print("\nTotal path distance: {:.3f}".format(total_distance))
    print("="*50)
    print(f"NODES EXPLORED: {nodes_explored}")
    print("="*50)

def run_tests():
    """
    Automatically run all tests in the test_astar_spatial_optimized folder.
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    import subprocess
    import os
    import sys
    
    test_folder = "tests"
    
    # Check if test folder exists
    if not os.path.exists(test_folder):
        print(f"⚠️  Test folder '{test_folder}' not found. Skipping tests.")
        return True
    
    print("🧪 Running A* Spatial Optimized Tests...")
    print("=" * 50)
    
    # Find all test files in the test folder
    test_files = []
    for file in os.listdir(test_folder):
        if file.startswith("test_") and file.endswith(".py"):
            test_files.append(os.path.join(test_folder, file))
    
    if not test_files:
        print(f"⚠️  No test files found in '{test_folder}'. Skipping tests.")
        return True
    
    all_tests_passed = True
    
    for test_file in sorted(test_files):
        print(f"\n🔍 Running {os.path.basename(test_file)}...")
        try:
            # Run the test file
            result = subprocess.run([sys.executable, test_file], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                print(f"✅ {os.path.basename(test_file)} - PASSED")
                # Print test output for visibility
                if result.stdout:
                    print(result.stdout)
            else:
                print(f"❌ {os.path.basename(test_file)} - FAILED")
                all_tests_passed = False
                if result.stderr:
                    print("STDERR:", result.stderr)
                if result.stdout:
                    print("STDOUT:", result.stdout)
                    
        except Exception as e:
            print(f"❌ Error running {os.path.basename(test_file)}: {e}")
            all_tests_passed = False
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("✅ ALL TESTS PASSED - Algorithm is robust and ready!")
    else:
        print("❌ SOME TESTS FAILED - Please check test results above.")
    print("=" * 50)
    
    return all_tests_passed

def main():
    """
    Main entry point for command-line usage of the enhanced pathfinding algorithm.
    
    Automatically runs tests before executing pathfinding to ensure algorithm robustness.
    Supports both legacy mode (7 arguments) and enhanced mode with tolerance (8+ arguments).
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Enhanced A* pathfinding with tolerance-based coordinate matching",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with automatic testing (default)
  python3 astar_spatial_optimized.py graph.json 152.3 17.9 160.1 139.2 28.2 140.0
  
  # Custom tolerance with testing
  python3 astar_spatial_optimized.py graph.json 152.3 17.9 160.1 139.2 28.2 140.0 --tolerance 0.5
  
  # Skip tests for production use
  python3 astar_spatial_optimized.py graph.json 152.3 17.9 160.1 139.2 28.2 140.0 --skip-tests
  
  # Strict tolerance for exact matches only
  python3 astar_spatial_optimized.py graph.json 152.3 17.9 160.1 139.2 28.2 140.0 --tolerance 0.01

Note: Tests are automatically run by default to ensure algorithm robustness.
      Use --skip-tests to disable for production environments.
        """
    )
    
    parser.add_argument('graph_file', help='JSON graph file path')
    parser.add_argument('start_x', type=float, help='Start X coordinate')
    parser.add_argument('start_y', type=float, help='Start Y coordinate')
    parser.add_argument('start_z', type=float, help='Start Z coordinate')
    parser.add_argument('goal_x', type=float, help='Goal X coordinate')
    parser.add_argument('goal_y', type=float, help='Goal Y coordinate')
    parser.add_argument('goal_z', type=float, help='Goal Z coordinate')
    parser.add_argument('--tolerance', type=float, default=1.0,
                        help='Tolerance for coordinate matching (default: 1.0 units)')
    parser.add_argument('--grid-size', type=float, default=1.0,
                        help='Grid cell size for spatial indexing (default: 1.0)')
    parser.add_argument('--skip-tests', action='store_true',
                        help='Skip automatic test execution (for production use)')
    
    args = parser.parse_args()
    
    # Run tests first to ensure algorithm robustness (unless skipped)
    if not args.skip_tests:
        print("🚀 A* Spatial Pathfinding with Automatic Testing")
        print("=" * 55)
        
        tests_passed = run_tests()
        
        if not tests_passed:
            print("\n⚠️  WARNING: Some tests failed. Algorithm may not be reliable.")
            print("   Consider fixing test failures before using in production.")
            response = input("\nContinue anyway? (y/N): ").lower().strip()
            if response != 'y':
                print("Exiting due to test failures.")
                return
        
        print(f"\n🎯 Starting Pathfinding Operation")
        print("=" * 55)
    else:
        print("🚀 A* Spatial Pathfinding (Tests Skipped)")
        print("=" * 45)
    
    # Parse coordinates
    start_point = (args.start_x, args.start_y, args.start_z)
    goal_point = (args.goal_x, args.goal_y, args.goal_z)
    
    # Display configuration
    print(f"Enhanced A* Pathfinding Algorithm")
    print(f"Graph file: {args.graph_file}")
    print(f"Tolerance: {args.tolerance} units")
    print(f"Grid size: {args.grid_size} units")
    
    # Initialize enhanced graph with tolerance
    graph = OptimizedSpatialGraph3D(args.graph_file, 
                                   grid_size=args.grid_size,
                                   tolerance=args.tolerance)
    
    # Execute pathfinding with tolerance
    print(f"\nSearching for path:")
    print(f"  Start: {format_point(start_point)}")
    print(f"  Goal:  {format_point(goal_point)}")
    
    path, match_info = graph.find_path_with_tolerance(start_point, goal_point)
    
    # Display results
    print_path_info(path, graph.nodes_explored)
    
    # Display matching information and recommendations
    if not match_info['both_usable']:
        print(f"\n" + "="*50)
        print("COORDINATE MATCHING ISSUES")
        print("="*50)
        if not match_info['start_usable']:
            start_match = match_info['start_match']
            print(f"Start point: Distance {start_match.distance:.3f} > tolerance {args.tolerance}")
            print(f"  Quality: {start_match.quality}")
        if not match_info['goal_usable']:
            goal_match = match_info['goal_match']
            print(f"Goal point: Distance {goal_match.distance:.3f} > tolerance {args.tolerance}")
            print(f"  Quality: {goal_match.quality}")
        
        # Provide recommendations
        max_distance = max(match_info['start_match'].distance, match_info['goal_match'].distance)
        recommended_tolerance = max(1.0, round(max_distance * 1.1, 1))
        print(f"\nRecommendations:")
        print(f"  1. Increase tolerance to {recommended_tolerance} units")
        print(f"  2. Use coordinates closer to existing graph nodes")
        print(f"  3. Check if your coordinates are in the correct coordinate system")
        print("="*50)

if __name__ == "__main__":
    main() 
    