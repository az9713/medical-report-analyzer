from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader, select_autoescape
import json


def generate_report(*, normalized: List[Dict[str, Any]], trends: List[Dict[str, Any]], scored: List[Dict[str, Any]], out_dir: Path, title: str, favorites: list[str]):
    out_dir.mkdir(parents=True, exist_ok=True)
    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )

    assets_dir = out_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    _write_assets(assets_dir)

    # Aggregate latest per test for KPI and table
    latest_by_code: Dict[str, Dict[str, Any]] = {}
    for r in scored:
        code = r["test_code"]
        existing = latest_by_code.get(code)
        if not existing:
            latest_by_code[code] = r
            continue
        r_dt = r.get("measured_at")
        e_dt = existing.get("measured_at")
        if r_dt and (not e_dt or r_dt > e_dt):
            latest_by_code[code] = r

    # Group by category
    by_category: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in latest_by_code.values():
        by_category[r.get("category", "unknown")].append(r)

    # Overview
    index_tpl = env.get_template("index.html")
    index_html = index_tpl.render(
        title=title,
        favorites=favorites,
        latest=latest_by_code,
        categories=by_category,
        data_json=json.dumps(scored),
    )
    (out_dir / "index.html").write_text(index_html, encoding="utf-8")

    # Tests index
    tests_tpl = env.get_template("tests/index.html")
    tests_html = tests_tpl.render(
        title=title,
        latest=latest_by_code,
    )
    (out_dir / "tests" ).mkdir(exist_ok=True)
    (out_dir / "tests" / "index.html").write_text(tests_html, encoding="utf-8")


def _write_assets(assets_dir: Path):
    css = """
    :root { --ok:#22c55e; --warn:#f59e0b; --bad:#ef4444; --muted:#6b7280; }
    * { box-sizing:border-box; }
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; margin:0; background:#0b1020; color:#e5e7eb; }
    header, footer { padding:16px 24px; }
    header { display:flex; align-items:center; justify-content:space-between; background:#0f172a; border-bottom:1px solid #1f2937; }
    .title { font-weight:700; letter-spacing:0.2px; }
    .container { padding: 16px 24px; }
    .filters { display:flex; gap:12px; flex-wrap:wrap; margin-bottom:16px; }
    .tile-grid { display:grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap:12px; }
    .tile { background:#121a34; border:1px solid #1f2937; border-radius:10px; padding:12px; }
    .tile .label { color:#9ca3af; font-size:12px; }
    .tile .value { font-size:20px; font-weight:700; }
    .status-ok { color: var(--ok); }
    .status-warn { color: var(--warn); }
    .status-bad { color: var(--bad); }
    table { width:100%; border-collapse: collapse; }
    th, td { text-align:left; padding:10px; border-bottom:1px solid #1f2937; }
    th { color:#9ca3af; font-weight:600; }
    a { color:#93c5fd; text-decoration:none; }
    .muted { color:#9ca3af; }
    .grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
    @media (max-width: 900px){ .grid { grid-template-columns: 1fr; } }
    """
    (assets_dir / "style.css").write_text(css, encoding="utf-8")

    js = """
    function statusClass(status){
      if(status==='in_range') return 'status-ok';
      if(status==='high') return 'status-bad';
      if(status==='low') return 'status-warn';
      return 'muted';
    }
    """
    (assets_dir / "app.js").write_text(js, encoding="utf-8")

