#!/usr/bin/env python3
"""
Añade PE, PC y uno o varios PI_n a un grafo JSON.

Formato esperado del fichero de puntos (--points-json):

{
  "PE": {"x": 161.248, "y": 26.922, "z": 162.313},
  "PC": {"x": 161.248, "y": 25.145, "z": 160.124},
  "PI_1": {"x": 161.248, "y": 25.145, "z": 162.313},
  "PI_2": {"x": 161.248, "y": 26.922, "z": 160.124},
  "metadata": {
      "tolerance": 0.001,
      ...
  }
}

• PE se conecta con cada PI_n
• Cada PI_n se conecta con PC
• Si PC cae en mitad de una arista se hace *edge-split* con la tolerancia indicada.

Uso:
  python3 add_points_to_graph_multi.py base.json salida.json --points-json puntos.json
"""

import argparse
import json
from math import sqrt
from pathlib import Path
from typing import Dict, List, Tuple, Optional

Coord = Tuple[float, float, float]
Graph = Dict[Coord, List[Coord]]

# ────────────────────────  Geometría  ───────────────────────── #

def distance(a: Coord, b: Coord) -> float:
    return sqrt(sum((u - v) ** 2 for u, v in zip(a, b)))

def point_on_segment(p: Coord, a: Coord, b: Coord, tol: float) -> bool:
    """True si p está sobre el segmento [a-b] con error ≤ tol."""
    ab = tuple(bi - ai for ai, bi in zip(a, b))
    ap = tuple(pi - ai for ai, pi in zip(a, p))
    ab_len2 = sum(c * c for c in ab)
    if ab_len2 == 0:
        return False
    t = sum(ai * bi for ai, bi in zip(ap, ab)) / ab_len2
    if t < -1e-12 or t > 1 + 1e-12:
        return False
    proj = tuple(ai + t * abi for ai, abi in zip(a, ab))
    return distance(p, proj) <= tol

# ────────────────────────  Helpers IO  ─────────────────────── #

def str_to_coord(s: str) -> Coord:
    s = s.strip().lstrip("(").rstrip(")")
    return tuple(float(x) for x in s.split(","))

def coord_to_str(c: Coord) -> str:
    return f"({c[0]}, {c[1]}, {c[2]})"

def load_graph(path: str) -> Graph:
    with open(path, "r") as f:
        raw = json.load(f)
    return {str_to_coord(k): [tuple(n) for n in neigh] for k, neigh in raw.items()}

def save_graph(graph: Graph, path: str) -> None:
    serial = {coord_to_str(k): [list(n) for n in neigh] for k, neigh in graph.items()}
    with open(path, "w") as f:
        json.dump(serial, f, indent=2)
    print(f"🟢 Grafo actualizado guardado en {path}")

# ──────────────────────  Operaciones grafo  ─────────────────── #

def find_existing_node(graph: Graph, c: Coord, tol: float) -> Optional[Coord]:
    for n in graph:
        if distance(n, c) <= tol:
            return n
    return None

def ensure_node(graph: Graph, c: Coord, tol: float) -> Coord:
    node = find_existing_node(graph, c, tol)
    if node:
        return node
    graph[c] = []
    return c

def split_edge(graph: Graph, u: Coord, v: Coord, p: Coord) -> None:
    """Reemplaza la arista (u,v) por (u,p)+(p,v)."""
    if v in graph[u]:
        graph[u].remove(v)
    if u in graph[v]:
        graph[v].remove(u)
    if p not in graph:
        graph[p] = []
    for a, b in ((u, p), (p, v)):
        if b not in graph[a]:
            graph[a].append(b)
        if a not in graph[b]:
            graph[b].append(a)

def ensure_pc_node(graph: Graph, pc: Coord, tol: float) -> Coord:
    """Garantiza que PC sea nodo, partiendo la arista si es necesario."""
    node = find_existing_node(graph, pc, tol)
    if node:
        return node
    processed = set()
    for u in graph:
        for v in graph[u]:
            if (v, u) in processed:
                continue
            processed.add((u, v))
            if point_on_segment(pc, u, v, tol):
                split_edge(graph, u, v, pc)
                return pc
    graph[pc] = []
    return pc

# ──────────────────────────  CLI  ──────────────────────────── #

def parse_points_json(path: str, external_point: Optional[Coord] = None) -> Tuple[Coord, Coord, List[Coord], Optional[float]]:
    """Devuelve (PE, PC, lista_PI, tolerance_from_json)."""
    data = json.loads(Path(path).read_text())
    
    # Check if it's the new connector format
    if "projection" in data and "best_manhattan_path" in data:
        # Extract PC from projection
        pc = tuple(data["projection"])
        
        # Extract PI points from best_manhattan_path (excluding first and last points)
        path_points = data["best_manhattan_path"]["points"]
        if len(path_points) < 3:
            raise SystemExit("❌ El path debe tener al menos 3 puntos (PE, PI(s), PC)")
        
        # First point is PE, last is PC, middle points are PIs
        pe = tuple(path_points[0]) if external_point is None else external_point
        pis = [tuple(point) for point in path_points[1:-1]]
        
        if not pis:
            raise SystemExit("❌ No se encontraron puntos intermedios PI en el path")
        
        tol = data.get("tolerance", 1e-3)
        return pe, pc, pis, tol
    
    # Original format
    try:
        pe = (data["PE"]["x"], data["PE"]["y"], data["PE"]["z"])
        pc = (data["PC"]["x"], data["PC"]["y"], data["PC"]["z"])
    except KeyError:
        raise SystemExit("❌ El JSON debe tener objetos 'PE' y 'PC' con claves x,y,z o formato connector")

    pis = []
    for k, v in data.items():
        if k.upper().startswith("PI"):
            pis.append((v["x"], v["y"], v["z"]))
    if not pis:
        raise SystemExit("❌ No se encontraron claves PI_n en el JSON")

    tol = data.get("metadata", {}).get("tolerance", None)
    return pe, pc, pis, tol

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Inserta PE, PC y múltiples PI en un grafo JSON.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("input_json", help="Grafo base")
    ap.add_argument("output_json", help="Grafo resultante")
    ap.add_argument("--points-json", required=True,
                    help="Fichero con PE, PC y PI_n en el formato descrito")
    ap.add_argument("--tolerance", type=float, default=1e-3,
                    help="Tolerancia (se ignora si el JSON incluye metadata.tolerance)")
    ap.add_argument("--external-point", nargs=3, type=float, metavar=('X', 'Y', 'Z'),
                    help="Punto externo PE (x y z) si no está en el JSON")
    args = ap.parse_args()

    external_point = tuple(args.external_point) if args.external_point else None
    pe, pc, pi_list, tol_json = parse_points_json(args.points_json, external_point)
    tol = tol_json if tol_json is not None else args.tolerance

    graph = load_graph(args.input_json)

    pc_node = ensure_pc_node(graph, pc, tol)
    pe_node = ensure_node(graph, pe, tol)
    pi_nodes = [ensure_node(graph, pi, tol) for pi in pi_list]

    # Añadir aristas
    for pi in pi_nodes:
        for a, b in ((pe_node, pi), (pi, pc_node)):
            if b not in graph[a]:
                graph[a].append(b)
            if a not in graph[b]:
                graph[b].append(a)

    save_graph(graph, args.output_json)
    print("✅ Proceso completado con éxito")

if __name__ == "__main__":
    main() 