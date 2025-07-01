#!/usr/bin/env python3
"""
Improved External Point Connector – versión "2-rutas"
====================================================

Localiza la arista más cercana a un punto externo en un grafo 3D y devuelve
únicamente **las 2 rutas Manhattan más cortas** (la "cara" del cubo).

•  Puede funcionar con el grafo cargado en memoria o leerlo de un JSON.
•  Exporta resultado a JSON (si se utiliza como script) y, opcionalmente, a DXF.
•  El DXF requiere `ezdxf`; si no está instalado, el resto del algoritmo
   funciona sin problemas.

© 2025  –  MIT License
"""
from __future__ import annotations

import itertools
import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

import numpy as np

try:
    import ezdxf  # solo si se quiere DXF
    HAS_EZDXF = True
except ModuleNotFoundError:  # pragma: no cover
    HAS_EZDXF = False

Point3D = Tuple[float, float, float]
Edge3D = Tuple[Point3D, Point3D]


@dataclass
class ManhattanPath:
    order: str                   # Ej. "X→Z→Y"
    points: List[Point3D]        # Lista de vértices
    manhattan: float             # Distancia Manhattan total


class ImprovedExternalPointConnector:
    # ──────────────────────────── INIT ──────────────────────────────── #
    def __init__(
        self,
        graph_json_path: Optional[str] = None,
        *,
        graph_data: Optional[Dict[Point3D, List[Point3D]]] = None,
        grid_size: Optional[float] = None,
        verbose: bool = True,
    ) -> None:
        if graph_json_path is None and graph_data is None:
            raise ValueError("Debes proporcionar graph_json_path o graph_data.")

        self.verbose = verbose
        self.graph_data: Dict[Point3D, List[Point3D]] = (
            graph_data if graph_data is not None else self._load_json(graph_json_path)  # type: ignore[arg-type]
        )

        self.bounding_box = self._calc_bounding_box()
        self.grid_size = grid_size or self._calc_optimal_grid_size()
        self._log(f"grid_size = {self.grid_size:.3f}")

        self.edges: List[Edge3D] = self._build_edge_list()
        self.edge_grid_index = self._build_edge_spatial_index()

    # ────────────────────────── HELPERS ─────────────────────────────── #
    def _log(self, msg: str) -> None:  # pragma: no cover
        if self.verbose:
            print(msg)

    def _load_json(self, path: str) -> Dict[Point3D, List[Point3D]]:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        parsed: Dict[Point3D, List[Point3D]] = {}
        for k, lst in raw.items():
            node = tuple(float(c) for c in k.strip("()").split(","))
            parsed[node] = [tuple(float(c) for c in n) for n in lst]
        return parsed

    def _calc_bounding_box(self):
        coords = list(self.graph_data)
        mins = [min(p[i] for p in coords) for i in range(3)]
        maxs = [max(p[i] for p in coords) for i in range(3)]
        return {"min": mins, "max": maxs, "size": [maxs[i] - mins[i] for i in range(3)]}

    def _calc_optimal_grid_size(self) -> float:
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

    # floor para negativos (// trunca)
    def _cell(self, p: Point3D) -> Tuple[int, int, int]:
        return (math.floor(p[0] / self.grid_size),
                math.floor(p[1] / self.grid_size),
                math.floor(p[2] / self.grid_size))

    def _build_edge_list(self) -> List[Edge3D]:
        seen: Set[Edge3D] = set()
        for a, lst in self.graph_data.items():
            for b in lst:
                seen.add(tuple(sorted((a, b))))  # type: ignore[arg-type]
        return list(seen)

    # DDA para las celdas que cruza un segmento
    def _cells_of_segment(self, a: Point3D, b: Point3D) -> Set[Tuple[int, int, int]]:
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
        grid = defaultdict(list)
        for idx, (a, b) in enumerate(self.edges):
            for c in self._cells_of_segment(a, b):
                grid[c].append(idx)
        return dict(grid)

    # ────────────── GEOMETRÍA: distancia punto-segmento ─────────────── #
    @staticmethod
    def _dist_point_segment(p: Point3D, a: Point3D, b: Point3D) -> Tuple[float, Point3D]:
        ap = np.subtract(p, a)
        ab = np.subtract(b, a)
        denom = np.dot(ab, ab)
        t = float(max(0, min(1, np.dot(ap, ab) / denom))) if denom else 0.0
        proj = tuple(a_i + t * ab_i for a_i, ab_i in zip(a, ab))
        return math.dist(p, proj), proj

    # ────────────────────── ALGORITMO PRINCIPAL ─────────────────────── #
    def find_closest_edge(
        self,
        external: Point3D,
        *,
        max_radius: int | None = None,
        keep_paths: int = 2,  # ← solo las 2 más cortas
    ):
        # For very distant points, fall back to brute force which is more predictable
        if self._is_point_very_distant(external):
            self._log("Point is very distant, using brute force search...")
            return self._brute_force_search(external, keep_paths)
        
        centre = self._cell(external)
        if max_radius is None:
            max_radius = 100  # More reasonable limit

        best_d = math.inf
        best_idx = None
        best_proj = None
        seen: Set[int] = set()

        for r in range(max_radius + 1):
            # Only search the "shell" of radius r, not the entire cube
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
        }
    
    def _is_point_very_distant(self, point: Point3D) -> bool:
        """Check if point is very far from the bounding box"""
        bbox = self.bounding_box
        # Calculate distance from point to bounding box
        dist_to_bbox = 0.0
        for i in range(3):
            if point[i] < bbox["min"][i]:
                dist_to_bbox += (bbox["min"][i] - point[i]) ** 2
            elif point[i] > bbox["max"][i]:
                dist_to_bbox += (point[i] - bbox["max"][i]) ** 2
        
        dist_to_bbox = math.sqrt(dist_to_bbox)
        max_bbox_size = max(bbox["size"])
        
        # If point is more than 2x the bbox size away, consider it very distant
        return dist_to_bbox > 2 * max_bbox_size
    
    def _get_shell_cells(self, centre: Tuple[int, int, int], radius: int) -> List[Tuple[int, int, int]]:
        """Get only the cells on the shell of the given radius (much more efficient)"""
        if radius == 0:
            return [centre]
        
        cells = []
        cx, cy, cz = centre
        
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                for dz in range(-radius, radius + 1):
                    # Only include cells that are exactly at distance 'radius' (shell)
                    if max(abs(dx), abs(dy), abs(dz)) == radius:
                        cells.append((cx + dx, cy + dy, cz + dz))
        
        return cells
    
    def _brute_force_search(self, external: Point3D, keep_paths: int) -> dict:
        """Fallback brute force search for very distant points"""
        best_d = math.inf
        best_idx = None
        best_proj = None
        
        self._log(f"Checking {len(self.edges)} edges with brute force...")
        
        for idx, (a, b) in enumerate(self.edges):
            d, proj = self._dist_point_segment(external, a, b)
            if d < best_d:
                best_d, best_idx, best_proj = d, idx, proj
        
        if best_idx is None or best_proj is None:
            raise RuntimeError("No se encontró arista.")
        
        paths = self._manhattan_paths(external, best_proj, keep=keep_paths)
        
        return {
            "best_edge": self.edges[best_idx],
            "projection": best_proj,
            "euclidean": best_d,
            "best_manhattan_path": paths[0].__dict__,
            "all_paths": [p.__dict__ for p in paths],
        }

    # ─────────── Rutas Manhattan (solo 'keep' más cortas) ────────────── #
    def _manhattan_paths(
        self, start: Point3D, end: Point3D, *, keep: int = 2
    ) -> List[ManhattanPath]:
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
            
            # Skip if we've seen this exact path before
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

    # ─────────────────────────── EXPORT DXF ──────────────────────────── #
    def export_dxf(self, result, filename: str):
        if not HAS_EZDXF:
            raise RuntimeError("ezdxf no instalado.")
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        
        # Add the closest edge line
        edge = result["best_edge"]
        msp.add_line(edge[0], edge[1], dxfattribs={"color": 7})  # White/gray edge
        
        # Add projection point circle (red)
        msp.add_circle(result["projection"], radius=0.5, dxfattribs={"color": 1})
        
        # Add starting point circle (yellow) - only once
        if result["all_paths"]:
            starting_point = result["all_paths"][0]["points"][0]
            msp.add_circle(starting_point, radius=1.0, dxfattribs={"color": 2})  # Yellow
        
        # Add Manhattan paths with lines and point circles
        for i, p in enumerate(result["all_paths"]):
            path_color = 3 + i  # Green, cyan, etc.
            
            # Add lines between consecutive points
            for a, b in zip(p["points"], p["points"][1:]):
                msp.add_line(a, b, dxfattribs={"color": path_color})
            
            # Add circles for intermediate points only (skip start and end)
            for j, point in enumerate(p["points"]):
                if j == 0:
                    # Starting point - already added above as yellow circle
                    continue
                elif j == len(p["points"]) - 1:
                    # End point (projection) - already added above as red circle
                    continue
                else:
                    # Intermediate points - smaller circles, same color as path
                    msp.add_circle(point, radius=0.3, dxfattribs={"color": path_color})
        
        doc.saveas(filename)
        return filename


