"""Fail-closed contracts for the final G11 campaign controller."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict
from types import SimpleNamespace
from pathlib import Path

import pytest

from scripts.g11_campaign_workflow import (
    _stable_hash,
    augment_resource_freeze_accounting,
    build_publication_contract_amendment,
    build_campaign_budget_certificate,
    main,
    prepare_final_package,
    submit_authorized_phase,
    validate_completed_submission_record,
    validate_phase_budget_guard,
    validate_scheduler_completion,
    validate_scheduler_completion_accounting,
)


def test_completed_submission_record_requires_exact_successful_step_coverage(
    tmp_path: Path,
) -> None:
    path = tmp_path / "submission_job_ids.json"
    path.write_text(
        json.dumps(
            {
                "status": "COMPLETE",
                "run_id": "g11-final",
                "source_hash": "a" * 64,
                "config_hash": "b" * 64,
                "lock_hash": "c" * 64,
                "submission_job_ids": {"one": "101", "two": "102"},
            }
        ),
        encoding="utf-8",
    )

    observed = validate_completed_submission_record(
        path,
        expected_step_ids={"one", "two"},
        expected_identity={
            "run_id": "g11-final",
            "source_hash": "a" * 64,
            "config_hash": "b" * 64,
            "lock_hash": "c" * 64,
        },
    )
    assert observed == {"one": "101", "two": "102"}

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["submission_job_ids"].pop("two")
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="exactly cover"):
        validate_completed_submission_record(
            path,
            expected_step_ids={"one", "two"},
            expected_identity={
                "run_id": "g11-final",
                "source_hash": "a" * 64,
                "config_hash": "b" * 64,
                "lock_hash": "c" * 64,
            },
        )


def test_resource_freeze_binds_accepted_and_rejected_allocation_evidence() -> None:
    freeze = {
        "schema_version": 1,
        "status": "ACCEPTED",
        "source_hash": "a" * 64,
        "config_hash": "b" * 64,
        "lock_hash": "c" * 64,
        "telemetry_sha256": "d" * 64,
        "selections": {},
        "resource_freeze_sha256": "placeholder",
    }
    accounting = {
        "status": "COMPLETE",
        "pilot_accounting_sha256": "e" * 64,
        "observed_total_au": 81.25,
    }

    augmented = augment_resource_freeze_accounting(
        freeze,
        pilot_accounting=accounting,
        prior_sunk_au=114.63055555555556,
    )

    allocation = augmented["allocation_accounting"]
    assert allocation["accepted_pilot_observed_au"] == pytest.approx(81.25)
    assert allocation["prior_rejected_attempt_au"] == pytest.approx(114.63055555555556)
    assert allocation["spent_through_pilot_au"] == pytest.approx(195.88055555555556)
    assert len(augmented["resource_freeze_sha256"]) == 64

    with pytest.raises(ValueError, match="nonnegative"):
        augment_resource_freeze_accounting(
            freeze,
            pilot_accounting=accounting,
            prior_sunk_au=-1,
        )


def test_budget_certificate_adds_rejected_attempts_to_full_campaign_envelope() -> None:
    certificate = build_campaign_budget_certificate(
        run_id="g11-final",
        campaign_requested_au=23_700,
        prior_rejected_attempt_au=114.63055555555556,
        postprocessing_reserved_au=5.0,
        allocation_quota_au=25_000,
        resource_freeze_sha256="f" * 64,
        campaign_inventory_hash="1" * 64,
        contract_amendment_sha256="2" * 64,
        accepted_pilot_observed_au=100.0,
        development_resolution_observed_au=200.0,
        remaining_confirmatory_estimated_au=19_500.0,
        remaining_confirmatory_requested_au_with_shared_reserve=23_400.0,
    )
    assert certificate["status"] == "WITHIN_ALLOCATION"
    assert certificate["whole_campaign_projected_au"] == pytest.approx(
        23_819.630555555557
    )
    assert certificate["postprocessing_reserved_au"] == 5.0
    assert certificate["contract_amendment_sha256"] == "2" * 64

    with pytest.raises(ValueError, match="25,000-AU ceiling"):
        build_campaign_budget_certificate(
            run_id="g11-final",
            campaign_requested_au=24_950,
            prior_rejected_attempt_au=114.63055555555556,
            postprocessing_reserved_au=5.0,
            allocation_quota_au=25_000,
            resource_freeze_sha256="f" * 64,
            campaign_inventory_hash="1" * 64,
            contract_amendment_sha256="2" * 64,
            accepted_pilot_observed_au=100.0,
            development_resolution_observed_au=200.0,
            remaining_confirmatory_estimated_au=20_541.0,
            remaining_confirmatory_requested_au_with_shared_reserve=24_650.0,
        )

    with pytest.raises(ValueError, match="requires exact completed-phase accounting"):
        build_campaign_budget_certificate(
            run_id="g11-final",
            campaign_requested_au=23_700,
            prior_rejected_attempt_au=114.63055555555556,
            postprocessing_reserved_au=5.0,
            allocation_quota_au=25_000,
            resource_freeze_sha256="f" * 64,
            campaign_inventory_hash="1" * 64,
            contract_amendment_sha256="2" * 64,
        )


def test_budget_certificate_exposes_and_enforces_resolution_au_ceiling() -> None:
    accepted_pilot_au = 90.36944444444445
    prior_rejected_au = 192.55
    remaining_requested_au = 24_301
    resolution_limit = (
        25_000 - accepted_pilot_au - prior_rejected_au - remaining_requested_au - 5.0
    )
    certificate = build_campaign_budget_certificate(
        run_id="g11-final",
        campaign_requested_au=(
            accepted_pilot_au + resolution_limit + remaining_requested_au
        ),
        prior_rejected_attempt_au=prior_rejected_au,
        postprocessing_reserved_au=5.0,
        allocation_quota_au=25_000,
        resource_freeze_sha256="f" * 64,
        campaign_inventory_hash="1" * 64,
        contract_amendment_sha256="2" * 64,
        accepted_pilot_observed_au=accepted_pilot_au,
        development_resolution_observed_au=resolution_limit,
        remaining_confirmatory_estimated_au=20_250.751923076525,
        remaining_confirmatory_requested_au_with_shared_reserve=(
            remaining_requested_au
        ),
    )

    assert certificate["development_resolution_au_ceiling_for_selected_design"] == (
        pytest.approx(411.0805555555562)
    )
    assert certificate["whole_campaign_projected_au"] == pytest.approx(25_000)

    with pytest.raises(ValueError, match="25,000-AU ceiling"):
        build_campaign_budget_certificate(
            run_id="g11-final",
            campaign_requested_au=(
                accepted_pilot_au + resolution_limit + 0.01 + remaining_requested_au
            ),
            prior_rejected_attempt_au=prior_rejected_au,
            postprocessing_reserved_au=5.0,
            allocation_quota_au=25_000,
            resource_freeze_sha256="f" * 64,
            campaign_inventory_hash="1" * 64,
            contract_amendment_sha256="2" * 64,
            accepted_pilot_observed_au=accepted_pilot_au,
            development_resolution_observed_au=resolution_limit + 0.01,
            remaining_confirmatory_estimated_au=20_250.751923076525,
            remaining_confirmatory_requested_au_with_shared_reserve=(
                remaining_requested_au
            ),
        )


def test_budget_cli_replaces_completed_stage_estimates_with_actual_au(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    (package / "contract").mkdir(parents=True)
    summary = {
        "run_id": "g11-final",
        "source_hash": "a" * 64,
        "config_hash": "9" * 64,
        "lock_hash": "b" * 64,
        "campaign_inventory_hash": "1" * 64,
        "campaign_envelope": {
            "requested_au": 25_215,
            "stage_allocations": [
                {"stage_name": "pilot_conditioning", "estimated_au": 100.0},
                {"stage_name": "resolution", "estimated_au": 300.0},
                {"stage_name": "gate_b", "estimated_au": 20_000.0},
            ],
        },
    }
    summary_path = package / "package_summary.json"
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    amendment = {
        "contract_amendment_sha256": "2" * 64,
    }
    (package / "contract" / "fixed_family_amendment.json").write_text(
        json.dumps(amendment), encoding="utf-8"
    )
    freeze = {
        "source_hash": "a" * 64,
        "config_hash": "c" * 64,
        "lock_hash": "b" * 64,
        "resource_freeze_sha256": "f" * 64,
        "allocation_accounting": {
            "prior_rejected_attempt_au": 192.55,
            "accepted_pilot_observed_au": 90.36944444444445,
        },
    }
    freeze_path = tmp_path / "freeze.json"
    freeze_path.write_text(json.dumps(freeze), encoding="utf-8")
    completion_identity = {
        "schema_version": 1,
        "status": "PHASE_COMPLETE",
        "phase": "development",
        "run_id": "g11-final",
        "source_hash": "a" * 64,
        "config_hash": "c" * 64,
        "lock_hash": "b" * 64,
        "observed_total_au": 250.0,
    }
    completion_path = tmp_path / "development.json"
    completion_path.write_text(
        json.dumps(
            {
                **completion_identity,
                "completion_sha256": _stable_hash(completion_identity),
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "budget.json"

    assert (
        main(
            [
                "certify-budget",
                "--package-summary",
                str(summary_path),
                "--resource-freeze",
                str(freeze_path),
                "--development-completion",
                str(completion_path),
                "--allocation-quota",
                "25000",
                "--output",
                str(output),
            ]
        )
        == 0
    )

    certificate = json.loads(output.read_text(encoding="utf-8"))
    assert certificate["accepted_pilot_observed_au"] == pytest.approx(90.36944444444445)
    assert certificate["development_resolution_observed_au"] == 250.0
    assert certificate["remaining_confirmatory_estimated_au"] == 20_000.0
    assert certificate["remaining_confirmatory_requested_au_with_shared_reserve"] == (
        24_000
    )


def test_phase_budget_guard_blocks_single_phase_from_crossing_cap() -> None:
    allocations = (
        SimpleNamespace(
            stage_name="gate_b", estimated_au=14_418.0, requested_au=18_031.0
        ),
        SimpleNamespace(
            stage_name="applied_bootstrap", estimated_au=522.0, requested_au=652.0
        ),
        SimpleNamespace(
            stage_name="recovery", estimated_au=4_000.0, requested_au=6_639.0
        ),
    )
    initial = validate_phase_budget_guard(
        stage_allocations=allocations,
        completed_stage_names=set(),
        current_stage_names={"gate_b"},
        prior_rejected_attempt_au=192.55,
        accepted_pilot_observed_au=90.36944444444445,
        development_resolution_observed_au=250.0,
        completed_confirmatory_observed_au=0.0,
        postprocessing_reserved_au=5.0,
        allocation_quota_au=25_000.0,
    )
    assert initial["status"] == "PHASE_WITHIN_ALLOCATION"
    assert initial["current_phase_requested_au"] == 18_031.0

    with pytest.raises(ValueError, match="current phase could cross"):
        validate_phase_budget_guard(
            stage_allocations=allocations,
            completed_stage_names={"gate_b", "applied_bootstrap"},
            current_stage_names={"recovery"},
            prior_rejected_attempt_au=192.55,
            accepted_pilot_observed_au=90.36944444444445,
            development_resolution_observed_au=250.0,
            completed_confirmatory_observed_au=18_031.0 + 652.0,
            postprocessing_reserved_au=5.0,
            allocation_quota_au=25_000.0,
        )


def test_publication_amendment_changes_only_fixed_family_replicates() -> None:
    from rfm_pipeline.campaign_contract import G11_CONTRACT

    publication, amendment = build_publication_contract_amendment(G11_CONTRACT)

    before = asdict(G11_CONTRACT)
    after = asdict(publication)
    changed = {key for key in before if before[key] != after[key]}
    assert changed == {"fixed_family_replicates"}
    assert before["fixed_family_replicates"] == 1000
    assert publication.fixed_family_replicates == 200
    assert (
        len([scenario for scenario in publication.scenarios if scenario.kind == "null"])
        == 5
    )
    assert {
        scenario.n_replicates
        for scenario in publication.scenarios
        if scenario.kind == "null"
    } == {1000}
    assert amendment["changed_fields"] == {
        "fixed_family_replicates": {"before": 1000, "after": 200}
    }
    assert amendment["fixed_family_gate"]["largest_passing_false_selection_count"] == 11
    assert amendment["execution_rule"] == (
        "exactly 200 precommitted replicates; no interim testing, optional stopping, "
        "or later incremental expansion"
    )
    assert len(amendment["contract_amendment_sha256"]) == 64


def test_final_package_uses_amended_contract_but_preserves_pilot_freeze_basis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import rfm_pipeline.hpc_campaign_package as hpc
    from rfm_pipeline.campaign_contract import G11_CONTRACT, compute_contract_hash

    repo = tmp_path / "rfm"
    (repo / "src" / "rfm_pipeline").mkdir(parents=True)
    (repo / "pixi.lock").write_text("lock", encoding="utf-8")
    config = tmp_path / "campaign.yml"
    config.write_text("config", encoding="utf-8")
    freeze_path = tmp_path / "resource_freeze.json"
    freeze = {
        "schema_version": 1,
        "status": "ACCEPTED",
        "source_hash": "a" * 64,
        "config_hash": compute_contract_hash(G11_CONTRACT),
        "lock_hash": "b" * 64,
        "telemetry_sha256": "c" * 64,
        "selections": {},
        "allocation_accounting": {
            "prior_rejected_attempt_au": 192.55,
            "accepted_pilot_observed_au": 90.36944444444445,
        },
        "resource_freeze_sha256": "d" * 64,
    }
    freeze_path.write_text(json.dumps(freeze), encoding="utf-8")
    decision_path = tmp_path / "resolution_decision.json"
    decision_path.write_text(
        json.dumps(
            {
                "operation": "resolution",
                "status": "completed",
                "decision": "ACCEPTED",
                "terminal_record_count": 20,
                "contract_hash": compute_contract_hash(G11_CONTRACT),
                "selected_B_interaction": 999,
            }
        ),
        encoding="utf-8",
    )
    completion_identity = {
        "schema_version": 1,
        "status": "PHASE_COMPLETE",
        "phase": "development",
        "run_id": "g11-final",
        "source_hash": "a" * 64,
        "config_hash": compute_contract_hash(G11_CONTRACT),
        "lock_hash": "b" * 64,
        "observed_total_au": 250.0,
    }
    completion_path = tmp_path / "development_completion.json"
    completion_path.write_text(
        json.dumps(
            {
                **completion_identity,
                "completion_sha256": _stable_hash(completion_identity),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(hpc, "_validate_resource_freeze", lambda _freeze: None)
    monkeypatch.setattr(hpc, "_hash_python_tree", lambda _path: "a" * 64)
    monkeypatch.setattr(
        hpc, "_load_campaign_config", lambda _path: {"run_id": "g11-final"}
    )

    def fake_hash(path: Path) -> str:
        return "b" * 64 if Path(path).name == "pixi.lock" else "e" * 64

    monkeypatch.setattr(hpc, "_hash_file", fake_hash)
    observed: dict[str, object] = {}

    def fake_generate(**kwargs: object) -> SimpleNamespace:
        observed.update(kwargs)
        output = Path(str(kwargs["output_dir"]))
        (output / "contract").mkdir(parents=True)
        contract = kwargs["contract"]
        return SimpleNamespace(
            run_id="g11-final",
            output_dir=output,
            config_hash=compute_contract_hash(contract),
            campaign_inventory_hash="1" * 64,
            campaign_envelope=SimpleNamespace(
                requested_au=23_700.0,
                stage_allocations=(
                    SimpleNamespace(
                        stage_name="pilot_conditioning", estimated_au=100.0
                    ),
                    SimpleNamespace(stage_name="resolution", estimated_au=300.0),
                    SimpleNamespace(stage_name="gate_b", estimated_au=20_000.0),
                ),
            ),
        )

    monkeypatch.setattr(hpc, "generate_campaign_package", fake_generate)
    output = tmp_path / "final-package"
    certificate_path = tmp_path / "budget.json"

    dag, certificate = prepare_final_package(
        output_dir=output,
        resource_freeze_path=freeze_path,
        resolution_decision_path=decision_path,
        development_completion_path=completion_path,
        repo_root=repo,
        config_path=config,
        allocation_quota_au=25_000,
        postprocessing_reserved_au=5.0,
        budget_certificate_path=certificate_path,
    )

    selected = observed["contract"]
    assert selected.fixed_family_replicates == 200
    assert selected.B_interaction == 999
    assert selected.resolution_decision_sha256 == "e" * 64
    assert observed["resource_freeze"] == freeze
    amendment_path = output / "contract" / "fixed_family_amendment.json"
    amendment = json.loads(amendment_path.read_text(encoding="utf-8"))
    assert amendment["selected_contract_hash"] == dag.config_hash
    assert (
        certificate["contract_amendment_sha256"]
        == amendment["contract_amendment_sha256"]
    )
    assert certificate["accepted_pilot_observed_au"] == pytest.approx(90.36944444444445)
    assert certificate["development_resolution_observed_au"] == 250.0
    assert certificate["remaining_confirmatory_estimated_au"] == 20_000.0
    assert (
        certificate["remaining_confirmatory_requested_au_with_shared_reserve"] == 24_000
    )


def test_scheduler_completion_requires_exact_completed_zero_exit_rows() -> None:
    observed = validate_scheduler_completion(
        {"step-a": "101", "step-b": "102"},
        "101|COMPLETED|0:0\n101.batch|COMPLETED|0:0\n102|COMPLETED|0:0\n",
    )
    assert observed == {
        "step-a": {"job_id": "101", "state": "COMPLETED", "exit_code": "0:0"},
        "step-b": {"job_id": "102", "state": "COMPLETED", "exit_code": "0:0"},
    }

    with pytest.raises(ValueError, match="not exactly COMPLETED/0:0"):
        validate_scheduler_completion(
            {"step-a": "101", "step-b": "102"},
            "101|COMPLETED|0:0\n102|FAILED|1:0\n",
        )

    with pytest.raises(ValueError, match="exact top-level"):
        validate_scheduler_completion(
            {"step-a": "101", "step-b": "102"},
            "101|COMPLETED|0:0\n",
        )


def test_scheduler_completion_accounting_uses_exact_top_level_elapsed_nodes() -> None:
    observed, total_au = validate_scheduler_completion_accounting(
        {"step-a": "101", "step-b": "102"},
        "101|COMPLETED|0:0|3600|1\n"
        "101.batch|COMPLETED|0:0|3600|1\n"
        "102|COMPLETED|0:0|1800|2\n",
        cpu_charge_factor=10.0,
        qos_factor=1.0,
    )

    assert observed["step-a"]["elapsed_seconds"] == 3600
    assert observed["step-b"]["allocated_nodes"] == 2
    assert total_au == pytest.approx(20.0)

    with pytest.raises(ValueError, match="accounting row"):
        validate_scheduler_completion_accounting(
            {"step-a": "101"},
            "101|COMPLETED|0:0|-1|1\n",
            cpu_charge_factor=10.0,
            qos_factor=1.0,
        )


def test_phase_submission_journals_each_job_id_before_later_sbatch_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import rfm_pipeline.hpc_campaign_package as hpc

    plan = {
        "submission_plan_sha256": "1" * 64,
        "steps": [{"step_id": "one"}, {"step_id": "two"}],
    }
    monkeypatch.setattr(hpc, "build_campaign_phase_plan", lambda *_a, **_k: plan)

    def fail_second(_plan: object, *, run_command: object, **_kwargs: object) -> object:
        first = run_command(["sbatch", "one.sbatch"])
        assert first.stdout == "101\n"
        run_command(["sbatch", "two.sbatch"])
        raise RuntimeError("second submission failed")

    monkeypatch.setattr(hpc, "execute_campaign_phase_plan", fail_second)
    calls = iter(
        [
            subprocess.CompletedProcess([], 0, stdout="101\n", stderr=""),
            subprocess.CompletedProcess([], 1, stdout="", stderr="denied"),
        ]
    )
    monkeypatch.setattr(subprocess, "run", lambda *_a, **_k: next(calls))
    preflight = tmp_path / "preflight.json"
    authorization = tmp_path / "authorization.json"
    preflight.write_text(json.dumps({"preflight_sha256": "2" * 64}), encoding="utf-8")
    authorization.write_text(
        json.dumps({"authorization_sha256": "3" * 64}), encoding="utf-8"
    )
    record = tmp_path / "submission.json"
    dag = SimpleNamespace(
        run_id="g11-final",
        source_hash="a" * 64,
        config_hash="b" * 64,
        lock_hash="c" * 64,
        campaign_inventory_hash="d" * 64,
    )

    with pytest.raises(RuntimeError, match="second submission failed"):
        submit_authorized_phase(
            dag=dag,
            phase="gate_b",
            preflight_path=preflight,
            authorization_path=authorization,
            submission_record_path=record,
        )

    journal = record.with_suffix(".submission_journal.jsonl")
    rows = [
        json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()
    ]
    assert rows[0]["step_id"] == "one"
    assert rows[0]["job_id"] == "101"
    assert rows[1]["step_id"] == "two"
    assert rows[1]["returncode"] == 1
    assert not record.exists()
