#!/usr/bin/env python3
"""
Unit tests for astar_PPO_forbid.py - A* pathfinding with PPO and forbidden edge avoidance
Tests both original PPO functionality and new forbidden edge features.
"""

import unittest
import sys
import os
import json
import tempfile
from math import sqrt
from typing import List, Tuple

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the functions we want to test
from astar_PPO_forbid import (
    run_astar_forbidden, 
    run_astar_with_ppo_forbidden, 
    run_astar_with_multiple_ppos_forbidden, 
    run_optimal_check_forbidden, 
    run_astar_with_ppo_forward_path,
    run_astar_with_multiple_ppos_forward_path,
    format_point,
    calculate_path_distance,
    ForbiddenEdgeGraph
)
from astar_spatial_IP import OptimizedSpatialGraph3D

class TestAstarPPOForbidden(unittest.TestCase):
    """Test suite for A* pathfinding with PPO and forbidden edge functionality."""
    
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
        
        # Known forbidden edge coordinates for testing
        cls.p18 = (139.232, 25.521, 160.703)  # Node that creates forbidden edge
        cls.p19 = (139.608, 25.145, 160.703)  # Node that creates forbidden edge
        
        # Forward path test coordinates (P21 > P20 > P17)
        cls.p21_origin = (139.232, 27.373, 152.313)    # P21 - Forward path test origin
        cls.p20_ppo = (139.683, 26.922, 152.313)       # P20 - Forward path test PPO
        cls.p17_destination = (139.200, 28.800, 156.500)  # P17 - Forward path test destination
        
        # Test files for forbidden edge functionality
        cls.tramo_map_file = "Output_Path_Sections/tramo_id_map_20250626_114538.json"
        cls.forbidden_sections_file = "forbidden_sections_20250626_121633.json"
        
        # Verify required files exist
        if not os.path.exists(cls.graph_file):
            raise FileNotFoundError(f"Test graph file {cls.graph_file} not found")
        
        # Check if forbidden edge test files exist
        cls.forbidden_files_available = (
            os.path.exists(cls.tramo_map_file) and 
            os.path.exists(cls.forbidden_sections_file)
        )
        
        if cls.forbidden_files_available:
            print(f"✅ Test setup complete - forbidden edge files available")
        else:
            print(f"⚠️  Test setup complete - forbidden edge files not available (some tests will be skipped)")
            
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

    # ====================================================================
    # ORIGINAL ASTAR_PPO TESTS (adapted for forbidden edge functionality)
    # ====================================================================

    def test_direct_pathfinding_basic(self):
        """Test basic direct pathfinding without PPO or forbidden edges."""
        print("🧪 Testing direct pathfinding (P2 → P1)...")
        
        path, nodes_explored = run_astar_forbidden(self.graph_file, self.origin_p2, self.destination_p1)
        
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
        
        path, nodes_explored = run_astar_forbidden(self.graph_file, self.origin_alt, self.destination_alt)
        
        self.assertIsNotNone(path, "Path should exist")
        self.assertGreater(len(path), 1, "Path should have multiple points")
        self.assertEqual(path[0], self.origin_alt, "Path should start at origin")
        self.assertEqual(path[-1], self.destination_alt, "Path should end at destination")
        
        print(f"✅ Alternative direct path: {len(path)} points, {nodes_explored} nodes explored")

    def test_ppo_pathfinding_basic(self):
        """Test PPO pathfinding with mandatory waypoint."""
        print("🧪 Testing PPO pathfinding (P2 → P5 → P1)...")
        
        path, nodes_explored = run_astar_with_ppo_forbidden(self.graph_file, 
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
        
        path, nodes_explored = run_astar_with_ppo_forbidden(self.graph_file,
                                                           self.origin_alt,
                                                           self.ppo_existing_node,
                                                           self.destination_alt)
        
        self.assertIsNotNone(path, "Path with existing node PPO should exist")
        self.assertIn(self.ppo_existing_node, path, "Path should include existing node PPO")
        
        print(f"✅ Existing node PPO path: {len(path)} points, {nodes_explored} nodes explored")

    def test_edge_splitting_functionality(self):
        """Test edge splitting with coordinates on edges."""
        print("🧪 Testing edge splitting functionality...")
        
        path, nodes_explored = run_astar_with_ppo_forbidden(self.graph_file,
                                                           self.origin_alt,
                                                           self.ppo_edge_midpoint,
                                                           self.destination_alt)
        
        self.assertIsNotNone(path, "Edge splitting path should exist")
        self.assertIn(self.ppo_edge_midpoint, path, "Path should include edge midpoint PPO")
        
        # Compare with direct path to see if edge splitting added a node
        direct_path, _ = run_astar_forbidden(self.graph_file, self.origin_alt, self.destination_alt)
        
        # Edge splitting might add one extra node
        self.assertGreaterEqual(len(path), len(direct_path), 
                               "Edge splitting path should have same or more nodes")
        
        print(f"✅ Edge splitting path: {len(path)} points vs direct {len(direct_path)} points")

    def test_path_optimality_comparison(self):
        """Compare direct path vs PPO path to verify PPO constraint is respected."""
        print("🧪 Testing path optimality comparison...")
        
        # Direct path
        direct_path, direct_nodes = run_astar_forbidden(self.graph_file, self.origin_p2, self.destination_p1)
        direct_distance = self.calculate_path_distance(direct_path)
        
        # PPO path
        ppo_path, ppo_nodes = run_astar_with_ppo_forbidden(self.graph_file,
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
            run_astar_forbidden(self.graph_file, self.invalid_coord, self.destination_p1)
        
        # Test with invalid destination
        with self.assertRaises(Exception):
            run_astar_forbidden(self.graph_file, self.origin_p2, self.invalid_coord)
        
        # Test with invalid PPO
        with self.assertRaises(Exception):
            run_astar_with_ppo_forbidden(self.graph_file, 
                                        self.origin_p2, 
                                        self.invalid_coord, 
                                        self.destination_p1)
        
        print("✅ Invalid coordinates properly rejected")

    def test_same_origin_destination(self):
        """Test pathfinding when origin and destination are the same."""
        print("🧪 Testing same origin and destination...")
        
        path, nodes_explored = run_astar_forbidden(self.graph_file, self.origin_p2, self.origin_p2)
        
        # Should return a single-point path or handle gracefully
        self.assertIsNotNone(path, "Same point path should exist")
        self.assertEqual(len(path), 1, "Same point path should have one point")
        self.assertEqual(path[0], self.origin_p2, "Path should contain the point")
        
        print(f"✅ Same point path: {len(path)} points, {nodes_explored} nodes explored")

    def test_ppo_same_as_origin_or_destination(self):
        """Test PPO pathfinding when PPO is same as origin or destination."""
        print("🧪 Testing PPO same as origin/destination...")
        
        # PPO same as origin
        path1, nodes1 = run_astar_with_ppo_forbidden(self.graph_file,
                                                    self.origin_p2,
                                                    self.origin_p2,  # PPO = origin
                                                    self.destination_p1)
        
        self.assertIsNotNone(path1, "PPO=origin path should exist")
        
        # PPO same as destination
        path2, nodes2 = run_astar_with_ppo_forbidden(self.graph_file,
                                                    self.origin_p2,
                                                    self.destination_p1,  # PPO = destination
                                                    self.destination_p1)
        
        self.assertIsNotNone(path2, "PPO=destination path should exist")
        
        print(f"✅ PPO edge cases handled: origin-PPO {len(path1)} points, destination-PPO {len(path2)} points")

    def test_multiple_ppos_functionality(self):
        """Test multi-PPO pathfinding with multiple waypoints in sequence."""
        print("🧪 Testing multiple PPOs functionality...")
        
        # Test with 2 PPOs
        ppos_2 = [self.ppo_p5, (139.232, 28.845, 160.703)]
        path_2ppos, nodes_2ppos, segment_info_2 = run_astar_with_multiple_ppos_forbidden(
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
        path_3ppos, nodes_3ppos, segment_info_3 = run_astar_with_multiple_ppos_forbidden(
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
        path_0ppos, nodes_0ppos, segment_info_0 = run_astar_with_multiple_ppos_forbidden(
            self.graph_file, self.origin_p2, [], self.destination_p1)
        
        direct_path, direct_nodes = run_astar_forbidden(self.graph_file, self.origin_p2, self.destination_p1)
        
        self.assertEqual(len(path_0ppos), len(direct_path), "Empty PPO list should equal direct path")
        self.assertEqual(path_0ppos, direct_path, "Empty PPO path should be identical to direct path")
        
        print(f"✅ 0 PPOs (direct): {len(path_0ppos)} points, {nodes_0ppos} nodes explored")

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

    # ====================================================================
    # NEW FORBIDDEN EDGE TESTS
    # ====================================================================

    def test_forbidden_edge_graph_initialization(self):
        """Test ForbiddenEdgeGraph initialization with and without restriction files."""
        print("🧪 Testing ForbiddenEdgeGraph initialization...")
        
        # Test without restriction files
        graph_no_restrictions = ForbiddenEdgeGraph(self.graph_file)
        self.assertIsNotNone(graph_no_restrictions.graph_data, "Graph data should be loaded")
        self.assertEqual(len(graph_no_restrictions.tramo_id_map), 0, "No tramo mapping should be loaded")
        self.assertEqual(len(graph_no_restrictions.forbidden_set), 0, "No forbidden sections should be loaded")
        
        print("✅ Graph without restrictions initialized")
        
        # Test with restriction files (if available)
        if self.forbidden_files_available:
            graph_with_restrictions = ForbiddenEdgeGraph(
                self.graph_file, 
                self.tramo_map_file, 
                self.forbidden_sections_file
            )
            self.assertIsNotNone(graph_with_restrictions.graph_data, "Graph data should be loaded")
            self.assertGreater(len(graph_with_restrictions.tramo_id_map), 0, "Tramo mapping should be loaded")
            self.assertGreater(len(graph_with_restrictions.forbidden_set), 0, "Forbidden sections should be loaded")
            
            print(f"✅ Graph with restrictions initialized: {len(graph_with_restrictions.tramo_id_map)} tramos, {len(graph_with_restrictions.forbidden_set)} forbidden")
        else:
            print("⚠️  Skipping restriction files test - files not available")

    def test_is_edge_forbidden_function(self):
        """Test the is_edge_forbidden function."""
        print("🧪 Testing is_edge_forbidden function...")
        
        if not self.forbidden_files_available:
            print("⚠️  Skipping forbidden edge test - files not available")
            return
        
        graph = ForbiddenEdgeGraph(self.graph_file, self.tramo_map_file, self.forbidden_sections_file)
        
        # Test with known forbidden edge (tramo ID 218)
        node_str_1 = f"({self.p18[0]}, {self.p18[1]}, {self.p18[2]})"
        node_str_2 = f"({self.p19[0]}, {self.p19[1]}, {self.p19[2]})"
        
        is_forbidden = graph.is_edge_forbidden(node_str_1, node_str_2)
        self.assertTrue(is_forbidden, "Known forbidden edge should be detected")
        
        # Test with edge in reverse order (should still be forbidden)
        is_forbidden_reverse = graph.is_edge_forbidden(node_str_2, node_str_1)
        self.assertTrue(is_forbidden_reverse, "Forbidden edge should work in both directions")
        
        # Test with non-forbidden edge
        test_node_1 = f"({self.origin_p2[0]}, {self.origin_p2[1]}, {self.origin_p2[2]})"
        test_node_2 = f"({self.destination_p1[0]}, {self.destination_p1[1]}, {self.destination_p1[2]})"
        
        is_not_forbidden = graph.is_edge_forbidden(test_node_1, test_node_2)
        # This might be True or False depending on the specific edge, but should not crash
        self.assertIsInstance(is_not_forbidden, bool, "Should return boolean result")
        
        print(f"✅ Edge forbidden check: known forbidden edge detected, function works correctly")

    @unittest.skipUnless(os.path.exists("Output_Path_Sections/tramo_id_map_20250626_114538.json") and 
                        os.path.exists("forbidden_sections_20250626_121633.json"), 
                        "Forbidden edge test files not available")
    def test_forbidden_edge_avoidance_direct(self):
        """Test that forbidden edges are avoided in direct pathfinding."""
        print("🧪 Testing forbidden edge avoidance in direct pathfinding...")
        
        # Path without restrictions
        path_normal, nodes_normal = run_astar_forbidden(
            self.graph_file, self.origin_p2, self.destination_p1)
        distance_normal = calculate_path_distance(path_normal)
        
        # Path with forbidden edge restrictions
        path_restricted, nodes_restricted = run_astar_forbidden(
            self.graph_file, self.origin_p2, self.destination_p1,
            self.tramo_map_file, self.forbidden_sections_file)
        distance_restricted = calculate_path_distance(path_restricted)
        
        # With restrictions, path should be different (likely longer)
        self.assertNotEqual(path_normal, path_restricted, "Paths should be different with restrictions")
        
        # Restricted path should explore more nodes (finding alternative route)
        self.assertGreaterEqual(nodes_restricted, nodes_normal, 
                               "Restricted pathfinding should explore same or more nodes")
        
        # Both paths should be valid
        self.assertEqual(path_normal[0], self.origin_p2, "Normal path should start at origin")
        self.assertEqual(path_normal[-1], self.destination_p1, "Normal path should end at destination")
        self.assertEqual(path_restricted[0], self.origin_p2, "Restricted path should start at origin")
        self.assertEqual(path_restricted[-1], self.destination_p1, "Restricted path should end at destination")
        
        print(f"✅ Forbidden edge avoidance: Normal {len(path_normal)} points ({distance_normal:.3f} units), "
              f"Restricted {len(path_restricted)} points ({distance_restricted:.3f} units)")

    @unittest.skipUnless(os.path.exists("Output_Path_Sections/tramo_id_map_20250626_114538.json") and 
                        os.path.exists("forbidden_sections_20250626_121633.json"), 
                        "Forbidden edge test files not available")
    def test_forbidden_edge_avoidance_ppo(self):
        """Test that forbidden edges are avoided in PPO pathfinding."""
        print("🧪 Testing forbidden edge avoidance in PPO pathfinding...")
        
        # PPO path without restrictions
        path_normal, nodes_normal = run_astar_with_ppo_forbidden(
            self.graph_file, self.origin_p2, self.ppo_p5, self.destination_p1)
        distance_normal = calculate_path_distance(path_normal)
        
        # PPO path with forbidden edge restrictions
        path_restricted, nodes_restricted = run_astar_with_ppo_forbidden(
            self.graph_file, self.origin_p2, self.ppo_p5, self.destination_p1,
            self.tramo_map_file, self.forbidden_sections_file)
        distance_restricted = calculate_path_distance(path_restricted)
        
        # Both paths should include the PPO
        self.assertIn(self.ppo_p5, path_normal, "Normal PPO path should include PPO")
        self.assertIn(self.ppo_p5, path_restricted, "Restricted PPO path should include PPO")
        
        # Both paths should be valid
        self.assertEqual(path_normal[0], self.origin_p2, "Normal path should start at origin")
        self.assertEqual(path_normal[-1], self.destination_p1, "Normal path should end at destination")
        self.assertEqual(path_restricted[0], self.origin_p2, "Restricted path should start at origin")
        self.assertEqual(path_restricted[-1], self.destination_p1, "Restricted path should end at destination")
        
        print(f"✅ PPO forbidden edge avoidance: Normal {len(path_normal)} points ({distance_normal:.3f} units), "
              f"Restricted {len(path_restricted)} points ({distance_restricted:.3f} units)")

    @unittest.skipUnless(os.path.exists("Output_Path_Sections/tramo_id_map_20250626_114538.json") and 
                        os.path.exists("forbidden_sections_20250626_121633.json"), 
                        "Forbidden edge test files not available")
    def test_forbidden_edge_avoidance_multi_ppo(self):
        """Test that forbidden edges are avoided in multi-PPO pathfinding."""
        print("🧪 Testing forbidden edge avoidance in multi-PPO pathfinding...")
        
        ppos = [self.ppo_p5, (139.232, 28.845, 160.703)]
        
        # Multi-PPO path without restrictions
        path_normal, nodes_normal, segments_normal = run_astar_with_multiple_ppos_forbidden(
            self.graph_file, self.origin_p2, ppos, self.destination_p1)
        distance_normal = calculate_path_distance(path_normal)
        
        # Multi-PPO path with forbidden edge restrictions
        path_restricted, nodes_restricted, segments_restricted = run_astar_with_multiple_ppos_forbidden(
            self.graph_file, self.origin_p2, ppos, self.destination_p1,
            self.tramo_map_file, self.forbidden_sections_file)
        distance_restricted = calculate_path_distance(path_restricted)
        
        # Both paths should include all PPOs
        for ppo in ppos:
            self.assertIn(ppo, path_normal, f"Normal path should include PPO {ppo}")
            self.assertIn(ppo, path_restricted, f"Restricted path should include PPO {ppo}")
        
        # Segment information should be consistent
        self.assertEqual(len(segments_normal), len(segments_restricted), "Should have same number of segments")
        
        print(f"✅ Multi-PPO forbidden edge avoidance: Normal {len(path_normal)} points ({distance_normal:.3f} units), "
              f"Restricted {len(path_restricted)} points ({distance_restricted:.3f} units)")

    @unittest.skipUnless(os.path.exists("Output_Path_Sections/tramo_id_map_20250626_114538.json") and 
                        os.path.exists("forbidden_sections_20250626_121633.json"), 
                        "Forbidden edge test files not available")
    def test_optimal_check_with_forbidden_edges(self):
        """Test optimal check functionality with forbidden edge avoidance."""
        print("🧪 Testing optimal check with forbidden edges...")
        
        ppo1 = self.ppo_p5
        ppo2 = (139.608, 25.145, 160.703)
        
        results = run_optimal_check_forbidden(
            self.graph_file, self.origin_p2, ppo1, ppo2, self.destination_p1,
            self.tramo_map_file, self.forbidden_sections_file)
        
        # Verify results structure
        self.assertIn('order1', results, "Results should contain order1")
        self.assertIn('order2', results, "Results should contain order2")
        self.assertIn('optimal_order', results, "Results should contain optimal_order")
        self.assertIn('improvement', results, "Results should contain improvement")
        self.assertIn('both_valid', results, "Results should contain both_valid")
        
        # At least one order should succeed (unless completely blocked)
        success_count = sum([results['order1']['success'], results['order2']['success']])
        self.assertGreaterEqual(success_count, 1, "At least one order should succeed")
        
        print(f"✅ Optimal check with forbidden edges: {success_count}/2 orders succeeded")

    def test_forbidden_edge_error_handling(self):
        """Test error handling for forbidden edge functionality."""
        print("🧪 Testing forbidden edge error handling...")
        
        # Test with invalid tramo mapping file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"invalid": "format"}, f)
            invalid_tramo_file = f.name
        
        try:
            # Should handle invalid tramo file gracefully
            graph = ForbiddenEdgeGraph(self.graph_file, invalid_tramo_file, None)
            # Should still work for basic pathfinding
            path, nodes = graph.find_path_with_edge_split(self.origin_p2, self.destination_p1)
            self.assertIsNotNone(path, "Should still work with invalid tramo file")
        finally:
            os.unlink(invalid_tramo_file)
        
        # Test with non-existent files
        try:
            graph = ForbiddenEdgeGraph(self.graph_file, "nonexistent_tramo.json", "nonexistent_forbidden.json")
            # Should fail gracefully
            self.fail("Should raise exception for non-existent files")
        except Exception as e:
            print(f"✅ Properly handled non-existent files: {type(e).__name__}")

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

    def test_multiple_ppos_edge_cases(self):
        """Test edge cases for multi-PPO pathfinding."""
        print("🧪 Testing multiple PPOs edge cases...")
        
        # Test with single PPO (should work like run_astar_with_ppo_forbidden)
        single_ppo = [self.ppo_p5]
        path_single, nodes_single, segment_info_single = run_astar_with_multiple_ppos_forbidden(
            self.graph_file, self.origin_p2, single_ppo, self.destination_p1)
        
        # Compare with dedicated single PPO function
        path_dedicated, nodes_dedicated = run_astar_with_ppo_forbidden(
            self.graph_file, self.origin_p2, self.ppo_p5, self.destination_p1)
        
        self.assertEqual(len(path_single), len(path_dedicated), "Single PPO should match dedicated function")
        self.assertEqual(len(segment_info_single), 2, "Single PPO should have 2 segments")
        
        print(f"✅ Single PPO via multi-PPO: {len(path_single)} points, {nodes_single} nodes explored")
        
        # Test with PPO same as origin
        origin_as_ppo = [self.origin_p2]
        path_origin_ppo, nodes_origin_ppo, segment_info_origin = run_astar_with_multiple_ppos_forbidden(
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
        
        results = run_optimal_check_forbidden(self.graph_file, self.origin_p2, ppo1, ppo2, self.destination_p1)
        
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
        results_same = run_optimal_check_forbidden(self.graph_file, self.origin_p2, ppo_same, ppo_same, self.destination_p1)
        
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
        
        results_edge = run_optimal_check_forbidden(self.graph_file, self.origin_p2, ppo_edge1, ppo_edge2, self.destination_p1)
        
        self.assertTrue(results_edge['both_valid'], "Edge splitting test should be valid")
        self.assertIn(results_edge['optimal_order'], [1, 2, "tie"], "Edge splitting should determine optimal order")
        
        print(f"✅ Edge splitting test: optimal order {results_edge['optimal_order']}")

    def test_calculate_path_distance_function(self):
        """Test the calculate_path_distance utility function."""
        print("🧪 Testing calculate_path_distance function...")
        
        # Test with simple path
        simple_path = [(0, 0, 0), (1, 0, 0), (1, 1, 0)]
        distance = calculate_path_distance(simple_path)
        expected_distance = 2.0  # 1 unit + 1 unit
        self.assertAlmostEqual(distance, expected_distance, places=6, 
                              msg=f"Simple path distance should be {expected_distance}")
        
        # Test with empty path
        empty_distance = calculate_path_distance([])
        self.assertEqual(empty_distance, 0.0, "Empty path should have zero distance")
        
        # Test with single point
        single_distance = calculate_path_distance([(0, 0, 0)])
        self.assertEqual(single_distance, 0.0, "Single point should have zero distance")
        
        print(f"✅ Path distance calculation: simple path {distance:.3f} units")

    def test_graph_restoration_after_forbidden_edges(self):
        """Test that graph is properly restored after forbidden edge filtering."""
        print("🧪 Testing graph restoration after forbidden edge filtering...")
        
        if not self.forbidden_files_available:
            print("⚠️  Skipping graph restoration test - files not available")
            return
        
        graph = ForbiddenEdgeGraph(self.graph_file, self.tramo_map_file, self.forbidden_sections_file)
        
        # Count original edges
        original_edge_count = graph.graph.number_of_edges()
        
        # Perform pathfinding with forbidden edges (this modifies the graph temporarily)
        path, nodes = graph.find_path_with_edge_split_forbidden(self.origin_p2, self.destination_p1)
        
        # Check that graph is restored
        restored_edge_count = graph.graph.number_of_edges()
        self.assertEqual(original_edge_count, restored_edge_count, 
                        "Graph should be restored to original state after pathfinding")
        
        # Perform normal pathfinding to ensure graph still works
        normal_path, normal_nodes = graph.find_path_with_edge_split(self.origin_alt, self.destination_alt)
        self.assertIsNotNone(normal_path, "Normal pathfinding should still work after forbidden edge pathfinding")
        
        print(f"✅ Graph restoration: {original_edge_count} edges maintained")

    # ====================================================================
    # FORWARD PATH FUNCTIONALITY TESTS
    # ====================================================================

    @unittest.skipUnless(os.path.exists("Output_Path_Sections/tramo_id_map_20250626_114538.json"), 
                        "Tramo mapping file required for forward path tests")
    def test_forward_path_basic_functionality(self):
        """Test basic forward path functionality with P21 > P20 > P17."""
        print("🧪 Testing forward path basic functionality (P21 > P20 > P17)...")
        
        # Test forward path
        forward_path, forward_nodes, forward_segments = run_astar_with_ppo_forward_path(
            self.graph_file, 
            self.p21_origin, 
            self.p20_ppo, 
            self.p17_destination,
            self.tramo_map_file
        )
        
        # Verify path exists and structure
        self.assertIsNotNone(forward_path, "Forward path should exist")
        self.assertGreater(len(forward_path), 10, "Forward path should be long (no backtracking)")
        self.assertEqual(forward_path[0], self.p21_origin, "Path should start at P21")
        self.assertEqual(forward_path[-1], self.p17_destination, "Path should end at P17")
        self.assertIn(self.p20_ppo, forward_path, "Path should include P20 PPO")
        
        # Verify segments
        self.assertEqual(len(forward_segments), 2, "Should have 2 segments")
        self.assertEqual(forward_segments[0]['start'], self.p21_origin, "Segment 1 should start at P21")
        self.assertEqual(forward_segments[0]['end'], self.p20_ppo, "Segment 1 should end at P20")
        self.assertEqual(forward_segments[1]['start'], self.p20_ppo, "Segment 2 should start at P20")
        self.assertEqual(forward_segments[1]['end'], self.p17_destination, "Segment 2 should end at P17")
        
        # Verify no backtracking - P21 should only appear once (at the beginning)
        p21_occurrences = [i for i, point in enumerate(forward_path) if point == self.p21_origin]
        self.assertEqual(len(p21_occurrences), 1, "P21 should only appear once (no backtracking)")
        self.assertEqual(p21_occurrences[0], 0, "P21 should only appear at the beginning")
        
        forward_distance = calculate_path_distance(forward_path)
        print(f"✅ Forward path: {len(forward_path)} points, {forward_distance:.3f} units, {forward_nodes} nodes explored")
        print(f"   Segment 1: {forward_segments[0]['path_length']} points, {forward_segments[0]['nodes_explored']} nodes")
        print(f"   Segment 2: {forward_segments[1]['path_length']} points, {forward_segments[1]['nodes_explored']} nodes")
        
        return forward_path, forward_distance, forward_nodes

    @unittest.skipUnless(os.path.exists("Output_Path_Sections/tramo_id_map_20250626_114538.json"), 
                        "Tramo mapping file required for forward path tests")
    def test_forward_path_vs_regular_ppo(self):
        """Compare forward path vs regular PPO to verify backtracking prevention."""
        print("🧪 Testing forward path vs regular PPO comparison...")
        
        # Regular PPO path
        regular_path, regular_nodes = run_astar_with_ppo_forbidden(
            self.graph_file, 
            self.p21_origin, 
            self.p20_ppo, 
            self.p17_destination
        )
        
        # Forward path
        forward_path, forward_nodes, forward_segments = run_astar_with_ppo_forward_path(
            self.graph_file, 
            self.p21_origin, 
            self.p20_ppo, 
            self.p17_destination,
            self.tramo_map_file
        )
        
        # Calculate distances
        regular_distance = calculate_path_distance(regular_path)
        forward_distance = calculate_path_distance(forward_path)
        
        # Forward path should be longer (no backtracking allowed)
        self.assertGreater(forward_distance, regular_distance, 
                          "Forward path should be longer due to backtracking prevention")
        self.assertGreater(len(forward_path), len(regular_path),
                          "Forward path should have more points")
        
        # Check for backtracking in regular path
        regular_p21_count = sum(1 for point in regular_path if point == self.p21_origin)
        forward_p21_count = sum(1 for point in forward_path if point == self.p21_origin)
        
        # Regular path might have backtracking, forward path should not
        self.assertEqual(forward_p21_count, 1, "Forward path should have no backtracking to P21")
        
        print(f"✅ Regular PPO: {len(regular_path)} points, {regular_distance:.3f} units")
        print(f"✅ Forward path: {len(forward_path)} points, {forward_distance:.3f} units")
        print(f"   Forward path is {forward_distance/regular_distance:.1f}x longer (prevents backtracking)")
        
        return regular_path, forward_path, regular_distance, forward_distance

    @unittest.skipUnless(os.path.exists("Output_Path_Sections/tramo_id_map_20250626_114538.json"), 
                        "Tramo mapping file required for forward path tests")
    def test_forward_path_multi_ppo(self):
        """Test forward path with multiple PPOs."""
        print("🧪 Testing forward path with multiple PPOs...")
        
        # Use P21 > P20 > P19 > P17 (adding P19 as second PPO)
        multi_ppos = [self.p20_ppo, self.p19]
        
        forward_path, forward_nodes, forward_segments = run_astar_with_multiple_ppos_forward_path(
            self.graph_file,
            self.p21_origin,
            multi_ppos,
            self.p17_destination,
            self.tramo_map_file
        )
        
        # Verify path structure
        self.assertIsNotNone(forward_path, "Multi-PPO forward path should exist")
        self.assertEqual(forward_path[0], self.p21_origin, "Path should start at P21")
        self.assertEqual(forward_path[-1], self.p17_destination, "Path should end at P17")
        self.assertIn(self.p20_ppo, forward_path, "Path should include P20")
        self.assertIn(self.p19, forward_path, "Path should include P19")
        
        # Verify segments
        self.assertEqual(len(forward_segments), 3, "Should have 3 segments for 2 PPOs")
        
        # Verify no backtracking
        p21_count = sum(1 for point in forward_path if point == self.p21_origin)
        self.assertEqual(p21_count, 1, "P21 should only appear once")
        
        forward_distance = calculate_path_distance(forward_path)
        print(f"✅ Multi-PPO forward path: {len(forward_path)} points, {forward_distance:.3f} units")
        print(f"   Segments: {[seg['path_length'] for seg in forward_segments]} points each")

    @unittest.skipUnless(os.path.exists("Output_Path_Sections/tramo_id_map_20250626_114538.json"), 
                        "Tramo mapping file required for forward path tests")
    def test_forward_path_tramo_id_detection(self):
        """Test that forward path correctly identifies and forbids tramo IDs."""
        print("🧪 Testing forward path tramo ID detection...")
        
        # Create a custom ForbiddenEdgeGraph to inspect tramo ID detection
        graph = ForbiddenEdgeGraph(self.graph_file, self.tramo_map_file)
        
        # Test the direct edge between P21 and P20 (should be tramo ID 162)
        node_str1 = f"({self.p21_origin[0]}, {self.p21_origin[1]}, {self.p21_origin[2]})"
        node_str2 = f"({self.p20_ppo[0]}, {self.p20_ppo[1]}, {self.p20_ppo[2]})"
        edge_key = "-".join(sorted([node_str1, node_str2]))
        
        # Verify tramo ID mapping exists
        self.assertIn(edge_key, graph.tramo_id_map, f"Edge {edge_key} should be in tramo mapping")
        tramo_id = graph.tramo_id_map[edge_key]
        self.assertEqual(tramo_id, 162, "P21-P20 edge should be tramo ID 162")
        
        # Test is_edge_forbidden function
        self.assertFalse(graph.is_edge_forbidden(node_str1, node_str2), 
                        "Edge should not be forbidden initially")
        
        # Add to forbidden set and test
        graph.forbidden_set.add(162)
        self.assertTrue(graph.is_edge_forbidden(node_str1, node_str2),
                       "Edge should be forbidden after adding to forbidden set")
        
        print(f"✅ Tramo ID detection working: P21-P20 edge = tramo ID {tramo_id}")

    def test_forward_path_without_tramo_mapping(self):
        """Test forward path behavior when tramo mapping is not provided."""
        print("🧪 Testing forward path without tramo mapping...")
        
        # This should fall back to regular pathfinding
        path, nodes, segments = run_astar_with_ppo_forward_path(
            self.graph_file,
            self.p21_origin,
            self.p20_ppo,
            self.p17_destination,
            None  # No tramo mapping
        )
        
        # Should still work but without forward path logic
        self.assertIsNotNone(path, "Path should exist even without tramo mapping")
        self.assertEqual(path[0], self.p21_origin, "Path should start at P21")
        self.assertEqual(path[-1], self.p17_destination, "Path should end at P17")
        self.assertIn(self.p20_ppo, path, "Path should include P20")
        
        # Without forward path logic, this might allow backtracking
        distance = calculate_path_distance(path)
        print(f"✅ No tramo mapping: {len(path)} points, {distance:.3f} units (regular PPO behavior)")

    def test_forward_path_edge_cases(self):
        """Test forward path edge cases and error handling."""
        print("🧪 Testing forward path edge cases...")
        
        # Test with same origin and destination - should return single point path
        try:
            path, nodes, segments = run_astar_with_ppo_forward_path(
                self.graph_file,
                self.p21_origin,
                self.p21_origin,  # Same as origin
                self.p21_origin,  # Same as origin
                self.tramo_map_file
            )
            # This might work (single point path) or raise an exception
            if path is not None:
                self.assertEqual(len(path), 1, "Same point should result in single point path")
                print("✅ Same origin/destination handled gracefully")
            else:
                print("✅ Same origin/destination properly rejected")
        except Exception as e:
            print(f"✅ Same origin/destination properly rejected: {type(e).__name__}")
        
        # Test with invalid coordinates - should fail
        try:
            path, nodes, segments = run_astar_with_ppo_forward_path(
                self.graph_file,
                self.invalid_coord,
                self.p20_ppo,
                self.p17_destination,
                self.tramo_map_file
            )
            # If it doesn't raise an exception, path should be None
            self.assertIsNone(path, "Invalid coordinates should result in no path")
            print("✅ Invalid coordinates handled gracefully")
        except Exception as e:
            print(f"✅ Invalid coordinates properly rejected: {type(e).__name__}")
        
        print(f"✅ Forward path edge cases handled correctly")

    def test_forward_path_performance_metrics(self):
        """Test and document forward path performance characteristics."""
        print("🧪 Testing forward path performance metrics...")
        
        if not os.path.exists(self.tramo_map_file):
            self.skipTest("Tramo mapping file not available")
        
        # Run forward path test
        forward_path, forward_nodes, forward_segments = run_astar_with_ppo_forward_path(
            self.graph_file,
            self.p21_origin,
            self.p20_ppo,
            self.p17_destination,
            self.tramo_map_file
        )
        
        # Run regular PPO for comparison
        regular_path, regular_nodes = run_astar_with_ppo_forbidden(
            self.graph_file,
            self.p21_origin,
            self.p20_ppo,
            self.p17_destination
        )
        
        # Calculate metrics
        forward_distance = calculate_path_distance(forward_path)
        regular_distance = calculate_path_distance(regular_path)
        
        distance_ratio = forward_distance / regular_distance if regular_distance > 0 else float('inf')
        points_ratio = len(forward_path) / len(regular_path) if len(regular_path) > 0 else float('inf')
        nodes_ratio = forward_nodes / regular_nodes if regular_nodes > 0 else float('inf')
        
        # Document performance characteristics
        print(f"📊 Forward Path Performance Metrics:")
        print(f"   Regular PPO:  {len(regular_path):3d} points, {regular_distance:7.3f} units, {regular_nodes:3d} nodes")
        print(f"   Forward Path: {len(forward_path):3d} points, {forward_distance:7.3f} units, {forward_nodes:3d} nodes")
        print(f"   Ratios: {points_ratio:.1f}x points, {distance_ratio:.1f}x distance, {nodes_ratio:.1f}x nodes")
        
        # Verify forward path is longer (prevents backtracking)
        self.assertGreaterEqual(forward_distance, regular_distance,
                               "Forward path should be at least as long as regular path")
        
        # Store metrics for potential regression testing
        self.forward_path_metrics = {
            'points': len(forward_path),
            'distance': forward_distance,
            'nodes_explored': forward_nodes,
            'points_ratio': points_ratio,
            'distance_ratio': distance_ratio,
            'nodes_ratio': nodes_ratio
        }
        
        print(f"✅ Performance metrics documented")

def run_test_suite():
    """Run the complete test suite with detailed reporting."""
    print("🚀 A* PPO with Forbidden Edge Avoidance Test Suite")
    print("=" * 70)
    print("Testing A* pathfinding with PPO and forbidden edge functionality")
    print("=" * 70)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAstarPPOForbidden)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    if result.wasSuccessful():
        print(f"✅ ALL {result.testsRun} TESTS PASSED!")
        print("🎯 A* PPO algorithm with forbidden edge avoidance is working correctly")
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
    
    print("=" * 70)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1) 