# ─────────────────────────────── CLI ───────────────────────────────── #
def main(argv: Sequence[str] | None = None) -> None:
    argv = list(argv or sys.argv[1:])
    if len(argv) < 4:
        print(
            "Uso:\n  python connector_orto.py "
            "graph.json X Y Z [max_radius] [--json] [--dxf]"
        )
        sys.exit(1)

    graph_file, x, y, z, *rest = argv
    external = (float(x), float(y), float(z))
    max_radius = None
    want_dxf = False
    want_json = False
    for arg in rest:
        if arg == "--dxf":
            want_dxf = True
        elif arg == "--json":
            want_json = True
        else:
            max_radius = int(arg)

    conn = ImprovedExternalPointConnector(graph_json_path=graph_file, verbose=True)
    res = conn.find_closest_edge(external, max_radius=max_radius)
    
    # Show basic results
    print(f"Closest edge: {res['best_edge'][0]} to {res['best_edge'][1]}")
    print(f"Projection: {res['projection']}")
    print(f"Euclidean distance: {res['euclidean']:.3f}")
    print(f"Best Manhattan path: {res['best_manhattan_path']['manhattan']:.3f} units")
    
    if want_json:
        out_json = (
            f"improved_external_connection_{external[0]:.1f}_{external[1]:.1f}_{external[2]:.1f}.json"
        )
        Path(out_json).write_text(json.dumps(res, indent=2))
        print("JSON guardado en:", out_json)

    if want_dxf:
        base_name = f"improved_external_connection_{external[0]:.1f}_{external[1]:.1f}_{external[2]:.1f}"
        
        # Find the next available counter
        counter = 1
        while True:
            dxf_name = f"{base_name}_dxf_{counter}.dxf"
            if not Path(dxf_name).exists():
                break
            counter += 1
                
        conn.export_dxf(res, dxf_name)
        print("DXF generado:", dxf_name)


if __name__ == "__main__":
    main() 