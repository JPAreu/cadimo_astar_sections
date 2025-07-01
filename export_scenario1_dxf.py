#!/usr/bin/env python3
"""
Export Scenario 1 to DXF format showing:
- Forbidden sections (Tramo ID 4 and 200) as yellow labeled lines with coordinates
- Origin and destination as cyan labeled circles with coordinates  
- Direct path as magenta dashed line
- Algorithm path as green connected lines
"""

import json
import sys
import os
from typing import List, Tuple

def create_dxf_header():
    """Create DXF file header with AutoCAD LT compatibility."""
    return """0
SECTION
2
HEADER
9
$ACADVER
1
AC1015
9
$HANDSEED
5
FFFF
9
$DWGCODEPAGE
3
ANSI_1252
0
ENDSEC
0
SECTION
2
TABLES
0
TABLE
2
VPORT
5
8
330
0
100
AcDbSymbolTable
70
4
0
VPORT
5
2E
330
8
100
AcDbSymbolTableRecord
100
AcDbViewportTableRecord
2
*ACTIVE
70
0
10
0.0
20
0.0
11
1.0
21
1.0
12
210.0
22
148.5
13
0.0
23
0.0
14
10.0
24
10.0
15
10.0
25
10.0
16
0.0
26
0.0
36
1.0
17
0.0
27
0.0
37
0.0
40
341.0
41
1.24
42
50.0
43
0.0
44
0.0
50
0.0
51
0.0
71
0
72
100
73
1
74
3
75
0
76
0
77
0
78
0
281
0
65
1
110
0.0
120
0.0
130
0.0
111
1.0
121
0.0
131
0.0
112
0.0
122
1.0
132
0.0
79
0
146
0.0
0
ENDTAB
0
TABLE
2
LTYPE
5
5
330
0
100
AcDbSymbolTable
70
1
0
LTYPE
5
14
330
5
100
AcDbSymbolTableRecord
100
AcDbLinetypeTableRecord
2
BYBLOCK
70
0
3

72
65
73
0
40
0.0
0
LTYPE
5
15
330
5
100
AcDbSymbolTableRecord
100
AcDbLinetypeTableRecord
2
BYLAYER
70
0
3

72
65
73
0
40
0.0
0
LTYPE
5
16
330
5
100
AcDbSymbolTableRecord
100
AcDbLinetypeTableRecord
2
CONTINUOUS
70
0
3
Solid line
72
65
73
0
40
0.0
0
LTYPE
5
17
330
5
100
AcDbSymbolTableRecord
100
AcDbLinetypeTableRecord
2
DASHED
70
0
3
Dashed __ __ __ __ __ __ __ __ __ __ __ __ __ _
72
65
73
2
40
0.6
49
0.5
74
0
49
-0.1
74
0
0
ENDTAB
0
TABLE
2
LAYER
5
2
330
0
100
AcDbSymbolTable
70
10
0
LAYER
5
10
330
2
100
AcDbSymbolTableRecord
100
AcDbLayerTableRecord
2
0
70
0
62
7
6
CONTINUOUS
370
0
390
F
0
LAYER
5
18
330
2
100
AcDbSymbolTableRecord
100
AcDbLayerTableRecord
2
FORBIDDEN_SECTIONS
70
0
62
2
6
CONTINUOUS
370
0
390
F
0
LAYER
5
19
330
2
100
AcDbSymbolTableRecord
100
AcDbLayerTableRecord
2
ORIGIN_DEST
70
0
62
4
6
CONTINUOUS
370
0
390
F
0
LAYER
5
1A
330
2
100
AcDbSymbolTableRecord
100
AcDbLayerTableRecord
2
ALGORITHM_PATH
70
0
62
3
6
CONTINUOUS
370
0
390
F
0
LAYER
5
1B
330
2
100
AcDbSymbolTableRecord
100
AcDbLayerTableRecord
2
DIRECT_PATH
70
0
62
5
6
DASHED
370
0
390
F
0
LAYER
5
1C
330
2
100
AcDbSymbolTableRecord
100
AcDbLayerTableRecord
2
LABELS
70
0
62
7
6
CONTINUOUS
370
0
390
F
0
ENDTAB
0
TABLE
2
STYLE
5
3
330
0
100
AcDbSymbolTable
70
1
0
STYLE
5
11
330
3
100
AcDbSymbolTableRecord
100
AcDbTextStyleTableRecord
2
STANDARD
70
0
40
0.0
41
1.0
50
0.0
71
0
42
0.2
3
txt
4

0
ENDTAB
0
TABLE
2
UCS
5
7
330
0
100
AcDbSymbolTable
70
0
0
ENDTAB
0
TABLE
2
APPID
5
9
330
0
100
AcDbSymbolTable
70
2
0
APPID
5
12
330
9
100
AcDbSymbolTableRecord
100
AcDbRegAppTableRecord
2
ACAD
70
0
0
ENDTAB
0
TABLE
2
DIMSTYLE
5
A
330
0
100
AcDbSymbolTable
70
1
0
DIMSTYLE
105
27
330
A
100
AcDbSymbolTableRecord
100
AcDbDimStyleTableRecord
2
ISO-25
70
0
0
ENDTAB
0
TABLE
2
BLOCK_RECORD
5
1
330
0
100
AcDbSymbolTable
70
1
0
BLOCK_RECORD
5
1F
330
1
100
AcDbSymbolTableRecord
2
*MODEL_SPACE
340
22
0
BLOCK_RECORD
5
1B
330
1
100
AcDbSymbolTableRecord
2
*PAPER_SPACE
340
1E
0
ENDTAB
0
ENDSEC
0
SECTION
2
BLOCKS
0
BLOCK
5
20
330
1F
100
AcDbEntity
8
0
100
AcDbBlockBegin
2
*MODEL_SPACE
70
0
10
0.0
20
0.0
30
0.0
3
*MODEL_SPACE
1

0
ENDBLK
5
21
330
1F
100
AcDbEntity
8
0
100
AcDbBlockEnd
0
BLOCK
5
1C
330
1B
100
AcDbEntity
67
1
8
0
100
AcDbBlockBegin
2
*PAPER_SPACE
70
0
10
0.0
20
0.0
30
0.0
3
*PAPER_SPACE
1

0
ENDBLK
5
1D
330
1B
100
AcDbEntity
67
1
8
0
100
AcDbBlockEnd
0
ENDSEC
0
SECTION
2
ENTITIES
"""

