#!/usr/bin/env python
"""BSM semi-synthetic recovery study.

Prespecified ground-truth (semi-synthetic) study that validates the submitted
interaction-discovery methodology on the **executed BSM input design**: the
158-continuous + 2-binary, 160-column interface, with per-input empirical ranges
taken from the published input metadata (Appendix A).  The estimands, empirical
interaction-FWER, and comparator accounting are computed with the generic,
case-study-agnostic ``rfm_pipeline.recovery_study`` API; only the input design,
planted-truth construction, and scenario grid are BSM-specific and live here.

The candidate-family logic (marginal BH screening -> hierarchical residualized
interaction scoring -> exact finite-permutation max-statistic FWER selection) is
identical to the generic study; the scale is deliberately reduced so the full
study runs locally in minutes.  The reduction is documented in the reproduction
log; the family logic is unchanged.

Design notes
------------
* Continuous inputs are resampled independently over their published
  ``[min_sample_value, max_sample_value]`` ranges, matching the executed BSM
  Monte-Carlo sensitivity design (independent factor sampling).  The two binary
  scenario switches are drawn Bernoulli(0.5).  This preserves the empirical
  ranges and the 158-continuous + 2-binary structure without redistributing the
  raw 30k-run design.
* Planted signals cover continuous inputs, both binary inputs, binary-continuous
  interactions, and the binary-binary interaction, per the method-evidence
  requirement.  The planted support and coefficient-generation procedure are
  fixed before recovery results are examined.
* Independent train/test responses are generated per replicate; all screening,
  PCA, scoring, and selection use train rows only.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.decomposition import PCA

from rfm_pipeline import (
    ElasticNetBaseline,
    GBTBaseline,
    OracleOLSBaseline,
    compare_baselines,
    empirical_interaction_fwer,
    multiplicity_controlled_interaction_selection,
    recovery_estimands,
)
from rfm_pipeline.synthetic_dgp import DGPTrueSupport

ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_METADATA = ROOT / "configs" / "manuscript_input_metadata.yml"


# ---------------------------------------------------------------------------
# BSM input design
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BSMInputDesign:
    """Parsed BSM 160-column input design (names, ranges, binary flags)."""

    input_names: list[str]
    continuous_input_names: list[str]
    binary_input_names: list[str]
    lower: dict[str, float]
    upper: dict[str, float]

    @property
    def n_inputs(self) -> int:
        return len(self.input_names)


def load_bsm_input_design(metadata_path: Path | str = _DEFAULT_METADATA) -> BSMInputDesign:
    """Parse the published input metadata into a :class:`BSMInputDesign`."""
    with open(metadata_path) as fh:
        meta = yaml.safe_load(fh)
    names: list[str] = []
    continuous: list[str] = []
    binary: list[str] = []
    lower: dict[str, float] = {}
    upper: dict[str, float] = {}
    for entry in meta["inputs"]:
        name = entry["name"]
        names.append(name)
        lo = float(entry.get("min_sample_value", 0.0))
        hi = float(entry.get("max_sample_value", 1.0))
        lower[name] = lo
        upper[name] = hi
        if entry.get("is_binary_scenario", False):
            binary.append(name)
        else:
            continuous.append(name)
    return BSMInputDesign(
        input_names=names,
        continuous_input_names=continuous,
        binary_input_names=binary,
        lower=lower,
        upper=upper,
    )


def _subset_design(design: BSMInputDesign, n_inputs: int) -> BSMInputDesign:
    """Subset to *n_inputs* columns, always retaining the 2 binary switches."""
    n_bin = len(design.binary_input_names)
    n_cont = max(0, n_inputs - n_bin)
    cont = design.continuous_input_names[:n_cont]
    binary = list(design.binary_input_names)
    names = cont + binary
    return BSMInputDesign(
        input_names=names,
        continuous_input_names=cont,
        binary_input_names=binary,
        lower={k: design.lower[k] for k in names},
        upper={k: design.upper[k] for k in names},
    )


def _sample_inputs(
    design: BSMInputDesign, n_runs: int, rng: np.random.Generator
) -> np.ndarray:
    """Resample the input design: continuous ~ U[min,max], binary ~ Bernoulli(0.5)."""
    cols = []
    binset = set(design.binary_input_names)
    for name in design.input_names:
        if name in binset:
            cols.append(rng.integers(0, 2, size=n_runs).astype(np.float64))
        else:
            cols.append(rng.uniform(design.lower[name], design.upper[name], size=n_runs))
    return np.column_stack(cols)


def _coded_features(design: BSMInputDesign, X: np.ndarray) -> np.ndarray:
    """Range-code inputs to a comparable scale for truth construction.

    Continuous inputs -> (x - midpoint) / half-range in ~[-1, 1]; binary -> {-1, +1}.
    Deterministic (range-based, not data-based) so the planted truth is identical
    for train and test rows.
    """
    binset = set(design.binary_input_names)
    out = np.empty_like(X)
    for j, name in enumerate(design.input_names):
        if name in binset:
            out[:, j] = 2.0 * X[:, j] - 1.0
        else:
            lo, hi = design.lower[name], design.upper[name]
            mid = 0.5 * (lo + hi)
            half = 0.5 * (hi - lo) if hi > lo else 1.0
            out[:, j] = (X[:, j] - mid) / half
    return out


# ---------------------------------------------------------------------------
# Scenario grid (prespecified)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BSMScenario:
    """One prespecified recovery scenario on the BSM design."""

    name: str
    description: str
    n_main: int
    interaction_kinds: tuple[str, ...]  # each of "cc" (cont-cont), "cb", "bb"
    n_nonlinear: int
    snr: float
    misspecified: bool = False
    marginal_main_scale: float = 1.0  # 0.0 => pure-interaction (negligible marginal)


def prespecified_bsm_scenarios() -> list[BSMScenario]:
    """Return the fixed BSM recovery-scenario grid (declared before results)."""
    return [
        BSMScenario(
            name="global_null",
            description="Complete global null: no main, interaction, or transform signal.",
            n_main=0,
            interaction_kinds=(),
            n_nonlinear=0,
            snr=10.0,
        ),
        BSMScenario(
            name="interaction_null",
            description=(
                "Main effects (including both binary switches) and a nonlinear "
                "main-effect transform, but no true interactions."
            ),
            n_main=4,
            interaction_kinds=(),
            n_nonlinear=1,
            snr=10.0,
        ),
        BSMScenario(
            name="sparse_strong_hierarchical",
            description=(
                "Sparse strong-signal hierarchical model: main + continuous-continuous "
                "and continuous-binary interactions + a transformation term."
            ),
            n_main=4,
            interaction_kinds=("cc", "cb"),
            n_nonlinear=1,
            snr=12.0,
        ),
        BSMScenario(
            name="weak_signal",
            description="Same hierarchical support as sparse_strong but low signal-to-noise.",
            n_main=4,
            interaction_kinds=("cc", "cb"),
            n_nonlinear=1,
            snr=3.0,
        ),
        BSMScenario(
            name="correlated_redundant",
            description=(
                "Dense active set with many candidate pairs (redundant active and "
                "inactive predictors) stressing selection precision."
            ),
            n_main=8,
            interaction_kinds=("cc", "cb"),
            n_nonlinear=0,
            snr=8.0,
        ),
        BSMScenario(
            name="pure_interaction",
            description=(
                "Pure-interaction signals (continuous-continuous and binary-binary) "
                "with negligible marginal main effects; a required screen stress test."
            ),
            n_main=0,
            interaction_kinds=("cc", "bb"),
            n_nonlinear=0,
            snr=10.0,
            marginal_main_scale=0.0,
        ),
        BSMScenario(
            name="nonlinear_misspecified",
            description=(
                "Nonlinear main-effect signal via the declared transform library plus "
                "one misspecified form outside the library; a required stress test."
            ),
            n_main=2,
            interaction_kinds=(),
            n_nonlinear=1,
            snr=10.0,
            misspecified=True,
        ),
    ]


def _planted_support(
    scenario: BSMScenario, design: BSMInputDesign
) -> tuple[DGPTrueSupport, dict]:
    """Build the fixed planted support (named) plus a truth spec for generation."""
    cont = design.continuous_input_names
    binr = design.binary_input_names

    main_names: list[str] = []
    if scenario.n_main > 0:
        # Prefer at least one binary switch among the mains when available.
        picks: list[str] = []
        if scenario.name == "interaction_null" and len(binr) >= 2:
            picks = [cont[0], cont[1], binr[0], binr[1]]
        else:
            n_cont_main = max(0, scenario.n_main - (1 if binr else 0))
            picks = list(cont[:n_cont_main])
            if binr:
                picks.append(binr[0])
        main_names = picks[: scenario.n_main]

    interactions: list[tuple[str, str]] = []
    for kind in scenario.interaction_kinds:
        if kind == "cc" and len(cont) >= 2:
            interactions.append((cont[0], cont[1]))
        elif kind == "cb" and cont and binr:
            interactions.append((cont[2 % len(cont)], binr[0]))
        elif kind == "bb" and len(binr) >= 2:
            interactions.append((binr[0], binr[1]))

    nonlinear_names: list[str] = []
    if scenario.n_nonlinear > 0 and cont:
        nonlinear_names = [cont[0]]

    support = DGPTrueSupport(
        true_active_inputs=frozenset(main_names),
        true_active_interactions=frozenset(tuple(sorted(p)) for p in interactions),
        true_active_nonlinear=frozenset(nonlinear_names),
    )
    spec = {
        "main_names": main_names,
        "interactions": interactions,
        "nonlinear_names": nonlinear_names,
    }
    return support, spec


# ---------------------------------------------------------------------------
# Response generation from planted truth
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StudyScale:
    """Scale parameters for one BSM recovery run."""

    n_inputs: int
    n_outputs: int
    n_runs: int
    B: int
    B_screen: int
    fwer_reps: int
    alt_reps: int
    alpha: float
    description: str


_QUICK_SCALE = StudyScale(
    n_inputs=12,
    n_outputs=6,
    n_runs=300,
    B=19,
    B_screen=19,
    fwer_reps=10,
    alt_reps=1,
    alpha=0.1,
    description="quick-smoke",
)

_FULL_SCALE = StudyScale(
    n_inputs=30,
    n_outputs=40,
    n_runs=2000,
    B=199,
    B_screen=199,
    fwer_reps=100,
    alt_reps=20,
    alpha=0.1,
    description=(
        "reduced-local BSM design: n_inputs=30 (158-continuous + 2-binary structure, "
        "subset to 28 continuous + 2 binary), n_outputs=40, n_runs=2000, B=199, "
        "B_screen=199, fwer_reps=100, alt_reps=20 — deliberate reduction from the "
        "executed ~30 000-run / 23 495-output HPC scale. Preserves empirical input "
        "ranges, the 158-continuous + 2-binary structure, multivariate low-rank "
        "responses (PCA path), hierarchical residualized interaction discovery, and "
        "train-only selection. Candidate-family logic (BH screening -> "
        "fwer_max_stat_exact selection) unchanged."
    ),
)


def _feature_column(name: str, coded: np.ndarray, names_index: dict[str, int]) -> np.ndarray:
    return coded[:, names_index[name]]


def _generate_responses(
    design: BSMInputDesign,
    scenario: BSMScenario,
    spec: dict,
    coded: np.ndarray,
    n_outputs: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate multivariate responses from the planted truth for one input sample."""
    n = coded.shape[0]
    names_index = {name: j for j, name in enumerate(design.input_names)}
    planted_cols: list[np.ndarray] = []

    for m in spec["main_names"]:
        planted_cols.append(scenario.marginal_main_scale * _feature_column(m, coded, names_index))
    for a, b in spec["interactions"]:
        planted_cols.append(
            _feature_column(a, coded, names_index) * _feature_column(b, coded, names_index)
        )
    for t in spec["nonlinear_names"]:
        v = _feature_column(t, coded, names_index)
        planted_cols.append(v**2 - v.mean())  # declared quadratic transform
    if scenario.misspecified and design.continuous_input_names:
        # Misspecified form outside the transform library (structured nuisance).
        v = _feature_column(design.continuous_input_names[1], coded, names_index)
        planted_cols.append(np.sin(3.0 * v))

    if not planted_cols:
        # Global null: pure noise with unit scale.
        return rng.standard_normal((n, n_outputs))

    planted = np.column_stack(planted_cols)  # (n, n_planted)
    n_latent = min(3, planted.shape[1] + 1)
    coeffs = rng.standard_normal((planted.shape[1], n_latent))
    latent = planted @ coeffs  # (n, n_latent)
    loadings = rng.standard_normal((n_latent, n_outputs))
    signal = latent @ loadings  # (n, n_outputs)

    Y = np.empty_like(signal)
    for j in range(n_outputs):
        s_std = signal[:, j].std(ddof=1)
        noise_std = (s_std / np.sqrt(scenario.snr)) if s_std > 1e-12 else 1.0
        Y[:, j] = signal[:, j] + rng.normal(0.0, noise_std, size=n)
    return Y


