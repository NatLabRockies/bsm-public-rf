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
    # and alpha=0.05 the binomial SE is ~0.034, so alpha + ~3 SE ~= 0.15).
    assert stats["fwer_proportion"] <= alpha + 0.10, (
        f"{scenario_name}: empirical BSM interaction-FWER "
        f"{stats['fwer_proportion']:.3f} exceeds alpha={alpha} "
        f"(main-effect leakage into interaction scores?); flags={flags}"
    )


def test_bsm_replication_executed(driver, tmp_path):
    """Replication loops must execute alt_reps and fwer_reps, writing replicate records."""
    # Smoke-test: run a tiny scale with >1 replicate and verify records are written.
    scale = driver.StudyScale(
        n_inputs=158, n_outputs=4, n_runs=100, B=9, B_screen=9,
        fwer_reps=2, alt_reps=2, alpha=0.05, description="replication-smoke"
    )
    import sys
    args = [
        "scripts/run_bsm_recovery_study.py",
        "--seed", "42",
        "--quick",
        "--output-dir", str(tmp_path),
    ]
    # Monkey-patch the scale to force the tiny smoke scale.
    original_quick = driver._QUICK_SCALE
    driver._QUICK_SCALE = scale
    try:
        # Run the main driver.
        exit_code = driver.main(args[1:])
        assert exit_code == 0, "Driver must exit 0"
        
        # Check replicate_records.csv exists and has >1 row per scenario type.
        reps_path = tmp_path / "replicate_records.csv"
        assert reps_path.exists(), "replicate_records.csv must be written"
        reps_df = __import__("pandas").read_csv(reps_path)
        assert len(reps_df) > 0, "replicate_records.csv must have rows"
        
        # Check fwer_calibration.csv has passes_calibration column.
        calib_path = tmp_path / "fwer_calibration.csv"
        assert calib_path.exists(), "fwer_calibration.csv must be written"
        calib_df = __import__("pandas").read_csv(calib_path)
        assert "passes_calibration" in calib_df.columns, (
            "fwer_calibration.csv must have passes_calibration column"
        )
        assert calib_df["n_replicates"].min() >= 2, (
            "FWER replication must run >1 replicate per null scenario"
        )
        
        # Check recovery_estimands.csv has Monte-Carlo uncertainty fields.
        est_path = tmp_path / "recovery_estimands.csv"
        assert est_path.exists(), "recovery_estimands.csv must be written"
        est_df = __import__("pandas").read_csv(est_path)
        # Estimands should have _mean and _se columns.
        assert any("_mean" in c for c in est_df.columns), (
            "recovery_estimands.csv must have _mean fields for Monte-Carlo aggregation"
        )
        assert any("_se" in c for c in est_df.columns), (
            "recovery_estimands.csv must have _se fields for Monte-Carlo uncertainty"
        )
        
        # Check reproduction_log.md exists and contains required sections.
        log_path = tmp_path / "reproduction_log.md"
        assert log_path.exists(), "reproduction_log.md must be written"
        log_text = log_path.read_text()
        assert "bsm-public-rf commit:" in log_text, "Log must contain commit hash"
        assert "Validation gate" in log_text, "Log must contain gate result"
        assert "Artifact hashes (SHA-256)" in log_text, "Log must contain artifact hashes"
        assert "Per-scenario replicate status" in log_text, "Log must contain replicate status"
        
    finally:
        driver._QUICK_SCALE = original_quick


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


def test_bsm_driver_uses_production_pipeline(driver):
    """The driver must call run_production_recovery_pipeline, not a substitute."""
    import inspect
    source = inspect.getsource(driver.run_pipeline)
    assert "run_production_recovery_pipeline" in source, (
        "run_pipeline must delegate to run_production_recovery_pipeline"
    )
    # Smoke-test: run one replicate and verify production result is present.
    design = driver.load_bsm_input_design()
    scenario = driver.prespecified_bsm_scenarios()[0]
    scale = driver.StudyScale(
        n_inputs=158, n_outputs=6, n_runs=100, B=9, B_screen=9,
        fwer_reps=1, alt_reps=1, alpha=0.05, description="smoke"
    )
    import numpy as np
    data = driver.generate_bsm_dataset(
        driver.first_order_candidate_design(design), scenario, scale, seed=42
    )
    result = driver.run_pipeline(
        data, scale, np.random.default_rng(42), with_comparators=False
    )
    assert "production_result" in result, (
        "run_pipeline must return production_result from run_production_recovery_pipeline"
    )
    assert hasattr(result["production_result"], "screening_retained_set"), (
        "production_result must be a ProductionRecoveryResult"
    )
