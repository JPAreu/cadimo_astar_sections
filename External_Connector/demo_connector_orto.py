#!/usr/bin/env python3
"""
Demo: External Point Connector Algorithm
========================================

This demo showcases the connector_orto.py algorithm using point P10 and graph_LVA1.json.
Demonstrates both command-line usage and programmatic integration.

Point P10: (161.248, 26.922, 162.313)
Expected Results:
- Closest Edge: (152.666, 25.145, 160.124) ↔ (169.764, 25.145, 160.124)
- Euclidean Distance: ~2.82 units
- Manhattan Distance: ~3.97 units
- Two distinct orthogonal paths

© 2025
"""

import subprocess
import sys
import json
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from connector_orto import ImprovedExternalPointConnector


def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"{title.center(60)}")
    print(f"{'='*60}")


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'-'*40}")
    print(f"{title}")
    print(f"{'-'*40}")


def demo_command_line():
    """Demonstrate command-line usage of connector_orto.py."""
    print_header("COMMAND LINE DEMO")
    
    print_section("1. Basic Analysis (Terminal Output Only)")
    print("Command: python3 connector_orto.py ../graph_LVA1.json 161.248 26.922 162.313")
    print()
    
    try:
        result = subprocess.run([
            "python3", "connector_orto.py", "../graph_LVA1.json", "161.248", "26.922", "162.313"
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print("✅ SUCCESS - Algorithm Output:")
            print(result.stdout)
        else:
            print("❌ ERROR:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ EXECUTION ERROR: {e}")
    
    print_section("2. Generate DXF Visualization")
    print("Command: python3 connector_orto.py ../graph_LVA1.json 161.248 26.922 162.313 --dxf")
    print()
    
    try:
        result = subprocess.run([
            "python3", "connector_orto.py", "../graph_LVA1.json", "161.248", "26.922", "162.313", "--dxf"
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print("✅ SUCCESS - Algorithm Output:")
            print(result.stdout)
            
            # List DXF files
            dxf_files = list(Path(__file__).parent.glob("*161.2_26.9_162.3*.dxf"))
            if dxf_files:
                latest_dxf = max(dxf_files, key=os.path.getmtime)
                print(f"\n📐 Latest DXF File: {latest_dxf.name}")
                print(f"   Size: {latest_dxf.stat().st_size:,} bytes")
                print("   Content: Closest edge, projection point, Manhattan paths with colored circles")
        else:
            print("❌ ERROR:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ EXECUTION ERROR: {e}")


def demo_programmatic():
    """Demonstrate programmatic usage of the connector algorithm."""
    print_header("PROGRAMMATIC DEMO")
    
    print_section("1. Initialize Connector")
    
    try:
        # Initialize the connector
        graph_path = Path(__file__).parent.parent / "graph_LVA1.json"
        connector = ImprovedExternalPointConnector(
            graph_json_path=str(graph_path),
            verbose=True
        )
        print("✅ Connector initialized successfully")
        print(f"   Graph loaded with {len(connector.edges)} edges")
        print(f"   Grid size: {connector.grid_size:.3f}")
        
    except Exception as e:
        print(f"❌ INITIALIZATION ERROR: {e}")
        return
    
    print_section("2. Analyze Point P10")
    
    # Define point P10
    p10 = (161.248, 26.922, 162.313)
    print(f"Analyzing point P10: {p10}")
    print()
    
    try:
        # Find closest edge
        result = connector.find_closest_edge(p10)
        
        print("✅ ANALYSIS COMPLETE")
        print()
        print("📊 RESULTS:")
        print(f"   Closest Edge:")
        print(f"     Start: {result['best_edge'][0]}")
        print(f"     End:   {result['best_edge'][1]}")
        print(f"   Projection Point: {result['projection']}")
        print(f"   Euclidean Distance: {result['euclidean']:.3f} units")
        print(f"   Manhattan Distance: {result['best_manhattan_path']['manhattan']:.3f} units")
        print()
        
        print("🛤️  MANHATTAN PATHS:")
        for i, path in enumerate(result['all_paths'], 1):
            print(f"   Path {i} ({path['order']}):")
            print(f"     Distance: {path['manhattan']:.3f} units")
            print(f"     Points: {len(path['points'])} waypoints")
            for j, point in enumerate(path['points']):
                if j == 0:
                    print(f"       Start: {point}")
                elif j == len(path['points']) - 1:
                    print(f"       End:   {point}")
                else:
                    print(f"       Via:   {point}")
            print()
        
    except Exception as e:
        print(f"❌ ANALYSIS ERROR: {e}")
        return
    
    print_section("3. Export to DXF Programmatically")
    
    try:
        # Generate DXF file
        dxf_filename = "demo_p10_connection.dxf"
        dxf_path = Path(__file__).parent / dxf_filename
        
        connector.export_dxf(result, str(dxf_path))
        
        print(f"✅ DXF exported successfully: {dxf_filename}")
        print(f"   File size: {dxf_path.stat().st_size:,} bytes")
        print("   Content includes:")
        print("   - 🟡 Yellow circle: Starting point P10")
        print("   - 🔴 Red circle: Connection/projection point")
        print("   - ⚪ Gray line: Closest network edge")
        print("   - 🟢 Green elements: First Manhattan path")
        print("   - 🔵 Cyan elements: Second Manhattan path")
        
    except Exception as e:
        print(f"❌ DXF EXPORT ERROR: {e}")


def demo_validation():
    """Validate the demo results against expected values."""
    print_header("VALIDATION DEMO")
    
    print_section("Expected vs Actual Results for P10")
    
    try:
        # Initialize connector
        graph_path = Path(__file__).parent.parent / "graph_LVA1.json"
        connector = ImprovedExternalPointConnector(
            graph_json_path=str(graph_path),
            verbose=False  # Suppress output for cleaner validation
        )
        
        # Analyze P10
        p10 = (161.248, 26.922, 162.313)
        result = connector.find_closest_edge(p10)
        
        # Expected values
        expected_edge = ((152.666, 25.145, 160.124), (169.764, 25.145, 160.124))
        expected_projection = (161.248, 25.145, 160.124)
        expected_euclidean = 2.82  # Approximate
        expected_manhattan = 3.97  # Approximate
        
        print("🔍 VALIDATION RESULTS:")
        print()
        
        # Validate closest edge
        actual_edge = tuple(map(tuple, result['best_edge']))
        edge_match = actual_edge == expected_edge
        print(f"   Closest Edge: {'✅' if edge_match else '❌'}")
        print(f"     Expected: {expected_edge}")
        print(f"     Actual:   {actual_edge}")
        print()
        
        # Validate projection (with tolerance)
        actual_proj = tuple(result['projection'])
        proj_tolerance = 0.01
        proj_match = all(abs(actual_proj[i] - expected_projection[i]) < proj_tolerance for i in range(3))
        print(f"   Projection Point: {'✅' if proj_match else '❌'}")
        print(f"     Expected: {expected_projection}")
        print(f"     Actual:   {actual_proj}")
        print()
        
        # Validate distances (with tolerance)
        actual_euclidean = result['euclidean']
        actual_manhattan = result['best_manhattan_path']['manhattan']
        euclidean_match = abs(actual_euclidean - expected_euclidean) < 0.1
        manhattan_match = abs(actual_manhattan - expected_manhattan) < 0.1
        
        print(f"   Euclidean Distance: {'✅' if euclidean_match else '❌'}")
        print(f"     Expected: ~{expected_euclidean:.2f} units")
        print(f"     Actual:   {actual_euclidean:.3f} units")
        print()
        
        print(f"   Manhattan Distance: {'✅' if manhattan_match else '❌'}")
        print(f"     Expected: ~{expected_manhattan:.2f} units")
        print(f"     Actual:   {actual_manhattan:.3f} units")
        print()
        
        # Validate path count
        path_count = len(result['all_paths'])
        paths_match = path_count == 2
        print(f"   Path Count: {'✅' if paths_match else '❌'}")
        print(f"     Expected: 2 distinct paths")
        print(f"     Actual:   {path_count} paths")
        
        # Overall validation
        all_valid = all([edge_match, proj_match, euclidean_match, manhattan_match, paths_match])
        print()
        print(f"🎯 OVERALL VALIDATION: {'✅ ALL TESTS PASSED' if all_valid else '❌ SOME TESTS FAILED'}")
        
    except Exception as e:
        print(f"❌ VALIDATION ERROR: {e}")


def main():
    """Run the complete demo."""
    print_header("CONNECTOR_ORTO.PY DEMO")
    print("Demonstrating External Point Connector Algorithm")
    print("Point P10: (161.248, 26.922, 162.313)")
    print("Graph: graph_LVA1.json")
    
    try:
        # Run all demo sections
        demo_command_line()
        demo_programmatic()
        demo_validation()
        
        # Show summary
        print_header("DEMO COMPLETE")
        print("Demo finished successfully!")
        print("\nGenerated files:")
        demo_files = list(Path(__file__).parent.glob("*161.2_26.9_162.3*")) + \
                    list(Path(__file__).parent.glob("demo_p10_connection.dxf"))
        
        for file_path in demo_files:
            if file_path.exists():
                print(f"  - {file_path.name} ({file_path.stat().st_size:,} bytes)")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ DEMO ERROR: {e}")
    
    print("\n" + "="*60)
    print("Thank you for trying the External Point Connector Demo!")
    print("="*60)


if __name__ == "__main__":
    main() 