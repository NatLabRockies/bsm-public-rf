"""Pre-execution G0/B controls for the BSM recovery-study driver.

These tests intentionally exercise only deterministic contract, DGP, ledger,
and manifest behavior.  They do not start calibration, HPC, or production work.
"""

from __future__ import annotations

import importlib.util
import inspect
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

_ROOT = Path(__file__).resolve().parents[1]
_DRIVER = _ROOT / "scripts" / "run_bsm_recovery_study.py"


def _load_driver():
    spec = importlib.util.spec_from_file_location("_bsm_g0b_driver", _DRIVER)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_bsm_g0b_driver"] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def driver():
    return _load_driver()


@pytest.fixture(scope="module")
def contract(driver):
    return driver.load_execution_contract()


@pytest.fixture(scope="module")
def design(driver):
    return driver.load_bsm_input_design()


def _entry_for(ledger, scenario_name: str, replicate_index: int = 0):
    return next(
        entry
        for entry in ledger.entries
        if entry.scenario == scenario_name and entry.replicate_index == replicate_index
    )


def _terminal_record(
    driver,
    contract,
    entry,
    *,
    outcome: str,
    pair_family_count: int,
    false_pair_count: int,
):
    return driver.TerminalRecord(
        phase=entry.phase,
        scenario=entry.scenario,
        replicate_index=entry.replicate_index,
        attempt=0,
        status="ANALYSIS_COMPLETE",
        terminal_outcome=outcome,
        terminal_stage="interaction_reduction",
        contract_sha256=contract.contract_sha256,
        control_snapshot_sha256=contract.control_snapshot_sha256,
        seed=entry.seed,
        schedule_sha256="schedule-fixture",
        screened_count=2,
        pair_family_count=pair_family_count,
        truth_interaction_ids=(),
        retained_interaction_ids=(),
        false_pair_count=false_pair_count,
        exception=None,
        runtime_seconds=0.01,
        max_rss_bytes=1024,
    )


def test_pinned_control_snapshot_reconciles_with_contract(driver, contract):
    snapshot = driver.verify_pinned_control_snapshot(contract)

    assert snapshot.snapshot_sha256 == contract.control_snapshot_sha256
    assert snapshot.gates == {"G0": "OPEN", "A": "OPEN", "B": "OPEN"}
    assert snapshot.path.name == "g0b_preexecution_control.md"


def test_control_snapshot_hash_mismatch_fails_closed(driver, contract):
    with pytest.raises(driver.ContractError, match="checksum"):
        driver.verify_pinned_control_snapshot(
            replace(contract, control_snapshot_sha256="0" * 64)
        )


def test_contract_is_typed_open_and_has_no_duplicate_scientific_defaults(driver, contract):
    assert contract.phase == "development"
    assert contract.status == "OPEN"
    assert contract.input_schema.n_inputs == 160
    assert contract.input_schema.continuous_inputs == 158
    assert contract.input_schema.binary_inputs == 2
    assert contract.screening.bh_q == pytest.approx(0.05)
    assert contract.screening.permutation_count_B >= 3199
    assert contract.interaction.permutation_count_B >= 999
    assert contract.interaction.selection_method == "max_stat_adjusted_p_mc"
    assert contract.interaction.alpha == pytest.approx(0.05)
    assert contract.calibration.one_sided_confidence == pytest.approx(0.95)
    assert contract.calibration.tolerance == pytest.approx(0.04)
    assert len(contract.generic_lockfile_sha256) == 64

    with pytest.raises(driver.ContractError, match="duplicate"):
        driver.load_execution_contract_text(
            """
schema_version: 1
schema_version: 2
"""
        )


def test_full_160_input_design_is_the_only_candidate_schema(driver, contract, design):
    assert design.n_inputs == contract.input_schema.n_inputs == 160
    assert len(design.continuous_input_names) == 158
    assert tuple(design.binary_input_names) == contract.input_schema.binary_input_names
    assert set(design.input_names) == set(design.continuous_input_names) | set(
        design.binary_input_names
    )

    source = _DRIVER.read_text(encoding="utf-8")
    assert "first" + "_order_candidate_design" not in source
    assert "158" + "-continuous" not in source


def test_every_dgp_has_all_binary_cells_and_row_level_heteroscedasticity(
    driver, contract, design
):
    ledger = driver.load_seed_ledger(contract)
    scenario = contract.scenario("heteroscedastic_interaction_null")
    data = driver.generate_bsm_dataset(
        contract,
        design,
        scenario,
        _entry_for(ledger, scenario.name),
    )

    assert data.X_train.shape[1] == 160
    assert data.X_eval.shape[1] == 160
    binary_indices = [data.feature_names.index(name) for name in design.binary_input_names]
    expected_cells = {(0, 0), (0, 1), (1, 0), (1, 1)}
    train_cells = {tuple(row.astype(int)) for row in data.X_train[:, binary_indices]}
    eval_cells = {tuple(row.astype(int)) for row in data.X_eval[:, binary_indices]}
    assert train_cells == expected_cells
    assert eval_cells == expected_cells
    assert set(data.binary_cell_counts_train) == expected_cells
    assert set(data.binary_cell_counts_eval) == expected_cells

    assert data.row_noise_scale_train.max() / data.row_noise_scale_train.min() > 1.10
    assert data.row_noise_scale_eval.max() / data.row_noise_scale_eval.min() > 1.10
    assert data.realized_heteroscedasticity_ratio_train > 1.10
    assert data.realized_heteroscedasticity_ratio_eval > 1.10


