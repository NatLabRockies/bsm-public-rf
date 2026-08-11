"""Regenerate manuscript figures from committed final model artifacts.

Reads the committed CSVs in artifacts/ and writes the exact same
publication-ready figures (SVG + PDF where Chrome is available) to figures/.
No raw BSM data or HPC infrastructure required.

Usage
-----
    pixi run reproduce-artifacts
    pixi run reproduce-artifacts -- --validate-only
    python scripts/reproduce_artifacts.py [--output-dir figures/] [--validate-only]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FIGURE_DATA_DIR = REPO_ROOT / "artifacts" / "figure_data"
TABLES_DIR = REPO_ROOT / "artifacts" / "tables"
MANUSCRIPT_FIGURES = (
    "figure_nrmse_bootstrap_summary.pdf",
    "figure_support_composition.pdf",
    "figure_selected_by_module_count.pdf",
    "figure_per_output_nrmse_distribution.pdf",
    "fig_module_pair_heatmap.pdf",
)


def validate_manuscript_figure_pdfs(figures_dir: Path) -> None:
    """Fail unless all manuscript figure PDFs are nontrivial PDF documents."""
    missing = [name for name in MANUSCRIPT_FIGURES if not (figures_dir / name).exists()]
    if missing:
        raise ValueError(f"missing regenerated manuscript figure PDF(s): {', '.join(missing)}")
    truncated = [
        name for name in MANUSCRIPT_FIGURES if (figures_dir / name).stat().st_size <= 1024
    ]
    if truncated:
        raise ValueError(
            f"regenerated manuscript figure PDF(s) look empty/truncated: {', '.join(truncated)}"
        )
    invalid = [
        name
        for name in MANUSCRIPT_FIGURES
        if not _has_pdf_structure((figures_dir / name).read_bytes())
    ]
    if invalid:
        raise ValueError(
            f"regenerated manuscript figure PDF(s) are not valid PDFs: {', '.join(invalid)}"
        )


def _has_pdf_structure(contents: bytes) -> bool:
    """Check the portable PDF envelope without introducing a parser dependency."""
    return (
        contents.startswith(b"%PDF-")
        and b"startxref" in contents
        and contents.rstrip().endswith(b"%%EOF")
    )


def _save_pdf(svg_path: Path) -> bool:
    """Convert SVG to PDF using Chrome headless. Returns True on success."""
    svg_text = svg_path.read_text(encoding="utf-8")
    m = re.search(r'<svg[^>]+width="(\d+(?:\.\d+)?)"[^>]+height="(\d+(?:\.\d+)?)"', svg_text)
    w, h = (int(float(m.group(1))), int(float(m.group(2)))) if m else (1200, 600)
    html_content = (
        f"<!DOCTYPE html><html><head><style>"
        f"@page{{size:{w}px {h}px;margin:0}}"
        f"html,body{{margin:0;padding:0;width:{w}px;height:{h}px;overflow:hidden}}"
        f"</style></head><body><img src='file://{svg_path.resolve()}' "
        f"width='{w}' height='{h}'/></body></html>"
    )
    pdf_path = svg_path.with_suffix(".pdf")
    # Try platform-specific Chrome paths
    chrome_candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
    ]
    chrome = next((c for c in chrome_candidates if Path(c).exists()), None)
    if chrome is None:
        return False
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False, dir=svg_path.parent) as f:
        f.write(html_content)
        tmp_html = f.name
    try:
        subprocess.run(
            [
                chrome,
                "--headless=new",
                "--no-sandbox",
                "--disable-gpu",
                f"--print-to-pdf={pdf_path}",
                "--print-to-pdf-no-header",
                f"file://{tmp_html}",
            ],
            check=True,
            capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, OSError):
        return False
    finally:
        Path(tmp_html).unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output-dir", default=None, help="Output directory (default: figures/)"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate required release-figure PDFs without regenerating them.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else REPO_ROOT / "figures"
    if args.validate_only:
        try:
            validate_manuscript_figure_pdfs(output_dir)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)
        print(f"Validated {len(MANUSCRIPT_FIGURES)} manuscript figure PDFs in {output_dir}/")
        return

    from rfm_pipeline import regenerate_figures_from_committed_data

    print(f"Loading committed artifacts...")
    try:
        written = regenerate_figures_from_committed_data(
            figure_data_dir=FIGURE_DATA_DIR,
            tables_dir=TABLES_DIR,
            output_dir=output_dir,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    n_pdf = 0
    print(f"\nGenerating figures ({len(written)} SVG):")
    for name, svg_path in sorted(written.items()):
        ok = _save_pdf(svg_path)
        status = "+PDF" if ok else ""
        n_pdf += int(ok)
        print(f"  {svg_path.name}{status}")

    pdf_note = (
        f" and {n_pdf} PDF" if n_pdf else " (no Chrome found — SVG only; PDF skipped)"
    )
    print(f"\nDone. {len(written)} SVG{pdf_note} written to {output_dir}/")


if __name__ == "__main__":
    main()
