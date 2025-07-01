# A* Pathfinding with Cable Type and System Filtering - Enhanced Edition

A sophisticated **standalone** A* pathfinding system that incorporates cable type restrictions, system filtering, and **intelligent diagnostic capabilities** for realistic infrastructure routing.

## 🚀 Quick Start

```bash
# Test the system with automatic diagnosis
python3 astar_PPOF_systems.py diagnose 174.860 15.369 136.587 139.232 28.845 139.993

# Run the suggested command
python3 astar_PPOF_systems.py direct graph_LV_combined.json 174.860 15.369 136.587 139.232 28.845 139.993 --cable C
```

## 📋 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Cable Types](#cable-types)
- [Commands](#commands)
- [Diagnostic System](#diagnostic-system)
- [Graph Format](#graph-format)
- [Examples](#examples)
- [Error Handling](#error-handling)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)
- [Migration Guide](#migration-guide)

## ✨ Features

### Core Pathfinding
- **Cable Type Restrictions**: Support for different cable types with system access rules
- **System Filtering**: Automatic filtering of graph based on cable capabilities
- **Multiple Pathfinding Modes**: Direct, PPO (waypoint), Multi-PPO, and Forward Path
- **Standalone Operation**: No external dependencies - everything integrated in one file

### 🔍 Enhanced Diagnostic System
- **Automatic Error Diagnosis**: Intelligent analysis when pathfinding fails
- **Cross-Graph Analysis**: Check endpoints across multiple graph files
- **Smart Recommendations**: Specific cable type and graph suggestions
- **Auto-Discovery**: Automatic detection of available graph files
- **Enhanced Error Messages**: Detailed feedback with actionable solutions

### 🛡️ Intelligent Error Recovery
- **Fail-Fast Validation**: Early detection of invalid configurations
- **Alternative Suggestions**: Automatic recommendations for working configurations
- **System Compatibility Analysis**: Detailed breakdown of cable-system compatibility
- **Command Generation**: Ready-to-use command suggestions

## 🔧 Installation

### Prerequisites

- **Python 3.7 or higher**
- **No external dependencies** - everything is integrated!

### Setup

1. **Download the standalone script:**
   ```bash
   # Only one file needed:
   # - astar_PPOF_systems.py (fully integrated standalone script)
   ```

2. **Verify installation:**
   ```bash
   python3 astar_PPOF_systems.py --help
   ```

3. **Run diagnostic test:**
   ```bash
   python3 astar_PPOF_systems.py diagnose 100 200 300 120 200 300
   ```

## 🎯 Usage

### Basic Syntax

```bash
python3 astar_PPOF_systems.py <command> <arguments...>
```

### Command Structure

| Command | Purpose | Cable Required |
|---------|---------|----------------|
| `direct` | Direct pathfinding | ✅ |
| `ppo` | Single waypoint routing | ✅ |
| `multi_ppo` | Multiple waypoint routing | ✅ |
| `forward_path` | Backtracking prevention | ✅ |
| `diagnose` | Endpoint analysis | ❌ |

## 📡 Cable Types

| Cable Type | System Access | Use Case | Cross-System |
|------------|---------------|----------|--------------|
| **A** | System A only | Dedicated System A infrastructure | ❌ |
| **B** | System B only | Dedicated System B infrastructure | ❌ |
| **C** | Systems A & B | Cross-system integration cables | ✅ |

### Access Matrix

```
           │ System A │ System B │
───────────┼──────────┼──────────┤
 Cable A   │    ✅    │    ❌    │
 Cable B   │    ❌    │    ✅    │
 Cable C   │    ✅    │    ✅    │
```

## 🎮 Commands

### 1. Direct Pathfinding

Find the shortest path between two points.

```bash
python3 astar_PPOF_systems.py direct <graph_file> <cable_type> <x1> <y1> <z1> <x2> <y2> <z2>
```

**Example:**
```bash
python3 astar_PPOF_systems.py direct graph_LV1A.json A 139.232 28.845 139.993 152.290 17.883 160.124
```

### 2. PPO (Single Waypoint) Pathfinding

Route through a mandatory waypoint (Punto de Paso Obligatorio).

```bash
python3 astar_PPOF_systems.py ppo <graph_file> <cable_type> <x1> <y1> <z1> <xp> <yp> <zp> <x2> <y2> <z2>
```

**Example:**
```bash
python3 astar_PPOF_systems.py ppo graph_LV_combined.json C 139.232 28.845 139.993 145.0 25.0 150.0 174.860 15.369 136.587
```

### 3. Multi-PPO Pathfinding

Route through multiple mandatory waypoints in sequence.

```bash
python3 astar_PPOF_systems.py multi_ppo <graph_file> <cable_type> <x1> <y1> <z1> <xp1> <yp1> <zp1> <xp2> <yp2> <zp2> ... <x2> <y2> <z2>
```

**Example:**
```bash
python3 astar_PPOF_systems.py multi_ppo graph_LV1B.json B 174.860 15.369 136.587 170.0 20.0 140.0 165.0 25.0 145.0 160.0 30.0 150.0
```

### 4. Forward Path

Route with backtracking prevention.

```bash
python3 astar_PPOF_systems.py forward_path <graph_file> <cable_type> <x1> <y1> <z1> <xp> <yp> <zp> <x2> <y2> <z2>
```

### 5. 🔍 Diagnostic Analysis (NEW!)

Analyze endpoints across multiple graphs and get intelligent recommendations.

```bash
python3 astar_PPOF_systems.py diagnose <x1> <y1> <z1> <x2> <y2> <z2> [graph1] [graph2] ...
```

**Examples:**
```bash
# Auto-discover available graphs
python3 astar_PPOF_systems.py diagnose 174.860 15.369 136.587 139.232 28.845 139.993

# Specify specific graphs to check
python3 astar_PPOF_systems.py diagnose 174.860 15.369 136.587 139.232 28.845 139.993 graph_LV1A.json graph_LV1B.json
```

## 🔍 Diagnostic System

### Automatic Error Analysis

When pathfinding fails, the system automatically:

1. **Detects the Error Type**: Coordinate not found, system restrictions, etc.
2. **Runs Cross-Graph Analysis**: Checks endpoints across available graphs
3. **Provides Specific Recommendations**: Cable types, graph files, exact commands
4. **Suggests Alternatives**: Working configurations for your endpoints

### Diagnostic Output Example

```bash
🔍 Cross-System Endpoint Analysis
==================================================
Source: (174.860, 15.369, 136.587)
Destination: (139.232, 28.845, 139.993)

📍 Source Analysis:
   ✅ Found in graph_LV_combined.json (System B)
   ✅ Found in graph_LV1B.json (System B)

📍 Destination Analysis:
   ✅ Found in graph_LV_combined.json (System A)
   ✅ Found in graph_LV1A.json (System A)

🔌 Cable Compatibility Analysis:
   ✅ Compatible cable types: ['C']
      Cable C: Can access systems ['A', 'B']

💡 Routing Recommendations:
   ✅ Both endpoints found in: ['graph_LV_combined.json']
   🚀 Use cable type(s) ['C'] with any of these graphs
   💡 Try: python3 astar_PPOF_systems.py direct graph_LV_combined.json 174.860 15.369 136.587 139.232 28.845 139.993 --cable C
==================================================
```

### Auto-Discovery Features

- **Graph File Detection**: Automatically finds `graph_*.json` files
- **Pattern Matching**: Intelligent file pattern recognition
- **Multi-Graph Analysis**: Simultaneous analysis across multiple graphs
- **Smart Filtering**: Focuses on relevant graphs for your endpoints

## 📊 Graph Format

The system requires a tagged graph JSON format with system identifiers:

```json
{
  "nodes": {
    "(139.232, 28.845, 139.993)": {"sys": "A"},
    "(174.860, 15.369, 136.587)": {"sys": "B"},
    "(145.000, 25.000, 150.000)": {"sys": "A"}
  },
  "edges": [
    {"from": "(139.232, 28.845, 139.993)", "to": "(140.000, 29.000, 140.000)", "sys": "A"},
    {"from": "(174.860, 15.369, 136.587)", "to": "(175.000, 16.000, 137.000)", "sys": "B"},
    {"from": "(145.000, 25.000, 150.000)", "to": "(146.000, 26.000, 151.000)", "sys": "A"}
  ]
}
```

### Format Requirements

- **Coordinate Precision**: 3 decimal places: `"(x.xxx, y.yyy, z.zzz)"`
- **System Tags**: Must be `"A"` or `"B"`
- **Node Format**: `{"sys": "A"}` or `{"sys": "B"}`
- **Edge Format**: `{"from": "...", "to": "...", "sys": "A"}`

## 📝 Examples

### Example 1: Successful Cross-System Routing

```bash
# Use diagnostic to find the right configuration
python3 astar_PPOF_systems.py diagnose 174.860 15.369 136.587 139.232 28.845 139.993

# Output suggests Cable C with graph_LV_combined.json
python3 astar_PPOF_systems.py direct graph_LV_combined.json C 174.860 15.369 136.587 139.232 28.845 139.993

# Result:
# ✅ Direct path found: 74 points, 126.100 units, 326 nodes explored
```

### Example 2: System Boundary Enforcement with Auto-Diagnosis

```bash
# Try incompatible cable/system combination
python3 astar_PPOF_systems.py direct graph_LV1A.json A 174.860 15.369 136.587 139.232 28.845 139.993

# System automatically runs diagnosis:
# ❌ Error: Source node not found in graph: (174.860, 15.369, 136.587)
# 🔍 Running automatic diagnosis...
# [Diagnostic output with recommendations]
```

### Example 3: Multi-PPO with System Filtering

```bash
# Complex routing with multiple waypoints
python3 astar_PPOF_systems.py multi_ppo graph_LV1A.json A 139.232 28.845 139.993 145.0 25.0 150.0 148.0 27.0 148.0 152.290 17.883 160.124

# Output:
# ✅ Multi-PPO path found: 25 points, 67.543 units, 89 nodes explored
# 
# Segment breakdown:
#   Segment 1: 8 points, 28 nodes explored
#   Segment 2: 6 points, 31 nodes explored  
#   Segment 3: 11 points, 30 nodes explored
```

### Example 4: Diagnostic-Driven Workflow

```bash
# Start with diagnosis for unknown endpoints
python3 astar_PPOF_systems.py diagnose 100.000 200.000 300.000 150.000 250.000 350.000

# If endpoints not found, system suggests:
# ❌ Neither endpoint found in provided graphs
# 🔧 Check coordinate precision and graph file paths

# Adjust coordinates based on available data
python3 astar_PPOF_systems.py diagnose 139.232 28.845 139.993 152.290 17.883 160.124

# Get specific recommendations and execute
```

## 🛡️ Error Handling

### Enhanced Error Recovery

The system provides **three levels** of error handling:

1. **Preventive Validation**: Early detection of invalid inputs
2. **Automatic Diagnosis**: Intelligent analysis of failures
3. **Recovery Suggestions**: Specific recommendations for fixes

### Error Types and Solutions

#### Coordinate Not Found
```bash
❌ Error: Source node not found in graph: (174.860, 15.369, 136.587)

🔍 Running automatic diagnosis...
💡 Try: python3 astar_PPOF_systems.py direct graph_LV_combined.json ...
```

#### System Access Violation
```bash
❌ Source node in forbidden system 'B' (allowed: ['A']): (174.860, 15.369, 136.587)
💡 Source system 'B' is compatible with cable types: ['B', 'C']
```

#### No Route Found
```bash
❌ No route found inside the permitted system(s) {'A'}
🔍 Running automatic diagnosis...
[Detailed analysis and alternatives]
```

### Smart Recommendations

The system provides:
- **Exact command suggestions** with correct parameters
- **Alternative cable types** for cross-system routing
- **Graph file recommendations** based on endpoint analysis
- **Coordinate format validation** and correction hints

## 🧪 Testing

### Quick Test

```bash
# Test with sample graph
python3 astar_PPOF_systems.py direct sample_tagged_graph.json A 100 200 300 120 200 300

# Test diagnostic system
python3 astar_PPOF_systems.py diagnose 100 200 300 150 200 300
```

### Comprehensive Testing

```bash
# Run the full test suite (if available)
python3 tests/test_astar_systems.py

# Test all cable types
python3 astar_PPOF_systems.py direct graph_LV1A.json A 139.232 28.845 139.993 152.290 17.883 160.124
python3 astar_PPOF_systems.py direct graph_LV1B.json B 174.860 15.369 136.587 170.000 20.000 140.000
python3 astar_PPOF_systems.py direct graph_LV_combined.json C 174.860 15.369 136.587 139.232 28.845 139.993
```

### Test Scenarios

1. **✅ Valid Routing**: Same system with appropriate cable
2. **❌ System Violations**: Wrong cable for target system
3. **✅ Cross-System**: Cable C routing across systems
4. **🔍 Auto-Diagnosis**: Error detection and recovery
5. **📊 Multi-PPO**: Complex waypoint routing

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. "No graph files found"
```bash
❌ No graph files found. Please specify graph files or ensure graph files are in current directory.
```
**Solutions:**
- Ensure graph files are in current directory
- Use pattern `graph_*.json` for auto-discovery
- Specify graph files explicitly in diagnose command

#### 2. Coordinate format issues
```bash
❌ Error: Source node not found in graph: (174.86, 15.369, 136.587)
```
**Solutions:**
- Use exactly 3 decimal places: `174.860` not `174.86`
- Check coordinate precision in your graph files
- Use diagnostic command to verify available coordinates

#### 3. System access violations
```bash
❌ Source node in forbidden system 'B' (allowed: ['A'])
```
**Solutions:**
- Use Cable C for cross-system routing
- Check endpoint systems with diagnostic command
- Use appropriate cable type for target system

#### 4. No route found
```bash
❌ No route found inside the permitted system(s) {'A'}
```
**Solutions:**
- Verify connectivity within the system
- Check if endpoints are in the same connected component
- Use diagnostic command to analyze alternative graphs

### Debug Workflow

1. **Start with Diagnosis**: Always use `diagnose` for unknown endpoints
2. **Check Recommendations**: Follow the specific command suggestions
3. **Verify Graph Files**: Ensure proper graph format and system tags
4. **Test Connectivity**: Use Cable C to test basic connectivity
5. **Check Precision**: Ensure coordinate format matches exactly

## 📚 API Reference

### Integrated Functions

Since this is now a **standalone script**, all functionality is integrated:

#### Core Functions
- `run_direct_systems()`: Direct pathfinding with error handling
- `run_ppo_systems()`: PPO pathfinding with error handling  
- `run_multi_ppo_systems()`: Multi-PPO pathfinding with error handling
- `run_diagnose_systems()`: Diagnostic analysis

#### Diagnostic Functions
- `diagnose_endpoints()`: Comprehensive endpoint analysis
- `check_endpoints_across_graphs()`: Multi-graph endpoint checking
- `enhanced_error_handling()`: Automatic error diagnosis decorator

#### Utility Functions
- `load_tagged_graph()`: Load graph with system tags
- `build_adj()`: Create filtered adjacency list
- `validate_endpoints()`: Validate endpoint systems
- `calculate_path_distance()`: Calculate total path distance
- `format_point()`: Format coordinates for display

#### Classes
- `SystemFilteredGraph`: Main graph class with system filtering
- `FilteredGraph`: Lightweight A* implementation

### Constants

```python
ALLOWED = {
    "A": {"A"},      # Cable A: System A only
    "B": {"B"},      # Cable B: System B only
    "C": {"A", "B"}  # Cable C: Both systems
}
```

## 🔄 Migration Guide

### From Previous Versions

If you were using the previous multi-file version:

#### Old Usage (Multiple Files Required)
```bash
# Required: astar_PPOF_systems.py, cable_filter.py, astar_PPO_forbid.py
python3 astar_PPOF_systems.py direct graph.json 100 200 300 120 200 300 --cable A

# Separate diagnostic tool
python3 diagnose_endpoints.py 100 200 300 120 200 300 graph1.json graph2.json
```

#### New Usage (Single File)
```bash
# Only required: astar_PPOF_systems.py (standalone)
python3 astar_PPOF_systems.py direct graph.json A 100 200 300 120 200 300

# Integrated diagnostic
python3 astar_PPOF_systems.py diagnose 100 200 300 120 200 300
```

### Key Changes

1. **✅ Standalone Operation**: No external file dependencies
2. **🔍 Integrated Diagnostics**: Built-in error analysis and recommendations
3. **🛡️ Enhanced Error Handling**: Automatic diagnosis on failures
4. **📊 Simplified Commands**: Streamlined command structure
5. **🚀 Auto-Discovery**: Intelligent graph file detection

### Compatibility

- **Graph Format**: ✅ Same tagged JSON format
- **Coordinate Format**: ✅ Same precision requirements
- **Cable Types**: ✅ Same A/B/C system
- **Command Results**: ✅ Same pathfinding output
- **Performance**: ✅ Same or better performance

## 📄 License

This project is part of the CADIMO A* spatial sections pathfinding system.

## 🔗 Related Files

- `graph_LV1A.json`: System A graph data
- `graph_LV1B.json`: System B graph data  
- `graph_LV_combined.json`: Combined system graph
- `sample_tagged_graph.json`: Example graph for testing
- `tests/test_astar_systems.py`: Comprehensive test suite
- `ASTAR_SYSTEMS_SUMMARY.md`: Technical documentation

---

## 🎯 Quick Reference

### Most Common Commands

```bash
# Diagnose any endpoint pair
python3 astar_PPOF_systems.py diagnose <x1> <y1> <z1> <x2> <y2> <z2>

# Direct routing
python3 astar_PPOF_systems.py direct <graph> <cable> <x1> <y1> <z1> <x2> <y2> <z2>

# Cross-system routing (use Cable C)
python3 astar_PPOF_systems.py direct graph_LV_combined.json C <x1> <y1> <z1> <x2> <y2> <z2>

# Get help
python3 astar_PPOF_systems.py --help
```

**🚀 Pro Tip**: Always start with `diagnose` when working with new endpoints - it will save you time and provide exact commands to use! 