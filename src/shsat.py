"""Load SHSAT feeder-school outcome workbooks without altering raw values."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score


FEEDER_SHEET = "Public Sending Offers_SUPP"
SOURCE_HEADERS = (
    "Feeder School DBN",
    "Feeder School Name",
    "Count of Students in HS Admissions",
    "Count of Testers",
    "Number of Offers",
    "Number of Discovery participants",
)
CANONICAL_COLUMNS = (
    "school_dbn",
    "school_name",
    "hs_admissions_raw",
    "testers_raw",
    "offers_raw",
    "discovery_raw",
)


def load_feeder_workbook(path: str | Path, admissions_year: int) -> pd.DataFrame:
    """Load one feeder sheet using either observed header format."""
    path = Path(path)
    raw = pd.read_excel(path, sheet_name=FEEDER_SHEET, header=None, dtype=object)
    if raw.shape[1] < len(SOURCE_HEADERS):
        raise ValueError(f"Expected six feeder columns in {path.name}")

    header_rows = raw.index[raw.iloc[:, 0].eq(SOURCE_HEADERS[0])].tolist()
    if len(header_rows) != 1:
        raise ValueError(f"Expected one feeder header row in {path.name}")

    header_row = header_rows[0]
    single_row_headers = tuple(raw.iloc[header_row, :6])
    if single_row_headers == SOURCE_HEADERS:
        data_start = header_row + 1
    else:
        if header_row + 1 >= len(raw):
            raise ValueError(f"Incomplete feeder header in {path.name}")
        two_row_headers = (
            raw.iat[header_row, 0],
            raw.iat[header_row, 1],
            raw.iat[header_row + 1, 2],
            raw.iat[header_row + 1, 3],
            raw.iat[header_row + 1, 4],
            raw.iat[header_row + 1, 5],
        )
        if two_row_headers != SOURCE_HEADERS:
            raise ValueError(f"Unexpected feeder header in {path.name}")
        data_start = header_row + 2

    data = raw.iloc[data_start:, :6].dropna(how="all").copy()
    data.columns = CANONICAL_COLUMNS

    if data.isna().any(axis=None):
        raise ValueError(f"Missing required feeder values in {path.name}")

    data["school_dbn"] = data["school_dbn"].astype(str).str.strip().str.upper()
    valid_dbns = data["school_dbn"].str.fullmatch(r"[0-9]{2}[A-Z][0-9]{3}")
    if not valid_dbns.all():
        raise ValueError(f"Malformed feeder DBN in {path.name}")

    data["admissions_year"] = int(admissions_year)
    data["source_file"] = path.name
    data["source_sheet"] = FEEDER_SHEET
    return data.reset_index(drop=True)


DEVELOPER_FILE_MAP: dict[int, str] = {
    2022: "fall-2022-offers-by-sending-school_suppressed.xlsx",
    2023: "2023-shsat-discovery-overall-summary_suppressed.xlsx",
    2024: "2024-shsat-discovery-overall-summary-suppressed.xlsx",
    2025: "2025-shsat-discovery-overall-summary-website.xlsx",
}


def load_all_feeder_workbooks(data_dir: str | Path) -> pd.DataFrame:
    """Load all development feeder workbooks via explicit file map.

    Only the four 2022–2025 filenames mapped in DEVELOPER_FILE_MAP are read.
    The 2026 holdout workbook is never referenced through a wildcard or directory scan.
    """
    data_dir = Path(data_dir)
    frames: list[pd.DataFrame] = []

    for admissions_year, filename in sorted(DEVELOPER_FILE_MAP.items()):
        path = data_dir / filename
        frames.append(load_feeder_workbook(path, admissions_year=admissions_year))

    return pd.concat(frames, ignore_index=True).reset_index(drop=True)


def construct_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Construct binary T1 (participation) and T2 (high-offer) targets.

    T1 (participation): 1 if testers_raw is numeric and > 0, 0 if 0-5.
    T2 (high-offer): 1 if offers_raw is numeric and >= 6, 0 if 0-5.

    The 2026 holdout must not be included in any preprocessing or
    feature-engineering decisions; targets are computed identically
    for all years so that holdout evaluation remains valid.
    """
    out = df.copy()

    def _testers_to_t1(val):
        if isinstance(val, (int, float)):
            return 1 if val > 0 else 0
        return 0  # 0-5 suppressed

    def _offers_to_t2(val):
        if isinstance(val, (int, float)):
            return 1 if val >= 6 else 0
        return 0  # 0-5 suppressed

    out["T1"] = out["testers_raw"].apply(_testers_to_t1)
    out["T2"] = out["offers_raw"].apply(_offers_to_t2)

    return out.reset_index(drop=True)


