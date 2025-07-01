#!/usr/bin/env python3
"""
Unit tests for astar_PPO.py - A* pathfinding with PPO (Mandatory Waypoint) and edge splitting
Tests both direct pathfinding and PPO pathfinding with various scenarios including edge splitting.
"""

import unittest
import sys
import os
from math import sqrt
from typing import List, Tuple

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the functions we want to test
from astar_PPO import run_astar, run_astar_with_ppo, run_astar_with_multiple_ppos, run_optimal_check, format_point
from astar_spatial_IP import OptimizedSpatialGraph3D

class TestAstarPPO(unittest.TestCase):
    """Test suite for A* pathfinding with PPO and edge splitting functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before running tests."""
        cls.graph_file = "graph_LVA1.json"
        
        # Test coordinates based on known working examples
        cls.origin_p2 = (152.290, 17.883, 160.124)
        cls.ppo_p5 = (143.382, 25.145, 160.703)
        cls.destination_p1 = (139.232, 28.845, 139.993)
        
        # Additional test coordinates
        cls.origin_alt = (145.475, 28.926, 145.041)
        cls.destination_alt = (122.331, 10.427, 161.623)
        cls.ppo_existing_node = (140.183, 28.000, 149.385)  # Known existing node
        cls.ppo_edge_midpoint = (140.431, 28.0, 149.385)   # Midpoint between two nodes
        
        # Invalid coordinates (outside graph bounds or unreachable)
        cls.invalid_coord = (999.0, 999.0, 999.0)
        
        # Verify graph file exists
        if not os.path.exists(cls.graph_file):
            raise FileNotFoundError(f"Test graph file {cls.graph_file} not found")
            
        print(f"✅ Test setup complete - using graph: {cls.graph_file}")

    def setUp(self):
        """Set up before each test method."""
        self.graph = OptimizedSpatialGraph3D(self.graph_file)

    def calculate_path_distance(self, path: List[Tuple[float, float, float]]) -> float:
        """Calculate total distance of a path."""
        if not path or len(path) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(1, len(path)):
            dist = sqrt(sum((a - b) ** 2 for a, b in zip(path[i-1], path[i])))
            total_distance += dist
        return total_distance

    def test_direct_pathfinding_basic(self):
        """Test basic direct pathfinding without PPO."""
        print("🧪 Testing direct pathfinding (P2 → P1)...")
        
        path, nodes_explored = run_astar(self.graph_file, self.origin_p2, self.destination_p1)
        
        # Verify path exists and is valid
        self.assertIsNotNone(path, "Path should exist")
        self.assertGreater(len(path), 1, "Path should have multiple points")
        self.assertEqual(path[0], self.origin_p2, "Path should start at origin")
        self.assertEqual(path[-1], self.destination_p1, "Path should end at destination")
        self.assertGreater(nodes_explored, 0, "Should explore some nodes")
        
        # Verify path continuity (each step should be connected)
        for i in range(1, len(path)):
            distance = sqrt(sum((a - b) ** 2 for a, b in zip(path[i-1], path[i])))
            self.assertLess(distance, 10.0, f"Step {i} too large: {distance}")
        
        print(f"✅ Direct path: {len(path)} points, {nodes_explored} nodes explored")

    def test_direct_pathfinding_alternative(self):
        """Test direct pathfinding with alternative coordinates."""
        print("🧪 Testing direct pathfinding (alternative coordinates)...")
        
        path, nodes_explored = run_astar(self.graph_file, self.origin_alt, self.destination_alt)
        
        self.assertIsNotNone(path, "Path should exist")
        self.assertGreater(len(path), 1, "Path should have multiple points")
        self.assertEqual(path[0], self.origin_alt, "Path should start at origin")
        self.assertEqual(path[-1], self.destination_alt, "Path should end at destination")
        
        print(f"✅ Alternative direct path: {len(path)} points, {nodes_explored} nodes explored")

    def test_ppo_pathfinding_basic(self):
        """Test PPO pathfinding with mandatory waypoint."""
        print("🧪 Testing PPO pathfinding (P2 → P5 → P1)...")
        
        path, nodes_explored = run_astar_with_ppo(self.graph_file, 
                                                  self.origin_p2, 
                                                  self.ppo_p5, 
                                                  self.destination_p1)
        
        # Verify path exists and includes PPO
        self.assertIsNotNone(path, "PPO path should exist")
        self.assertGreater(len(path), 2, "PPO path should have multiple segments")
        self.assertEqual(path[0], self.origin_p2, "Path should start at origin")
        self.assertEqual(path[-1], self.destination_p1, "Path should end at destination")
        self.assertIn(self.ppo_p5, path, "Path should include PPO waypoint")
        
        # Find PPO position in path
        ppo_index = path.index(self.ppo_p5)
        self.assertGreater(ppo_index, 0, "PPO should not be at start")
        self.assertLess(ppo_index, len(path) - 1, "PPO should not be at end")
        
        print(f"✅ PPO path: {len(path)} points, PPO at position {ppo_index + 1}, {nodes_explored} nodes explored")

    def test_ppo_with_existing_node(self):
        """Test PPO pathfinding where PPO is an existing graph node."""
        print("🧪 Testing PPO with existing node...")
        
        path, nodes_explored = run_astar_with_ppo(self.graph_file,
                                                  self.origin_alt,
                                                  self.ppo_existing_node,
                                                  self.destination_alt)
        
        self.assertIsNotNone(path, "Path with existing node PPO should exist")
        self.assertIn(self.ppo_existing_node, path, "Path should include existing node PPO")
        
        print(f"✅ Existing node PPO path: {len(path)} points, {nodes_explored} nodes explored")

    def test_edge_splitting_functionality(self):
        """Test edge splitting with coordinates on edges."""
        print("🧪 Testing edge splitting functionality...")
        
        path, nodes_explored = run_astar_with_ppo(self.graph_file,
                                                  self.origin_alt,
                                                  self.ppo_edge_midpoint,
                                                  self.destination_alt)
        
        self.assertIsNotNone(path, "Edge splitting path should exist")
        self.assertIn(self.ppo_edge_midpoint, path, "Path should include edge midpoint PPO")
        
        # Compare with direct path to see if edge splitting added a node
        direct_path, _ = run_astar(self.graph_file, self.origin_alt, self.destination_alt)
        
        # Edge splitting might add one extra node
        self.assertGreaterEqual(len(path), len(direct_path), 
                               "Edge splitting path should have same or more nodes")
        
        print(f"✅ Edge splitting path: {len(path)} points vs direct {len(direct_path)} points")

    def test_path_optimality_comparison(self):
        """Compare direct path vs PPO path to verify PPO constraint is respected."""
        print("🧪 Testing path optimality comparison...")
        
        # Direct path
        direct_path, direct_nodes = run_astar(self.graph_file, self.origin_p2, self.destination_p1)
        direct_distance = self.calculate_path_distance(direct_path)
        
        # PPO path
        ppo_path, ppo_nodes = run_astar_with_ppo(self.graph_file,
                                                 self.origin_p2,
                                                 self.ppo_p5,
                                                 self.destination_p1)
        ppo_distance = self.calculate_path_distance(ppo_path)
        
        # PPO path should be longer or equal (constraint adds cost)
        self.assertGreaterEqual(ppo_distance, direct_distance * 0.9,  # Allow 10% tolerance
                               "PPO path should not be significantly shorter than direct path")
        
        # PPO path must include the mandatory waypoint
        self.assertIn(self.ppo_p5, ppo_path, "PPO path must include mandatory waypoint")
        
        print(f"✅ Direct: {direct_distance:.3f} units, PPO: {ppo_distance:.3f} units")

    def test_invalid_coordinates_handling(self):
        """Test handling of invalid or unreachable coordinates."""
        print("🧪 Testing invalid coordinates handling...")
        
        # Test with invalid origin
        with self.assertRaises(Exception):
            run_astar(self.graph_file, self.invalid_coord, self.destination_p1)
        
        # Test with invalid destination
        with self.assertRaises(Exception):
            run_astar(self.graph_file, self.origin_p2, self.invalid_coord)
        
        # Test with invalid PPO
        with self.assertRaises(Exception):
            run_astar_with_ppo(self.graph_file, 
                              self.origin_p2, 
                              self.invalid_coord, 
                              self.destination_p1)
        
        print("✅ Invalid coordinates properly rejected")

    def test_same_origin_destination(self):
        """Test pathfinding when origin and destination are the same."""
        print("🧪 Testing same origin and destination...")
        
        path, nodes_explored = run_astar(self.graph_file, self.origin_p2, self.origin_p2)
        
        # Should return a single-point path or handle gracefully
        self.assertIsNotNone(path, "Same point path should exist")
        self.assertEqual(len(path), 1, "Same point path should have one point")
        self.assertEqual(path[0], self.origin_p2, "Path should contain the point")
        
        print(f"✅ Same point path: {len(path)} points, {nodes_explored} nodes explored")

    def test_ppo_same_as_origin_or_destination(self):
        """Test PPO pathfinding when PPO is same as origin or destination."""
        print("🧪 Testing PPO same as origin/destination...")
        
        # PPO same as origin
        path1, nodes1 = run_astar_with_ppo(self.graph_file,
                                          self.origin_p2,
                                          self.origin_p2,  # PPO = origin
                                          self.destination_p1)
        
        self.assertIsNotNone(path1, "PPO=origin path should exist")
        
        # PPO same as destination
        path2, nodes2 = run_astar_with_ppo(self.graph_file,
                                          self.origin_p2,
                                          self.destination_p1,  # PPO = destination
                                          self.destination_p1)
        
        self.assertIsNotNone(path2, "PPO=destination path should exist")
        
        print(f"✅ PPO edge cases handled: origin-PPO {len(path1)} points, destination-PPO {len(path2)} points")

    def test_graph_initialization(self):
        """Test that graph initializes correctly with expected properties."""
        print("🧪 Testing graph initialization...")
        
        # Test graph properties
        self.assertIsNotNone(self.graph.graph_data, "Graph data should be loaded")
        self.assertGreater(len(self.graph.graph.nodes), 0, "Graph should have nodes")
        self.assertGreater(len(self.graph.graph.edges), 0, "Graph should have edges")
        self.assertIsNotNone(self.graph.grid_index, "Spatial index should be built")
        
        # Test tolerance setting
        self.assertEqual(self.graph.tolerance, 1.0, "Default tolerance should be 1.0")
        
        print(f"✅ Graph: {len(self.graph.graph.nodes)} nodes, {len(self.graph.graph.edges)} edges")

    def test_edge_split_detection(self):
        """Test that edge splitting is properly detected and executed."""
        print("🧪 Testing edge split detection...")
        
        # Test with coordinates that should trigger edge splitting
        test_graph = OptimizedSpatialGraph3D(self.graph_file)
        
        # Use edge splitting method directly
        path, nodes_explored = test_graph.find_path_with_edge_split(
            self.origin_alt, 
            self.ppo_edge_midpoint
        )
        
        self.assertIsNotNone(path, "Edge split path should exist")
        self.assertIn(self.ppo_edge_midpoint, path, "Path should include edge split point")
        
        print(f"✅ Edge split detection: {len(path)} points, {nodes_explored} nodes explored")

    def test_format_point_function(self):
        """Test the point formatting utility function."""
        print("🧪 Testing format_point function...")
        
        test_point = (123.456, 78.901, 234.567)
        formatted = format_point(test_point)
        
        self.assertIsInstance(formatted, str, "format_point should return string")
        self.assertIn("123.456", formatted, "Should contain x coordinate")
        self.assertIn("78.901", formatted, "Should contain y coordinate") 
        self.assertIn("234.567", formatted, "Should contain z coordinate")
        
        print(f"✅ Point formatting: {formatted}")

    def test_multiple_ppos_functionality(self):
        """Test multi-PPO pathfinding with multiple waypoints in sequence."""
        print("🧪 Testing multiple PPOs functionality...")
        
        # Test with 2 PPOs
        ppos_2 = [self.ppo_p5, (139.232, 28.845, 160.703)]
        path_2ppos, nodes_2ppos, segment_info_2 = run_astar_with_multiple_ppos(
            self.graph_file, self.origin_p2, ppos_2, self.destination_p1)
        
        self.assertIsNotNone(path_2ppos, "Multi-PPO path should exist")
        self.assertEqual(path_2ppos[0], self.origin_p2, "Path should start at origin")
        self.assertEqual(path_2ppos[-1], self.destination_p1, "Path should end at destination")
        
        # Verify all PPOs are in the path
        for ppo in ppos_2:
            self.assertIn(ppo, path_2ppos, f"Path should include PPO {ppo}")
        
        # Verify segment information
        self.assertEqual(len(segment_info_2), 3, "Should have 3 segments for 2 PPOs")
        
        print(f"✅ 2 PPOs: {len(path_2ppos)} points, {nodes_2ppos} nodes explored, {len(segment_info_2)} segments")
        
        # Test with 3 PPOs including edge splitting
        ppos_3 = [(147.156, 25.145, 160.703), (145.269, 25.145, 160.703), (143.382, 25.145, 160.703)]
        path_3ppos, nodes_3ppos, segment_info_3 = run_astar_with_multiple_ppos(
            self.graph_file, self.origin_p2, ppos_3, self.destination_p1)
        
        self.assertIsNotNone(path_3ppos, "3-PPO path should exist")
        self.assertEqual(len(segment_info_3), 4, "Should have 4 segments for 3 PPOs")
        
        # Verify PPO ordering in path
        ppo_indices = []
        for ppo in ppos_3:
            if ppo in path_3ppos:
                ppo_indices.append(path_3ppos.index(ppo))
        
        # PPO indices should be in ascending order (proper sequence)
        self.assertEqual(ppo_indices, sorted(ppo_indices), "PPOs should appear in correct order in path")
        
        print(f"✅ 3 PPOs: {len(path_3ppos)} points, {nodes_3ppos} nodes explored, {len(segment_info_3)} segments")
        
        # Test with empty PPOs (should behave like direct pathfinding)
        path_0ppos, nodes_0ppos, segment_info_0 = run_astar_with_multiple_ppos(
            self.graph_file, self.origin_p2, [], self.destination_p1)
        
        direct_path, direct_nodes = run_astar(self.graph_file, self.origin_p2, self.destination_p1)
        
        self.assertEqual(len(path_0ppos), len(direct_path), "Empty PPO list should equal direct path")
        self.assertEqual(path_0ppos, direct_path, "Empty PPO path should be identical to direct path")
        
        print(f"✅ 0 PPOs (direct): {len(path_0ppos)} points, {nodes_0ppos} nodes explored")

    def test_multiple_ppos_edge_cases(self):
        """Test edge cases for multi-PPO pathfinding."""
        print("🧪 Testing multiple PPOs edge cases...")
        
        # Test with single PPO (should work like run_astar_with_ppo)
        single_ppo = [self.ppo_p5]
        path_single, nodes_single, segment_info_single = run_astar_with_multiple_ppos(
            self.graph_file, self.origin_p2, single_ppo, self.destination_p1)
        
        # Compare with dedicated single PPO function
        path_dedicated, nodes_dedicated = run_astar_with_ppo(
            self.graph_file, self.origin_p2, self.ppo_p5, self.destination_p1)
        
        self.assertEqual(len(path_single), len(path_dedicated), "Single PPO should match dedicated function")
        self.assertEqual(len(segment_info_single), 2, "Single PPO should have 2 segments")
        
        print(f"✅ Single PPO via multi-PPO: {len(path_single)} points, {nodes_single} nodes explored")
        
        # Test with PPO same as origin
        origin_as_ppo = [self.origin_p2]
        path_origin_ppo, nodes_origin_ppo, segment_info_origin = run_astar_with_multiple_ppos(
            self.graph_file, self.origin_p2, origin_as_ppo, self.destination_p1)
        
        self.assertIsNotNone(path_origin_ppo, "PPO=origin should work")
        self.assertEqual(len(segment_info_origin), 2, "Origin PPO should have 2 segments")
        
        print(f"✅ PPO=origin: {len(path_origin_ppo)} points, {nodes_origin_ppo} nodes explored")

    def test_optimal_check_functionality(self):
        """Test optimal check functionality that compares PPO orderings."""
        print("🧪 Testing optimal check functionality...")
        
        # Test with coordinates that should show a clear difference
        ppo1 = (143.382, 25.145, 160.703)
        ppo2 = (139.608, 25.145, 160.703)
        
        results = run_optimal_check(self.graph_file, self.origin_p2, ppo1, ppo2, self.destination_p1)
        
        # Verify results structure
        self.assertIn('order1', results, "Results should contain order1")
        self.assertIn('order2', results, "Results should contain order2")
        self.assertIn('optimal_order', results, "Results should contain optimal_order")
        self.assertIn('improvement', results, "Results should contain improvement")
        self.assertIn('both_valid', results, "Results should contain both_valid")
        
        # Verify both orders succeeded
        self.assertTrue(results['order1']['success'], "Order 1 should succeed")
        self.assertTrue(results['order2']['success'], "Order 2 should succeed")
        self.assertTrue(results['both_valid'], "Both orders should be valid")
        
        # Verify order1 data
        order1 = results['order1']
        self.assertIsNotNone(order1['path'], "Order 1 should have a path")
        self.assertIsNotNone(order1['distance'], "Order 1 should have a distance")
        self.assertGreater(order1['points'], 0, "Order 1 should have points")
        self.assertGreater(order1['nodes_explored'], 0, "Order 1 should explore nodes")
        self.assertEqual(len(order1['segments']), 3, "Order 1 should have 3 segments")
        
        # Verify order2 data
        order2 = results['order2']
        self.assertIsNotNone(order2['path'], "Order 2 should have a path")
        self.assertIsNotNone(order2['distance'], "Order 2 should have a distance")
        self.assertGreater(order2['points'], 0, "Order 2 should have points")
        self.assertGreater(order2['nodes_explored'], 0, "Order 2 should explore nodes")
        self.assertEqual(len(order2['segments']), 3, "Order 2 should have 3 segments")
        
        # Verify sequence order
        expected_seq1 = [self.origin_p2, ppo1, ppo2, self.destination_p1]
        expected_seq2 = [self.origin_p2, ppo2, ppo1, self.destination_p1]
        self.assertEqual(order1['sequence'], expected_seq1, "Order 1 sequence should be correct")
        self.assertEqual(order2['sequence'], expected_seq2, "Order 2 sequence should be correct")
        
        # Verify optimal order determination
        self.assertIn(results['optimal_order'], [1, 2, "tie"], "Optimal order should be 1, 2, or tie")
        
        if results['optimal_order'] == 1:
            self.assertLessEqual(order1['distance'], order2['distance'], "Order 1 should be better or equal")
            print(f"✅ Order 1 optimal: {order1['distance']:.3f} vs {order2['distance']:.3f}")
        elif results['optimal_order'] == 2:
            self.assertLessEqual(order2['distance'], order1['distance'], "Order 2 should be better or equal")
            print(f"✅ Order 2 optimal: {order2['distance']:.3f} vs {order1['distance']:.3f}")
        else:  # tie
            self.assertAlmostEqual(order1['distance'], order2['distance'], places=6, msg="Tie should have equal distances")
            print(f"✅ Tie: both orders {order1['distance']:.3f} units")
        
        print(f"✅ Optimal check: Order 1 ({order1['points']} points, {order1['nodes_explored']} nodes) vs Order 2 ({order2['points']} points, {order2['nodes_explored']} nodes)")

    def test_optimal_check_edge_cases(self):
        """Test edge cases for optimal check functionality."""
        print("🧪 Testing optimal check edge cases...")
        
        # Test with same PPO coordinates (should be identical)
        ppo_same = (143.382, 25.145, 160.703)
        results_same = run_optimal_check(self.graph_file, self.origin_p2, ppo_same, ppo_same, self.destination_p1)
        
        self.assertTrue(results_same['both_valid'], "Same PPO test should be valid")
        self.assertEqual(results_same['optimal_order'], "tie", "Same PPOs should result in tie")
        self.assertEqual(results_same['improvement'], 0.0, "Same PPOs should have no improvement")
        
        # Verify both paths are identical
        self.assertEqual(results_same['order1']['distance'], results_same['order2']['distance'], 
                        "Same PPOs should have identical distances")
        
        print(f"✅ Same PPO test: tie with {results_same['order1']['distance']:.3f} units")
        
        # Test with PPO coordinates that create edge splitting
        ppo_edge1 = (145.269, 25.145, 160.703)  # Midpoint coordinate
        ppo_edge2 = (143.382, 25.145, 160.703)  # Existing node
        
        results_edge = run_optimal_check(self.graph_file, self.origin_p2, ppo_edge1, ppo_edge2, self.destination_p1)
        
        self.assertTrue(results_edge['both_valid'], "Edge splitting test should be valid")
        self.assertIn(results_edge['optimal_order'], [1, 2, "tie"], "Edge splitting should determine optimal order")
        
        print(f"✅ Edge splitting test: optimal order {results_edge['optimal_order']}")

def run_test_suite():
    """Run the complete test suite with detailed reporting."""
    print("🚀 A* PPO Algorithm Test Suite")
    print("=" * 60)
    print("Testing A* pathfinding with PPO (Mandatory Waypoint) and edge splitting")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAstarPPO)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if result.wasSuccessful():
        print(f"✅ ALL {result.testsRun} TESTS PASSED!")
        print("🎯 A* PPO algorithm with edge splitting is working correctly")
    else:
        print(f"❌ {len(result.failures)} FAILURES, {len(result.errors)} ERRORS")
        print("⚠️  Algorithm needs attention")
        
        if result.failures:
            print("\nFAILURES:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback}")
                
        if result.errors:
            print("\nERRORS:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback}")
    
    print("=" * 60)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1) 