"""Keystone gate: the BSM semi-synthetic recovery study must control the
interaction family-wise error rate under the null-interaction scenarios.

The BSM design preserves the executed 158-continuous + 2-binary input structure.
Scenarios ``global_null`` and ``interaction_null`` contain main effects (and, for
``interaction_null``, nonlinear main-effect transforms) but **no true
interactions**, so a faithful hierarchical interaction-discovery stage must
control the interaction FWER at the configured ``alpha`` -- i.e. it must not let
main-effect (or binary main-effect) signal leak into the interaction scores.

This mirrors the generic rfm-pipeline RS-S04 gate but on the BSM 160-column
design, so the manuscript's method-evidence claim is validated on the actual
case-study input structure.
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

    alpha = 0.1
    scale = driver.StudyScale(
        n_inputs=24,
        n_outputs=12,
        n_runs=500,
        B=99,
        B_screen=99,
        fwer_reps=40,
        alt_reps=1,
        alpha=alpha,
        description="BSM RS gate scale",
    )
    scenarios = {s.name: s for s in driver.prespecified_bsm_scenarios()}
    scenario = scenarios[scenario_name]

    master_rng = np.random.default_rng(20240711)
    flags = driver.run_fwer_replicates(scenario, scale, master_rng)
    stats = empirical_interaction_fwer(flags)

    # FWER must be controlled at alpha (allow Monte-Carlo slack: at fwer_reps=40
    # and alpha=0.1 the binomial SE is ~0.047, so alpha + ~3 SE ~= 0.24).
    assert stats["fwer_proportion"] <= alpha + 0.16, (
        f"{scenario_name}: empirical BSM interaction-FWER "
        f"{stats['fwer_proportion']:.3f} exceeds alpha={alpha} "
        f"(main-effect / binary leakage into interaction scores?); flags={flags}"
    )


def test_bsm_design_has_two_binary_inputs(driver):
    """The BSM semi-synthetic design must expose exactly the 2 binary scenario inputs."""
    design = driver.load_bsm_input_design()
    assert design.n_inputs == 160
    assert len(design.binary_input_names) == 2, (
        f"expected 2 binary scenario inputs, got {design.binary_input_names}"
    )
    assert len(design.continuous_input_names) == 158
