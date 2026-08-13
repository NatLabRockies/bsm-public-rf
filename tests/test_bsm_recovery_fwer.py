"""Pre-execution G0/B controls for the BSM recovery-study driver.

These tests intentionally exercise only deterministic contract, DGP, ledger,
and manifest behavior.  They do not start calibration, HPC, or production work.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

_ROOT = Path(__file__).resolve().parents[1]
_DRIVER = _ROOT / "scripts" / "run_bsm_recovery_study.py"
_ADAPTER = _ROOT / "scripts" / "g11_campaign_adapter.py"
_APPLIED_PREPARER = _ROOT / "scripts" / "prepare_g11_applied_data.py"


def _load_driver():
    spec = importlib.util.spec_from_file_location("_bsm_g0b_driver", _DRIVER)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_bsm_g0b_driver"] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _load_adapter():
    spec = importlib.util.spec_from_file_location("_bsm_g11_campaign_adapter", _ADAPTER)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_bsm_g11_campaign_adapter"] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _load_applied_preparer():
    spec = importlib.util.spec_from_file_location(
        "_bsm_g11_applied_preparer", _APPLIED_PREPARER
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_bsm_g11_applied_preparer"] = mod
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


@pytest.fixture(scope="module")
def dgp_contract(driver):
    return driver.load_bsm_dgp_contract()


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


def test_contract_is_typed_open_and_has_no_duplicate_scientific_defaults(
    driver, contract
):
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


def test_production_dgp_contract_contains_no_method_scale_seed_or_scheduler_controls(
    driver, dgp_contract
):
    text = dgp_contract.path.read_text(encoding="utf-8")
    serialized_payload = repr(driver._load_yaml_text(text))
    assert dgp_contract.input_schema.n_inputs == 160
    for forbidden in (
        "permutation_count_B",
        "B_screen",
        "B_interaction",
        "n_train",
        "n_eval",
        "n_outputs",
        "replicates",
        "seed_ledger",
        "scheduler",
    ):
        assert forbidden not in serialized_payload


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
    binary_indices = [
        data.feature_names.index(name) for name in design.binary_input_names
    ]
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


def test_every_prespecified_regime_uses_the_same_full_binary_schema(
    driver, contract, design
):
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
            assert (
                data.correlation_record["train"]["mean_pairwise_rank_correlation"]
                > 0.50
            )


def test_typed_truth_uses_one_surface_for_train_and_evaluation(
    driver, contract, design
):
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
    np.testing.assert_allclose(
        data.noise_standard_deviation_train,
        data.noise_standard_deviation_eval,
        atol=0.0,
        rtol=0.0,
    )


def test_confirmatory_scale_is_explicit_and_not_taken_from_development_defaults(
    driver, contract, design
):
    ledger = driver.load_seed_ledger(contract)
    scenario = contract.scenario("binary_continuous_strong")
    scale = driver.DatasetScale(n_train=2000, n_eval=500, n_outputs=40)

    data = driver.generate_bsm_dataset(
        contract,
        design,
        scenario,
        _entry_for(ledger, scenario.name),
        scale=scale,
    )

    assert data.X_train.shape == (2000, 160)
    assert data.X_eval.shape == (500, 160)
    assert data.Y_train.shape == (2000, 40)
    assert data.Y_eval.shape == (500, 40)
    assert len(data.truth.intercept) == 40


@pytest.mark.parametrize(
    ("scenario_id", "expected_shape"),
    [
        ("global_null", (160, 80, 4)),
        ("strong_bc", (2000, 500, 40)),
    ],
)
def test_campaign_adapter_maps_exact_rfm_scenario_scale_and_seed(
    driver, dgp_contract, scenario_id: str, expected_shape: tuple[int, int, int]
):
    from rfm_pipeline.campaign_contract import (
        G11_CONTRACT,
        compute_contract_hash,
        derive_seed,
    )

    design = driver.load_bsm_input_design(contract=dgp_contract)

    data = driver.generate_campaign_dataset(
        campaign_contract=G11_CONTRACT,
        bsm_contract=dgp_contract,
        design=design,
        scenario_id=scenario_id,
        replicate_index=7,
    )
    entry = driver.campaign_seed_entry(
        campaign_contract=G11_CONTRACT,
        scenario_id=scenario_id,
        replicate_index=7,
        bsm_scenario_name=driver._CAMPAIGN_TO_BSM_SCENARIO[scenario_id],
    )

    n_train, n_eval, n_outputs = expected_shape
    assert data.X_train.shape == (n_train, 160)
    assert data.X_eval.shape == (n_eval, 160)
    assert data.Y_train.shape == (n_train, n_outputs)
    assert data.Y_eval.shape == (n_eval, n_outputs)
    assert entry.seed == derive_seed(
        compute_contract_hash(G11_CONTRACT), scenario_id, 7
    )


def test_scenario_grid_has_required_binary_and_misspecified_truth(
    driver, contract, design
):
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
    assert {entry.key: entry.stage_seeds for entry in reversed_entries} == {
        entry.key: entry.stage_seeds for entry in ledger.entries
    }


def test_seed_ledger_hash_mismatch_fails_before_dgp_generation(driver, contract):
    with pytest.raises(driver.ContractError, match="checksum"):
        driver.load_seed_ledger(replace(contract, seed_ledger_sha256="0" * 64))


def test_empty_and_one_pair_records_are_counted_without_silent_failure(
    driver, contract
):
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


def test_manifest_is_truthful_preexecution_control_not_result_claim(
    driver, contract, design
):
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
    assert "execution_contract" in source
    assert "execution_controls" not in source
    assert "except" not in source


def test_null_calibration_can_skip_recovery_comparators(
    driver, dgp_contract, design, monkeypatch, tmp_path: Path
):
    import rfm_pipeline
    from rfm_pipeline import recovery_study

    expected = SimpleNamespace(comparator_predictions=None)
    monkeypatch.setattr(
        driver,
        "_verify_execution_authorization",
        lambda *args, **kwargs: {},
    )
    monkeypatch.setattr(
        rfm_pipeline,
        "run_production_recovery_pipeline",
        lambda *args, **kwargs: expected,
    )
    monkeypatch.setattr(
        recovery_study,
        "run_recovery_comparators",
        lambda *args, **kwargs: pytest.fail(
            "null calibration must not execute recovery comparators"
        ),
    )
    data = SimpleNamespace(
        feature_names=design.input_names,
        X_train=np.zeros((4, 160), dtype=float),
        Y_train=np.zeros((4, 2), dtype=float),
        X_eval=np.zeros((2, 160), dtype=float),
        Y_eval=np.zeros((2, 2), dtype=float),
    )

    result = driver.run_pipeline(
        data,
        dgp_contract,
        artifact_dir=tmp_path / "pipeline",
        authorization_manifest=tmp_path / "authorization.json",
        phase="gate_b",
        include_recovery_comparators=False,
    )

    assert result is expected


@pytest.mark.parametrize(
    ("scenario_kind", "expected"),
    [("null", False), ("strong", True), ("stress", True)],
)
def test_campaign_adapter_scopes_comparators_to_recovery_population(
    scenario_kind: str, expected: bool
):
    adapter = _load_adapter()

    assert adapter._requires_recovery_comparators(scenario_kind) is expected


def test_runtime_surfaces_have_no_legacy_158_exact_or_free_text_gate_claims(driver):
    runtime_paths = [
        _ROOT / "scripts" / "run_bsm_recovery_study.py",
        _ROOT / "configs" / "bsm_dgp_contract.yaml",
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
    runtime_text = "\n".join(
        path.read_text(encoding="utf-8") for path in runtime_paths
    ).lower()
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


def test_campaign_adapter_requires_manifest_bound_contract_and_dgp_paths(
    monkeypatch, tmp_path: Path
):
    adapter = _load_adapter()
    monkeypatch.setattr(
        adapter,
        "_load_driver",
        lambda record: pytest.fail(
            "driver loaded before manifest-bound paths were validated"
        ),
    )
    record = {
        "operation": "gate_b",
        "config_hash": "0" * 64,
        "bsm_dgp_contract_path": str(tmp_path / "missing-dgp.yaml"),
        "bsm_dgp_contract_sha256": "0" * 64,
    }

    with pytest.raises(ValueError, match="contract_config_path"):
        adapter.execute_scientific_work_unit(record, tmp_path / "shard")


def _adapter_reduction_record(
    tmp_path: Path,
    *,
    index: int,
    operation: str,
    terminal: dict[str, object],
) -> dict[str, object]:
    from rfm_pipeline.campaign_contract import load_contract

    contract_path = _ROOT / "configs" / "g11_campaign_contract.toml"
    _, contract_hash = load_contract(contract_path)
    shard = tmp_path / f"task-{index:04d}"
    shard.mkdir(parents=True)
    terminal_path = shard / "terminal_record.json"
    terminal_path.write_text(json.dumps(terminal), encoding="utf-8")
    (shard / "result.json").write_text(
        json.dumps(
            {
                "operation": operation,
                "status": "completed",
                "terminal_record": str(terminal_path),
            }
        ),
        encoding="utf-8",
    )
    return {
        "operation": operation,
        "output_dir": str(shard),
        "shard_id": f"task-{index:04d}",
        "contract_config_path": str(contract_path),
        "config_hash": contract_hash,
    }


def test_campaign_adapter_reduces_resolution_with_exact_coverage(tmp_path: Path):
    adapter = _load_adapter()
    from rfm_pipeline.campaign_contract import G11_CONTRACT

    records = []
    base = G11_CONTRACT.resolution_base_draws
    for fixture in ("nondegenerate_null", "strong_planted"):
        for schedule_index in range(10):
            p_values = np.linspace(0.001, 0.999, 100).tolist()
            terminal = {
                "operation": "resolution",
                "fixture_kind": fixture,
                "schedule_index": schedule_index,
                "adjusted_p_values": {
                    str(base): p_values,
                    str(2 * base): p_values,
                    str(4 * base): p_values,
                },
                "status": "completed",
            }
            records.append(
                _adapter_reduction_record(
                    tmp_path,
                    index=len(records),
                    operation="resolution",
                    terminal=terminal,
                )
            )

    result = adapter.reduce_scientific_stage(records, tmp_path / "reduced")

    assert result["status"] == "completed"
    assert result["selected_B_interaction"] == base
    assert (tmp_path / "reduced" / "resolution_decision.json").is_file()


def test_campaign_adapter_reduction_rejects_missing_terminal_record(tmp_path: Path):
    adapter = _load_adapter()
    records = _adapter_reduction_record(
        tmp_path,
        index=0,
        operation="gate_b",
        terminal={"operation": "gate_b", "status": "completed"},
    )
    Path(records["output_dir"]).joinpath("terminal_record.json").unlink()

    with pytest.raises(ValueError, match="terminal"):
        adapter.reduce_scientific_stage([records], tmp_path / "reduced")


def test_applied_data_preparer_physically_separates_and_seals_holdout(tmp_path: Path):
    import pandas as pd

    preparer = _load_applied_preparer()
    source = tmp_path / "source"
    source.mkdir()
    cells = [(0, 0), (0, 1), (1, 0), (1, 1)] * 2
    ids = list(range(8))
    x = pd.DataFrame(
        {
            "sample_id": ids,
            "scenario": [f"scenario-{index % 4}" for index in ids],
            "run_id": ids,
            "x000": np.linspace(0.0, 1.0, 8),
            preparer.SOURCE_BINARY_INPUT_NAMES[0]: [cell[0] for cell in cells],
            preparer.SOURCE_BINARY_INPUT_NAMES[1]: [cell[1] for cell in cells],
        }
    )
    y = pd.DataFrame(
        {"sample_id": ids, "y0": np.arange(8.0), "y1": np.arange(8.0) + 1.0}
    )
    assignments = pd.DataFrame(
        {"sample_id": ids, "split": ["train"] * 4 + ["test"] * 4}
    )
    catalog = pd.DataFrame(
        {
            "feature_name": ["x000", *preparer.SOURCE_BINARY_INPUT_NAMES],
            "feature_type": "numeric",
        }
    )
    x.to_parquet(source / "X.parquet", index=False)
    y.to_parquet(source / "Y.parquet", index=False)
    assignments.to_parquet(source / "holdout_assignments.parquet", index=False)
    catalog.to_parquet(source / "actual_input_feature_catalog.parquet", index=False)

    target = tmp_path / "prepared"
    manifest = preparer.prepare_applied_data_layout(
        source,
        target,
        expected_rows=8,
        expected_inputs=3,
        expected_outputs=2,
        expected_train_rows=4,
        expected_holdout_rows=4,
    )

    assert manifest["status"] == "PREPARED_HOLDOUT_SEALED"
    assert manifest["source_split_labels"] == {"train": "train", "test": "holdout"}
    assert manifest["preparer_sha256"] == preparer._sha256(_APPLIED_PREPARER)
    assert (target / "adaptive_train" / "Y.parquet").is_file()
    assert (target / "sealed_holdout" / "Y.parquet").stat().st_mode & 0o777 == 0
    assert not (target / "adaptive_train" / "holdout_Y.parquet").exists()
    prepared_x = pd.read_parquet(target / "adaptive_train" / "X.parquet")
    assert prepared_x.columns.tolist() == [
        "sample_id",
        "x000",
        *preparer.BINARY_INPUT_NAMES,
    ]
    prepared_catalog = pd.read_parquet(
        target / "metadata" / "manuscript_feature_catalog.parquet"
    )
    assert prepared_catalog["feature_name"].tolist() == [
        "x000",
        *preparer.BINARY_INPUT_NAMES,
    ]
    assert set(prepared_catalog["feature_type"]) == {"first_order"}


def test_applied_data_preparer_rejects_nonbinary_scenario_values(tmp_path: Path):
    import pandas as pd

    preparer = _load_applied_preparer()
    source = tmp_path / "source"
    source.mkdir()
    ids = list(range(8))
    cells = [(0.5, 0), (0, 1), (1, 0), (1, 1)] * 2
    pd.DataFrame(
        {
            "sample_id": ids,
            "scenario": [f"scenario-{index % 4}" for index in ids],
            "run_id": ids,
            "x000": np.linspace(0.0, 1.0, 8),
            preparer.SOURCE_BINARY_INPUT_NAMES[0]: [cell[0] for cell in cells],
            preparer.SOURCE_BINARY_INPUT_NAMES[1]: [cell[1] for cell in cells],
        }
    ).to_parquet(source / "X.parquet", index=False)
    pd.DataFrame(
        {"sample_id": ids, "y0": np.arange(8.0), "y1": np.arange(8.0) + 1.0}
    ).to_parquet(source / "Y.parquet", index=False)
    pd.DataFrame({"sample_id": ids, "split": ["train"] * 4 + ["test"] * 4}).to_parquet(
        source / "holdout_assignments.parquet", index=False
    )
    pd.DataFrame(
        {
            "feature_name": ["x000", *preparer.SOURCE_BINARY_INPUT_NAMES],
            "feature_type": "numeric",
        }
    ).to_parquet(source / "actual_input_feature_catalog.parquet", index=False)

    with pytest.raises(ValueError, match="exactly binary"):
        preparer.prepare_applied_data_layout(
            source,
            tmp_path / "prepared",
            expected_rows=8,
            expected_inputs=3,
            expected_outputs=2,
            expected_train_rows=4,
            expected_holdout_rows=4,
        )


def test_applied_data_preparer_rejects_misaligned_x_y_row_order(tmp_path: Path):
    import pandas as pd

    preparer = _load_applied_preparer()
    source = tmp_path / "source"
    source.mkdir()
    ids = list(range(8))
    cells = [(0, 0), (0, 1), (1, 0), (1, 1)] * 2
    pd.DataFrame(
        {
            "sample_id": ids,
            "scenario": [f"scenario-{index % 4}" for index in ids],
            "run_id": ids,
            "x000": np.linspace(0.0, 1.0, 8),
            preparer.SOURCE_BINARY_INPUT_NAMES[0]: [cell[0] for cell in cells],
            preparer.SOURCE_BINARY_INPUT_NAMES[1]: [cell[1] for cell in cells],
        }
    ).to_parquet(source / "X.parquet", index=False)
    pd.DataFrame(
        {
            "sample_id": list(reversed(ids)),
            "y0": np.arange(8.0),
            "y1": np.arange(8.0) + 1.0,
        }
    ).to_parquet(source / "Y.parquet", index=False)
    pd.DataFrame({"sample_id": ids, "split": ["train"] * 4 + ["test"] * 4}).to_parquet(
        source / "holdout_assignments.parquet", index=False
    )
    pd.DataFrame(
        {
            "feature_name": ["x000", *preparer.SOURCE_BINARY_INPUT_NAMES],
            "feature_type": "numeric",
        }
    ).to_parquet(source / "actual_input_feature_catalog.parquet", index=False)

    with pytest.raises(ValueError, match="row order"):
        preparer.prepare_applied_data_layout(
            source,
            tmp_path / "prepared",
            expected_rows=8,
            expected_inputs=3,
            expected_outputs=2,
            expected_train_rows=4,
            expected_holdout_rows=4,
        )
