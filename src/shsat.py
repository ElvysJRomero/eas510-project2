"""Load SHSAT feeder-school outcome workbooks without altering raw values."""

from pathlib import Path

import pandas as pd


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
