#!/usr/bin/env python3
"""ultimate_xlsx_graph_generator.py  (v3‑csv)

🆕 Now handles **Excel *and* CSV** source files.

Convert a spreadsheet that lists cable‑tray endpoints into the *subsystem‑tagged*
JSON expected by the cable‑aware A* router.

───────────────────────────────────────────────────────────────────────────────
Highlights
──────────
* **Mixed input** – pass either an *.xlsx* (or *.xls*) file *or* a *.csv/ txt*.
* **Multi‑point rows** – if a row contains *n* endpoints p0 … pn‑1 we emit
  *n‑1* edges p0‑p1, p1‑p2, … so the graph remains pairwise.
* **Subsystem tagging** – use a dedicated column (default *Sistema*) or a
  constant via `--default-sys`.

CLI example
───────────
```bash
# Excel → JSON
python ultimate_xlsx_graph_generator.py \
       --infile "LV1A ordenado.xlsx" \
       --out     graph_LVA1.json

# CSV (semicolon‑delimited) → JSON, forcing subsystem B for all rows
python ultimate_xlsx_graph_generator.py \
       --infile LV1B_checked.csv \
       --delimiter ';'           \
       --default-sys B           \
       --out graph_LV1B.json
```

JSON schema
───────────
```json5
{
  "nodes": {"(x,y,z)": {"sys": "A"}, ...},
  "edges": [
    {"from": "(x,y,z)", "to": "(x,y,z)", "sys": "A"},
    ...
  ]
}
```
"""
import argparse
import json
import re
from pathlib import Path
from collections import defaultdict
from typing import Union, Optional

import pandas as pd

# -----------------------------------------------------------------------------
# Coordinate helpers
# -----------------------------------------------------------------------------
def canonical(pt):
    """Return a stable string key for (x, y, z) rounded to 3 decimals."""
    x, y, z = (round(float(v), 3) for v in pt)
    return f"({x:.3f}, {y:.3f}, {z:.3f})"

def parse_endpoint(token: str):
    parts = re.split(r"\s+", token.strip())
    if len(parts) != 3:
        raise ValueError(
            f"Coordinate group '{token}' does not have exactly 3 numbers (x y z)"
        )
    return tuple(map(float, parts))

# -----------------------------------------------------------------------------
# Graph builder
# -----------------------------------------------------------------------------
def build_graph(df: pd.DataFrame, coord_col: str, sys_col: Optional[str], default_sys: Optional[str]):
    """Create `nodes` + `edges` from DataFrame rows."""
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    for ridx, row in df.iterrows():
        sys_tag = (
            row[sys_col]
            if sys_col and sys_col in row and pd.notna(row[sys_col])
            else default_sys
        )
        if sys_tag is None:
            raise ValueError(
                f"Row {ridx}: subsystem column '{sys_col}' empty and --default-sys not provided"
            )

        raw_line = str(row[coord_col])
        tokens = [tok.strip() for tok in raw_line.split("|") if tok.strip()]
        if len(tokens) < 2:
            raise ValueError(
                f"Row {ridx}: column '{coord_col}' must contain ≥2 endpoints separated by '|'"
            )

        pts = [parse_endpoint(tok) for tok in tokens]
        keys = [canonical(pt) for pt in pts]

        for k in keys:
            nodes.setdefault(k, {"sys": sys_tag})

        for a, b in zip(keys, keys[1:]):
            edges.append({"from": a, "to": b, "sys": sys_tag})

    return {"nodes": nodes, "edges": edges}

# -----------------------------------------------------------------------------
# Main entry
# -----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", required=True, help="Source file (.xlsx, .xls, .csv, .txt …)")
    ap.add_argument("--out", required=True, help="Output JSON file")
    ap.add_argument("--sheet", default=0, help="Sheet name or index for Excel sources")
    ap.add_argument("--delimiter", default=",", help="CSV delimiter – ignored for Excel sources")
    ap.add_argument("--coord-col", default="Puntos", help="Column with the endpoints string")
    ap.add_argument("--sys-col", default="Sistema", help="Column with subsystem tag (optional)")
    ap.add_argument(
        "--default-sys",
        default=None,
        help="Subsystem tag to use when --sys-col is absent/blank",
    )
    args = ap.parse_args()

    src_path = Path(args.infile)
    if not src_path.exists():
        raise SystemExit(f"✗ File not found: {src_path}")

    # ── Load either Excel or CSV ───────────────────────────────────────────
    ext = src_path.suffix.lower()
    if ext in {".xlsx", ".xls", ".xlsm"}:
        df = pd.read_excel(src_path, sheet_name=args.sheet)
    elif ext in {".csv", ".txt"}:
        df = pd.read_csv(src_path, delimiter=args.delimiter)
    else:
        raise SystemExit(
            f"✗ Unsupported extension '{ext}'. Use .xlsx/.xls/.csv/.txt or adjust the script."
        )

    graph = build_graph(
        df,
        coord_col=args.coord_col,
        sys_col=args.sys_col if args.sys_col else None,
        default_sys=args.default_sys,
    )

    Path(args.out).write_text(json.dumps(graph, indent=2))
    print(
        f"✓ Wrote {len(graph['nodes'])} nodes and {len(graph['edges'])} edges → {args.out}"
    )


if __name__ == "__main__":  # pragma: no cover
    main() 