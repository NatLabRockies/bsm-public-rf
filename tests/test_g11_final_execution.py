"""End-to-end control contracts for the one-shot final G11 campaign."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.g11_final_execution import (
    _prepare_artifact_job,
    _submit_artifact_job,
    _validate_rfm_runtime_binding,
    advance_campaign,
    inspect_submitted_phase,
    render_final_campaign_config,
)


def test_final_controller_direct_cli_entry_point_loads() -> None:
    repo = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "g11_final_execution.py"), "--help"],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "{initialize,advance,watch}" in completed.stdout

    advance_help = subprocess.run(
        [
            sys.executable,
            str(repo / "scripts" / "g11_final_execution.py"),
            "advance",
            "--help",
        ],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    assert advance_help.returncode == 0, advance_help.stderr
    assert "--remaining-au" in advance_help.stdout


def test_final_controller_requires_the_frozen_rfm_runtime(tmp_path: Path) -> None:
    rfm_root = tmp_path / "rfm"
    expected = rfm_root / "src" / "rfm_pipeline" / "hpc_campaign_package.py"
    expected.parent.mkdir(parents=True)
    expected.write_text("# frozen runtime marker\n", encoding="utf-8")
    required = {
        "collect_pilot_accounting",
        "generate_campaign_package",
        "select_pilot_resources",
    }

    assert (
        _validate_rfm_runtime_binding(
            rfm_root,
            module_path=expected,
            available_names=required,
        )
        == expected.resolve()
    )
    with pytest.raises(RuntimeError, match="frozen RFM runtime"):
        _validate_rfm_runtime_binding(
            rfm_root,
            module_path=tmp_path / "site-packages" / "hpc_campaign_package.py",
            available_names=required,
        )
    with pytest.raises(RuntimeError, match="collect_pilot_accounting"):
        _validate_rfm_runtime_binding(
            rfm_root,
            module_path=expected,
            available_names=required - {"collect_pilot_accounting"},
        )


def _completed(stdout: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], 0, stdout=stdout, stderr="")


def _submission(path: Path) -> None:
    from scripts.g11_campaign_workflow import _stable_hash

    identity = {
        "schema_version": 1,
        "status": "SUBMITTED",
        "phase": "gate_b",
        "run_id": "g11-final-20260815a",
        "source_hash": "a" * 64,
        "config_hash": "b" * 64,
        "lock_hash": "c" * 64,
        "campaign_inventory_hash": "d" * 64,
        "preflight_sha256": "e" * 64,
        "authorization_sha256": "f" * 64,
        "submission_plan_sha256": "1" * 64,
        "submission_job_ids": {"gate_b-worker": "101", "gate_b-reducer": "102"},
    }
    path.write_text(
        json.dumps({**identity, "submission_record_sha256": _stable_hash(identity)}),
        encoding="utf-8",
    )


def test_final_config_gets_unique_collision_safe_run_identity(tmp_path: Path) -> None:
    base = tmp_path / "base.yml"
    base.write_text(
        """hpc_campaign:
  run_id: g11-kestrel-nosubmit
  scheduler_submission_permitted: false
  cluster:
    account: nationalpfa
    scratch_template: /scratch/{user}/bsm_runs/{run_id}