def test_every_prespecified_regime_uses_the_same_full_binary_schema(driver, contract, design):
    ledger = driver.load_seed_ledger(contract)
    expected_cells = {(0, 0), (0, 1), (1, 0), (1, 1)}
    for scenario in contract.scenarios:
        data = driver.generate_bsm_dataset(
            contract,
            design,
            scenario,
            _entry_for(ledger, scenario.name),
        )
        assert data.X_train.shape[1] == 160
        assert set(data.binary_cell_counts_train) == expected_cells
        assert set(data.binary_cell_counts_eval) == expected_cells
        if scenario.correlated_inputs:
            assert data.correlation_record["train"]["mean_pairwise_rank_correlation"] > 0.50


def test_typed_truth_uses_one_surface_for_train_and_evaluation(driver, contract, design):
    ledger = driver.load_seed_ledger(contract)
    scenario = contract.scenario("binary_continuous_strong")
    data = driver.generate_bsm_dataset(
        contract,
        design,
        scenario,
        _entry_for(ledger, scenario.name),
    )

    np.testing.assert_allclose(
        data.noiseless_train,
        data.truth.evaluate(design, data.X_train),
        atol=1e-12,
    )
    np.testing.assert_allclose(
        data.noiseless_eval,
        data.truth.evaluate(design, data.X_eval),
        atol=1e-12,
    )
    assert not np.array_equal(data.Y_train[: data.Y_eval.shape[0]], data.Y_eval)
    assert data.truth.surface_sha256 == data.surface_sha256
    assert any(
        term.term_id.kind == "binary_continuous_interaction"
        for term in data.truth.terms
    )


def test_scenario_grid_has_required_binary_and_misspecified_truth(driver, contract, design):
    scenario_names = {scenario.name for scenario in contract.scenarios}
    assert {
        "global_null",
        "interaction_null",
        "correlated_interaction_null",
        "heteroscedastic_interaction_null",
        "binary_main_interaction_null",
        "sparse_strong_hierarchical",
        "binary_continuous_strong",
        "binary_binary_strong",
        "weak_signal",
        "correlated_redundant",
        "pure_interaction",
        "nonlinear_misspecified",
    }.issubset(scenario_names)

    ledger = driver.load_seed_ledger(contract)
    misspecified = contract.scenario("nonlinear_misspecified")
    data = driver.generate_bsm_dataset(
        contract,
        design,
        misspecified,
        _entry_for(ledger, misspecified.name),
    )
    sine_terms = [term for term in data.truth.terms if term.term_id.transform == "sine"]
    assert len(sine_terms) == 1
    assert sine_terms[0].in_library is False


def test_seed_ledger_is_scenario_keyed_and_order_independent(driver, contract):
    ledger = driver.load_seed_ledger(contract)

    assert ledger.contract_sha256 == contract.contract_sha256
    assert len(ledger.entries) == len(set(entry.key for entry in ledger.entries))
    assert all(entry.phase == "development" for entry in ledger.entries)
    for entry in ledger.entries:
        assert entry.seed == driver.derive_replicate_seed(
            contract.contract_sha256,
            entry.phase,
            entry.scenario,
            entry.replicate_index,
        )
        assert entry.stage_seeds == {
            stage: driver.derive_stage_seed(
                contract.contract_sha256,
                entry.phase,
                entry.scenario,
                entry.replicate_index,
                stage,
            )
            for stage in driver.STAGE_NAMES
        }

    reversed_entries = tuple(reversed(ledger.entries))
    assert {
        entry.key: entry.stage_seeds for entry in reversed_entries
    } == {entry.key: entry.stage_seeds for entry in ledger.entries}


def test_seed_ledger_hash_mismatch_fails_before_dgp_generation(driver, contract):
    with pytest.raises(driver.ContractError, match="checksum"):
        driver.load_seed_ledger(replace(contract, seed_ledger_sha256="0" * 64))


