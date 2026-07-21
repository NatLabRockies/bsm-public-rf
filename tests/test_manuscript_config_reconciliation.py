"""Reconciliation gate: case-study config and manuscript figures must match
the corrected 123-feature canonical run.

Written test-first for slice PA-S01. Fails until
``configs/manuscript_case_study.yml`` is reconciled from the old 132-feature
values and the manuscript figure PDFs are regenerated. Runs without HPC access
or BSM input data.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG = REPO_ROOT / "configs" / "manuscript_case_study.yml"
FIGURES = REPO_ROOT / "figures"
FIGURE_DATA = REPO_ROOT / "artifacts" / "figure_data"

# Five figures referenced by the manuscript.
MANUSCRIPT_FIGURES = [
    "figure_nrmse_bootstrap_summary.pdf",
    "figure_support_composition.pdf",
    "figure_selected_by_module_count.pdf",
    "figure_per_output_nrmse_distribution.pdf",
    "fig_module_pair_heatmap.pdf",
]


@pytest.fixture(scope="module")
def case_study() -> dict:
    with CONFIG.open() as fh:
        return yaml.safe_load(fh)["case_study"]


def test_final_model_counts(case_study):
    fm = case_study["final_model"]
    assert fm["final_predictor_count"] == 123
    assert fm["final_main_effect_count"] == 52
    assert fm["final_interaction_count"] == 49
    assert fm["final_transformation_count"] == 22
    # Support composition must sum to the final predictor count.
    assert (
        fm["final_main_effect_count"]
        + fm["final_interaction_count"]
        + fm["final_transformation_count"]
        == fm["final_predictor_count"]
    )


def test_final_model_nrmse(case_study):
    fm = case_study["final_model"]
    assert fm["intermediate_penalized_holdout_nrmse"] == pytest.approx(0.0706, abs=5e-5)
    assert fm["final_ols_holdout_nrmse"] == pytest.approx(0.0714, abs=5e-5)
    assert fm["final_ols_holdout_nrmse_ci_lower"] == pytest.approx(0.0699, abs=5e-5)
    assert fm["final_ols_holdout_nrmse_ci_upper"] == pytest.approx(0.0724, abs=5e-5)


def test_stage_counts(case_study):
    assert (
        case_study["output_conditioning"]["temporary_reduction"]["retained_components"]
        == 17
    )
    assert case_study["empirical_null_screen"]["retained_terms"] == 70
    assert case_study["interaction_discovery"]["retained_pairs"] == 62
    assert case_study["nonlinear_discovery"]["identified_transformations"] == 25
    assert case_study["nonlinear_discovery"]["final_support_transformations"] == 22
    assert (
        case_study["sparse_selection"]["source_selected_feature_count_reference"] == 157
    )


def test_no_stale_numbers(case_study):
    fm = case_study["final_model"]
    stale = {132, 172, 54, 29}
    for key in (
        "final_predictor_count",
        "final_main_effect_count",
        "final_interaction_count",
        "final_transformation_count",
    ):
        assert fm[key] not in stale, f"{key} still carries a stale value {fm[key]}"


@pytest.mark.parametrize("name", MANUSCRIPT_FIGURES)
def test_manuscript_figure_regenerated(name):
    path = FIGURES / name
    assert path.exists(), f"missing regenerated figure: {name}"
    assert path.stat().st_size > 1024, f"figure looks empty/truncated: {name}"


def test_support_composition_figure_data_matches_canonical_counts(case_study):
    """Support-composition figure data must break transforms out separately and
    match the 123-feature canonical breakdown (regression for the 74/49/0 bug
    where library transforms were folded into First Order)."""
    import csv

    fm = case_study["final_model"]
    path = FIGURE_DATA / "figure_support_composition_data.csv"
    assert path.exists(), "missing figure_support_composition_data.csv"
    with path.open() as fh:
        rows = {r["feature_type"]: int(r["n_features"]) for r in csv.DictReader(fh)}
    assert rows.get("First Order") == fm["final_main_effect_count"] == 52
    assert rows.get("Second Order") == fm["final_interaction_count"] == 49
    assert rows.get("Non-Linear") == fm["final_transformation_count"] == 22
    assert sum(rows.values()) == fm["final_predictor_count"] == 123


def test_selected_by_module_figure_data_sums_to_final_support(case_study):
    """Module-count figure data must sum to the final predictor count (123),
    not the stale 132."""
    import csv

    path = FIGURE_DATA / "figure_selected_by_module_data.csv"
    assert path.exists(), "missing figure_selected_by_module_data.csv"
    with path.open() as fh:
        total = sum(int(r["n_selected_inputs"]) for r in csv.DictReader(fh))
    assert total == case_study["final_model"]["final_predictor_count"] == 123