def create_dxf_footer():
    """Create DXF file footer with proper AutoCAD structure."""
    return """0
ENDSEC
0
SECTION
2
OBJECTS
0
DICTIONARY
5
C
330
0
100
AcDbDictionary
3
ACAD_GROUP
350
D
3
ACAD_MLINESTYLE
350
17
0
DICTIONARY
5
D
330
C
100
AcDbDictionary
0
DICTIONARY
5
1A
330
C
100
AcDbDictionary
0
ENDSEC
0
EOF
"""

def add_line_to_dxf(x1: float, y1: float, z1: float, x2: float, y2: float, z2: float, layer: str = "0", color: int = 7, handle_counter: list = [100]):
    """Add a 3D line to DXF with proper AutoCAD formatting."""
    handle_counter[0] += 1
    return f"""0
LINE
5
{handle_counter[0]:X}
330
1F
100
AcDbEntity
8
{layer}
62
{color}
100
AcDbLine
10
{x1:.6f}
20
{y1:.6f}
30
{z1:.6f}
11
{x2:.6f}
21
{y2:.6f}
31
{z2:.6f}
"""

def add_circle_to_dxf(x: float, y: float, z: float, radius: float = 1.0, layer: str = "0", color: int = 7, handle_counter: list = [200]):
    """Add a circle to DXF with proper AutoCAD formatting."""
    handle_counter[0] += 1
    return f"""0
CIRCLE
5
{handle_counter[0]:X}
330
1F
100
AcDbEntity
8
{layer}
62
{color}
100
AcDbCircle
10
{x:.6f}
20
{y:.6f}
30
{z:.6f}
40
{radius:.6f}
"""

