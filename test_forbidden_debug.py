#!/usr/bin/env python3
"""
Debug forbidden sections functionality
"""

import json
from astar_PPO_forbid import ForbiddenEdgeGraph

def test_forbidden_functionality():
    """Test if forbidden sections are working correctly."""
    
    print("🔧 Testing forbidden sections functionality")
    
    # Load the forbidden sections
    with open('forbidden_tramos_c2_c3.json', 'r') as f:
        forbidden_ids = json.load(f)
    print(f"🚫 Forbidden tramo IDs: {forbidden_ids}")
    
    # Create the forbidden graph
    graph = ForbiddenEdgeGraph('graph_LV_combined_legacy.json', 'tramo_map_combined.json', 'forbidden_tramos_c2_c3.json')
    
    # Test specific forbidden edge
    test_edges = [
        ("(178.482, 14.056, 157.295)", "(178.858, 13.680, 157.295)"),  # Tramo 53
        ("(178.858, 13.680, 157.295)", "(179.234, 13.304, 157.295)"),  # Tramo 54
        ("(177.381, 14.056, 157.295)", "(178.482, 14.056, 157.295)"),  # Tramo 163
        ("(179.234, 13.304, 157.295)", "(182.946, 13.304, 157.295)"),  # Tramo 164
    ]
    
    print("\n🔍 Testing forbidden edge detection:")
    for node1, node2 in test_edges:
        is_forbidden = graph.is_edge_forbidden(node1, node2)
        edge_key = "-".join(sorted([node1, node2]))
        tramo_id = graph.tramo_id_map.get(edge_key, "NOT_FOUND")
        print(f"   {edge_key}")
        print(f"     Tramo ID: {tramo_id}")
        print(f"     Forbidden: {is_forbidden}")
        print()

if __name__ == "__main__":
    test_forbidden_functionality()
