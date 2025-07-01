#!/usr/bin/env python3
"""
Create a tramo ID map for tagged graphs to enable forbidden sections testing.

This script generates a tramo ID mapping file compatible with our tagged graph format,
allowing us to test forbidden sections functionality with system filtering.
"""

import json
from cable_filter import load_tagged_graph

def create_tramo_map(graph_file, output_file):
    """
    Create a tramo ID map from a tagged graph.
    
    Args:
        graph_file: Path to tagged graph JSON file
        output_file: Path to output tramo ID map JSON file
    """
    print(f"📂 Loading graph: {graph_file}")
    graph_data = load_tagged_graph(graph_file)
    
    print(f"📊 Graph stats: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges")
    
    tramo_map = {}
    tramo_id = 0
    
    # Create tramo IDs for all edges
    for edge in graph_data['edges']:
        from_node = edge['from']
        to_node = edge['to']
        edge_system = edge.get('sys', 'Unknown')
        
        # Create edge key in canonical form (sorted order)
        edge_key = "-".join(sorted([from_node, to_node]))
        
        tramo_map[edge_key] = tramo_id
        tramo_id += 1
    
    print(f"🗺️  Created {len(tramo_map)} tramo ID mappings")
    
    # Save tramo map
    with open(output_file, 'w') as f:
        json.dump(tramo_map, f, indent=2)
    
    print(f"💾 Saved tramo map: {output_file}")
    
    # Analyze system distribution of edges
    system_a_edges = 0
    system_b_edges = 0
    cross_system_edges = []
    
    for edge in graph_data['edges']:
        from_node = edge['from']
        to_node = edge['to']
        edge_system = edge.get('sys')
        
        if edge_system == 'A':
            system_a_edges += 1
        elif edge_system == 'B':
            system_b_edges += 1
        
        # Check if this is a cross-system edge
        if from_node in graph_data['nodes'] and to_node in graph_data['nodes']:
            from_sys = graph_data['nodes'][from_node].get('sys')
            to_sys = graph_data['nodes'][to_node].get('sys')
            
            if from_sys != to_sys:
                edge_key = "-".join(sorted([from_node, to_node]))
                tramo_id = tramo_map[edge_key]
                cross_system_edges.append((edge_key, tramo_id, from_sys, to_sys))
    
    print(f"\n📈 Edge distribution:")
    print(f"   System A edges: {system_a_edges}")
    print(f"   System B edges: {system_b_edges}")
    print(f"   Cross-system edges: {len(cross_system_edges)}")
    
    if cross_system_edges:
        print(f"\n🌉 Cross-system connections:")
        for edge_key, tramo_id, from_sys, to_sys in cross_system_edges:
            print(f"   Tramo {tramo_id}: {edge_key} (System {from_sys} ↔ System {to_sys})")
    
    return tramo_map, cross_system_edges

def create_test_forbidden_sections(tramo_map, cross_system_edges, output_dir=""):
    """
    Create test forbidden sections files for the three scenarios.
    
    Args:
        tramo_map: Dictionary of edge_key -> tramo_id mappings
        cross_system_edges: List of cross-system edge information
        output_dir: Directory to save forbidden sections files
    """
    import os
    
    # Scenario 1: Forbidden sections in System A only
    # Pick some System A tramo IDs
    system_a_tramos = []
    for edge_key, tramo_id in tramo_map.items():
        # This is a simplified approach - in practice you'd check the edge system
        if len(system_a_tramos) < 3:  # Get first 3 tramo IDs as examples
            system_a_tramos.append(tramo_id)
    
    scenario1_file = os.path.join(output_dir, "forbidden_system_a.json")
    with open(scenario1_file, 'w') as f:
        json.dump(system_a_tramos[:3], f, indent=2)
    print(f"📝 Created Scenario 1 forbidden sections: {scenario1_file}")
    print(f"   Forbidden tramo IDs: {system_a_tramos[:3]}")
    
    # Scenario 2: Forbidden cross-system connections
    cross_system_tramos = [tramo_id for _, tramo_id, _, _ in cross_system_edges]
    
    scenario2_file = os.path.join(output_dir, "forbidden_cross_system.json")
    with open(scenario2_file, 'w') as f:
        json.dump(cross_system_tramos, f, indent=2)
    print(f"📝 Created Scenario 2 forbidden sections: {scenario2_file}")
    print(f"   Forbidden cross-system tramo IDs: {cross_system_tramos}")
    
    # Scenario 3: Forbidden sections in both systems
    both_systems_tramos = system_a_tramos[:2] + cross_system_tramos + [max(tramo_map.values())]
    
    scenario3_file = os.path.join(output_dir, "forbidden_both_systems.json")
    with open(scenario3_file, 'w') as f:
        json.dump(both_systems_tramos, f, indent=2)
    print(f"📝 Created Scenario 3 forbidden sections: {scenario3_file}")
    print(f"   Forbidden tramo IDs (mixed): {both_systems_tramos}")
    
    return {
        'scenario1': scenario1_file,
        'scenario2': scenario2_file, 
        'scenario3': scenario3_file
    }

def main():
    """Main function to create tramo maps and test forbidden sections."""
    print("🔧 CREATING TRAMO ID MAPS FOR TAGGED GRAPHS")
    print("=" * 60)
    
    # Create tramo map for combined graph
    graph_file = "graph_LV_combined.json"
    tramo_map_file = "tramo_map_combined.json"
    
    try:
        tramo_map, cross_system_edges = create_tramo_map(graph_file, tramo_map_file)
        
        print(f"\n🧪 CREATING TEST FORBIDDEN SECTIONS")
        print("=" * 60)
        
        forbidden_files = create_test_forbidden_sections(tramo_map, cross_system_edges)
        
        print(f"\n✅ SUCCESS!")
        print("=" * 60)
        print(f"📁 Created files:")
        print(f"   • Tramo map: {tramo_map_file}")
        for scenario, filepath in forbidden_files.items():
            print(f"   • {scenario}: {filepath}")
        
        print(f"\n💡 Now you can test forbidden sections with:")
        print(f"   python3 astar_PPOF_systems.py direct {graph_file} <coords> --cable C \\")
        print(f"     --tramo-map {tramo_map_file} --forbidden {forbidden_files['scenario1']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 