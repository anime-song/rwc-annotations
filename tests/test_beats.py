from pathlib import Path
import pandas as pd
import pytest

BEATS_DIR = Path("01_annotations_preprocessed") / "beats"
BEAT_FILES = sorted(BEATS_DIR.rglob("*.csv"))


def test_beats_folder_exists():
    """Check that the preprocessed beat annotation folder exists.

    Examples
    --------
    The repository is expected to contain
    ``01_annotations_preprocessed/beats`` before individual beat files are
    inspected.
    """
    assert BEATS_DIR.exists(), f"beats folder not found: {BEATS_DIR}"


def test_beat_files_exist():
    """Check that at least one beat CSV file is available.

    Examples
    --------
    A repository with files such as ``beats/RWC-P/RWC_P001.csv`` is expected
    to pass. An empty ``beats`` folder is expected to fail.
    """
    assert BEAT_FILES, f"No beat CSV files found under: {BEATS_DIR}"


@pytest.mark.parametrize(
    "csv_path",
    BEAT_FILES,
    ids=lambda p: str(p.relative_to(BEATS_DIR)),
)
def test_beats_format_header_and_nonempty(csv_path: Path):
    """Check the basic CSV format for one beat annotation file.

    Parameters
    ----------
    csv_path
        Beat CSV file under test.

    Examples
    --------
    A file with header ``t;beat`` and at least one data row is expected to
    pass. A comma-separated file or a file with columns ``time;position`` is
    expected to fail.
    """
    df = pd.read_csv(csv_path, sep=";")

    # enforce delimiter + structure
    assert (
        df.shape[1] == 2
    ), f"{csv_path} has {df.shape[1]} columns, expected 2 (t;beat)"

    expected_header = ["t", "beat"]
    assert (
        list(df.columns) == expected_header
    ), f"{csv_path} wrong header. Expected {expected_header}, got {list(df.columns)}"

    assert len(df) > 0, f"{csv_path} has no data rows"


@pytest.mark.parametrize(
    "csv_path", BEAT_FILES, ids=lambda p: str(p.relative_to(BEATS_DIR))
)
def test_time_positive(csv_path):
    """Check that beat timestamps are numeric and non-negative.

    Parameters
    ----------
    csv_path
        Beat CSV file under test.

    Examples
    --------
    Timestamp values ``[0.0, 0.5, 1.0]`` are expected to pass. Values such as
    ``[-0.1, 0.5]`` or ``["intro", 0.5]`` are expected to fail.
    """
    df = pd.read_csv(csv_path, sep=";")
    t = pd.to_numeric(df["t"], errors="coerce")
    assert t.notna().all()
    assert (t >= 0).all()


@pytest.mark.parametrize(
    "csv_path", BEAT_FILES, ids=lambda p: str(p.relative_to(BEATS_DIR))
)
def test_time_monotonically_increasing(csv_path):
    """Check that beat timestamps strictly increase.

    Parameters
    ----------
    csv_path
        Beat CSV file under test.

    Examples
    --------
    Timestamp values ``[0.0, 0.5, 1.0]`` are expected to pass. Values
    ``[0.0, 0.5, 0.5]`` or ``[0.0, 1.0, 0.5]`` are expected to fail.
    """
    df = pd.read_csv(csv_path, sep=";")
    t = pd.to_numeric(df["t"], errors="coerce")
    dt = t.diff().dropna()
    assert (dt > 0).all()


@pytest.mark.parametrize(
    "csv_path", BEAT_FILES, ids=lambda p: str(p.relative_to(BEATS_DIR))
)
def test_beats_plausible_range(csv_path: Path):
    """Check that beat numbers are integer positions in a plausible range.

    Parameters
    ----------
    csv_path
        Beat CSV file under test.

    Examples
    --------
    Beat values ``[1, 2, 3, 4]`` are expected to pass. Values such as ``0``,
    ``17``, or ``2.5`` are expected to fail.
    """
    df = pd.read_csv(csv_path, sep=";")

    beat = pd.to_numeric(df["beat"], errors="coerce")
    assert beat.notna().all(), f"{csv_path} has non-numeric beat values"

    assert (beat % 1 == 0).all(), f"{csv_path} has non-integer beat values"
    beat = beat.astype(int)

    assert (beat >= 1).all(), f"{csv_path} has beat values < 1"
    assert (beat <= 16).all(), f"{csv_path} has beat values > 16"


@pytest.mark.parametrize(
    "csv_path", BEAT_FILES, ids=lambda p: str(p.relative_to(BEATS_DIR))
)
def test_beat_order_plus_one_or_reset_to_one(csv_path: Path):
    """Check that beat positions advance by one or reset to one.

    Parameters
    ----------
    csv_path
        Beat CSV file under test.

    Examples
    --------
    Beat values ``[1, 2, 3, 4, 1, 2]`` are expected to pass. Values
    ``[1, 2, 4]`` are expected to fail because the sequence skips ``3``.
    """
    df = pd.read_csv(csv_path, sep=";")

    beat = pd.to_numeric(df["beat"], errors="coerce")
    assert beat.notna().all(), f"{csv_path} has non-numeric beat values"

    beat = beat.astype(int)

    prev = beat.shift(1)

    # ignore first row (no previous beat)
    cur = beat.iloc[1:]
    prev = prev.iloc[1:]

    ok = (cur == prev + 1) | (cur == 1)

    if not ok.all():
        i = ok[~ok].index[0]
        raise AssertionError(
            f"{csv_path} invalid beat transition at row {i}: "
            f"prev={beat.iloc[i-1]}, current={beat.iloc[i]} "
            f"(allowed: prev+1 or 1)"
        )
