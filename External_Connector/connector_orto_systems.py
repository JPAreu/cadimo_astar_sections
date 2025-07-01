#!/usr/bin/env python3
"""
Enhanced External Point Connector with System Filtering

This script extends connector_orto.py to support system-aware external point connection.
It can work with tagged graphs and filter edges based on cable type/system constraints.

System Rules:
- System A: Only considers nodes/edges with sys: "A"
- System B: Only considers nodes/edges with sys: "B"  
- System C: Considers all nodes/edges (both A and B systems)

Usage:
    python3 connector_orto_systems.py graph.json X Y Z [--system A|B|C] [--json] [--dxf]
"""

import json
import math
import sys
import itertools
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple, Union
import numpy as np

try:
    import ezdxf
    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False

Point3D = Tuple[float, float, float]
Edge3D = Tuple[Point3D, Point3D]

@dataclass
class ManhattanPath:
    order: str                   # e.g. "X→Z→Y"
    points: List[Point3D]        # List of vertices
    manhattan: float             # Total Manhattan distance

class SystemAwareExternalPointConnector:
    """Enhanced External Point Connector with system filtering support."""
    
    def __init__(
        self,
        graph_json_path: Optional[str] = None,
        *,
        graph_data: Optional[Dict] = None,
        system_filter: str = "C",
        grid_size: Optional[float] = None,
        verbose: bool = True,
    ) -> None:
        self.verbose = verbose
        self.system_filter = system_filter
        
        # Load and filter graph data
        if graph_json_path:
            self.raw_graph_data = self._load_json(graph_json_path)
        elif graph_data:
            self.raw_graph_data = graph_data
        else:
            raise ValueError("Must provide either graph_json_path or graph_data")
        
        # Filter graph based on system
        self.graph_data = self._filter_graph_by_system()
        
        if not self.graph_data:
            raise ValueError(f"No nodes found for system filter '{system_filter}'")
        
        self._log(f"Loaded {len(self.raw_graph_data.get('nodes', self.raw_graph_data))} total nodes")
        self._log(f"Filtered to {len(self.graph_data)} nodes for system '{system_filter}'")
        
        self.bounding_box = self._calc_bounding_box()
        self.grid_size = grid_size or self._calc_optimal_grid_size()
        self.edges = self._build_edge_list()
        self.edge_grid_index = self._build_edge_spatial_index()
        
        self._log(f"Grid size: {self.grid_size:.3f}")
        self._log(f"Found {len(self.edges)} edges")

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(f"[SystemConnector] {msg}")

    def _load_json(self, path: str) -> Dict:
        """Load graph JSON - supports both adjacency and tagged formats."""
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return raw

    def _filter_graph_by_system(self) -> Dict[Point3D, List[Point3D]]:
        """Filter graph data based on system constraint."""
        
        # Check if this is a tagged graph format
        if "nodes" in self.raw_graph_data and "edges" in self.raw_graph_data:
            return self._filter_tagged_graph()
        else:
            # Assume it's adjacency format - no filtering possible
            self._log("Adjacency format detected - no system filtering applied")
            parsed: Dict[Point3D, List[Point3D]] = {}
            for k, lst in self.raw_graph_data.items():
                node = tuple(float(c) for c in k.strip("()").split(","))
                parsed[node] = [tuple(float(c) for c in n) for n in lst]
            return parsed

    def _filter_tagged_graph(self) -> Dict[Point3D, List[Point3D]]:
        """Filter tagged graph based on system constraint."""
        nodes_data = self.raw_graph_data["nodes"]
        edges_data = self.raw_graph_data["edges"]
        
        # Define allowed systems based on filter
        if self.system_filter == "A":
            allowed_systems = {"A"}
        elif self.system_filter == "B":
            allowed_systems = {"B"}
        elif self.system_filter == "C":
            allowed_systems = {"A", "B"}
        else:
            raise ValueError(f"Invalid system filter: {self.system_filter}")
        
        self._log(f"System filter '{self.system_filter}' allows systems: {sorted(allowed_systems)}")
        
        # Filter nodes by system
        allowed_nodes = set()
        for node_key, node_data in nodes_data.items():
            node_sys = node_data.get("sys")
            if node_sys in allowed_systems:
                allowed_nodes.add(node_key)
        
        self._log(f"Found {len(allowed_nodes)} allowed nodes")
        
        # Filter edges by system and ensure both endpoints are allowed
        filtered_adjacency: Dict[Point3D, List[Point3D]] = defaultdict(list)
        edge_count = 0
        
        for edge in edges_data:
            edge_sys = edge.get("sys")
            from_node = edge["from"]
            to_node = edge["to"]
            
            # Check if edge system is allowed and both nodes are allowed
            if (edge_sys in allowed_systems and 
                from_node in allowed_nodes and 
                to_node in allowed_nodes):
                
                # Convert string coordinates to tuples
                from_coord = self._parse_coord_string(from_node)
                to_coord = self._parse_coord_string(to_node)
                
                # Add bidirectional edges
                if to_coord not in filtered_adjacency[from_coord]:
                    filtered_adjacency[from_coord].append(to_coord)
                if from_coord not in filtered_adjacency[to_coord]:
                    filtered_adjacency[to_coord].append(from_coord)
                
                edge_count += 1
        
        self._log(f"Found {edge_count} allowed edges")
        
        return dict(filtered_adjacency)

    def _parse_coord_string(self, coord_str: str) -> Point3D:
        """Parse coordinate string like '(x, y, z)' to tuple."""
        clean_str = coord_str.strip("()")
        parts = [float(c.strip()) for c in clean_str.split(",")]
        return tuple(parts)

    def _calc_bounding_box(self):
        """Calculate bounding box of filtered graph."""
        coords = list(self.graph_data.keys())
        if not coords:
            return {"min": [0, 0, 0], "max": [0, 0, 0], "size": [0, 0, 0]}
        
        mins = [min(p[i] for p in coords) for i in range(3)]
        maxs = [max(p[i] for p in coords) for i in range(3)]
        return {"min": mins, "max": maxs, "size": [maxs[i] - mins[i] for i in range(3)]}

    def _calc_optimal_grid_size(self) -> float:
        """Calculate optimal grid size based on filtered graph."""
        if not self.graph_data:
            return 1.0
        
        vol = math.prod(self.bounding_box["size"])
        n = len(self.graph_data)
        avg_cubic = (vol / n) ** (1 / 3) if n else 1.0

        total_len = cnt = 0
        for a, lst in self.graph_data.items():
            for b in lst:
                total_len += math.dist(a, b)
                cnt += 1
        avg_edge = total_len / cnt if cnt else avg_cubic
        return min(avg_cubic, avg_edge * 2)

    def _cell(self, p: Point3D) -> Tuple[int, int, int]:
        """Convert point to grid cell coordinates."""
        return (math.floor(p[0] / self.grid_size),
                math.floor(p[1] / self.grid_size),
                math.floor(p[2] / self.grid_size))

    def _build_edge_list(self) -> List[Edge3D]:
        """Build list of unique edges from filtered graph."""
        seen: Set[Edge3D] = set()
        for a, lst in self.graph_data.items():
            for b in lst:
                seen.add(tuple(sorted((a, b))))
        return list(seen)

    def _cells_of_segment(self, a: Point3D, b: Point3D) -> Set[Tuple[int, int, int]]:
        """Get all grid cells that a segment passes through."""
        c0, c1 = self._cell(a), self._cell(b)
        if c0 == c1:
            return {c0}
        dx, dy, dz = (b[i] - a[i] for i in range(3))
        steps = max(abs(c1[i] - c0[i]) for i in range(3))
        inc = (dx / steps, dy / steps, dz / steps)
        cells = set()
        x, y, z = a
        for _ in range(steps + 1):
            cells.add(self._cell((x, y, z)))
            x += inc[0]
            y += inc[1]
            z += inc[2]
        return cells

    def _build_edge_spatial_index(self):
        """Build spatial index of edges for fast lookup."""
        grid = defaultdict(list)
        for idx, (a, b) in enumerate(self.edges):
            for c in self._cells_of_segment(a, b):
                grid[c].append(idx)
        return dict(grid)

    @staticmethod
    def _dist_point_segment(p: Point3D, a: Point3D, b: Point3D) -> Tuple[float, Point3D]:
        """Calculate distance from point to line segment and projection point."""
        ap = np.subtract(p, a)
        ab = np.subtract(b, a)
        denom = np.dot(ab, ab)
        t = float(max(0, min(1, np.dot(ap, ab) / denom))) if denom else 0.0
        proj = tuple(a_i + t * ab_i for a_i, ab_i in zip(a, ab))
        return math.dist(p, proj), proj

    def find_closest_edge(
        self,
        external: Point3D,
        *,
        max_radius: Optional[int] = None,
        keep_paths: int = 2,
    ):
        """Find closest edge in filtered graph and generate Manhattan paths."""
        
        if not self.edges:
            raise RuntimeError(f"No edges available for system '{self.system_filter}'")
        
        # For very distant points, fall back to brute force
        if self._is_point_very_distant(external):
            self._log("Point is very distant, using brute force search...")
            return self._brute_force_search(external, keep_paths)
        
        centre = self._cell(external)
        if max_radius is None:
            max_radius = 100

        best_d = math.inf
        best_idx = None
        best_proj = None
        seen: Set[int] = set()

        for r in range(max_radius + 1):
            shell_cells = self._get_shell_cells(centre, r)
            
            cand = {
                idx
                for c in shell_cells
                for idx in self.edge_grid_index.get(c, [])
                if idx not in seen
            }
            
            if not cand:
                continue
                
            for idx in cand:
                d, proj = self._dist_point_segment(external, *self.edges[idx])
                if d < best_d:
                    best_d, best_idx, best_proj = d, idx, proj
                    
            seen.update(cand)
            
            # Early termination if we found a good match
            if best_d <= (r + 1) * self.grid_size * 0.5:
                break
                
            # Progress logging for long searches
            if r % 10 == 0 and r > 0:
                self._log(f"Radius {r}: best distance so far: {best_d:.3f}")

        # If spatial search failed, fall back to brute force
        if best_idx is None or best_proj is None:
            self._log("Spatial search failed, falling back to brute force...")
            return self._brute_force_search(external, keep_paths)

        paths = self._manhattan_paths(external, best_proj, keep=keep_paths)

        return {
            "best_edge": self.edges[best_idx],
            "projection": best_proj,
            "euclidean": best_d,
            "best_manhattan_path": paths[0].__dict__,
            "all_paths": [p.__dict__ for p in paths],
            "system_filter": self.system_filter,
            "total_edges_considered": len(self.edges),
        }

    def _is_point_very_distant(self, point: Point3D) -> bool:
        """Check if point is very far from the bounding box."""
        bbox = self.bounding_box
        dist_to_bbox = 0.0
        for i in range(3):
            if point[i] < bbox["min"][i]:
                dist_to_bbox += (bbox["min"][i] - point[i]) ** 2
            elif point[i] > bbox["max"][i]:
                dist_to_bbox += (point[i] - bbox["max"][i]) ** 2
        
        dist_to_bbox = math.sqrt(dist_to_bbox)
        max_bbox_size = max(bbox["size"]) if any(bbox["size"]) else 1.0
        
        return dist_to_bbox > 2 * max_bbox_size

    def _get_shell_cells(self, centre: Tuple[int, int, int], radius: int) -> List[Tuple[int, int, int]]:
        """Get cells on the shell of given radius around center."""
        if radius == 0:
            return [centre]
        
        cells = []
        cx, cy, cz = centre
        
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                for dz in range(-radius, radius + 1):
                    if max(abs(dx), abs(dy), abs(dz)) == radius:
                        cells.append((cx + dx, cy + dy, cz + dz))
        
        return cells

    def _brute_force_search(self, external: Point3D, keep_paths: int) -> dict:
        """Fallback brute force search for very distant points."""
        best_d = math.inf
        best_idx = None
        best_proj = None
        
        self._log(f"Checking {len(self.edges)} edges with brute force...")
        
        for idx, (a, b) in enumerate(self.edges):
            d, proj = self._dist_point_segment(external, a, b)
            if d < best_d:
                best_d, best_idx, best_proj = d, idx, proj
        
        if best_idx is None or best_proj is None:
            raise RuntimeError("No edge found.")
        
        paths = self._manhattan_paths(external, best_proj, keep=keep_paths)
        
        return {
            "best_edge": self.edges[best_idx],
            "projection": best_proj,
            "euclidean": best_d,
            "best_manhattan_path": paths[0].__dict__,
            "all_paths": [p.__dict__ for p in paths],
            "system_filter": self.system_filter,
            "total_edges_considered": len(self.edges),
        }

    def _manhattan_paths(
        self, start: Point3D, end: Point3D, *, keep: int = 2
    ) -> List[ManhattanPath]:
        """Generate Manhattan paths from start to end."""
        axes = ("X", "Y", "Z")
        delta = [end[i] - start[i] for i in range(3)]
        out: List[ManhattanPath] = []
        seen_paths: Set[Tuple[Point3D, ...]] = set()

        for perm in itertools.permutations(range(3)):
            cur = list(start)
            pts = [tuple(cur)]
            dist = 0.0
            order_parts = []
            
            for idx in perm:
                if delta[idx] != 0:
                    cur[idx] += delta[idx]
                    pts.append(tuple(cur))
                    dist += abs(delta[idx])
                    order_parts.append(axes[idx])
            
            path_tuple = tuple(pts)
            if path_tuple in seen_paths:
                continue
            seen_paths.add(path_tuple)
            
            out.append(
                ManhattanPath(
                    order="→".join(order_parts),
                    points=pts,
                    manhattan=dist,
                )
            )
        return sorted(out, key=lambda p: p.manhattan)[:keep]

    def export_dxf(self, result, filename: str):
        """Export results to DXF file."""
        if not HAS_EZDXF:
            raise RuntimeError("ezdxf not installed.")
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        
        # Add the closest edge line
        edge = result["best_edge"]
        msp.add_line(edge[0], edge[1], dxfattribs={"color": 7})  # White/gray edge
        
        # Add projection point circle (red)
        msp.add_circle(result["projection"], radius=0.5, dxfattribs={"color": 1})
        
        # Add starting point circle (yellow)
        if result["all_paths"]:
            starting_point = result["all_paths"][0]["points"][0]
            msp.add_circle(starting_point, radius=1.0, dxfattribs={"color": 2})  # Yellow
        
        # Add Manhattan paths with lines and point circles
        for i, p in enumerate(result["all_paths"]):
            path_color = 3 + i  # Green, cyan, etc.
            
            # Add lines between consecutive points
            for a, b in zip(p["points"], p["points"][1:]):
                msp.add_line(a, b, dxfattribs={"color": path_color})
            
            # Add circles for intermediate points only
            for j, point in enumerate(p["points"]):
                if j == 0 or j == len(p["points"]) - 1:
                    continue  # Skip start and end points
                else:
                    msp.add_circle(point, radius=0.3, dxfattribs={"color": path_color})
        
        doc.saveas(filename)
        return filename


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Main CLI function with system filtering support."""
    argv = list(argv or sys.argv[1:])
    if len(argv) < 4:
        print(
            "Usage:\n  python connector_orto_systems.py "
            "graph.json X Y Z [--system A|B|C] [--json] [--dxf] [max_radius]"
        )
        print("\nSystem options:")
        print("  A - Only consider System A nodes/edges")
        print("  B - Only consider System B nodes/edges") 
        print("  C - Consider all systems (A and B)")
        sys.exit(1)

    graph_file, x, y, z, *rest = argv
    external = (float(x), float(y), float(z))
    
    # Parse optional arguments
    max_radius = None
    want_dxf = False
    want_json = False
    system_filter = "C"  # Default to all systems
    
    i = 0
    while i < len(rest):
        arg = rest[i]
        if arg == "--dxf":
            want_dxf = True
        elif arg == "--json":
            want_json = True
        elif arg == "--system":
            if i + 1 < len(rest) and rest[i + 1] in ["A", "B", "C"]:
                system_filter = rest[i + 1]
                i += 1  # Skip the next argument
            else:
                print("Error: --system requires A, B, or C")
                sys.exit(1)
        else:
            try:
                max_radius = int(arg)
            except ValueError:
                print(f"Warning: Unknown argument '{arg}' ignored")
        i += 1

    print(f"🔧 System Filter: {system_filter}")
    print(f"📍 External Point: {external}")
    
    try:
        conn = SystemAwareExternalPointConnector(
            graph_json_path=graph_file, 
            system_filter=system_filter,
            verbose=True
        )
        res = conn.find_closest_edge(external, max_radius=max_radius)
        
        # Show results
        print(f"\n✅ Results for System '{system_filter}':")
        print(f"   Closest edge: {res['best_edge'][0]} ↔ {res['best_edge'][1]}")
        print(f"   Projection: {res['projection']}")
        print(f"   Euclidean distance: {res['euclidean']:.3f} units")
        print(f"   Best Manhattan path: {res['best_manhattan_path']['manhattan']:.3f} units")
        print(f"   Edges considered: {res['total_edges_considered']}")
        
        if want_json:
            out_json = (
                f"system_{system_filter}_connection_{external[0]:.1f}_{external[1]:.1f}_{external[2]:.1f}.json"
            )
            Path(out_json).write_text(json.dumps(res, indent=2))
            print(f"📄 JSON saved: {out_json}")

        if want_dxf:
            base_name = f"system_{system_filter}_connection_{external[0]:.1f}_{external[1]:.1f}_{external[2]:.1f}"
            
            counter = 1
            while True:
                dxf_name = f"{base_name}_dxf_{counter}.dxf"
                if not Path(dxf_name).exists():
                    break
                counter += 1
                    
            conn.export_dxf(res, dxf_name)
            print(f"📐 DXF generated: {dxf_name}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
 