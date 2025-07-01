# DEMO: Scenario A - Cable-Aware Pathfinding with Forbidden Sections

## Overview

This demo showcases **Scenario A**, a comprehensive test case for the `astar_PPOF_systems.py` cable-aware pathfinding system. It demonstrates the complete workflow from file validation to pathfinding execution and result analysis.

## Use Case Description

**Scenario A** represents a real-world cable routing situation where:

- **Origin (A1)**: Cable installation starts at `(170.839, 12.530, 156.634)`
- **Destination (A2)**: Cable must reach `(182.946, 13.304, 157.295)`
- **Cable Type**: Cable A (restricted to System A only)
- **Forbidden Section**: Edge between `(177.381, 14.056, 157.295)` and `(178.482, 14.056, 157.295)` (Tramo ID 163)
- **PPO Point (A5)**: Mandatory waypoint at `(196.310, 18.545, 153.799)` for maintenance access

## Demo Features

### 🎯 Three Pathfinding Scenarios

1. **Direct Path (GREEN)** - Optimal route without restrictions
2. **Forbidden-Avoiding Path (RED)** - Route that avoids blocked sections
3. **PPO Path (MAGENTA)** - Route through mandatory waypoint with restrictions

### 📊 Comprehensive Analysis

- Path length comparison (points)
- Distance calculations (3D Euclidean)
- Node exploration efficiency
- Execution time measurements
- Impact factor analysis

### 🔧 System Validation

- File existence verification
- Coordinate validation against graph
- System compatibility checks
- Cable type restrictions

## Running the Demo

```bash
python3 demo_scenario_A.py
```

## Expected Results

Based on the current graph configuration:

| Scenario | Points | Nodes Explored | Distance (units) | Time (s) |
|----------|--------|----------------|------------------|----------|
| **Direct (GREEN)** | 18 | 20 | 14.227 | 0.001 |
| **Forbidden-Avoid (RED)** | 51 | 72 | 79.332 | 0.008 |
| **PPO (MAGENTA)** | 101 | 145 | 126.518 | 0.008 |

### Key Findings

- **Forbidden Section Impact**: 2.8x path length increase, 5.6x distance increase
- **System Filtering**: Successfully restricts routing to Cable A (System A only)
- **Performance**: Sub-millisecond execution for direct paths, ~8ms for complex scenarios

## File Dependencies

The demo requires these supporting files:

- `graph_LV_combined.json` (91,376 bytes) - Combined graph with system labels
- `tramo_map_combined.json` (32,008 bytes) - Edge ID mappings
- `forbidden_scenario_A.json` (5 bytes) - Contains `[163]` (forbidden Tramo ID)

## Technical Architecture

### Algorithm Flow

1. **System Filtering**: Loads graph and filters by cable type permissions
2. **Coordinate Validation**: Verifies all points exist in the filtered graph
3. **Engine Selection**: 
   - Simple `FilteredGraph` for direct paths
   - `ForbiddenEdgeGraph` for restriction-aware routing
4. **A* Execution**: Runs pathfinding with Euclidean heuristic
5. **Result Processing**: Calculates distances and performance metrics

### Cable System Logic

```python
CABLE_A = {
    'allowed_systems': {'A'},
    'description': 'System A only'
}
```

- Cable A restricts routing to System A nodes only
- Graph filtering removes 261 System B nodes (507 → 246 nodes)
- Maintains full connectivity within permitted system

### Forbidden Edge Processing

- Tramo ID 163 maps to edge `(177.381, 14.056, 157.295) ↔ (178.482, 14.056, 157.295)`
- Coordinate formatting uses 3-decimal precision: `f"({x:.3f}, {y:.3f}, {z:.3f})"`
- Edge removal forces pathfinding to find alternative routes

## Code Structure

```python
class ScenarioADemo:
    def __init__(self):
        # Scenario coordinates and configuration
        
    def validate_files(self):
        # Check required files exist
        
    def show_scenario_info(self):
        # Display configuration details
        
    def verify_coordinates(self):
        # Validate points exist in graph
        
    def run_pathfinding_tests(self):
        # Execute all three scenarios
        
    def analyze_results(self):
        # Compare and analyze results
        
    def run_complete_demo(self):
        # Orchestrate full demonstration
```

## Integration Points

This demo integrates with:

- **`astar_PPOF_systems.py`**: Main pathfinding engine
- **`cable_filter.py`**: System filtering utilities
- **`astar_PPO_forbid.py`**: Forbidden edge handling
- **Graph JSON files**: Spatial network data
- **Tramo mapping**: Edge identification system

## Validation Results

✅ **File Validation**: All required files present and properly sized
✅ **Coordinate Verification**: All 5 key points found in System A
✅ **Pathfinding Execution**: All 3 scenarios completed successfully
✅ **System Filtering**: Proper restriction to Cable A permissions
✅ **Forbidden Edge Handling**: Tramo 163 correctly avoided

## Use Cases

This demo is ideal for:

- **System Testing**: Validate pathfinding algorithms
- **Performance Benchmarking**: Measure execution times
- **Constraint Validation**: Test forbidden section handling
- **Multi-scenario Analysis**: Compare different routing approaches
- **Integration Testing**: Verify component interactions

## Next Steps

To extend this demo:

1. **Add DXF Export**: Visual output for CAD systems
2. **Multiple Cable Types**: Test Cable B and Cable C scenarios
3. **Batch Processing**: Run multiple scenarios automatically
4. **Performance Profiling**: Detailed execution analysis
5. **Error Handling**: Comprehensive edge case testing

## Conclusion

Scenario A successfully demonstrates the complete cable-aware pathfinding workflow, showing significant impact from forbidden sections (5.6x distance increase) while maintaining system compatibility and performance. The demo validates that the `astar_PPOF_systems.py` algorithm is ready for production use in real-world cable routing applications. 