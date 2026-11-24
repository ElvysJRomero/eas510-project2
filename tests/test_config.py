"""Unit tests for config.py pipeline constants."""

import unittest
from config import (
    PIPELINE_SUMMARY,
    CANONICAL_COLUMNS,
    DEVELOPER_FILE_MAP,
    EVAL_YEARS,
    FEEDER_SHEET_NAME,
    HOLDOUT_YEAR,
    RANDOM_SEED,
    T1_BASELINE,
    T1_POSITIVE_THRESHOLD,
    T2_BASELINE,
    T2_HIGH_OFFER_THRESHOLD,
    TRAIN_YEARS,
)


class ConfigExportTests(unittest.TestCase):
    """Verify all required configuration keys are exported from config.py."""

    def test_required_keys_exist(self):
        """All documented constants must be exported from config.py."""
        expected_keys = {
            "TRAIN_YEARS",
            "EVAL_YEARS",
            "HOLDOUT_YEAR",
            "RANDOM_SEED",
            "T1_POSITIVE_THRESHOLD",
            "T2_HIGH_OFFER_THRESHOLD",
            "T1_BASELINE",
            "T2_BASELINE",
            "PIPELINE_SUMMARY",
            "FEEDER_SHEET_NAME",
            "CANONICAL_COLUMNS",
            "DEVELOPER_FILE_MAP",
        }
        config_attributes = [k for k in dir(__import__("config", fromlist=[""])) if not k.startswith("_")]
        for key in expected_keys:
            self.assertIn(key, config_attributes, f"Missing exported config key: {key}")

    def test_train_years(self):
        self.assertEqual(TRAIN_YEARS, [2022, 2023, 2024])

    def test_eval_years(self):
        self.assertEqual(EVAL_YEARS, [2025])

    def test_holdout_year(self):
        self.assertEqual(HOLDOUT_YEAR, 2026)

    def test_random_seed(self):
        self.assertEqual(RANDOM_SEED, 42)

    def test_t1_positive_threshold(self):
        self.assertEqual(T1_POSITIVE_THRESHOLD, 0)

    def test_t2_high_offer_threshold(self):
        self.assertEqual(T2_HIGH_OFFER_THRESHOLD, 6)

    def test_t1_baseline_content(self):
        self.assertEqual(T1_BASELINE["method"], "mean")
        self.assertEqual(T1_BASELINE["metric"], "MAE / RMSE")
        self.assertIn("description", T1_BASELINE)

    def test_t2_baseline_content(self):
        self.assertEqual(T2_BASELINE["method"], "prevalence")
        self.assertEqual(T2_BASELINE["metric"], "AP / positive_prevalence")
        self.assertIn("description", T2_BASELINE)

    def test_pipeline_summary_structure(self):
        self.assertIn("name", PIPELINE_SUMMARY)
        self.assertIn("question", PIPELINE_SUMMARY)
        self.assertIn("train_years", PIPELINE_SUMMARY)
        self.assertIn("eval_years", PIPELINE_SUMMARY)
        self.assertIn("holdout_year", PIPELINE_SUMMARY)
        self.assertIn("random_seed", PIPELINE_SUMMARY)
        self.assertIn("targets", PIPELINE_SUMMARY)
        self.assertIn("T1", PIPELINE_SUMMARY["targets"])
        self.assertIn("T2", PIPELINE_SUMMARY["targets"])

    def test_developer_file_map_keys(self):
        self.assertEqual(set(DEVELOPER_FILE_MAP.keys()), {2022, 2023, 2024, 2025})

    def test_feeder_sheet_name(self):
        self.assertEqual(FEEDER_SHEET_NAME, "Public Sending Offers_SUPP")

    def test_canonical_columns(self):
        self.assertEqual(len(CANONICAL_COLUMNS), 6)
        self.assertEqual(CANONICAL_COLUMNS[0], "school_dbn")
        self.assertEqual(CANONICAL_COLUMNS[1], "school_name")


if __name__ == "__main__":
    unittest.main()
