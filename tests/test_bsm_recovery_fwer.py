"""Keystone gate: the BSM semi-synthetic recovery study must control the
interaction family-wise error rate under the null-interaction scenarios.

The recovery study screens the 158-continuous first-order candidate design --
the space production actually screened. The two binary scenario switches
(AFSC/UAEORO) are part of the 160-input interface but are excluded from the
first-order candidate set exactly as the production feature catalog excludes
them; they are scenario/stratification variables, not predictor candidates.
Scenarios ``global_null`` and ``interaction_null`` contain continuous main
effects (and, for ``interaction_null``, a nonlinear main-effect transform) but
**no true interactions**, so a faithful hierarchical interaction-discovery stage
must control the interaction FWER at the configured ``alpha`` -- i.e. it must not
let main-effect signal leak into the interaction scores.

This mirrors the generic rfm-pipeline RS-S04 gate but on the BSM 158-continuous
first-order candidate design, so the manuscript's method-evidence claim is
validated on the actual case-study candidate structure.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

_DRIVER = (
    Path(__file__).resolve().parents[1] / "scripts" / "run_bsm_recovery_study.py"
)


def _load_driver():
    spec = importlib.util.spec_from_file_location("_bsm_rrs_driver", _DRIVER)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_bsm_rrs_driver"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def driver():
    return _load_driver()


@pytest.mark.parametrize("scenario_name", ["global_null", "interaction_null"])
def test_bsm_interaction_null_fwer_controlled(driver, scenario_name):
    from rfm_pipeline import empirical_interaction_fwer

    alpha = 0.05
    scale = driver.StudyScale(
        n_inputs=158,
        n_outputs=12,
        n_runs=500,
        B=199,
        B_screen=199,
        fwer_reps=40,
        alt_reps=1,
        alpha=alpha,
        description="BSM RS gate scale",
        family_error_method="fwer_max_stat_exact",
        min_exact_permutation_draws=199,
    )
    scenarios = {s.name: s for s in driver.prespecified_bsm_scenarios()}
    scenario = scenarios[scenario_name]

    master_rng = np.random.default_rng(20240711)
    flags = driver.run_fwer_replicates(scenario, scale, master_rng)
    stats = empirical_interaction_fwer(flags)

    # FWER must be controlled at alpha (allow Monte-Carlo slack: at fwer_reps=40
    # and alpha=0.05 the binomial SE is ~0.034, so alpha + ~3 SE ~= 0.15).
    assert stats["fwer_proportion"] <= alpha + 0.10, (
        f"{scenario_name}: empirical BSM interaction-FWER "
        f"{stats['fwer_proportion']:.3f} exceeds alpha={alpha} "
        f"(main-effect leakage into interaction scores?); flags={flags}"
    )


def test_bsm_design_has_two_binary_inputs(driver):
    """The BSM semi-synthetic design must expose exactly the 2 binary scenario inputs."""
    design = driver.load_bsm_input_design()
    assert design.n_inputs == 160
    assert len(design.binary_input_names) == 2, (
        f"expected 2 binary scenario inputs, got {design.binary_input_names}"
    )
    assert len(design.continuous_input_names) == 158


def test_first_order_candidate_design_excludes_binaries(driver):
    """The first-order candidate design must be the 158 continuous inputs, no binaries."""
    design = driver.load_bsm_input_design()
    candidate = driver.first_order_candidate_design(design)
    assert candidate.n_inputs == 158
    assert candidate.binary_input_names == []
    assert len(candidate.continuous_input_names) == 158
    assert candidate.continuous_input_names == design.continuous_input_names


def test_full_160_candidate_design_includes_binaries(driver):
    """full_160_candidate_design must return all 160 inputs including both binary switches."""
    design = driver.load_bsm_input_design()
    full = driver.full_160_candidate_design(design)
    assert full.n_inputs == 160
    assert len(full.binary_input_names) == 2
    assert len(full.continuous_input_names) == 158


def test_prespecified_scenarios_include_all_binary_regimes(driver):
    """prespecified_bsm_scenarios must include all three binary-regime scenarios."""
    scenarios = {s.name: s for s in driver.prespecified_bsm_scenarios()}
    required = {"binary_main_null", "binary_continuous_planted", "binary_binary_planted"}
    missing = required - set(scenarios)
    assert not missing, f"Missing binary scenarios: {missing}"

    # binary_main_null: no interaction signal, binary mains only
    s = scenarios["binary_main_null"]
    assert s.n_main_binary >= 1
    assert not s.interaction_kinds

    # binary_continuous_planted: bc interaction
    s = scenarios["binary_continuous_planted"]
    assert "bc" in s.interaction_kinds

    # binary_binary_planted: bb interaction
    s = scenarios["binary_binary_planted"]
    assert "bb" in s.interaction_kinds


def test_binary_candidate_scenarios_set_is_consistent(driver):
    """_BINARY_CANDIDATE_SCENARIOS names must match scenarios in prespecified_bsm_scenarios."""
    all_scenario_names = {s.name for s in driver.prespecified_bsm_scenarios()}
    for name in driver._BINARY_CANDIDATE_SCENARIOS:
        assert name in all_scenario_names, f"{name!r} in _BINARY_CANDIDATE_SCENARIOS but not in scenarios"


def test_binary_main_null_planted_support_has_no_interactions(driver):
    """binary_main_null planted support must have zero true interactions."""
    full_design = driver.load_bsm_input_design()
    full = driver.full_160_candidate_design(full_design)
    scenarios = {s.name: s for s in driver.prespecified_bsm_scenarios()}
    support, spec = driver._planted_support(scenarios["binary_main_null"], full)
    assert len(support.true_active_interactions) == 0, (
        f"binary_main_null should have no true interactions, got {support.true_active_interactions}"
    )
    # Binary mains should be planted.
    assert len(support.true_active_inputs) >= 1


def test_binary_continuous_planted_has_bc_interaction(driver):
    """binary_continuous_planted must plant exactly one binary-continuous interaction."""
    full_design = driver.load_bsm_input_design()
    full = driver.full_160_candidate_design(full_design)
    scenarios = {s.name: s for s in driver.prespecified_bsm_scenarios()}
    support, spec = driver._planted_support(scenarios["binary_continuous_planted"], full)
    assert len(support.true_active_interactions) == 1
    (pair,) = support.true_active_interactions
    binary_names = set(full.binary_input_names)
    cont_names = set(full.continuous_input_names)
    # Exactly one member binary, one continuous.
    a, b = pair
    assert (a in binary_names) != (b in binary_names), (
        f"Expected exactly one binary and one continuous member in bc interaction, got {pair}"
    )


def test_binary_binary_planted_has_bb_interaction(driver):
    """binary_binary_planted must plant exactly one binary-binary interaction."""
    full_design = driver.load_bsm_input_design()
    full = driver.full_160_candidate_design(full_design)
    scenarios = {s.name: s for s in driver.prespecified_bsm_scenarios()}
    support, spec = driver._planted_support(scenarios["binary_binary_planted"], full)
    assert len(support.true_active_interactions) == 1
    (pair,) = support.true_active_interactions
    binary_names = set(full.binary_input_names)
    a, b = pair
    assert a in binary_names and b in binary_names, (
        f"Both members of bb interaction must be binary, got {pair}"
    )


@pytest.mark.parametrize("scenario_name", ["binary_main_null"])
def test_binary_null_fwer_controlled_quick(driver, scenario_name):
    """binary_main_null FWER must be controlled at alpha under a quick scale."""
    from rfm_pipeline import empirical_interaction_fwer

    alpha = 0.05
    scale = driver.StudyScale(
        n_inputs=160,
        n_outputs=8,
        n_runs=300,
        B=199,
        B_screen=199,
        fwer_reps=15,
        alt_reps=1,
        alpha=alpha,
        description="binary FWER quick gate scale",
        family_error_method="fwer_max_stat_exact",
        min_exact_permutation_draws=199,
    )
    scenarios = {s.name: s for s in driver.prespecified_bsm_scenarios()}
    scenario = scenarios[scenario_name]
    full_design = driver.load_bsm_input_design()
    full = driver.full_160_candidate_design(full_design)

    master_rng = np.random.default_rng(20260809)
    flags: list[int] = []
    for _ in range(scale.fwer_reps):
        rep_seed = int(master_rng.integers(2**31))
        data = driver.generate_bsm_dataset(full, scenario, scale, rep_seed)
        result = driver.run_pipeline(data, scale, np.random.default_rng(rep_seed), with_comparators=False)
        flags.append(len(result["selected_support"].true_active_interactions))
    stats = empirical_interaction_fwer(flags)

    # Allow generous Monte-Carlo slack at fwer_reps=15.
    assert stats["fwer_proportion"] <= alpha + 0.20, (
        f"{scenario_name}: empirical BSM binary interaction-FWER "
        f"{stats['fwer_proportion']:.3f} exceeds alpha={alpha}+0.20; flags={flags}"
    )
