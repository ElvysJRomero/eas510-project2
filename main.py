"""Run baseline evaluations and save reproducible results."""

from __future__ import annotations

import json
from pathlib import Path

from config import (
    HOLDOUT_YEAR,
    PIPELINE_SUMMARY,
    TRAIN_YEARS,
    EVAL_YEARS,
    RANDOM_SEED,
)
from src.shsat import (
    load_all_feeder_workbooks,
    construct_targets,
    build_sample_bundle,
    train_mean_baseline,
    train_prevalence_baseline,
)


def run_pipeline(data_dir: str | Path) -> dict:
    """Run the full baseline pipeline and return serializable results.

    Loads development feeder data, constructs T1/T2 targets,
    evaluates mean (T1) and prevalence (T2) baselines with
    the configuration from `src.config`, and builds a sample bundle.

    Parameters
    ----------
    data_dir : Path to the directory containing feeder workbooks.

    Returns
    -------
    dict with keys: pipeline_summary, metrics, sample_bundle, evaluation_conditions
    """
    data_dir = Path(data_dir)

    feeder = load_all_feeder_workbooks(data_dir)
    targets = construct_targets(feeder)

    mean_result = train_mean_baseline(
        df=targets,
        train_years=TRAIN_YEARS,
        eval_years=EVAL_YEARS,
    )

    prevalence_result = train_prevalence_baseline(
        df=targets,
        train_years=TRAIN_YEARS,
        eval_years=EVAL_YEARS,
    )

    sample_bundle = build_sample_bundle(
        df=targets,
        data_dir=data_dir,
        sample_size=50,
        exclude_2026=True,
    )

    return {
        "pipeline_summary": PIPELINE_SUMMARY,
        "metrics": {"T1": mean_result, "T2": prevalence_result},
        "sample_bundle": sample_bundle.to_dict(orient="records"),
        "evaluation_conditions": {
            "train_years": TRAIN_YEARS,
            "eval_years": EVAL_YEARS,
            "holdout_year": HOLDOUT_YEAR,
            "random_seed": RANDOM_SEED,
        },
    }


def save_results(results: dict, output_dir: str | Path) -> None:
    """Save pipeline results to disk as reproducible JSON files.

    Writes two files:
    - pipeline.json: full pipeline summary, metrics, and evaluation conditions
    - sample_bundle.json: the sampled school data used for development

    Parameters
    ----------
    results : The dict returned by `run_pipeline`.
    output_dir : Directory path where JSON files will be saved.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results_path = output_dir / "pipeline.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    sample_path = output_dir / "sample_bundle.json"
    with open(sample_path, "w") as f:
        json.dump(results["sample_bundle"], f, indent=2, default=str)

    print(f"Saved pipeline.json -> {results_path}")
    print(f"Saved sample_bundle.json -> {sample_path}")


def main() -> None:
    """Entry point: run baselines on real data and save results."""
    data_dir = Path(__file__).resolve().parent / "data" / "raw" / "shsat"
    if not data_dir.exists():
        print(f"Error: data directory not found at {data_dir}")
        return

    results = run_pipeline(data_dir)

    results_output = Path(__file__).resolve().parent / "results" / "sample"
    save_results(results, results_output)


if __name__ == "__main__":
    main()
