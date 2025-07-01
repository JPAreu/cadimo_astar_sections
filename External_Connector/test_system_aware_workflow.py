#!/usr/bin/env python3
"""
Comprehensive Test of System-Aware External Connector Workflow

This script tests the complete system-aware workflow:
1. System-filtered Manhattan path connection
2. System-aware graph extension  
3. System-aware A* pathfinding with astar_PPOF_systems.py

Usage:
    python3 test_system_aware_workflow.py [--system A|B|C]
"""

import subprocess
import json
import argparse
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return the result."""
    print(f"\n🔧 {description}")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"   ✅ Success")
        if result.stdout.strip():
            print(f"   Output: {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e}")
        if e.stdout:
            print(f"   Stdout: {e.stdout}")
        if e.stderr:
            print(f"   Stderr: {e.stderr}")
        raise

def test_system_workflow(system_filter="A"):
    """Test the complete system-aware workflow."""
    
    print(f"🚀 Testing System-Aware External Connector Workflow")
    print(f"🔧 System Filter: {system_filter}")
    
    # Test coordinates
    external_point = (180.839, 22.530, 166.634)
    
    # Step 1: System-filtered Manhattan Path Connection
    step1_cmd = [
        "python3", "connector_orto_systems.py",
        "tagged_extended_graph.json",
        str(external_point[0]), str(external_point[1]), str(external_point[2]),
        "--system", system_filter,
        "--json"
    ]
    
    run_command(step1_cmd, f"Step 1: System {system_filter} Manhattan Path Connection")
    
    # Check if connection file was created
    connection_file = f"system_{system_filter}_connection_{external_point[0]:.1f}_{external_point[1]:.1f}_{external_point[2]:.1f}.json"
    if not Path(connection_file).exists():
        raise FileNotFoundError(f"Connection file not created: {connection_file}")
    
    # Step 2: System-aware Graph Extension
    extended_graph_file = f"tagged_extended_graph_system_{system_filter}.json"
    step2_cmd = [
        "python3", "add_points_to_graph_multi_systems.py",
        "tagged_extended_graph.json",
        extended_graph_file,
        "--points-json", connection_file,
        "--external-point", str(external_point[0]), str(external_point[1]), str(external_point[2]),
        "--system", system_filter
    ]
    
    run_command(step2_cmd, f"Step 2: System {system_filter} Graph Extension")
    
    # Step 3: Test A* pathfinding with the extended graph
    # Test different scenarios based on system
    if system_filter == "A":
        # Test PE → A1 (same system)
        target_point = (170.839, 12.530, 156.634)  # A1
        step3_cmd = [
            "python3", "../astar_PPOF_systems.py", "direct",
            extended_graph_file,
            str(external_point[0]), str(external_point[1]), str(external_point[2]),
            str(target_point[0]), str(target_point[1]), str(target_point[2]),
            "--cable", "A"
        ]
        run_command(step3_cmd, f"Step 3: System {system_filter} A* Pathfinding (PE → A1)")
        
    elif system_filter == "B":
        # Test PE → B3 (same system)
        target_point = (176.062, 2.416, 153.960)  # B3
        step3_cmd = [
            "python3", "../astar_PPOF_systems.py", "direct",
            extended_graph_file,
            str(external_point[0]), str(external_point[1]), str(external_point[2]),
            str(target_point[0]), str(target_point[1]), str(target_point[2]),
            "--cable", "B"
        ]
        run_command(step3_cmd, f"Step 3: System {system_filter} A* Pathfinding (PE → B3)")
        
    else:  # System C
        # Test PE → A1 and PE → B3 (cross-system with cable C)
        targets = [
            ((170.839, 12.530, 156.634), "A1", "C"),  # A1 with cable C (cross-system)
            ((176.062, 2.416, 153.960), "B3", "C"),  # B3 with cable C (cross-system)
        ]
        
        for target_point, target_name, cable_type in targets:
            step3_cmd = [
                "python3", "../astar_PPOF_systems.py", "direct",
                extended_graph_file,
                str(external_point[0]), str(external_point[1]), str(external_point[2]),
                str(target_point[0]), str(target_point[1]), str(target_point[2]),
                "--cable", cable_type
            ]
            run_command(step3_cmd, f"Step 3: System {system_filter} A* Pathfinding (PE → {target_name})")
    
    print(f"\n🎉 System {system_filter} workflow completed successfully!")
    print(f"📁 Files created:")
    print(f"   - {connection_file}")
    print(f"   - {extended_graph_file}")

def main():
    parser = argparse.ArgumentParser(description="Test system-aware external connector workflow")
    parser.add_argument("--system", choices=["A", "B", "C"], default="A",
                        help="System to test (A, B, or C)")
    
    args = parser.parse_args()
    
    try:
        test_system_workflow(args.system)
    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()
