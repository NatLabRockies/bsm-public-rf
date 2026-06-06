"""Generate manuscript figures from committed model artifacts.

Reads committed CSVs under artifacts/ and writes publication-ready SVG/PDF
figures to figures/. No raw BSM data or HPC infrastructure required.

Usage
-----
    pixi run reproduce-artifacts
    # or directly:
    python scripts/generate_manuscript_figures.py [--output-dir figures/]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

matplotlib.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "axes.linewidth": 0.8,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "lines.linewidth": 1.2,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
    }
)

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_ROOT = REPO_ROOT / "artifacts"


def _load_artifacts(artifact_root: Path) -> dict[str, pd.DataFrame]:
    """Load committed CSVs; raise FileNotFoundError if any are missing."""
    files = {
        "ablation": artifact_root / "tables" / "ablation_table.csv",
        "per_output_nrmse": artifact_root / "tables" / "per_output_nrmse.csv",
        "nrmse_summary": artifact_root / "tables" / "per_output_nrmse_summary.csv",
        "workflow_stages": artifact_root / "tables" / "workflow_stage_summary.csv",
        "support_features": artifact_root / "final_model" / "final_support_features.csv",
        "pruning_impact": artifact_root / "final_model" / "feature_pruning_impact.csv",
    }
    missing = [str(p) for p in files.values() if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required committed artifacts:\n" + "\n".join(f"  {m}" for m in missing)
            + "\nRun the full pipeline first: pixi run reproduce-full"
        )
    return {k: pd.read_csv(v) for k, v in files.items()}


# ──────────────────────────────────────────────────────────────────────────────
# Figure 1 — Model performance ablation (horizontal bar + CI whiskers)
# ──────────────────────────────────────────────────────────────────────────────
_MODEL_DISPLAY = {
    "null_mean": "Null mean\nbaseline",
    "main_effects_ols": "Main effects\nOLS",
    "screened_ols": "Screened\nOLS",
    "penalized_ols": "Penalized\nOLS (elastic net)",
    "final_ols": "Final OLS\n(sparse support)",
}
_MODEL_ORDER = ["null_mean", "main_effects_ols", "screened_ols", "penalized_ols", "final_ols"]
_MODEL_COLORS = {
    "null_mean": "#aaaaaa",
    "main_effects_ols": "#7fc7d9",
    "screened_ols": "#5ba8c0",
    "penalized_ols": "#2879a5",
    "final_ols": "#1a5e8a",
}


def figure_model_performance(df: pd.DataFrame, out_dir: Path) -> None:
    df = df.copy()
    df = df[df["model_name"].isin(_MODEL_ORDER)].copy()
    df["model_name"] = pd.Categorical(df["model_name"], categories=_MODEL_ORDER, ordered=True)
    df = df.sort_values("model_name").reset_index(drop=True)
    labels = [_MODEL_DISPLAY.get(m, m) for m in df["model_name"]]
    colors = [_MODEL_COLORS.get(m, "#555") for m in df["model_name"]]

    fig, ax = plt.subplots(figsize=(9, 2.9))
    y = np.arange(len(df))
    xerr = np.array([df["nrmse"] - df["ci_lower"], df["ci_upper"] - df["nrmse"]])
    ax.barh(y, df["nrmse"], color=colors, height=0.55, zorder=2)
    ax.errorbar(
        df["nrmse"], y, xerr=xerr, fmt="none", ecolor="k", capsize=3, linewidth=0.8, zorder=3
    )
    for i, (val, ci_lo, ci_hi) in enumerate(
        zip(df["nrmse"], df["ci_lower"], df["ci_upper"])
    ):
        ax.text(
            ci_hi + 0.002, i, f"{val:.3f}",
            va="center", ha="left", fontsize=7.5, color="#333"
        )
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Holdout macro nRMSE (lower is better)")
    ax.set_xlim(0, df["ci_upper"].max() * 1.18)
    ax.invert_yaxis()
    ax.axvline(df.loc[df["model_name"] == "final_ols", "nrmse"].values[0],
               color="#1a5e8a", linestyle="--", linewidth=0.7, alpha=0.5, zorder=1)
    ax.set_axisbelow(True)
    ax.xaxis.grid(True, linestyle=":", linewidth=0.5, color="#ccc", zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_title("Model Performance Ablation", pad=6)

    _save(fig, out_dir, "figure_model_performance")


# ──────────────────────────────────────────────────────────────────────────────
# Figure 2 — Per-output holdout nRMSE distribution
# ──────────────────────────────────────────────────────────────────────────────
def figure_per_output_nrmse_distribution(
    df_nrmse: pd.DataFrame, df_summary: pd.DataFrame, out_dir: Path
) -> None:
    nrmse = df_nrmse["nrmse"].values
    s = df_summary.iloc[0]

    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.hist(nrmse, bins=80, color="#2879a5", alpha=0.75, edgecolor="none", density=True)

    # Mark percentiles
    pct_vals = {
        "P10": s["p10"], "P25": s["p25"], "P50": s["p50"],
        "P75": s["p75"], "P90": s["p90"],
    }
    y_top = ax.get_ylim()[1]
    for label, val in pct_vals.items():
        ax.axvline(val, color="#d44", linewidth=0.8, linestyle="--", alpha=0.7)
        ax.text(val, y_top * 0.92, label, ha="center", va="top", fontsize=7, color="#d44")

    ax.set_xlabel("Per-output holdout nRMSE")
    ax.set_ylabel("Density")
    ax.set_title(
        f"Holdout nRMSE Distribution — {len(nrmse):,} model outputs\n"
        f"Macro nRMSE = {nrmse.mean():.4f}  |  Median = {s['p50']:.4f}  |  P90 = {s['p90']:.4f}",
        pad=6,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    _save(fig, out_dir, "figure_per_output_nrmse_distribution")


# ──────────────────────────────────────────────────────────────────────────────
# Figure 3 — Feature support composition
# ──────────────────────────────────────────────────────────────────────────────
_TYPE_DISPLAY = {
    "numeric": "First Order",
    "interaction": "Second Order",
    "transformation": "Non-Linear",
}
_TYPE_COLORS = {
    "First Order": "#2879a5",
    "Second Order": "#e07b39",
    "Non-Linear": "#5ba832",
}


def figure_support_composition(df_features: pd.DataFrame, out_dir: Path) -> None:
    counts = (
        df_features["feature_type"]
        .map(_TYPE_DISPLAY)
        .value_counts()
        .reindex(["First Order", "Second Order", "Non-Linear"])
        .fillna(0)
        .astype(int)
    )
    colors = [_TYPE_COLORS[k] for k in counts.index]
    total = counts.sum()

    fig, ax = plt.subplots(figsize=(9, 2.2))
    bars = ax.barh(counts.index, counts.values, color=colors, height=0.55)
    for bar, val in zip(bars, counts.values):
        ax.text(
            bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
            f"{val} ({val/total:.0%})", va="center", ha="left", fontsize=8
        )
    ax.set_xlabel("Number of features in final support")
    ax.set_xlim(0, counts.max() * 1.3)
    ax.set_title(f"Final Model Support Composition  (n={total} features)", pad=6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.invert_yaxis()
    ax.xaxis.grid(True, linestyle=":", linewidth=0.5, color="#ccc", zorder=0)
    ax.set_axisbelow(True)

    _save(fig, out_dir, "figure_support_composition")


# ──────────────────────────────────────────────────────────────────────────────
# Figure 4 — Feature pruning curve
# ──────────────────────────────────────────────────────────────────────────────
def figure_feature_pruning_curve(df_pruning: pd.DataFrame, out_dir: Path) -> None:
    df = df_pruning.sort_values("retained_features", ascending=False).reset_index(drop=True)
    x = df["retained_features"].values
    y = df["approx_macro_nrmse_upper_bound"].values

    # Cutoff boundary: min retained_features where effective_cutoff == True
    cutoff_mask = df["selected_by_effective_cutoff"] == True  # noqa: E712
    cutoff_n = df.loc[cutoff_mask, "retained_features"].min() if cutoff_mask.any() else None

    fig, ax = plt.subplots(figsize=(10, 5.8))
    ax.step(x, y, color="#2879a5", linewidth=1.2, where="post")
    ax.fill_between(x, y, step="post", alpha=0.10, color="#2879a5")

    if cutoff_n is not None:
        cutoff_y = df.loc[df["retained_features"] == cutoff_n, "approx_macro_nrmse_upper_bound"].values[0]
        ax.axvline(cutoff_n, color="#d44", linewidth=0.9, linestyle="--", alpha=0.85)
        ax.scatter([cutoff_n], [cutoff_y], color="#d44", s=40, zorder=5)
        ax.text(
            cutoff_n + 1, cutoff_y,
            f"Selected cutoff\n({cutoff_n} features)",
            va="bottom", ha="left", fontsize=7.5, color="#d44"
        )

    ax.set_xlabel("Retained features")
    ax.set_ylabel("Approximate macro nRMSE upper bound")
    ax.set_title("Feature Pruning Curve — Impact of Sequential Feature Removal", pad=6)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(20))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, linestyle=":", linewidth=0.5, color="#ccc")

    _save(fig, out_dir, "figure_feature_pruning_curve")


# ──────────────────────────────────────────────────────────────────────────────
# Figure 5 — Workflow stage summary
# ──────────────────────────────────────────────────────────────────────────────
_STAGE_DISPLAY = {
    "output_conditioning": "Output conditioning",
    "empirical_null_screening": "Null screening",
    "interaction_discovery": "Interaction discovery",
    "nonlinear_discovery": "Nonlinear discovery",
    "sparse_selection_and_stability": "Sparse + stability selection",
    "final_inferential_filter": "Inferential filter (HC3)",
    "feature_pruning": "Feature pruning",
    "final_ols": "Final OLS",
}
_STAGE_QUANTITY_DISPLAY = {
    "retained_scalar_outputs": "Scalar outputs retained",
    "retained_pca_components": "PCA components retained",
    "retained_terms": "Screened terms retained",
    "retained_pairs": "Interaction pairs retained",
    "retained_transformations": "Nonlinear terms retained",
    "final_stable_support_terms": "Stable support terms",
    "hc3_retained_terms": "HC3-retained terms",
    "removed_terms_after_hc3": "Terms pruned",
    "holdout_nrmse": "Holdout macro nRMSE",
}


def figure_workflow_stage_summary(df_stages: pd.DataFrame, out_dir: Path) -> None:
    rows = []
    for _, row in df_stages.iterrows():
        stage = _STAGE_DISPLAY.get(row["stage"], row["stage"])
        qty = _STAGE_QUANTITY_DISPLAY.get(row["primary_quantity"], row["primary_quantity"])
        val = row["recomputed_value"]
        rows.append({"Stage": stage, "Quantity": qty, "Value": val})
    df_disp = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(9, len(df_disp) * 0.45 + 0.9))
    ax.axis("off")
    col_widths = [0.35, 0.45, 0.20]
    table = ax.table(
        cellText=[[
            r["Stage"],
            r["Quantity"],
            f"{r['Value']:.4f}" if r["Value"] < 1 else f"{int(r['Value']):,}"
        ] for _, r in df_disp.iterrows()],
        colLabels=["Stage", "Primary Quantity", "Value"],
        loc="center",
        cellLoc="left",
        colWidths=col_widths,
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.5)
    table.scale(1, 1.4)
    for (row_idx, col_idx), cell in table.get_celld().items():
        if row_idx == 0:
            cell.set_facecolor("#2879a5")
            cell.set_text_props(color="white", weight="bold")
        elif row_idx % 2 == 0:
            cell.set_facecolor("#f0f4f8")
        cell.set_edgecolor("#cccccc")
    ax.set_title("Workflow Stage Summary", pad=8, fontsize=10)

    _save(fig, out_dir, "figure_workflow_stage_summary")


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def _save(fig: plt.Figure, out_dir: Path, name: str) -> None:
    for fmt in ("pdf", "svg"):
        path = out_dir / f"{name}.{fmt}"
        fig.savefig(path)
        try:
            label = str(path.relative_to(REPO_ROOT))
        except ValueError:
            label = str(path)
        print(f"  Saved: {label}")
    plt.close(fig)


def generate_all(artifact_root: Path = ARTIFACT_ROOT, output_dir: Path | None = None) -> None:
    out_dir = output_dir or REPO_ROOT / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading committed artifacts from {artifact_root.relative_to(REPO_ROOT)} ...")
    data = _load_artifacts(artifact_root)

    print("\nGenerating figures:")
    figure_model_performance(data["ablation"], out_dir)
    figure_per_output_nrmse_distribution(data["per_output_nrmse"], data["nrmse_summary"], out_dir)
    figure_support_composition(data["support_features"], out_dir)
    figure_feature_pruning_curve(data["pruning_impact"], out_dir)
    figure_workflow_stage_summary(data["workflow_stages"], out_dir)

    print(f"\nDone. {len(list(out_dir.glob('*.pdf')))} PDF and "
          f"{len(list(out_dir.glob('*.svg')))} SVG figures written to {out_dir}/")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", default=None, help="Output directory (default: figures/)")
    parser.add_argument(
        "--artifact-root", default=None,
        help="Root of artifact directory (default: artifacts/)"
    )
    args = parser.parse_args()

    artifact_root = Path(args.artifact_root) if args.artifact_root else ARTIFACT_ROOT
    output_dir = Path(args.output_dir) if args.output_dir else None

    try:
        generate_all(artifact_root=artifact_root, output_dir=output_dir)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
