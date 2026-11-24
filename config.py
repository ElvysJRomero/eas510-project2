"""Document and export verified pipeline configuration constants.

This module records the split, random seed, target construction,
and baseline settings used in the interim baseline evaluation.
It is the single source of truth for reproducing the documented
chronological boundaries and baseline parameters.
"""

from __future__ import annotations

from src.shsat import (
    CANONICAL_COLUMNS,
    DEVELOPER_FILE_MAP,
    FEEDER_SHEET,
)

# ---------------------------------------------------------------------------
# Chronological boundaries
# ---------------------------------------------------------------------------

#: Years used for training (development data only).
TRAIN_YEARS: list[int] = [2022, 2023, 2024]

#: Evaluation years (chronological holdout from training; 2026 is separate holdout).
EVAL_YEARS: list[int] | None = [2025]

#: Chronological holdout year excluded from all training and evaluation.
HOLDOUT_YEAR: int = 2026

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

#: Random seed for all stochastic operations (e.g. sample selection).
RANDOM_SEED: int = 42

# ---------------------------------------------------------------------------
# Target definitions
# ---------------------------------------------------------------------------

#: T1 (participation) positive threshold: testers_raw > 0 maps to 1.
T1_POSITIVE_THRESHOLD: int = 0

#: T2 (high-offer) positive threshold: offers_raw >= 6 maps to 1.
T2_HIGH_OFFER_THRESHOLD: int = 6

# ---------------------------------------------------------------------------
# Baseline configurations
# ---------------------------------------------------------------------------

#: T1 baseline: mean participation rate across training years.
T1_BASELINE: dict[str, str | float] = {
    "method": "mean",
    "metric": "MAE / RMSE",
    "description": "Predict the global mean T1 score from training years for all evaluation schools.",
}

#: T2 baseline: prevalence (mean) high-offer rate across training years.
T2_BASELINE: dict[str, str | float] = {
    "method": "prevalence",
    "metric": "AP / positive_prevalence",
    "description": "Predict the global mean T2 score from training years for all evaluation schools.",
}

# ---------------------------------------------------------------------------
# Data ingestion constants (imported from shsat for single-source clarity)
# ---------------------------------------------------------------------------

#: Excel sheet name containing feeder data.
FEEDER_SHEET_NAME: str = FEEDER_SHEET

#: Canonical column names after normalization.
CANONICAL_COLUMNS: tuple[str, str, str, str, str, str] = CANONICAL_COLUMNS

#: Explicit 2022-2025 file map (no wildcard or 2026 reference).
DEVELOPER_FILE_MAP: dict[int, str] = DEVELOPER_FILE_MAP

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

#: Human-readable summary of the full pipeline configuration.
PIPELINE_SUMMARY: dict = {
    "name": "SHSAT Baseline Pipeline",
    "question": "Representation gaps across feeder schools for SHSAT admissions.",
    "train_years": TRAIN_YEARS,
    "eval_years": EVAL_YEARS,
    "holdout_year": HOLDOUT_YEAR,
    "random_seed": RANDOM_SEED,
    "targets": {
        "T1": {
            "name": "participation",
            "positive_threshold": T1_POSITIVE_THRESHOLD,
            "baseline": T1_BASELINE,
        },
        "T2": {
            "name": "high_offer",
            "positive_threshold": T2_HIGH_OFFER_THRESHOLD,
            "baseline": T2_BASELINE,
        },
    },
}
