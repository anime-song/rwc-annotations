from pathlib import Path
import pandas as pd
import pytest

CHORDS_DIR = Path("01_annotations_preprocessed") / "chords"
CHORD_FILES = sorted(CHORDS_DIR.rglob("*.csv"))  # change to *.lab if needed


def test_chords_folder_exists():
    """Check that the preprocessed chord annotation folder exists.

    Examples
    --------
    The repository is expected to contain
    ``01_annotations_preprocessed/chords`` before individual chord files are
    inspected.
    """
    assert CHORDS_DIR.exists(), f"chords folder not found: {CHORDS_DIR}"


def test_chord_files_exist():
    """Check that at least one chord CSV file is available.

    Examples
    --------
    A repository with files such as ``chords/RWC-P/RWC_P001.csv`` is expected
    to pass. An empty ``chords`` folder is expected to fail.
    """
    assert CHORD_FILES, f"No chord files found under: {CHORDS_DIR}"


@pytest.mark.parametrize(
    "csv_path", CHORD_FILES, ids=lambda p: str(p.relative_to(CHORDS_DIR))
)
def test_chords_have_3_columns_and_nonempty(csv_path: Path):
    """Check the basic CSV structure for one chord annotation file.

    Parameters
    ----------
    csv_path
        Chord CSV file under test.

    Examples
    --------
    A semicolon-separated file with three columns such as ``t_start``,
    ``t_end``, and ``chord`` and at least one data row is expected to pass.
    A two-column file is expected to fail.
    """
    df = pd.read_csv(csv_path, sep=";")

    assert df.shape[1] == 3, f"{csv_path} has {df.shape[1]} columns, expected 3"
    assert len(df) > 0, f"{csv_path} has no rows"


@pytest.mark.parametrize(
    "csv_path", CHORD_FILES, ids=lambda p: str(p.relative_to(CHORDS_DIR))
)
def test_chords_time_values_plausible(csv_path: Path):
    """Check that chord time intervals are numeric, non-negative, and ordered.

    Parameters
    ----------
    csv_path
        Chord CSV file under test.

    Examples
    --------
    A row with ``t_start == 1.0`` and ``t_end == 2.0`` is expected to pass.
    Rows with negative times, non-numeric times, or ``t_end <= t_start`` are
    expected to fail.
    """
    df = pd.read_csv(csv_path, sep=";")  # <-- header is used

    # enforce column count (also enforces delimiter)
    assert df.shape[1] == 3, f"{csv_path} has {df.shape[1]} columns, expected 3"

    # (optional) enforce header names if you want
    # assert list(df.columns) == ["t_start", "t_end", "chord"]

    t_start = pd.to_numeric(df["t_start"], errors="coerce")
    t_end = pd.to_numeric(df["t_end"], errors="coerce")

    assert t_start.notna().all(), f"{csv_path} has non-numeric t_start values"
    assert t_end.notna().all(), f"{csv_path} has non-numeric t_end values"

    assert (t_start >= 0).all(), f"{csv_path} has negative t_start"
    assert (t_end >= 0).all(), f"{csv_path} has negative t_end"
    assert (t_end > t_start).all(), f"{csv_path} has t_end <= t_start"
