# A* Pathfinding with Cable Type and System Filtering

A sophisticated A* pathfinding system that incorporates cable type restrictions and system filtering for realistic infrastructure routing.

## 🚀 Quick Start

```bash
# Clone or download the project files
# Run a simple test
python3 astar_PPOF_systems.py direct sample_tagged_graph.json 100 200 300 120 200 300 --cable A
```

## 📋 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Cable Types](#cable-types)
- [Graph Format](#graph-format)
- [Commands](#commands)
- [Examples](#examples)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)
- [Contributing](#contributing)

## ✨ Features

- **Cable Type Restrictions**: Support for different cable types with system access rules
- **System Filtering**: Automatic filtering of graph based on cable capabilities
- **Multiple Pathfinding Modes**: Direct, PPO (waypoint), Multi-PPO, and Forward Path
- **Early Validation**: Fail-fast approach for invalid endpoint combinations
- **Comprehensive Testing**: Full test suite with multiple scenarios
- **Clear Error Messages**: Detailed feedback for debugging and troubleshooting

## 🔧 Installation

### Prerequisites

- Python 3.7 or higher
- Required Python modules (included in standard library):
  - `json`
  - `argparse`
  - `heapq`
  - `math`
  - `collections`

### Setup

1. **Download the required files:**
   ```bash
   # Core files needed:
   # - astar_PPOF_systems.py (main script)
   # - cable_filter.py (utility module)
   # - astar_PPO_forbid.py (dependency)
   ```

2. **Verify installation:**
   ```bash
   python3 astar_PPOF_systems.py help
   ```

3. **Run tests:**
   ```bash
   python3 test_astar_systems.py
   ```

## 🎯 Usage

### Basic Syntax

```bash
python3 astar_PPOF_systems.py <command> <graph_file> <coordinates> --cable <A|B|C> [options]
```

### Required Arguments

- `command`: Pathfinding command (direct, ppo, multi_ppo, forward_path)
- `graph_file`: Path to tagged graph JSON file
- `coordinates`: Space-separated coordinates (format varies by command)
- `--cable`: Cable type (A, B, or C)

### Optional Arguments

- `--ppo X Y Z`: Add PPO waypoint (multi_ppo command only)
- `help`: Display help information

## 📡 Cable Types

| Cable Type | System Access | Use Case |
|------------|---------------|----------|
| **A** | System A only | Dedicated System A infrastructure |
| **B** | System B only | Dedicated System B infrastructure |
| **C** | Systems A & B | Cross-system integration cables |

### Access Rules

- **Cable A**: ✅ System A nodes/edges, ❌ System B nodes/edges
- **Cable B**: ❌ System A nodes/edges, ✅ System B nodes/edges  
- **Cable C**: ✅ System A nodes/edges, ✅ System B nodes/edges

## 📊 Graph Format

The system requires a tagged graph JSON format with system identifiers:

```json
{
  "nodes": {
    "(100.0, 200.0, 300.0)": {"sys": "A"},
    "(150.0, 200.0, 300.0)": {"sys": "B"},
    "(125.0, 210.0, 300.0)": {"sys": "A"}
  },
  "edges": [
    {"from": "(100.0, 200.0, 300.0)", "to": "(110.0, 200.0, 300.0)", "sys": "A"},
    {"from": "(130.0, 200.0, 300.0)", "to": "(140.0, 200.0, 300.0)", "sys": "B"},
    {"from": "(125.0, 210.0, 300.0)", "to": "(125.0, 220.0, 300.0)", "sys": "A"}
  ]
}
```

### Format Requirements

- **Nodes**: Dictionary with coordinate strings as keys and system tags as values
- **Edges**: Array of edge objects with `from`, `to`, and `sys` properties
- **Coordinates**: String format `"(x, y, z)"` with consistent precision
- **System Tags**: Must be `"A"` or `"B"`

## 🎮 Commands

### 1. Direct Pathfinding

Find the shortest path between two points.

```bash
python3 astar_PPOF_systems.py direct <graph_file> <origin_x> <origin_y> <origin_z> <dest_x> <dest_y> <dest_z> --cable <A|B|C>
```

**Example:**
```bash
python3 astar_PPOF_systems.py direct sample_tagged_graph.json 100 200 300 120 200 300 --cable A
```

### 2. PPO (Single Waypoint) Pathfinding

Route through a mandatory waypoint (Punto de Paso Obligatorio).

```bash
python3 astar_PPOF_systems.py ppo <graph_file> <origin_x> <origin_y> <origin_z> <ppo_x> <ppo_y> <ppo_z> <dest_x> <dest_y> <dest_z> --cable <A|B|C>
```

**Example:**
```bash
python3 astar_PPOF_systems.py ppo sample_tagged_graph.json 100 200 300 125 210 300 100 210 300 --cable A
```

### 3. Multi-PPO Pathfinding

Route through multiple mandatory waypoints in sequence.

```bash
python3 astar_PPOF_systems.py multi_ppo <graph_file> <origin_x> <origin_y> <origin_z> <dest_x> <dest_y> <dest_z> --cable <A|B|C> --ppo <x> <y> <z> [--ppo <x> <y> <z> ...]
```

**Example:**
```bash
python3 astar_PPOF_systems.py multi_ppo sample_tagged_graph.json 100 200 300 100 210 300 --cable A --ppo 120 200 300 --ppo 125 210 300
```

### 4. Forward Path

Route with backtracking prevention (currently uses PPO logic).

```bash
python3 astar_PPOF_systems.py forward_path <graph_file> <origin_x> <origin_y> <origin_z> <ppo_x> <ppo_y> <ppo_z> <dest_x> <dest_y> <dest_z> --cable <A|B|C>
```

## 📝 Examples

### Example 1: System A Cable Routing

```bash
# Route Cable A within System A (succeeds)
python3 astar_PPOF_systems.py direct sample_tagged_graph.json 100 200 300 120 200 300 --cable A

# Output:
# ✅ Direct path found!
#    Path length: 3 points
#    Nodes explored: 3
#    Total distance: 20.000 units
#    Cable type: A (Systems: A)
```

### Example 2: System Boundary Enforcement

```bash
# Try to route Cable A to System B (fails)
python3 astar_PPOF_systems.py direct sample_tagged_graph.json 100 200 300 150 200 300 --cable A

# Output:
# ❌ Error: Destination node in forbidden system 'B': (150.0, 200.0, 300.0)
```

### Example 3: Cross-System Routing

```bash
# Route Cable C across systems (succeeds)
python3 astar_PPOF_systems.py direct sample_tagged_graph.json 100 200 300 150 200 300 --cable C

# Output:
# ✅ Direct path found!
#    Path length: 6 points
#    Nodes explored: 6
#    Total distance: 50.000 units
#    Cable type: C (Systems: A, B)
```

### Example 4: Multi-PPO with System Filtering

```bash
# Route through multiple waypoints with Cable A
python3 astar_PPOF_systems.py multi_ppo sample_tagged_graph.json 100 200 300 100 210 300 --cable A --ppo 120 200 300 --ppo 125 210 300

# Output:
# ✅ Multi-PPO path found!
#    Path length: 5 points
#    Total nodes explored: 7
#    Total distance: 56.180 units
#    Cable type: A (Systems: A)
#
# 📊 Segment breakdown:
#    Segment 1: 3 points, 3 nodes explored
#    Segment 2: 1 points, 2 nodes explored
#    Segment 3: 1 points, 2 nodes explored
```

## 🧪 Testing

### Run All Tests

```bash
python3 test_astar_systems.py
```

### Test Categories

1. **System A Routing**: Cable A within System A infrastructure
2. **System B Routing**: Cable B within System B infrastructure
3. **Cross-System Routing**: Cable C across both systems
4. **Boundary Enforcement**: Proper blocking of forbidden access
5. **PPO Functionality**: Waypoint routing with system filtering
6. **Multi-PPO Functionality**: Multiple waypoint routing

### Sample Test Output

```
🚀 A* Pathfinding with Cable Type and System Filtering - Test Suite
================================================================================

🧪 Cable A: Direct pathfinding within System A (should succeed)
✅ SUCCESS

🧪 Cable A: Trying to reach System B destination (should fail)
❌ EXPECTED FAILURE

🎯 Test Suite Complete!
   ✅ Successful tests show the cable type restrictions working correctly
   ❌ Failed tests demonstrate proper system boundary enforcement
```

## 🐛 Troubleshooting

### Common Issues

#### 1. "Graph file not found"
```bash
❌ Error: Graph file not found: your_graph.json
```
**Solution**: Verify the graph file path and ensure the file exists.

#### 2. "Node not found in graph"
```bash
❌ Error: Source node not found in graph: (100.0, 200.0, 300.0)
```
**Solution**: Check coordinate format and ensure exact match with graph nodes.

#### 3. "Destination node in forbidden system"
```bash
❌ Error: Destination node in forbidden system 'B': (150.0, 200.0, 300.0)
```
**Solution**: Use appropriate cable type (Cable C for cross-system routing).

#### 4. "No route found inside permitted systems"
```bash
❌ Error: No route found inside the permitted system(s) {'A'}
```
**Solution**: Verify connectivity within allowed systems or use different cable type.

### Debug Tips

1. **Check Graph Structure**: Verify nodes and edges have proper system tags
2. **Validate Coordinates**: Ensure coordinate format matches exactly
3. **Test Connectivity**: Use Cable C to test if path exists across systems
4. **Run Test Suite**: Use `test_astar_systems.py` to verify installation

## 📚 API Reference

### Cable Filter Module (`cable_filter.py`)

#### Functions

- `load_tagged_graph(path)`: Load graph with system tags
- `build_adj(graph_json, allowed_systems)`: Create filtered adjacency list
- `validate_endpoints(graph_json, src, dst, allowed_systems)`: Validate endpoint systems
- `get_cable_info(cable_type)`: Get cable type information
- `coord_to_key(coord)`: Convert coordinate tuple to string key
- `key_to_coord(key)`: Convert string key to coordinate tuple

#### Constants

- `ALLOWED`: Dictionary mapping cable types to allowed systems

### Main Script (`astar_PPOF_systems.py`)

#### Classes

- `SystemFilteredGraph`: Main graph class with system filtering
- `FilteredGraph`: Lightweight A* implementation for filtered adjacency

#### Key Methods

- `find_path_direct(origin, destination)`: Direct pathfinding
- `find_path_with_ppo(origin, ppo, destination)`: Single PPO pathfinding
- `find_path_with_multiple_ppos(origin, ppos, destination)`: Multi-PPO pathfinding

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Run the test suite
5. Submit a pull request

### Code Style

- Follow PEP 8 guidelines
- Add docstrings for all functions
- Include type hints where appropriate
- Write comprehensive tests for new features

### Testing New Features

```bash
# Run existing tests
python3 test_astar_systems.py

# Add new test cases to test_astar_systems.py
# Test with sample graph and real-world scenarios
```

## 📄 License

This project is part of the CADIMO A* spatial sections pathfinding system.

## 🔗 Related Files

- `astar_PPO_forbid.py`: Base pathfinding functionality
- `cable_filter.py`: System filtering utilities
- `sample_tagged_graph.json`: Example graph for testing
- `test_astar_systems.py`: Comprehensive test suite
- `ASTAR_SYSTEMS_SUMMARY.md`: Detailed technical documentation

---

For more detailed technical information, see `ASTAR_SYSTEMS_SUMMARY.md`. 