def add_text_to_dxf(x: float, y: float, z: float, text: str, height: float = 0.5, layer: str = "0", color: int = 7, handle_counter: list = [300]):
    """Add text to DXF with proper AutoCAD formatting."""
    handle_counter[0] += 1
    return f"""0
TEXT
5
{handle_counter[0]:X}
330
1F
100
AcDbEntity
8
{layer}
62
{color}
100
AcDbText
10
{x:.6f}
20
{y:.6f}
30
{z:.6f}
40
{height:.6f}
1
{text}
50
0.0
51
0.0
7
STANDARD
71
0
72
0
11
{x:.6f}
21
{y:.6f}
31
{z:.6f}
100
AcDbText
"""

def parse_coordinate_string(coord_str: str) -> Tuple[float, float, float]:
    """Parse coordinate string like '(139.232, 28.845, 139.993)' to tuple."""
    clean_str = coord_str.strip().strip('()')
    parts = [float(x.strip()) for x in clean_str.split(',')]
    return tuple(parts)

def run_algorithm_and_get_path():
    """Run the algorithm and extract the path."""
    try:
        from astar_PPOF_systems import SystemFilteredGraph
        
        # Create the graph with system filtering and forbidden sections
        graph = SystemFilteredGraph(
            'graph_LV_combined.json', 
            'A',  # Cable type A
            'tramo_map_combined.json',
            'forbidden_scenario1.json'
        )
        
        # Define origin and destination
        origin = (139.232, 28.845, 139.993)
        destination = (152.290, 17.883, 160.124)
        
        # Find the path
        path, nodes_explored = graph.find_path_direct(origin, destination)
        
        print(f"✅ Algorithm found path with {len(path)} points, {nodes_explored} nodes explored")
        return path
        
    except Exception as e:
        print(f"❌ Error running algorithm: {e}")
        return None

