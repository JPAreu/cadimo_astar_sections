#!/usr/bin/env python3
"""
Export forbidden sections to DXF for visualization
"""

import json
import sys
from typing import List, Tuple

try:
    import ezdxf
except ImportError:
    print("Error: ezdxf library not found. Install it with: pip install ezdxf")
    sys.exit(1)

def parse_edge_key(edge_key: str) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    """Parse edge key format: '(x1,y1,z1)-(x2,y2,z2)' into two coordinate tuples."""
    parts = edge_key.split('-')
    if len(parts) != 2:
        raise ValueError(f"Invalid edge key format: {edge_key}")
    
    def parse_coord(coord_str):
        coord_str = coord_str.strip('()')
        coords = [float(x.strip()) for x in coord_str.split(',')]
        return tuple(coords)
    
    return parse_coord(parts[0]), parse_coord(parts[1])

def export_forbidden_sections_to_dxf(tramo_map_file: str, forbidden_file: str, output_file: str):
    """Export forbidden sections to DXF."""
    
    # Load files
    with open(tramo_map_file, 'r') as f:
        tramo_map = json.load(f)
    
    with open(forbidden_file, 'r') as f:
        forbidden_ids = json.load(f)
    
    print(f"🚫 Forbidden tramo IDs: {forbidden_ids}")
    
    # Create reverse mapping: tramo_id -> edge_key
    id_to_edge = {}
    for edge_key, tramo_id in tramo_map.items():
        id_to_edge[tramo_id] = edge_key
    
    # Find forbidden edges
    forbidden_edges = []
    for tramo_id in forbidden_ids:
        if tramo_id in id_to_edge:
            forbidden_edges.append((tramo_id, id_to_edge[tramo_id]))
    
    print(f"🚫 Found {len(forbidden_edges)} forbidden edges:")
    for tramo_id, edge_key in forbidden_edges:
        print(f"   Tramo {tramo_id}: {edge_key}")
    
    # Create DXF document
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Add layers
    doc.layers.new('FORBIDDEN_SECTIONS', dxfattribs={'color': 1})    # Red
    doc.layers.new('FORBIDDEN_POINTS', dxfattribs={'color': 5})      # Blue
    doc.layers.new('ANNOTATIONS', dxfattribs={'color': 7})           # White
    
    # Draw forbidden sections
    all_points = []
    for tramo_id, edge_key in forbidden_edges:
        try:
            point1, point2 = parse_edge_key(edge_key)
            
            # Draw the forbidden section as a thick line
            msp.add_line(point1, point2, dxfattribs={
                'layer': 'FORBIDDEN_SECTIONS',
                'lineweight': 50  # Thick line
            })
            
            # Add points as circles
            msp.add_circle(point1, radius=1.0, dxfattribs={'layer': 'FORBIDDEN_POINTS'})
            msp.add_circle(point2, radius=1.0, dxfattribs={'layer': 'FORBIDDEN_POINTS'})
            
            # Add tramo ID annotation at midpoint
            midpoint = (
                (point1[0] + point2[0]) / 2,
                (point1[1] + point2[1]) / 2,
                (point1[2] + point2[2]) / 2
            )
            
            text = msp.add_text(f"Tramo {tramo_id}", dxfattribs={
                'layer': 'ANNOTATIONS',
                'height': 0.8
            })
            text.set_placement((midpoint[0], midpoint[1] + 0.5, midpoint[2]))
            
            all_points.extend([point1, point2])
            
        except Exception as e:
            print(f"Warning: Could not parse edge {edge_key}: {e}")
    
    # Add title and summary
    if all_points:
        # Find bounds
        min_x = min(p[0] for p in all_points)
        max_x = max(p[0] for p in all_points)
        min_y = min(p[1] for p in all_points)
        max_y = max(p[1] for p in all_points)
        
        # Add title
        title_text = f"FORBIDDEN SECTIONS C2-C3\nTramo IDs: {', '.join(map(str, forbidden_ids))}\nTotal sections: {len(forbidden_edges)}"
        title = msp.add_text(title_text, dxfattribs={
            'layer': 'ANNOTATIONS',
            'height': 1.5
        })
        title.set_placement((min_x, max_y + 3, all_points[0][2]))
        
        # Add coordinate info for each section
        y_offset = max_y + 8
        for i, (tramo_id, edge_key) in enumerate(forbidden_edges):
            try:
                point1, point2 = parse_edge_key(edge_key)
                coord_text = f"Tramo {tramo_id}: {point1} → {point2}"
                coord_annotation = msp.add_text(coord_text, dxfattribs={
                    'layer': 'ANNOTATIONS',
                    'height': 0.6
                })
                coord_annotation.set_placement((min_x, y_offset + i * 1.5, all_points[0][2]))
            except:
                pass
    
    # Save DXF
    doc.saveas(output_file)
    
    print(f"✅ Forbidden sections DXF saved: {output_file}")
    print(f"   Layers: FORBIDDEN_SECTIONS (red lines), FORBIDDEN_POINTS (blue circles), ANNOTATIONS (white text)")
    print(f"   Sections exported: {len(forbidden_edges)}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 export_forbidden_sections_dxf.py tramo_map.json forbidden.json output.dxf")
        sys.exit(1)
    
    export_forbidden_sections_to_dxf(sys.argv[1], sys.argv[2], sys.argv[3])
