from pathlib import Path
import pandas as pd
import pytest
import numpy as np

MELODY_DIR = Path("01_annotations_preprocessed") / "melody"
META_PATH = Path("metadata.csv")

MELODY_FILES = sorted(
    csv_path for csv_path in MELODY_DIR.rglob("*.csv") if csv_path.parent != MELODY_DIR
)
META = pd.read_csv(META_PATH, sep=";") if META_PATH.exists() else None


def test_melody_folder_exists():
    """Check that the preprocessed melody annotation folder exists.

    Examples
    --------
    The repository is expected to contain
    ``01_annotations_preprocessed/melody`` before individual melody files are
    inspected.
    """
    assert MELODY_DIR.exists(), f"melody folder not found: {MELODY_DIR}"


def test_melody_files_exist():
    """Check that at least one per-track melody CSV file is available.

    Examples
    --------
    A repository with files such as ``melody/RWC-P/RWC_P001.csv`` is expected
    to pass. A melody folder containing only metadata mapping tables is
    expected to fail.
    """
    assert MELODY_FILES, f"No melody CSV files found under: {MELODY_DIR}"


def test_metadata_file_exists():
    """Check that the repository-level metadata table exists.

    Examples
    --------
    ``metadata.csv`` is expected at the repository root because melody tests
    and integration tests use it as the track index.
    """
    assert META_PATH.exists(), f"metadata.csv not found: {META_PATH}"


@pytest.mark.parametrize(
    "csv_path",
    MELODY_FILES,
    ids=lambda p: str(p.relative_to(MELODY_DIR)),
)
def test_melody_format_header_and_nonempty(csv_path: Path):
    """Check the basic CSV format for one melody annotation file.

    Parameters
    ----------
    csv_path
        Melody CSV file under test.

    Examples
    --------
    A semicolon-separated file with header ``t;f0`` and at least one data row
    is expected to pass. A mapping CSV with columns such as ``RWCID`` and
    ``MIDITrackNo`` is expected to fail if collected as a melody annotation.
    """
    df = pd.read_csv(csv_path, sep=";")

    assert df.shape[1] == 2, f"{csv_path} has {df.shape[1]} columns, expected 2 (t, f0)"

    expected_header = ["t", "f0"]
    assert (
        list(df.columns) == expected_header
    ), f"{csv_path} wrong header. Expected {expected_header}, got {list(df.columns)}"

    assert len(df) > 0, f"{csv_path} has no data rows"


@pytest.mark.parametrize(
    "csv_path",
    MELODY_FILES,
    ids=lambda p: str(p.relative_to(MELODY_DIR)),
)
def test_melody_time_numeric_nonnegative_and_strictly_increasing(csv_path: Path):
    """Check that melody timestamps are numeric, non-negative, and increasing.

    Parameters
    ----------
    csv_path
        Melody CSV file under test.

    Examples
    --------
    Timestamp values ``[0.00, 0.01, 0.02]`` are expected to pass. Values
    ``[0.00, 0.02, 0.01]`` or non-numeric entries are expected to fail.
    """
    df = pd.read_csv(csv_path, sep=";")

    t = pd.to_numeric(df["t"], errors="coerce")
    assert t.notna().all(), f"{csv_path} has non-numeric t values"
    assert (t >= 0).all(), f"{csv_path} has negative t values"

    dt = t.diff().dropna()
    assert (dt > 0).all(), f"{csv_path} t values are not strictly increasing"


@pytest.mark.parametrize(
    "csv_path",
    MELODY_FILES,
    ids=lambda p: str(p.relative_to(MELODY_DIR)),
)
def test_melody_time_is_10ms_steps(csv_path: Path):
    """Check that melody timestamps start at zero and use 10 ms frame steps.

    Parameters
    ----------
    csv_path
        Melody CSV file under test.

    Examples
    --------
    Timestamp values ``[0.00, 0.01, 0.02]`` are expected to pass. Values
    ``[0.00, 0.02, 0.04]`` are expected to fail because the frame step is
    ``0.02`` seconds instead of ``0.01`` seconds.
    """
    df = pd.read_csv(csv_path, sep=";")

    t = pd.to_numeric(df["t"], errors="coerce")
    assert t.notna().all(), f"{csv_path} has non-numeric time values"

    # check first entry
    assert np.isclose(
        t.iloc[0], 0.0
    ), f"{csv_path} first timestamp is {t.iloc[0]}, expected 0.0"

    # check frame step
    dt = t.diff().dropna()

    assert np.isclose(
        dt, 0.01
    ).all(), f"{csv_path} timestamps are not spaced by 0.01 seconds"


@pytest.mark.parametrize(
    "csv_path",
    MELODY_FILES,
    ids=lambda p: str(p.relative_to(MELODY_DIR)),
)
def test_melody_f0_nonnegative_and_plausible(csv_path: Path):
    """Check that melody frequencies are numeric and in a plausible range.

    Parameters
    ----------
    csv_path
        Melody CSV file under test.

    Examples
    --------
    Frequency values ``[0.0, 220.0, 440.0]`` are expected to pass, where
    ``0.0`` represents an unvoiced frame. Negative values or voiced values
    greater than or equal to ``20000`` Hz are expected to fail.
    """
    df = pd.read_csv(csv_path, sep=";")

    f0 = pd.to_numeric(df["f0"], errors="coerce")
    assert f0.notna().all(), f"{csv_path} has non-numeric f0 values"

    # 0 is allowed for unvoiced frames
    assert (f0 >= 0).all(), f"{csv_path} has f0 values < 0"

    voiced = f0[f0 > 0]
    assert (voiced < 20000).all(), f"{csv_path} has voiced f0 values >= 20000 Hz"


@pytest.mark.parametrize(
    "csv_path",
    MELODY_FILES,
    ids=lambda p: str(p.relative_to(MELODY_DIR)),
)
def test_melody_starts_at_zero(csv_path: Path):
    """Check that each melody time grid starts at exactly zero seconds.

    Parameters
    ----------
    csv_path
        Melody CSV file under test.

    Examples
    --------
    A first timestamp of ``0.0`` is expected to pass. A first timestamp of
    ``0.01`` is expected to fail, even if later frame steps are regular.
    """
    df = pd.read_csv(csv_path, sep=";")

    t = pd.to_numeric(df["t"], errors="coerce")
    assert t.notna().all(), f"{csv_path} has non-numeric time values"

    first_t = float(t.iloc[0])
    assert first_t == 0.0, f"{csv_path} first timestamp is {first_t}, expected 0.0"