def calculate_distance(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
    """Calculate 3D distance between two points."""
    return ((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2 + (p2[2] - p1[2])**2)**0.5

def calculate_path_distance(path_points: List[Tuple[float, float, float]]) -> float:
    """Calculate total distance of a path."""
    total_distance = 0.0
    for i in range(len(path_points) - 1):
        total_distance += calculate_distance(path_points[i], path_points[i + 1])
    return total_distance

def validate_dxf_elements(dxf_content: str) -> bool:
    """Validate that DXF contains all required elements."""
    required_elements = [
        'FORBIDDEN_SECTIONS', 'ORIGIN_DEST', 'ALGORITHM_PATH', 'DIRECT_PATH',
        'TRAMO_4', 'TRAMO_200', 'ORIGIN', 'DESTINATION'
    ]
    
    missing_elements = []
    for element in required_elements:
        if element not in dxf_content:
            missing_elements.append(element)
    
    if missing_elements:
        print(f"⚠️  Warning: Missing elements: {missing_elements}")
        return False
    
    print("✅ All required elements present in DXF")
    return True

def main():
    """Main function to create Scenario 1 DXF export."""
    print("🎨 Creating AutoCAD LT compatible DXF export for Scenario 1")
    print("=" * 60)
    
    # Define scenario data
    origin = (139.232, 28.845, 139.993)
    destination = (152.290, 17.883, 160.124)
    
    # Initialize handle counters for proper AutoCAD entity handles
    line_handles = [100]
    circle_handles = [200]  
    text_handles = [300]
    
    # Load tramo map to get forbidden section coordinates
    try:
        with open('tramo_map_combined.json', 'r') as f:
            tramo_map = json.load(f)
        print(f"✅ Loaded tramo map with {len(tramo_map)} entries")
    except FileNotFoundError:
        print("❌ Error: tramo_map_combined.json not found")
        return

    # Find forbidden sections (Tramo ID 4 and 200)
    forbidden_sections = []
    id_to_edge = {tramo_id: edge_key for edge_key, tramo_id in tramo_map.items()}
    
    for tramo_id in [4, 200]:
        if tramo_id in id_to_edge:
            edge_key = id_to_edge[tramo_id]
            nodes = edge_key.split('-')
            if len(nodes) == 2:
                node1 = parse_coordinate_string(nodes[0])
                node2 = parse_coordinate_string(nodes[1])
                forbidden_sections.append({
                    'tramo_id': tramo_id,
                    'node1': node1,
                    'node2': node2
                })
                print(f"📍 Tramo ID {tramo_id}: {nodes[0]} ↔ {nodes[1]}")
        else:
            print(f"⚠️  Warning: Tramo ID {tramo_id} not found in map")

    if len(forbidden_sections) != 2:
        print(f"❌ Error: Expected 2 forbidden sections, found {len(forbidden_sections)}")
        return

    # Get algorithm path
    print("\n🔄 Running algorithm to get path...")
    path_points = run_algorithm_and_get_path()
    
    if not path_points:
        print("❌ Could not get path from algorithm")
        return

    print(f"✅ Extracted path with {len(path_points)} points")

    # Start building DXF content with AutoCAD LT compatibility
    print("\n🔧 Building AutoCAD LT compatible DXF structure...")
    dxf_content = create_dxf_header()

    # Add forbidden sections (YELLOW)
    print("🟡 Adding forbidden sections...")
    for section in forbidden_sections:
        tramo_id = section['tramo_id']
        node1 = section['node1']
        node2 = section['node2']
        
        # Main line
        dxf_content += add_line_to_dxf(
            node1[0], node1[1], node1[2],
            node2[0], node2[1], node2[2],
            layer="FORBIDDEN_SECTIONS",
            color=2,  # Yellow
            handle_counter=line_handles
        )
        
        # Label at midpoint
        mid_x = (node1[0] + node2[0]) / 2
        mid_y = (node1[1] + node2[1]) / 2
        mid_z = (node1[2] + node2[2]) / 2
        
        dxf_content += add_text_to_dxf(
            mid_x, mid_y, mid_z + 1.0,
            f"TRAMO_{tramo_id}",
            height=1.0,
            layer="LABELS",
            color=2,
            handle_counter=text_handles
        )
        
        # Endpoint markers
        dxf_content += add_circle_to_dxf(
            node1[0], node1[1], node1[2],
            radius=0.5,
            layer="FORBIDDEN_SECTIONS",
            color=2,
            handle_counter=circle_handles
        )
        
        dxf_content += add_circle_to_dxf(
            node2[0], node2[1], node2[2],
            radius=0.5,
            layer="FORBIDDEN_SECTIONS",
            color=2,
            handle_counter=circle_handles
        )
        
        # Coordinate labels
        dxf_content += add_text_to_dxf(
            node1[0] + 0.5, node1[1], node1[2] - 1.0,
            f"({node1[0]:.1f},{node1[1]:.1f},{node1[2]:.1f})",
            height=0.4,
            layer="LABELS",
            color=2,
            handle_counter=text_handles
        )
        
        dxf_content += add_text_to_dxf(
            node2[0] + 0.5, node2[1], node2[2] - 1.0,
            f"({node2[0]:.1f},{node2[1]:.1f},{node2[2]:.1f})",
            height=0.4,
            layer="LABELS",
            color=2,
            handle_counter=text_handles
        )

    # Add origin and destination (CYAN)
    print("🔵 Adding origin and destination...")
    
    # Origin
    dxf_content += add_circle_to_dxf(
        origin[0], origin[1], origin[2],
        radius=2.0,
        layer="ORIGIN_DEST",
        color=4,  # Cyan
        handle_counter=circle_handles
    )
    
    dxf_content += add_text_to_dxf(
        origin[0] + 2.5, origin[1], origin[2],
        "ORIGIN",
        height=1.5,
        layer="LABELS",
        color=4,
        handle_counter=text_handles
    )
    
    dxf_content += add_text_to_dxf(
        origin[0] + 2.5, origin[1] - 1.5, origin[2],
        f"({origin[0]:.1f},{origin[1]:.1f},{origin[2]:.1f})",
        height=0.8,
        layer="LABELS",
        color=4,
        handle_counter=text_handles
    )
    
    # Destination
    dxf_content += add_circle_to_dxf(
        destination[0], destination[1], destination[2],
        radius=2.0,
        layer="ORIGIN_DEST",
        color=4,  # Cyan
        handle_counter=circle_handles
    )
    
    dxf_content += add_text_to_dxf(
        destination[0] + 2.5, destination[1], destination[2],
        "DESTINATION",
        height=1.5,
        layer="LABELS",
        color=4,
        handle_counter=text_handles
    )
    
    dxf_content += add_text_to_dxf(
        destination[0] + 2.5, destination[1] - 1.5, destination[2],
        f"({destination[0]:.1f},{destination[1]:.1f},{destination[2]:.1f})",
        height=0.8,
        layer="LABELS",
        color=4,
        handle_counter=text_handles
    )

    # Add direct path (MAGENTA)
    print("🟣 Adding direct path...")
    dxf_content += add_line_to_dxf(
        origin[0], origin[1], origin[2],
        destination[0], destination[1], destination[2],
        layer="DIRECT_PATH",
        color=5,  # Magenta
        handle_counter=line_handles
    )
    
    direct_mid_x = (origin[0] + destination[0]) / 2
    direct_mid_y = (origin[1] + destination[1]) / 2
    direct_mid_z = (origin[2] + destination[2]) / 2
    
    dxf_content += add_text_to_dxf(
        direct_mid_x, direct_mid_y, direct_mid_z + 1.0,
        "DIRECT_PATH",
        height=0.8,
        layer="LABELS",
        color=5,
        handle_counter=text_handles
    )

    # Add algorithm path (GREEN)
    print("🟢 Adding algorithm path...")
    for i in range(len(path_points) - 1):
        p1 = path_points[i]
        p2 = path_points[i + 1]
        
        dxf_content += add_line_to_dxf(
            p1[0], p1[1], p1[2],
            p2[0], p2[1], p2[2],
            layer="ALGORITHM_PATH",
            color=3,  # Green
            handle_counter=line_handles
        )

    # Add path point labels (every 3rd point)
    for i in range(0, len(path_points), 3):
        point = path_points[i]
        dxf_content += add_text_to_dxf(
            point[0], point[1], point[2] + 0.5,
            f"P{i+1}",
            height=0.3,
            layer="LABELS",
            color=3,
            handle_counter=text_handles
        )

    # Add footer
    dxf_content += create_dxf_footer()

    # Validate DXF content
    print("\n🔍 Validating DXF content...")
    validate_dxf_elements(dxf_content)

    # Write DXF file
    output_dir = "export_data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_file = os.path.join(output_dir, "scenario1_forbidden_sections.dxf")
    
    try:
        with open(output_file, 'w') as f:
            f.write(dxf_content)
        print(f"✅ DXF file written successfully")
    except Exception as e:
        print(f"❌ Error writing DXF file: {e}")
        return

    # Calculate distances
    direct_distance = calculate_distance(origin, destination)
    algorithm_distance = calculate_path_distance(path_points)

    # Final report
    print(f"\n✅ DXF export completed!")
    print(f"📁 Output file: {output_file}")
    
    # Verify file
    try:
        file_size = os.path.getsize(output_file)
        print(f"📋 File verification:")
        print(f"   • File size: {file_size} bytes")
        if file_size < 1000:
            print(f"   • ⚠️  Warning: File size seems small")
        else:
            print(f"   • File size: ✅ Good")
    except Exception as e:
        print(f"   • ❌ Error checking file: {e}")

    print(f"\n📊 Contents:")
    print(f"   • {len(forbidden_sections)} forbidden sections (YELLOW with coordinates)")
    print(f"   • 2 endpoint markers (CYAN with coordinates)")
    print(f"   • 1 direct path (MAGENTA dashed line)")
    print(f"   • {len(path_points)} algorithm path points ({len(path_points)-1} GREEN lines)")

    print(f"\n📏 Distance comparison:")
    print(f"   • Direct path: {direct_distance:.3f} units")
    print(f"   • Algorithm path: {algorithm_distance:.3f} units")
    print(f"   • Detour: +{algorithm_distance - direct_distance:.3f} units ({((algorithm_distance/direct_distance - 1) * 100):.1f}% longer)")

    print(f"\n📋 Layer summary:")
    print(f"   • FORBIDDEN_SECTIONS (Yellow): Tramo 4 & 200 with exact coordinates")
    print(f"   • ORIGIN_DEST (Cyan): Start/end points with coordinates")
    print(f"   • DIRECT_PATH (Magenta): Straight line (crosses forbidden sections)")
    print(f"   • ALGORITHM_PATH (Green): Calculated path (avoids forbidden sections)")
    print(f"   • LABELS: Text labels and coordinates for all elements")

if __name__ == "__main__":
    main() 