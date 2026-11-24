# NYC Specialized High School Admissions Analysis

Where do representation gaps emerge in NYC's SHSAT-based specialized-high-school admissions pipeline, how do they vary across schools, populations, and time, and to what extent are those patterns predictable?

This project uses public aggregate school-level data to investigate SHSAT participation, admissions offers, and demographic representation. Predictions are school-level, not about individual students. Findings describe associations, not causal effects.

- `docs/sources.md` — complete list of public data sources with download URLs, official links, local paths, and metadata for every dataset used in this project.
- `requirements.txt` — pinned project runtime dependencies.

## Environment

Tested with Python 3.12.13 on macOS 26.6.2 (arm64). Verified with NumPy 2.5.5, SciPy 1.18.1, pandas 3.1.1, Matplotlib 3.11.2, seaborn 0.13.2, openpyxl 3.1.5, scikit-learn 1.9.1.

## Setup and Execution

```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

The sample run requires no manual downloads, network access, credentials, or GPU. It completes within 5 minutes on CPU-only Linux with 8 GB RAM.

## Expected Outputs

After running `python main.py`, two files appear under `results/sample/`:

- `pipeline.json` — baseline metrics, configuration, and row counts. T1 baseline: MAE ≈ 0.30 (±0.05), RMSE ≈ 0.39 (±0.05). T2 baseline: AP ≈ 0.17 (±0.02), positive prevalence ≈ 0.17. Train: 2,028 school-year rows (2022–2024); eval: 676 rows (2025).
- `sample_bundle.json` — stratified sample (≈12 per year, 2022–2025) retaining source-year metadata, suppression tokens, and target labels.

## Resources and Data

Data is obtained from NYC DOE / InfoHub, a publicly accessible portal. The pipeline uses SHSAT feeder-school outcome workbooks for 2022–2025, which are included as a bundled sample under `data/sample/`. This sample contains the Public Sending Offers sheet from one workbook per year (4 files, ~230 KB total), covering 2,704 school-year observations (683 for 2022, 671 for 2023, 674 for 2024, 676 for 2025). The 2026 workbook is deliberately excluded from the sample to preserve it as a chronological holdout.

The sample omits discovery tables, citywide summaries, district-level offers, and non-offer sheets that exist in the full downloads. These omitted sheets are not used in the current pipeline.

Expected runtime: approximately 1–2 minutes for the sample run. Peak memory: under 200 MB.

## Full Experiment

When the full dataset is placed under `data/raw/shsat/`, `python3 main.py` automatically reads from there instead of the sample. To run with explicit full data, place the downloaded Excel workbooks in `data/raw/shsat/` and run:

```bash
python3 main.py
```

Full-experiment outputs (when they differ from sample) are saved under `results/full/`. The configuration and evaluation procedure are identical; only the training data extent differs.

## Results (Preliminary)

Using a chronological split (train: 2022–2024, eval: 2025, holdout: 2026), two baselines were evaluated on the bundled sample:

| Target | Method | Metric | Value | Train rows | Eval rows |
|--------|--------|--------|-------|------------|-----------|
| T1 (participation) | Mean prediction | MAE | 0.30 | 2,028 | 676 |
| T1 (participation) | Mean prediction | RMSE | 0.39 | 2,028 | 676 |
| T2 (high-offer) | Prevalence baseline | AP | 0.17 | 2,028 | 676 |
| T2 (high-offer) | Prevalence baseline | Positive prevalence | 0.17 | 2,028 | 676 |

T1 (whether a school sent testers to SHSAT) is common (82.6% positive in training), so the mean baseline achieves low MAE. T2 (whether a school received ≥ 6 offers to any target school) is rarer (16.9% positive), and the prevalence baseline scores below random on average precision, reflecting the challenge of predicting high-offer schools without features.