@dataclass(frozen=True)
class GeneratedData:
    X_train: np.ndarray
    Y_train: np.ndarray
    X_eval: np.ndarray
    Y_eval: np.ndarray
    feature_names: list[str]
    true_support: DGPTrueSupport


def generate_bsm_dataset(
    design: BSMInputDesign, scenario: BSMScenario, scale: StudyScale, seed: int
) -> GeneratedData:
    """Generate one semi-synthetic replicate (independent train/test)."""
    sub = _subset_design(design, scale.n_inputs)
    support, spec = _planted_support(scenario, sub)
    rng = np.random.default_rng(seed)

    n_train = scale.n_runs
    n_eval = max(64, scale.n_runs // 4)
    X_train = _sample_inputs(sub, n_train, rng)
    X_eval = _sample_inputs(sub, n_eval, rng)
    coded_train = _coded_features(sub, X_train)
    coded_eval = _coded_features(sub, X_eval)

    # Shared truth (coeffs/loadings) across train and eval via a dedicated rng.
    truth_rng = np.random.default_rng(seed + 987_654)
    Y_train = _generate_responses(sub, scenario, spec, coded_train, scale.n_outputs, truth_rng)
    truth_rng = np.random.default_rng(seed + 987_654)
    Y_eval = _generate_responses(sub, scenario, spec, coded_eval, scale.n_outputs, truth_rng)

    return GeneratedData(
        X_train=X_train,
        Y_train=Y_train,
        X_eval=X_eval,
        Y_eval=Y_eval,
        feature_names=list(sub.input_names),
        true_support=support,
    )


# ---------------------------------------------------------------------------
# Reduced workflow (identical candidate-family logic to the generic study)
# ---------------------------------------------------------------------------


def _pca_reduce(Y: np.ndarray, n_components: int) -> np.ndarray:
    n, p = Y.shape
    k = min(n_components, p, n - 1)
    if k <= 0:
        return Y
    return PCA(n_components=k, random_state=0).fit_transform(Y)


def _benjamini_hochberg(p_values: np.ndarray, q: float) -> np.ndarray:
    m = len(p_values)
    if m == 0:
        return np.zeros(0, dtype=bool)
    order = np.argsort(p_values)
    sorted_p = p_values[order]
    thresholds = (np.arange(1, m + 1) * q) / m
    passing = np.where(sorted_p <= thresholds)[0]
    retained_sorted = np.zeros(m, dtype=bool)
    if passing.size > 0:
        retained_sorted[: passing[-1] + 1] = True
    retained = np.empty(m, dtype=bool)
    retained[order] = retained_sorted
    return retained


def _screen_inputs(
    X_train: np.ndarray,
    Y_pca: np.ndarray,
    feature_names: list[str],
    B: int,
    rng: np.random.Generator,
    bh_q: float = 0.20,
) -> list[str]:
    n, p_in = X_train.shape
    X_std = (X_train - X_train.mean(0)) / np.where(
        X_train.std(0, ddof=1) > 1e-12, X_train.std(0, ddof=1), 1.0
    )
    Y_std = (Y_pca - Y_pca.mean(0)) / np.where(
        Y_pca.std(0, ddof=1) > 1e-12, Y_pca.std(0, ddof=1), 1.0
    )
    observed = np.linalg.norm(X_std.T @ Y_std / n, axis=1)
    null_stats = np.zeros((B, p_in), dtype=np.float64)
    for b in range(B):
        perm = rng.permutation(n)
        null_stats[b] = np.linalg.norm(X_std.T @ Y_std[perm] / n, axis=1)
    p_values = (1.0 + (null_stats >= observed[None, :]).sum(0)) / (B + 1.0)
    retained_mask = _benjamini_hochberg(p_values, bh_q)
    return [feature_names[i] for i in range(p_in) if retained_mask[i]]


def _residualize_on(design: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Residual of *target* after least-squares projection onto [1, design]."""
    n = target.shape[0]
    M = np.column_stack([np.ones(n), design]) if design.size else np.ones((n, 1))
    coef, *_ = np.linalg.lstsq(M, target, rcond=None)
    return target - M @ coef


def _score_interaction_pairs(
    X_main: np.ndarray,
    Y_pca: np.ndarray,
    inter_columns: list[np.ndarray],
    B: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Hierarchical residualized interaction scoring with shared-response null."""
    n_pairs = len(inter_columns)
    if n_pairs == 0:
        return np.zeros(0, dtype=np.float64), np.zeros((B, 0), dtype=np.float64)
    n = Y_pca.shape[0]
    X_inter = np.column_stack(inter_columns)
    X_inter_res = _residualize_on(X_main, X_inter)
    Y_res = _residualize_on(X_main, Y_pca)
    X_inter_std = (X_inter_res - X_inter_res.mean(0)) / np.where(
        X_inter_res.std(0, ddof=1) > 1e-12, X_inter_res.std(0, ddof=1), 1.0
    )
    Y_std = (Y_res - Y_res.mean(0)) / np.where(
        Y_res.std(0, ddof=1) > 1e-12, Y_res.std(0, ddof=1), 1.0
    )
    observed = np.abs(X_inter_std.T @ Y_std / n).max(axis=1)
    null_stats = np.zeros((B, n_pairs), dtype=np.float64)
    for b in range(B):
        perm = rng.permutation(n)
        null_stats[b] = np.abs(X_inter_std.T @ Y_std[perm] / n).max(axis=1)
    return observed, null_stats


def _score_transformations(
    X_main: np.ndarray,
    transform_columns: list[np.ndarray],
    Y_pca: np.ndarray,
    B: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Hierarchical residualized transformation scoring (declared quadratic library).

    Each candidate transform (x_i^2) is residualized on the linear main-effect
    design so the score reflects nonlinear value added over the linear mains,
    with a shared-response permutation null.  Same maxT exact-FWER rule as
    interaction discovery.
    """
    n_t = len(transform_columns)
    if n_t == 0:
        return np.zeros(0, dtype=np.float64), np.zeros((B, 0), dtype=np.float64)
    n = Y_pca.shape[0]
    T = np.column_stack(transform_columns)
    T_res = _residualize_on(X_main, T)
    Y_res = _residualize_on(X_main, Y_pca)
    T_std = (T_res - T_res.mean(0)) / np.where(
        T_res.std(0, ddof=1) > 1e-12, T_res.std(0, ddof=1), 1.0
    )
    Y_std = (Y_res - Y_res.mean(0)) / np.where(
        Y_res.std(0, ddof=1) > 1e-12, Y_res.std(0, ddof=1), 1.0
    )
    observed = np.abs(T_std.T @ Y_std / n).max(axis=1)
    null_stats = np.zeros((B, n_t), dtype=np.float64)
    for b in range(B):
        perm = rng.permutation(n)
        null_stats[b] = np.abs(T_std.T @ Y_std[perm] / n).max(axis=1)
    return observed, null_stats


def run_pipeline(
    data: GeneratedData,
    scale: StudyScale,
    rng: np.random.Generator,
    *,
    with_comparators: bool = True,
) -> dict:
    """Run screening -> PCA -> hierarchical interaction discovery -> exact FWER.

    ``with_comparators`` is disabled inside the FWER replication loop, where only
    the count of falsely selected interaction pairs is needed.
    """
    X_train, Y_train = data.X_train, data.Y_train
    feature_names = data.feature_names
    n_pca = min(8, Y_train.shape[1])
    Y_pca = _pca_reduce(Y_train, n_pca)

    retained_names = _screen_inputs(X_train, Y_pca, feature_names, scale.B_screen, rng)
    stage_retention = {
        "screening": {"n_candidates": len(feature_names), "n_retained": len(retained_names)}
    }

    retained_indices = [feature_names.index(n) for n in retained_names]
    pair_names_list: list[str] = []
    pair_indices_list: list[tuple[int, int]] = []
    for a, b in combinations(range(len(retained_indices)), 2):
        li, lj = retained_indices[a], retained_indices[b]
        pair_names_list.append(f"{feature_names[li]}:{feature_names[lj]}")
        pair_indices_list.append((li, lj))

    selected_interactions: frozenset[tuple[str, str]] = frozenset()
    observed_scores = np.zeros(0, dtype=np.float64)
    null_stats_arr = np.zeros((scale.B, 0), dtype=np.float64)

    if pair_names_list and scale.B >= 1:
        X_ret = X_train[:, retained_indices]
        X_main = np.column_stack([X_ret, X_ret**2]) if X_ret.size else X_ret
        inter_columns = [X_train[:, li] * X_train[:, lj] for li, lj in pair_indices_list]
        observed_scores, null_stats_arr = _score_interaction_pairs(
            X_main, Y_pca, inter_columns, scale.B, rng
        )
        selected_bool, _p_adj, _thr = multiplicity_controlled_interaction_selection(
            observed_scores, null_stats_arr, scale.alpha, method="fwer_max_stat_exact"
        )
        selected_interactions = frozenset(
            tuple(sorted(pair_names_list[k].split(":", 1)))
            for k in range(len(pair_names_list))
            if selected_bool[k]
        )

    stage_retention["interaction_selection"] = {
        "n_candidates": len(pair_names_list),
        "n_retained": len(selected_interactions),
    }

    # Stage 4: transformation discovery (declared quadratic library) on retained
    # continuous inputs, hierarchical over linear main effects, exact-FWER.
    binary_names = set(load_bsm_input_design().binary_input_names)
    retained_cont = [n for n in retained_names if n not in binary_names]
    selected_transforms: frozenset[str] = frozenset()
    if retained_cont and scale.B >= 1:
        cont_indices = [feature_names.index(n) for n in retained_cont]
        X_ret_lin = X_train[:, retained_indices]
        transform_cols = [
            (X_train[:, ci] - X_train[:, ci].mean()) ** 2 for ci in cont_indices
        ]
        t_obs, t_null = _score_transformations(
            X_ret_lin, transform_cols, Y_pca, scale.B, rng
        )
        t_selected, _tp, _tt = multiplicity_controlled_interaction_selection(
            t_obs, t_null, scale.alpha, method="fwer_max_stat_exact"
        )
        selected_transforms = frozenset(
            retained_cont[k] for k in range(len(retained_cont)) if t_selected[k]
        )
    stage_retention["transformation_selection"] = {
        "n_candidates": len(retained_cont),
        "n_retained": len(selected_transforms),
    }

    selected_support = DGPTrueSupport(
        true_active_inputs=frozenset(retained_names),
        true_active_interactions=selected_interactions,
        true_active_nonlinear=selected_transforms,
    )

    oracle = OracleOLSBaseline(
        true_active_inputs=data.true_support.true_active_inputs,
        feature_names=feature_names,
    )
    gbt = GBTBaseline(n_estimators=20, max_depth=2)
    en = ElasticNetBaseline(alpha=0.01)
    if with_comparators and data.X_eval.shape[0] >= 2:
        comparator_df = compare_baselines(
            [oracle, gbt, en], X_train, Y_train, data.X_eval, data.Y_eval
        )
    else:
        comparator_df = pd.DataFrame()

    return {
        "selected_support": selected_support,
        "stage_retention": stage_retention,
        "comparator_df": comparator_df,
    }


# ---------------------------------------------------------------------------
# FWER replication + study orchestration
# ---------------------------------------------------------------------------


def run_fwer_replicates(
    scenario: BSMScenario, scale: StudyScale, master_rng: np.random.Generator
) -> list[int]:
    """Run *scale.fwer_reps* replicates; return per-replicate false interaction counts."""
    design = load_bsm_input_design()
    flags: list[int] = []
    for _ in range(scale.fwer_reps):
        rep_seed = int(master_rng.integers(2**31))
        data = generate_bsm_dataset(design, scenario, scale, rep_seed)
        result = run_pipeline(
            data, scale, np.random.default_rng(rep_seed), with_comparators=False
        )
        flags.append(len(result["selected_support"].true_active_interactions))
    return flags


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def _estimand_rows(scenario_name: str, true_support: DGPTrueSupport, result: dict) -> list[dict]:
    est = recovery_estimands(true_support, result["selected_support"])
    rows = []
    for family, m in est.items():
        rows.append(
            {
                "scenario": scenario_name,
                "family": family,
                "precision": m["precision"],
                "recall": m["recall"],
                "fdp": m["fdp"],
                "exact_support_recovery": m["exact_support_recovery"],
                "selected_size": m["selected_size"],
            }
        )
    return rows


_NULL_INTERACTION_SCENARIOS = {"global_null", "interaction_null"}


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="BSM semi-synthetic recovery study.")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--quick", action="store_true", help="fast smoke-scale run")
    p.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "artifacts" / "recovery_study",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the BSM recovery study end-to-end and write artifacts; return exit code."""
    args = _parse_args(argv)
    scale = _QUICK_SCALE if args.quick else _FULL_SCALE
    design = load_bsm_input_design()
    scenarios = prespecified_bsm_scenarios()
    out = args.output_dir
    print(f"[bsm_recovery] scale={scale.description[:60]}...")
    print(f"[bsm_recovery] output_dir={out}")

    master = np.random.default_rng(args.seed)
    fwer_rows: list[dict] = []
    estimand_rows: list[dict] = []
    comparator_frames: list[pd.DataFrame] = []
    retention_rows: list[dict] = []

    for scenario in scenarios:
        print(f"[bsm_recovery]  scenario={scenario.name}")
        # Alternative-recovery point estimate (single representative replicate).
        rep_seed = int(master.integers(2**31))
        data = generate_bsm_dataset(design, scenario, scale, rep_seed)
        result = run_pipeline(data, scale, np.random.default_rng(rep_seed))
        estimand_rows.extend(_estimand_rows(scenario.name, data.true_support, result))
        for stage, counts in result["stage_retention"].items():
            retention_rows.append(
                {
                    "scenario": scenario.name,
                    "stage": stage,
                    "n_candidates": counts["n_candidates"],
                    "n_retained": counts["n_retained"],
                }
            )
        cdf = result["comparator_df"].copy()
        if not cdf.empty:
            cdf.insert(0, "scenario", scenario.name)
            comparator_frames.append(cdf)

        if scenario.name in _NULL_INTERACTION_SCENARIOS:
            flags = run_fwer_replicates(scenario, scale, master)
            stats = empirical_interaction_fwer(flags)
            print(
                f"[bsm_recovery]    FWER({scenario.name}): "
                f"{stats['fwer_proportion']:.3f} "
                f"[{stats['wilson_ci_lower']:.3f}, {stats['wilson_ci_upper']:.3f}] "
                f"n={stats['n_replicates']}"
            )
            fwer_rows.append(
                {
                    "scenario": scenario.name,
                    "alpha": scale.alpha,
                    "fwer_proportion": stats["fwer_proportion"],
                    "wilson_ci_lower": stats["wilson_ci_lower"],
                    "wilson_ci_upper": stats["wilson_ci_upper"],
                    "n_replicates": stats["n_replicates"],
                    "n_false_pair_replicates": stats["n_false_pair_replicates"],
                    "mean_false_pair_count": stats["mean_false_pair_count"],
                }
            )

    _write_csv(pd.DataFrame(fwer_rows), out / "fwer_calibration.csv")
    _write_csv(pd.DataFrame(estimand_rows), out / "recovery_estimands.csv")
    _write_csv(pd.DataFrame(retention_rows), out / "stage_retention.csv")
    if comparator_frames:
        _write_csv(pd.concat(comparator_frames, ignore_index=True), out / "comparator_metrics.csv")

    manifest = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "master_seed": args.seed,
        "scale": scale.description,
        "n_inputs": scale.n_inputs,
        "n_outputs": scale.n_outputs,
        "n_runs": scale.n_runs,
        "B": scale.B,
        "B_screen": scale.B_screen,
        "fwer_reps": scale.fwer_reps,
        "alpha": scale.alpha,
        "binary_input_names": design.binary_input_names,
        "scenarios": [{"name": s.name, "description": s.description} for s in scenarios],
    }
    (out / "recovery_manifest.json").write_text(json.dumps(manifest, indent=2))
    _write_reproduction_log(out, scale, design, scenarios, fwer_rows, args.seed)
    print(f"[bsm_recovery] Done. Artifacts written to {out}")
    return 0


def _write_reproduction_log(
    out: Path,
    scale: StudyScale,
    design: BSMInputDesign,
    scenarios: list[BSMScenario],
    fwer_rows: list[dict],
    seed: int,
) -> None:
    """Write a clean-environment reproduction log for the study."""
    lines = [
        "# BSM Semi-Synthetic Recovery Study — Reproduction Log",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Master seed: {seed}",
        "",
        "## Reproduce",
        "",
        "```bash",
        "pixi install --locked",
        f"pixi run python scripts/run_bsm_recovery_study.py --seed {seed}",
        "```",
        "",
        "## Scale (deliberate reduction from executed HPC scale)",
        "",
        scale.description,
        "",
        "## Input design",
        "",
        f"- Full executed interface: {design.n_inputs} inputs "
        f"({len(design.continuous_input_names)} continuous + "
        f"{len(design.binary_input_names)} binary scenario switches).",
        f"- Binary scenario switches: {', '.join(design.binary_input_names)}.",
        "- Continuous inputs resampled independently over their published "
        "[min_sample_value, max_sample_value] ranges (configs/"
        "manuscript_input_metadata.yml); binary switches drawn Bernoulli(0.5). "
        "This matches the executed independent-factor Monte-Carlo sensitivity "
        "design and preserves the empirical ranges and 158+2 structure without "
        "redistributing the raw run design.",
        "",
        "## Candidate-family logic (unchanged from the submitted workflow)",
        "",
        "Marginal permutation BH input screening -> PCA response reduction -> "
        "hierarchical residualized interaction scoring (interaction value added "
        "over linear + quadratic main-effect design) -> exact finite-permutation "
        "max-statistic (Westfall-Young) FWER selection; a parallel quadratic-"
        "library transformation-discovery stage uses the same residualized exact-"
        "FWER rule. All screening, PCA, scoring, and selection use train rows only.",
        "",
        "## Empirical interaction FWER (null-interaction scenarios)",
        "",
        "| scenario | alpha | FWER | Wilson 95% CI | n |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in fwer_rows:
        lines.append(
            f"| {r['scenario']} | {r['alpha']} | {r['fwer_proportion']:.3f} | "
            f"[{r['wilson_ci_lower']:.3f}, {r['wilson_ci_upper']:.3f}] | "
            f"{r['n_replicates']} |"
        )
    lines += [
        "",
        "## Scenario grid",
        "",
    ]
    for s in scenarios:
        lines.append(f"- **{s.name}**: {s.description}")
    lines += [
        "",
        "## Artifacts",
        "",
        "- `fwer_calibration.csv` — empirical interaction FWER + Wilson CI per null scenario.",
        "- `recovery_estimands.csv` — per-family (main/interaction/transformation/whole) "
        "precision, recall, FDP, exact-support recovery, selected size.",
        "- `stage_retention.csv` — candidates vs retained at each discovery stage.",
        "- `comparator_metrics.csv` — oracle-OLS, GBT, elastic-net predictive accuracy "
        "on independent test responses.",
        "- `recovery_manifest.json` — locked scale/seed/scenario manifest.",
    ]
    (out / "reproduction_log.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