def test_empty_and_one_pair_records_are_counted_without_silent_failure(driver, contract):
    ledger = driver.load_seed_ledger(contract)
    entries = [
        _entry_for(ledger, "interaction_null", 0),
        _entry_for(ledger, "interaction_null", 1),
    ]
    records = [
        _terminal_record(
            driver,
            contract,
            entries[0],
            outcome="NO_INTERACTION_CANDIDATES",
            pair_family_count=0,
            false_pair_count=0,
        ),
        _terminal_record(
            driver,
            contract,
            entries[1],
            outcome="COMPLETED",
            pair_family_count=1,
            false_pair_count=0,
        ),
    ]

    summary = driver.aggregate_null_terminal_records(contract, records)
    assert summary["denominator"] == 2
    assert summary["n_empty_family"] == 1
    assert summary["n_one_pair_family"] == 1
    assert summary["n_false_pair_replicates"] == 0
    assert summary["fwer_proportion"] == pytest.approx(0.0)
    assert summary["nondegenerate_rate"] == pytest.approx(0.0)

    assert driver.one_sided_wilson_upper(0, 1000, 0.95) == pytest.approx(
        0.002697, abs=0.00001
    )
    assert driver.largest_passing_event_count(contract.calibration, 1000) == 75


def test_canonical_pair_family_is_ordered_and_one_pair_is_valid(driver):
    assert driver.canonical_pair_family(("b", "a", "c")) == (
        "a:b",
        "a:c",
        "b:c",
    )
    assert driver.canonical_pair_family(("only_a", "only_b")) == ("only_a:only_b",)
    assert driver.canonical_pair_family(("only",)) == ()
    with pytest.raises(driver.ContractError, match="duplicate"):
        driver.canonical_pair_family(("a", "a"))


def test_terminal_ledger_fails_closed_on_failed_duplicate_or_missing_records(
    driver, contract
):
    ledger = driver.load_seed_ledger(contract)
    entries = [
        _entry_for(ledger, "global_null", 0),
        _entry_for(ledger, "global_null", 1),
    ]
    complete = _terminal_record(
        driver,
        contract,
        entries[0],
        outcome="NO_INTERACTION_CANDIDATES",
        pair_family_count=0,
        false_pair_count=0,
    )
    failed = driver.TerminalRecord(
        **{
            **complete.to_dict(),
            "status": "FAILED",
            "terminal_outcome": "FAILED",
            "exception": "fixture failure",
        }
    )

    with pytest.raises(driver.TerminalLedgerError, match="missing"):
        driver.validate_terminal_ledger(contract, ledger, [complete])
    with pytest.raises(driver.TerminalLedgerError, match="duplicate"):
        driver.validate_terminal_ledger(contract, ledger, [complete, complete])
    with pytest.raises(driver.TerminalLedgerError, match="failed"):
        driver.validate_terminal_ledger(contract, ledger, [complete, failed])


def test_null_aggregation_rejects_duplicate_records(driver, contract):
    ledger = driver.load_seed_ledger(contract)
    record = _terminal_record(
        driver,
        contract,
        _entry_for(ledger, "global_null", 0),
        outcome="NO_INTERACTION_CANDIDATES",
        pair_family_count=0,
        false_pair_count=0,
    )
    with pytest.raises(driver.TerminalLedgerError, match="duplicate"):
        driver.aggregate_null_terminal_records(contract, [record, record])


def test_manifest_is_truthful_preexecution_control_not_result_claim(driver, contract, design):
    ledger = driver.load_seed_ledger(contract)
    manifest = driver.build_preexecution_manifest(contract, design, ledger)

    assert manifest["execution_status"] == "NOT_EXECUTED"
    assert manifest["phase"] == "development"
    assert manifest["input_schema"]["n_inputs"] == 160
    assert manifest["candidate_schema"]["binary_inputs_included"] is True
    assert manifest["calibration_status"] == "NOT_RUN"
    assert manifest["terminal_records_status"] == "NOT_GENERATED"
    assert "fwer_proportion" not in manifest
    assert "representative" not in str(manifest).lower()


def test_open_controls_block_scientific_execution(driver):
    with pytest.raises(driver.PreexecutionBlockedError, match="not authorized"):
        driver.main(["--execute-development"])


def test_future_production_adapter_is_explicit_and_has_no_local_fallback(driver):
    source = inspect.getsource(driver.run_pipeline)
    assert "run_production_recovery_pipeline" in source
    assert "execution_controls" in source
    assert "except" not in source


def test_runtime_surfaces_have_no_legacy_158_exact_or_free_text_gate_claims(driver):
    runtime_paths = [
        _ROOT / "scripts" / "run_bsm_recovery_study.py",
        _ROOT / "configs" / "method_contract.yaml",
        _ROOT / "configs" / "manuscript_case_study.yml",
    ]
    forbidden = (
        "_".join(("fwer", "max", "stat", "exact")),
        "_".join(("min", "exact", "permutation", "draws")),
        "158" + "-continuous",
        "--" + "gate-summary",
        "--" + "log-only",
        "representative" + " replicate",
    )
    runtime_text = "\n".join(path.read_text(encoding="utf-8") for path in runtime_paths).lower()
    for phrase in forbidden:
        assert phrase.lower() not in runtime_text

    recovery_dir = _ROOT / "artifacts" / "recovery_study"
    stale_outputs = [
        path.name
        for path in recovery_dir.iterdir()
        if path.name != "README.md" and not path.name.startswith(".")
    ]
    assert stale_outputs == []
    assert "representative" not in inspect.getsource(driver).lower()
