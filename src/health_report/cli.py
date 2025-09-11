import argparse
from pathlib import Path

from .utils.io import ensure_dirs
from .config import load_config
from .extract.pdf_parser import extract_from_reports
from .normalize.normalize import normalize_measurements
from .analyze.trends import compute_trends
from .analyze.scoring import compute_scores
from .report.generator import generate_report


def main():
    parser = argparse.ArgumentParser(description="Generate health report from PDFs")
    parser.add_argument("--reports-dir", default=None, help="Directory containing PDF reports")
    parser.add_argument("--out-dir", default=None, help="Output directory for HTML report")
    parser.add_argument("--data-dir", default=None, help="Data dir for caches")
    parser.add_argument("--units", default=None, choices=["auto", "canonical", "original"], help="Units handling mode")
    args = parser.parse_args()

    cfg = load_config()
    if args.reports_dir:
        cfg["reports_dir"] = args.reports_dir
    if args.out_dir:
        cfg["out_dir"] = args.out_dir
    if args.data_dir:
        cfg["data_dir"] = args.data_dir
    if args.units:
        cfg["units_preference"] = args.units

    reports_dir = Path(cfg["reports_dir"]).resolve()
    out_dir = Path(cfg["out_dir"]).resolve()
    data_dir = Path(cfg["data_dir"]).resolve()
    ensure_dirs([out_dir, data_dir])

    extracted = extract_from_reports(reports_dir, data_dir, cache=cfg.get("parsing", {}).get("cache", True))
    normalized = normalize_measurements(extracted, data_dir, units_preference=cfg.get("units_preference", "auto"))
    trends = compute_trends(normalized, rolling_window_days=cfg.get("analytics", {}).get("rolling_window_days", 120))
    scored = compute_scores(trends)

    generate_report(
        normalized=normalized,
        trends=trends,
        scored=scored,
        out_dir=out_dir,
        title=cfg.get("report", {}).get("title", "Health Report Dashboard"),
        favorites=cfg.get("report", {}).get("favorites", []),
    )


if __name__ == "__main__":
    main()

