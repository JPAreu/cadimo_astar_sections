# A* Pathfinding with Cable Type and System Filtering

## Overview

The `astar_PPOF_systems.py` script implements a sophisticated A* pathfinding system that incorporates cable type restrictions and system filtering. This allows for realistic cable routing that respects system boundaries and cable capabilities.

## 🔧 **Core Components**

### **1. Cable Filter Module (`cable_filter.py`)**
- **Purpose**: Utility module for system filtering based on cable types
- **Key Functions**:
  - `load_tagged_graph()`: Loads graphs with system tags
  - `build_adj()`: Creates filtered adjacency lists
  - `validate_endpoints()`: Ensures endpoints are in allowed systems
  - `get_cable_info()`: Provides cable type information

### **2. Main Script (`astar_PPOF_systems.py`)**
- **Purpose**: Main pathfinding script with system filtering
- **Key Classes**:
  - `SystemFilteredGraph`: Manages filtered graph operations
  - `FilteredGraph`: Lightweight A* implementation for filtered adjacency

## 📋 **Cable Type Rules**

| Cable Type | Allowed Systems | Description |
|------------|----------------|-------------|
| **A** | System A only | Restricted to System A infrastructure |
| **B** | System B only | Restricted to System B infrastructure |
| **C** | Systems A & B | Can traverse both systems freely |

## 🎯 **Supported Commands**

### **1. Direct Pathfinding**
```bash
python3 astar_PPOF_systems.py direct <graph_file> <origin_x> <origin_y> <origin_z> <dest_x> <dest_y> <dest_z> --cable <A|B|C>
```

### **2. PPO (Single Waypoint) Pathfinding**
```bash
python3 astar_PPOF_systems.py ppo <graph_file> <origin_x> <origin_y> <origin_z> <ppo_x> <ppo_y> <ppo_z> <dest_x> <dest_y> <dest_z> --cable <A|B|C>
```

### **3. Multi-PPO Pathfinding**
```bash
python3 astar_PPOF_systems.py multi_ppo <graph_file> <origin_x> <origin_y> <origin_z> <dest_x> <dest_y> <dest_z> --cable <A|B|C> --ppo <x> <y> <z> [--ppo <x> <y> <z> ...]
```

### **4. Forward Path (Prevents Backtracking)**
```bash
python3 astar_PPOF_systems.py forward_path <graph_file> <origin_x> <origin_y> <origin_z> <ppo_x> <ppo_y> <ppo_z> <dest_x> <dest_y> <dest_z> --cable <A|B|C>
```

## 📊 **Graph Format**

The system expects a tagged graph JSON format:

```json
{
  "nodes": {
    "(x, y, z)": {"sys": "A"},
    "(x, y, z)": {"sys": "B"},
    ...
  },
  "edges": [
    {"from": "(x1, y1, z1)", "to": "(x2, y2, z2)", "sys": "A"},
    {"from": "(x3, y3, z3)", "to": "(x4, y4, z4)", "sys": "B"},
    ...
  ]
}
```

## 🔍 **System Filtering Logic**

### **Step-by-Step Process:**

1. **Load Graph**: Read tagged graph with system identifiers
2. **Select Cable Type**: User specifies cable type (A, B, or C)
3. **Determine Allowed Systems**: Map cable type to permitted systems
4. **Validate Endpoints**: Check if origin/destination are in allowed systems
5. **Filter Graph**: Remove edges/nodes not in allowed systems
6. **Run A* Algorithm**: Execute pathfinding on filtered graph
7. **Return Results**: Provide path or error message

### **Validation Rules:**
- **Endpoint Validation**: Both origin and destination must be in allowed systems
- **Edge Filtering**: Only edges tagged with allowed systems are included
- **Node Filtering**: Only nodes in allowed systems are accessible
- **Early Termination**: Fails fast if endpoints are in forbidden systems

## 🧪 **Test Results**

The comprehensive test suite (`test_astar_systems.py`) demonstrates:

### **✅ Successful Scenarios:**
- Cable A: Direct pathfinding within System A
- Cable B: Direct pathfinding within System B  
- Cable C: Cross-system pathfinding (A→B)
- Cable A: PPO pathfinding within System A
- Cable A: Multi-PPO pathfinding within System A
- Cable C: Cross-system Multi-PPO pathfinding

### **❌ Properly Blocked Scenarios:**
- Cable A: Trying to reach System B destination
- Cable B: Trying to reach System A destination

## 🚀 **Performance Characteristics**

### **Filtering Efficiency:**
- **Graph Loading**: O(V + E) where V = nodes, E = edges
- **System Filtering**: O(E) for edge filtering
- **Endpoint Validation**: O(1) per endpoint
- **A* Pathfinding**: Standard A* complexity on filtered graph

### **Memory Usage:**
- **Original Graph**: Loaded once, kept in memory
- **Filtered Graph**: Lightweight adjacency list for allowed systems
- **Pathfinding**: Standard A* memory requirements

## 📁 **File Structure**

```
cadimo_astar_spatial_sections/
├── astar_PPOF_systems.py          # Main script
├── cable_filter.py                # Filtering utilities  
├── sample_tagged_graph.json       # Sample graph for testing
├── test_astar_systems.py          # Comprehensive test suite
└── ASTAR_SYSTEMS_SUMMARY.md       # This documentation
```

## 🔗 **Integration with Existing System**

### **Compatibility:**
- **Builds on**: Existing `astar_PPO_forbid.py` functionality
- **Extends**: A* pathfinding with system awareness
- **Maintains**: All original PPO and forbidden edge capabilities
- **Adds**: Cable type restrictions and system filtering

### **Migration Path:**
- **Drop-in**: Can be used alongside existing scripts
- **Incremental**: Existing graphs can be tagged with system identifiers
- **Backward Compatible**: Original functionality preserved

## 🎯 **Use Cases**

### **1. Cable Installation Planning**
- Route cables through appropriate system infrastructure
- Ensure compliance with system separation requirements
- Optimize paths while respecting cable capabilities

### **2. Maintenance Route Planning**
- Plan maintenance access routes using appropriate cable types
- Avoid cross-system contamination during maintenance
- Ensure personnel use correct system pathways

### **3. System Integration**
- Plan integration points between System A and System B
- Use Cable C for cross-system connections
- Maintain system isolation where required

## 🚀 **Future Enhancements**

### **Potential Extensions:**
- **Dynamic System Assignment**: Runtime system tag modification
- **Cable Capacity Modeling**: Weight/capacity constraints per cable type
- **Multi-Criteria Optimization**: Distance + system preference weighting
- **Temporal Constraints**: Time-based system availability
- **Export Integration**: DXF export with system color coding

## 📝 **Example Usage**

```bash
# Cable A routing within System A
python3 astar_PPOF_systems.py direct graph_tagged.json 100 200 300 120 200 300 --cable A

# Cable C cross-system routing with waypoints  
python3 astar_PPOF_systems.py multi_ppo graph_tagged.json 100 200 300 150 210 300 --cable C --ppo 125 210 300 --ppo 140 200 300

# System boundary enforcement (will fail)
python3 astar_PPOF_systems.py direct graph_tagged.json 100 200 300 150 200 300 --cable A
```

This implementation provides a robust foundation for cable-aware pathfinding with system isolation, enabling realistic infrastructure routing while maintaining the flexibility and performance of the original A* implementation. 