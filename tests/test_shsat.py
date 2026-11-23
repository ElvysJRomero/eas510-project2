import tempfile
import unittest
from pathlib import Path

import pandas as pd
from openpyxl import Workbook

from src.shsat import (
    DEVELOPER_FILE_MAP,
    build_sample_bundle,
    construct_targets,
    load_all_feeder_workbooks,
    load_feeder_workbook,
    split_data_by_year,
)


class LoadFeederWorkbookTests(unittest.TestCase):
    def test_loads_two_row_header_and_preserves_suppression(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fall-2022-feeder.xlsx"
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Public Sending Offers_SUPP"
            sheet.append(
                [
                    "Feeder School DBN",
                    "Feeder School Name",
                    "Fall 2022 Admissions",
                    None,
                    None,
                    None,
                ]
            )
            sheet.append(
                [
                    None,
                    None,
                    "Count of Students in HS Admissions",
                    "Count of Testers",
                    "Number of Offers",
                    "Number of Discovery participants",
                ]
            )
            sheet.append([" 01m001 ", "Example School", 42, 10, "0-5", "0-5"])
            sheet.append(["02X002", "Second School", 35, "0-5", 7, 6])
            workbook.save(path)
            workbook.close()

            result = load_feeder_workbook(path, admissions_year=2022)

        self.assertEqual(
            result.to_dict(orient="records"),
            [
                {
                    "school_dbn": "01M001",
                    "school_name": "Example School",
                    "hs_admissions_raw": 42,
                    "testers_raw": 10,
                    "offers_raw": "0-5",
                    "discovery_raw": "0-5",
                    "admissions_year": 2022,
                    "source_file": "fall-2022-feeder.xlsx",
                    "source_sheet": "Public Sending Offers_SUPP",
                },
                {
                    "school_dbn": "02X002",
                    "school_name": "Second School",
                    "hs_admissions_raw": 35,
                    "testers_raw": "0-5",
                    "offers_raw": 7,
                    "discovery_raw": 6,
                    "admissions_year": 2022,
                    "source_file": "fall-2022-feeder.xlsx",
                    "source_sheet": "Public Sending Offers_SUPP",
                },
            ],
        )

    def test_loads_title_then_single_header_row(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fall-2023-feeder.xlsx"
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Public Sending Offers_SUPP"
            sheet.append(
                [
                    "Specialized High School Offers by Sending School, Fall 2023 Admissions",
                    None,
                    None,
                    None,
                    None,
                    None,
                ]
            )
            sheet.append(
                [
                    "Feeder School DBN",
                    "Feeder School Name",
                    "Count of Students in HS Admissions",
                    "Count of Testers",
                    "Number of Offers",
                    "Number of Discovery participants",
                ]
            )
            sheet.append(["03m003", "Third School", 50, 12, "0-5", 8])
            workbook.save(path)
            workbook.close()

            result = load_feeder_workbook(path, admissions_year=2023)

        self.assertEqual(
            result.to_dict(orient="records"),
            [
                {
                    "school_dbn": "03M003",
                    "school_name": "Third School",
                    "hs_admissions_raw": 50,
                    "testers_raw": 12,
                    "offers_raw": "0-5",
                    "discovery_raw": 8,
                    "admissions_year": 2023,
                    "source_file": "fall-2023-feeder.xlsx",
                    "source_sheet": "Public Sending Offers_SUPP",
                }
            ],
        )


EXPECTED_ROW_COUNTS: dict[int, int] = {
    2022: 683,
    2023: 671,
    2024: 674,
    2025: 676,
}

EXPECTED_SUPPRESSIONS: dict[str, int] = {
    "hs_admissions_raw": 78,
    "testers_raw": 479,
    "offers_raw": 2246,
    "discovery_raw": 2559,
}

EXPECTED_TOTAL_ROWS: int = 2704


class DevelopmentIngestionValidation(unittest.TestCase):
    DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "raw" / "shsat"

    def _skip_if_no_data(self) -> None:
        first_file = self.DATA_DIR / DEVELOPER_FILE_MAP[2022]
        if not first_file.exists():
            self.skipTest("data/raw/shsat not available")

    def test_total_row_count(self):
        self._skip_if_no_data()
        df = load_all_feeder_workbooks(self.DATA_DIR)
        self.assertEqual(len(df), EXPECTED_TOTAL_ROWS)

    def test_per_year_row_counts(self):
        self._skip_if_no_data()
        df = load_all_feeder_workbooks(self.DATA_DIR)
        for year, expected in EXPECTED_ROW_COUNTS.items():
            actual = (df.admissions_year == year).sum()
            self.assertEqual(actual, expected, f"Year {year} expected {expected}, got {actual}")

    def test_no_missing_required_columns(self):
        self._skip_if_no_data()
        df = load_all_feeder_workbooks(self.DATA_DIR)
        raw_cols = [
            "school_dbn",
            "hs_admissions_raw",
            "testers_raw",
            "offers_raw",
            "discovery_raw",
        ]
        missing = df[raw_cols].isnull().sum().sum()
        self.assertEqual(missing, 0, f"Found {missing} missing required values")

    def test_unique_dbn_year_keys(self):
        self._skip_if_no_data()
        df = load_all_feeder_workbooks(self.DATA_DIR)
        unique_keys = df[["school_dbn", "admissions_year"]].drop_duplicates().shape[0]
        self.assertEqual(unique_keys, len(df), f"Found {len(df) - unique_keys} duplicate keys")

    def test_all_dbns_valid(self):
        self._skip_if_no_data()
        df = load_all_feeder_workbooks(self.DATA_DIR)
        invalid = (~df.school_dbn.str.fullmatch(r"[0-9]{2}[A-Z][0-9]{3}")).sum()
        self.assertEqual(invalid, 0, f"Found {invalid} invalid DBNs")

    def test_2026_holdout_excluded(self):
        self._skip_if_no_data()
        df = load_all_feeder_workbooks(self.DATA_DIR)
        has_2026 = df.source_file.str.contains("2026").any()
        self.assertFalse(has_2026, "2026 holdout file was referenced")

    def test_suppression_counts_match_source_audit(self):
        self._skip_if_no_data()
        df = load_all_feeder_workbooks(self.DATA_DIR)
        for col, expected in EXPECTED_SUPPRESSIONS.items():
            actual = (df[col] == "0-5").sum()
            self.assertEqual(
                actual,
                expected,
                f"{col} suppression mismatch: expected {expected}, got {actual}",
            )

    def test_only_mapped_filenames_referenced(self):
        self._skip_if_no_data()
        df = load_all_feeder_workbooks(self.DATA_DIR)
        referenced = set(df.source_file.unique())
        mapped = set(DEVELOPER_FILE_MAP.values())
        self.assertEqual(referenced, mapped, f"Unexpected files: {referenced - mapped}")


class TargetConstructionTests(unittest.TestCase):
    DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "raw" / "shsat"

    def _skip_if_no_data(self) -> None:
        first_file = self.DATA_DIR / DEVELOPER_FILE_MAP[2022]
        if not first_file.exists():
            self.skipTest("data/raw/shsat not available")

    def test_construct_targets_binary_t1(self):
        data = [
            {"school_dbn": "01M001", "testers_raw": 100, "offers_raw": "0-5"},
            {"school_dbn": "02X002", "testers_raw": "0-5", "offers_raw": 12},
            {"school_dbn": "03Z003", "testers_raw": 0, "offers_raw": 0},
        ]
        df = pd.DataFrame(data)
        result = construct_targets(df)

        self.assertEqual(result.loc[0, "T1"], 1)
        self.assertEqual(result.loc[1, "T1"], 0)
        self.assertEqual(result.loc[2, "T1"], 0)

    def test_construct_targets_binary_t2(self):
        data = [
            {"school_dbn": "01M001", "testers_raw": 100, "offers_raw": 12},
            {"school_dbn": "02X002", "testers_raw": "0-5", "offers_raw": "0-5"},
            {"school_dbn": "03Z003", "testers_raw": 10, "offers_raw": 5},
        ]
        df = pd.DataFrame(data)
        result = construct_targets(df)

        self.assertEqual(result.loc[0, "T2"], 1)
        self.assertEqual(result.loc[1, "T2"], 0)
        self.assertEqual(result.loc[2, "T2"], 0)

    def test_construct_targets_preserves_original_columns(self):
        data = [
            {"school_dbn": "01M001", "testers_raw": 50, "offers_raw": 10},
        ]
        df = pd.DataFrame(data)
        result = construct_targets(df)

        self.assertIn("school_dbn", result.columns)
        self.assertIn("testers_raw", result.columns)
        self.assertIn("offers_raw", result.columns)
        self.assertIn("T1", result.columns)
        self.assertIn("T2", result.columns)

    def test_construct_targets_from_real_data(self):
        self._skip_if_no_data()
        df = load_all_feeder_workbooks(self.DATA_DIR)
        result = construct_targets(df)

        self.assertEqual(len(result), EXPECTED_TOTAL_ROWS)
        self.assertIn("T1", result.columns)
        self.assertIn("T2", result.columns)
        t1_counts = result["T1"].value_counts()
        self.assertEqual(t1_counts.get(1, 0), 2225)
        self.assertEqual(t1_counts.get(0, 0), 479)
        t2_counts = result["T2"].value_counts()
        self.assertEqual(t2_counts.get(1, 0), 458)
        self.assertEqual(t2_counts.get(0, 0), 2246)


class DataSplittingTests(unittest.TestCase):
    DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "raw" / "shsat"

    def _skip_if_no_data(self) -> None:
        first_file = self.DATA_DIR / DEVELOPER_FILE_MAP[2022]
        if not first_file.exists():
            self.skipTest("data/raw/shsat not available")

    def test_split_data_by_year_train_only(self):
        data = [
            {"school_dbn": "01M001", "admissions_year": 2022, "T1": 1},
            {"school_dbn": "02X002", "admissions_year": 2023, "T1": 0},
            {"school_dbn": "03Z003", "admissions_year": 2025, "T1": 1},
            {"school_dbn": "04A004", "admissions_year": 2026, "T1": 0},
        ]
        df = pd.DataFrame(data)
        splits = split_data_by_year(df, train_years=[2022, 2023, 2025])

        self.assertEqual(len(splits["train"]), 3)
        self.assertEqual(set(splits["train"]["admissions_year"].tolist()), {2022, 2023, 2025})

    def test_split_data_by_year_with_eval(self):
        data = [
            {"school_dbn": "01M001", "admissions_year": 2022, "T1": 1},
            {"school_dbn": "02X002", "admissions_year": 2024, "T1": 0},
            {"school_dbn": "03Z003", "admissions_year": 2025, "T1": 1},
            {"school_dbn": "04A004", "admissions_year": 2026, "T1": 0},
        ]
        df = pd.DataFrame(data)
        splits = split_data_by_year(
            df, train_years=[2022, 2024], eval_years=[2025]
        )

        self.assertEqual(len(splits["train"]), 2)
        self.assertEqual(set(splits["train"]["admissions_year"].tolist()), {2022, 2024})
        self.assertEqual(len(splits["eval"]), 1)
        self.assertEqual(set(splits["eval"]["admissions_year"].tolist()), {2025})

    def test_split_data_excludes_holdout(self):
        data = [
            {"school_dbn": "01M001", "admissions_year": 2022, "T1": 1},
            {"school_dbn": "02X002", "admissions_year": 2026, "T1": 0},
        ]
        df = pd.DataFrame(data)
        splits = split_data_by_year(df, train_years=[2022])

        all_years = splits["train"]["admissions_year"].tolist()
        self.assertNotIn(2026, all_years)

    def test_split_data_by_year_real(self):
        self._skip_if_no_data()
        df = load_all_feeder_workbooks(self.DATA_DIR)
        splits = split_data_by_year(df, train_years=[2022, 2023, 2024, 2025])

        self.assertEqual(len(splits["train"]), 2704)
        train_years = set(splits["train"]["admissions_year"].tolist())
        self.assertEqual(train_years, {2022, 2023, 2024, 2025})


class SampleBundleTests(unittest.TestCase):
    DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "raw" / "shsat"

    def _skip_if_no_data(self) -> None:
        first_file = self.DATA_DIR / DEVELOPER_FILE_MAP[2022]
        if not first_file.exists():
            self.skipTest("data/raw/shsat not available")

    def test_build_sample_bundle_excludes_2026(self):
        self._skip_if_no_data()
        df = load_all_feeder_workbooks(self.DATA_DIR)
        df = construct_targets(df)
        bundle = build_sample_bundle(df, self.DATA_DIR, exclude_2026=True)

        self.assertFalse((bundle["admissions_year"] == 2026).any())

    def test_build_sample_bundle_default_size(self):
        self._skip_if_no_data()
        df = load_all_feeder_workbooks(self.DATA_DIR)
        df = construct_targets(df)
        bundle = build_sample_bundle(df, self.DATA_DIR)

        per_year = bundle.groupby("admissions_year").size()
        for year in [2022, 2023, 2024, 2025]:
            self.assertGreaterEqual(per_year.get(year, 0), 10)

    def test_build_sample_bundle_respects_size_limit(self):
        self._skip_if_no_data()
        df = load_all_feeder_workbooks(self.DATA_DIR)
        df = construct_targets(df)
        bundle = build_sample_bundle(df, self.DATA_DIR, sample_size=50)

        self.assertLessEqual(len(bundle), 50)

    def test_build_sample_bundle_preserves_raw_and_target_columns(self):
        self._skip_if_no_data()
        df = load_all_feeder_workbooks(self.DATA_DIR)
        df = construct_targets(df)
        bundle = build_sample_bundle(df, self.DATA_DIR)

        self.assertIn("T1", bundle.columns)
        self.assertIn("T2", bundle.columns)
        self.assertIn("testers_raw", bundle.columns)
        self.assertIn("offers_raw", bundle.columns)

    def test_build_sample_bundle_empty_on_2026_only(self):
        data = [
            {"school_dbn": "01M001", "admissions_year": 2026, "testers_raw": 50, "offers_raw": 10},
        ]
        df = pd.DataFrame(data)
        bundle = build_sample_bundle(df, self.DATA_DIR, exclude_2026=True)

        self.assertEqual(len(bundle), 0)


if __name__ == "__main__":
    unittest.main()