""",
        encoding="utf-8",
    )
    destination = tmp_path / "campaign.yml"

    render_final_campaign_config(
        base_config_path=base,
        output_path=destination,
        run_id="g11-final-20260815a",
    )

    rendered = destination.read_text(encoding="utf-8")
    assert "run_id: g11-final-20260815a" in rendered
    assert "scheduler_submission_permitted: false" in rendered
    assert "scratch_template: /scratch/{user}/bsm_runs/{run_id}" in rendered

    with pytest.raises(ValueError, match="unique final campaign ID"):
        render_final_campaign_config(
            base_config_path=base,
            output_path=tmp_path / "bad.yml",
            run_id="g11-kestrel-nosubmit",
        )
    with pytest.raises(ValueError, match="refusing to overwrite"):
        render_final_campaign_config(
            base_config_path=base,
            output_path=destination,
            run_id="g11-final-20260815b",
        )


def test_phase_probe_waits_until_jobs_leave_queue_and_sacct_is_complete(
    tmp_path: Path,
) -> None:
    submission = tmp_path / "submission.json"
    _submission(submission)
    calls = iter(
        [
            _completed("101|RUNNING\n102|PENDING\n"),
            _completed(""),
            _completed("101|COMPLETED|0:0\n"),
        ]
    )

    waiting = inspect_submitted_phase(
        submission, run_command=lambda *_a, **_k: next(calls)
    )
    assert waiting["status"] == "WAITING_FOR_SCHEDULER"

    accounting_lag = inspect_submitted_phase(
        submission, run_command=lambda *_a, **_k: next(calls)
    )
    assert accounting_lag["status"] == "WAITING_FOR_SACCT"


def test_phase_probe_fails_closed_on_any_terminal_scheduler_failure(
    tmp_path: Path,
) -> None:
    submission = tmp_path / "submission.json"
    _submission(submission)
    calls = iter(
        [
            _completed(""),
            _completed("101|COMPLETED|0:0\n102|OUT_OF_MEMORY|0:125\n"),
        ]
    )

    with pytest.raises(RuntimeError, match="OUT_OF_MEMORY/0:125"):
        inspect_submitted_phase(submission, run_command=lambda *_a, **_k: next(calls))


def test_phase_probe_marks_only_exact_completion_ready_for_verification(
    tmp_path: Path,
) -> None:
    submission = tmp_path / "submission.json"
    _submission(submission)
    calls = iter(
        [
            _completed(""),
            _completed(
                "101|COMPLETED|0:0\n101.batch|COMPLETED|0:0\n102|COMPLETED|0:0\n"
            ),
        ]
    )

    observed = inspect_submitted_phase(
        submission, run_command=lambda *_a, **_k: next(calls)
    )
    assert observed["status"] == "READY_TO_VERIFY"
    assert observed["job_count"] == 2


def test_advance_uses_fresh_per_invocation_remaining_au(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "control"
    (root / "development_package").mkdir(parents=True)
    (root / "development_package" / "package_summary.json").write_text(
        "{}", encoding="utf-8"
    )
    (root / "resource_freeze.json").write_text("{}", encoding="utf-8")
    config = root / "final_campaign.yml"
    config.write_text("config", encoding="utf-8")
    repo = tmp_path / "rfm"
    repo.mkdir()
    control = {
        "campaign_root": str(root),
        "final_config_path": str(config),
        "rfm_repo_root": str(repo),
        "remaining_au_for_live_preflight": 25_000,
    }
    development = SimpleNamespace(run_id="g11-final")
    observed: dict[str, object] = {}

    monkeypatch.setattr(
        "scripts.g11_final_execution._load_control", lambda _path: control
    )
    monkeypatch.setattr(
        "scripts.g11_final_execution.load_packaged_dag", lambda **_kwargs: development
    )

    def fake_advance_phase(**kwargs: object) -> dict[str, str]:
        observed.update(kwargs)
        return {"status": "EXECUTION_FLAG_REQUIRED", "phase": "development"}

    monkeypatch.setattr(
        "scripts.g11_final_execution._advance_phase", fake_advance_phase
    )

    result = advance_campaign(
        tmp_path / "control_manifest.json",
        execute=True,
        remaining_au=12_345,
    )

    assert result == {
        "status": "EXECUTION_FLAG_REQUIRED",
        "phase": "development",
    }
    assert observed["remaining_au"] == 12_345

    with pytest.raises(ValueError, match="live remaining AU must be positive"):
        advance_campaign(
            tmp_path / "control_manifest.json",
            execute=True,
            remaining_au=0,
        )


def test_controller_never_crosses_a_phase_or_publication_gate_out_of_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "control"
    root.mkdir()
    config = root / "final_campaign.yml"
    config.write_text("config", encoding="utf-8")
    rfm = tmp_path / "rfm"
    bsm = tmp_path / "bsm"
    pilot_package = tmp_path / "pilot-package"
    pilot_submission = tmp_path / "pilot-submission.json"
    for directory in (rfm, bsm, pilot_package):
        directory.mkdir()
    pilot_submission.write_text("{}", encoding="utf-8")
    control = {
        "campaign_root": str(root),
        "final_config_path": str(config),
        "rfm_repo_root": str(rfm),
        "bsm_runtime_root": str(bsm),
        "pilot_package_root": str(pilot_package),
        "pilot_submission_record": str(pilot_submission),
        "prior_sunk_au": 114.63055555555556,
        "remaining_au_for_live_preflight": 25_000,
        "allocation_quota_au": 25_000.0,
        "postprocessing_reserved_au": 5.0,
    }
    dags = {
        str(pilot_package): SimpleNamespace(name="pilot"),
        str(root / "development_package"): SimpleNamespace(name="development"),
        str(root / "final_confirmatory_package"): SimpleNamespace(name="final"),
    }
    phase_state = {
        "development": "PHASE_COMPLETE",
        "gate_b": "WAITING_FOR_SCHEDULER",
        "gate_p": "WAITING_FOR_SCHEDULER",
        "gate_c": "WAITING_FOR_SCHEDULER",
    }
    phase_calls: list[str] = []

    monkeypatch.setattr(
        "scripts.g11_final_execution._load_control", lambda _path: control
    )
    monkeypatch.setattr(
        "scripts.g11_final_execution.load_packaged_dag",
        lambda **kwargs: dags[str(kwargs["package_root"])],
    )

    def fake_close(**_kwargs: object) -> None:
        (root / "resource_freeze.json").write_text("{}", encoding="utf-8")

    def fake_prepare_development(**_kwargs: object) -> None:
        package = root / "development_package"
        package.mkdir()
        (package / "package_summary.json").write_text("{}", encoding="utf-8")

    def fake_prepare_final(**_kwargs: object) -> None:
        package = root / "final_confirmatory_package"
        package.mkdir()
        (package / "package_summary.json").write_text("{}", encoding="utf-8")
        (root / "budget_certificate.json").write_text("{}", encoding="utf-8")

    def fake_advance_phase(**kwargs: object) -> dict[str, str]:
        phase = str(kwargs["phase"])
        phase_calls.append(phase)
        return {"status": phase_state[phase], "phase": phase}

    def fake_prepare_artifact(**_kwargs: object) -> None:
        job = root / "publication_job"
        job.mkdir()
        (job / "artifact_job_inputs.json").write_text("{}", encoding="utf-8")

    def fake_submit(_root: Path) -> None:
        (root / "publication_job" / "submission.json").write_text(
            "{}", encoding="utf-8"
        )

    def fake_verify(_root: Path) -> dict[str, str]:
        (root / "publication_job" / "completion.json").write_text(
            "{}", encoding="utf-8"
        )
        return {"status": "HPC_AND_PUBLICATION_BUNDLE_COMPLETE"}

    monkeypatch.setattr("scripts.g11_final_execution.close_completed_pilot", fake_close)
    monkeypatch.setattr(
        "scripts.g11_final_execution.prepare_development_package",
        fake_prepare_development,
    )
    monkeypatch.setattr(
        "scripts.g11_final_execution.prepare_final_package", fake_prepare_final
    )
    monkeypatch.setattr(
        "scripts.g11_final_execution._advance_phase", fake_advance_phase
    )
    monkeypatch.setattr(
        "scripts.g11_final_execution._stage_artifact",
        lambda _dag, stage, filename: root / stage / filename,
    )
    monkeypatch.setattr(
        "scripts.g11_final_execution._validate_budget_certificate",
        lambda **_kwargs: {},
    )
    monkeypatch.setattr(
        "scripts.g11_final_execution._confirmatory_phase_budget_guard",
        lambda **_kwargs: {
            "status": "PHASE_WITHIN_ALLOCATION",
            "phase_budget_guard_sha256": "a" * 64,
        },
    )
    monkeypatch.setattr(
        "scripts.g11_final_execution._prepare_artifact_job", fake_prepare_artifact
    )
    monkeypatch.setattr("scripts.g11_final_execution._submit_artifact_job", fake_submit)
    monkeypatch.setattr(
        "scripts.g11_final_execution.inspect_submitted_phase",
        lambda _path: {"status": "READY_TO_VERIFY"},
    )
    monkeypatch.setattr(
        "scripts.g11_final_execution._verify_publication_job", fake_verify
    )
    monkeypatch.setattr(
        "scripts.g11_final_execution._validate_publication_completion",
        lambda _root: {"status": "HPC_AND_PUBLICATION_BUNDLE_COMPLETE"},
    )

    manifest = tmp_path / "control_manifest.json"
    assert advance_campaign(manifest, execute=False)["status"] == (
        "PILOT_CLOSED_AND_RESOURCES_FROZEN"
    )
    assert advance_campaign(manifest, execute=False)["status"] == (
        "DEVELOPMENT_PACKAGE_READY"
    )
    assert advance_campaign(manifest, execute=False)["status"] == (
        "FINAL_CONFIRMATORY_PACKAGE_BUDGET_CERTIFIED"
    )
    assert phase_calls == ["development"]

    assert advance_campaign(manifest, execute=True)["phase"] == "gate_b"
    assert phase_calls[-1:] == ["gate_b"]
    phase_state["gate_b"] = "PHASE_COMPLETE"
    assert advance_campaign(manifest, execute=True)["phase"] == "gate_p"
    assert phase_calls[-2:] == ["gate_b", "gate_p"]
    phase_state["gate_p"] = "PHASE_COMPLETE"
    assert advance_campaign(manifest, execute=True)["phase"] == "gate_c"
    assert phase_calls[-3:] == ["gate_b", "gate_p", "gate_c"]
    phase_state["gate_c"] = "PHASE_COMPLETE"

    assert advance_campaign(manifest, execute=True)["status"] == (
        "PUBLICATION_JOB_PREPARED_NO_SUBMIT"
    )
    assert advance_campaign(manifest, execute=False)["status"] == (
        "EXECUTION_FLAG_REQUIRED"
    )
    assert advance_campaign(manifest, execute=True)["status"] == (
        "PUBLICATION_JOB_SUBMITTED"
    )
    assert advance_campaign(manifest, execute=True)["status"] == (
        "HPC_AND_PUBLICATION_BUNDLE_COMPLETE"
    )
    assert advance_campaign(manifest, execute=True)["status"] == (
        "HPC_AND_PUBLICATION_BUNDLE_COMPLETE"
    )


def _artifact_job_fixture(tmp_path: Path) -> tuple[Path, SimpleNamespace, Path]:
    campaign_root = tmp_path / "campaign"
    package_root = tmp_path / "package"
    results_root = tmp_path / "results"
    reducer = results_root / "stages" / "gate_b" / "reducer"
    reducer.mkdir(parents=True)
    package_root.mkdir()
    bsm_runtime = tmp_path / "bsm-runtime"
    python = bsm_runtime / ".pixi" / "envs" / "default" / "bin" / "python"
    builder = bsm_runtime / "scripts" / "build_g11_publication_artifacts.py"
    python.parent.mkdir(parents=True)
    builder.parent.mkdir(parents=True)
    python.write_text("#!/bin/sh\n", encoding="utf-8")
    builder.write_text("print('builder')\n", encoding="utf-8")
    dag = SimpleNamespace(
        run_id="g11-final-20260815a",
        output_dir=package_root,
        campaign_inventory_hash="a" * 64,
        stages=(SimpleNamespace(reducer_output_dir=reducer),),
    )
    return campaign_root, dag, bsm_runtime


def test_publication_job_script_has_exactly_one_value_for_each_cli_option(
    tmp_path: Path,
) -> None:
    root, dag, bsm_runtime = _artifact_job_fixture(tmp_path)

    inputs = _prepare_artifact_job(
        root=root,
        dag=dag,
        bsm_runtime_root=bsm_runtime,
    )

    script = Path(inputs["script_path"]).read_text(encoding="utf-8")
    command = shlex.split(script.splitlines()[-1])
    assert command.count("--package-root") == 1
    assert command.count("--results-root") == 1
    assert command.count("--output-root") == 1
    assert command[command.index("--results-root") + 1] == str(tmp_path / "results")


def test_publication_submission_journals_returned_job_id_before_final_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.g11_campaign_workflow import _sha256_path

    root, dag, bsm_runtime = _artifact_job_fixture(tmp_path)
    _prepare_artifact_job(root=root, dag=dag, bsm_runtime_root=bsm_runtime)
    monkeypatch.setattr(
        "scripts.g11_final_execution.subprocess.run",
        lambda *_a, **_k: subprocess.CompletedProcess(
            [], 0, stdout="12345;cluster\n", stderr=""
        ),
    )

    submission = _submit_artifact_job(root)

    journal = root / "publication_job" / "submission_journal.jsonl"
    assert journal.is_file()
    with journal.open(encoding="utf-8") as handle:
        os.fsync(handle.fileno())
        entry = json.loads(handle.read())
    assert entry["job_id"] == "12345"
    assert entry["returncode"] == 0
    assert submission["submission_journal_sha256"] == _sha256_path(journal)