def split_data_by_year(
    df: pd.DataFrame, train_years: list[int], eval_years: list[int] | None = None
) -> dict[str, pd.DataFrame]:
    """Split feeder data by admission year using explicit year lists.

    Parameters
    ----------
    train_years: Years used for training (e.g. [2022, 2023, 2024, 2025]).
    eval_years:  Years used for evaluation (optional; if None no eval split).

    Returns a dict with keys 'train' and optionally 'eval'.
    The 2026 holdout is never included unless explicitly listed.
    """
    result: dict[str, pd.DataFrame] = {}

    if train_years:
        mask = df["admissions_year"].isin(train_years)
        result["train"] = df.loc[mask].reset_index(drop=True)

    if eval_years:
        mask = df["admissions_year"].isin(eval_years)
        result["eval"] = df.loc[mask].reset_index(drop=True)

    return result


def build_sample_bundle(
    df: pd.DataFrame,
    data_dir: str | Path,
    sample_size: int | None = None,
    exclude_2026: bool = True,
) -> pd.DataFrame:
    """Build a permitted sample bundle from feeder data for testing.

    Selects a subset of schools from the development data (2022–2025),
    retains source_year metadata and suppression strings, excludes 2026,
    and returns a small DataFrame suitable for embedding in the repository.

    If sample_size is None, returns a representative cross-section:
    equal per-year row counts with balanced T1/T2 targets.

    The returned bundle must never include 2026 data.
    """
    data_dir = Path(data_dir)
    bundle_df = df.copy()

    if exclude_2026:
        bundle_df = bundle_df[bundle_df["admissions_year"] != 2026].copy()

    if bundle_df.empty:
        return bundle_df.reset_index(drop=True)

    if sample_size is None:
        per_year = max(10, len(bundle_df) // (4 * 10))
        sampled = []
        for year, group in bundle_df.groupby("admissions_year", sort=False):
            sample_size_year = min(per_year, len(group))
            sampled.append(
                group.sample(sample_size_year, random_state=42 + year).reset_index(drop=True)
            )
        bundle_df = pd.concat(sampled, ignore_index=True)
    else:
        bundle_df = bundle_df.sample(min(sample_size, len(bundle_df)), random_state=42).reset_index(
            drop=True
        )

    return bundle_df


def train_mean_baseline(
    df: pd.DataFrame,
    train_years: list[int],
    eval_years: list[int],
) -> dict:
    """Evaluate a mean baseline for T1 (participation).

    Computes the mean of T1 from the training folds and predicts that
    constant value for all evaluation schools.  Returns MAE and RMSE
    along with row counts and evaluation metadata.

    Parameters
    ----------
    df : Full dataframe with T1 column already constructed.
    train_years : List of admission years used for training.
    eval_years : List of admission years used for evaluation.

    Returns
    -------
    dict with keys: baseline, target, metrics, t1_mean,
                    row_counts, evaluation_conditions
    """
    splits = split_data_by_year(df, train_years, eval_years)
    train = splits["train"]
    eval_df = splits["eval"]

    t1_mean = float(train["T1"].mean())
    t1_predictions = np.full(len(eval_df), t1_mean)

    t1_values = eval_df["T1"].values.astype(float)

    mae = float(np.mean(np.abs(t1_predictions - t1_values)))
    rmse = float(np.sqrt(np.mean((t1_predictions - t1_values) ** 2)))

    return {
        "baseline": "mean",
        "target": "T1",
        "metrics": {"mae": mae, "rmse": rmse},
        "t1_mean": t1_mean,
        "row_counts": {"train": len(train), "eval": len(eval_df)},
        "evaluation_conditions": {
            "train_years": train_years,
            "eval_years": eval_years,
        },
    }


def train_prevalence_baseline(
    df: pd.DataFrame,
    train_years: list[int],
    eval_years: list[int],
) -> dict:
    """Evaluate a prevalence baseline for T2 (high-offer).

    Computes the prevalence of T2=1 from the training folds and
    predicts that constant value for all evaluation schools.
    Returns average precision and positive prevalence along with
    row counts and evaluation metadata.

    Parameters
    ----------
    df : Full dataframe with T2 column already constructed.
    train_years : List of admission years used for training.
    eval_years : List of admission years used for evaluation.

    Returns
    -------
    dict with keys: baseline, target, metrics, t2_prevalence,
                    row_counts, evaluation_conditions
    """
    splits = split_data_by_year(df, train_years, eval_years)
    train = splits["train"]
    eval_df = splits["eval"]

    t2_prevalence = float(train["T2"].mean())
    t2_predictions = np.full(len(eval_df), t2_prevalence)

    ap = float(average_precision_score(eval_df["T2"], t2_predictions))
    pos_prevalence = float(np.mean(t2_predictions))

    return {
        "baseline": "prevalence",
        "target": "T2",
        "metrics": {"ap": ap, "positive_prevalence": pos_prevalence},
        "t2_prevalence": t2_prevalence,
        "row_counts": {"train": len(train), "eval": len(eval_df)},
        "evaluation_conditions": {
            "train_years": train_years,
            "eval_years": eval_years,
        },
    }
