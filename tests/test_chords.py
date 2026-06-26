from pathlib import Path
import csv
import re

import pandas as pd
import pytest

CHORDS_DIR = Path("01_annotations_preprocessed") / "chords"
CHORD_FILES = sorted(CHORDS_DIR.rglob("*.csv"))  # change to *.lab if needed
EXPECTED_CHORD_HEADER = ["t_start", "t_end", "chord"]
ROOT_PATTERN = r"[A-G](?:#|b)?"
CHORD_LABEL_RE = re.compile(
    rf"^(?:N|{ROOT_PATTERN}(?::[A-Za-z0-9#b*(),]+)?(?:/[#b]?\d+)?)$"
)


def read_chord_rows(csv_path: Path) -> list[list[str]]:
    """Read raw chord CSV rows with the documented semicolon parser.

    Parameters
    ----------
    csv_path
        Chord CSV file to parse.

    Returns
    -------
    list[list[str]]
        Raw rows as parsed by ``csv.reader`` with ``delimiter=";"``.

    Examples
    --------
    A line ``0.0;0.104;N`` is expected to parse as
    ``["0.0", "0.104", "N"]``. A comma-separated line
    ``0.0,0.104,N`` is expected to parse as one field and fail the format
    tests.
    """
    with csv_path.open(newline="") as file:
        return list(csv.reader(file, delimiter=";"))


def is_valid_chord_label(chord_label: str) -> bool:
    """Return whether a chord label matches the annotation label grammar.

    The observed annotations use a compact Harte-style spelling: ``N`` for no
    chord, otherwise a root, optional quality or extension after ``:``, and an
    optional inversion degree after ``/``.

    Parameters
    ----------
    chord_label
        Chord label string to validate.

    Returns
    -------
    bool
        ``True`` if the label matches the accepted annotation grammar.

    Examples
    --------
    ``N``, ``Ab:min``, ``C:sus4(b7)``, ``B:maj(*1,*5)/3``, and ``D:maj/b7``
    are expected to pass. Empty labels, labels with spaces, and labels with an
    invalid root such as ``H:maj`` are expected to fail.
    """
    return CHORD_LABEL_RE.fullmatch(chord_label) is not None


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
    A semicolon-separated file with header ``t_start;t_end;chord`` and at
    least one data row is expected to pass. A comma-separated file or a file
    with columns in a different order is expected to fail.
    """
    rows = read_chord_rows(csv_path)
    assert rows, f"{csv_path} is empty"
    assert (
        rows[0] == EXPECTED_CHORD_HEADER
    ), f"{csv_path} wrong header. Expected {EXPECTED_CHORD_HEADER}, got {rows[0]}"

    malformed_rows = [
        row_number
        for row_number, row in enumerate(rows[1:], start=2)
        if len(row) != len(EXPECTED_CHORD_HEADER)
    ]
    assert not malformed_rows, (
        f"{csv_path} has rows with the wrong number of semicolon-separated "
        f"fields: {malformed_rows}"
    )

    df = pd.read_csv(csv_path, sep=";")

    assert df.shape[1] == 3, f"{csv_path} has {df.shape[1]} columns, expected 3"
    assert list(df.columns) == EXPECTED_CHORD_HEADER, (
        f"{csv_path} wrong header. Expected {EXPECTED_CHORD_HEADER}, "
        f"got {list(df.columns)}"
    )
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


@pytest.mark.parametrize(
    "csv_path", CHORD_FILES, ids=lambda p: str(p.relative_to(CHORDS_DIR))
)
def test_chord_labels_match_annotation_parser(csv_path: Path):
    """Check that chord labels match the grammar used by the annotations.

    Parameters
    ----------
    csv_path
        Chord CSV file under test.

    Examples
    --------
    Labels such as ``N``, ``Gb:maj6``, ``C:sus4(b7)``, and ``B:maj(*1,*5)/3``
    are expected to pass. Empty labels, labels with spaces, and unknown root
    spellings such as ``H:maj`` are expected to fail.
    """
    df = pd.read_csv(csv_path, sep=";")
    chord_labels = df["chord"].astype(str)

    empty_labels = chord_labels[chord_labels.str.len() == 0]
    assert empty_labels.empty, f"{csv_path} has empty chord labels"

    labels_with_whitespace = chord_labels[
        chord_labels != chord_labels.str.strip()
    ].unique()
    assert len(labels_with_whitespace) == 0, (
        f"{csv_path} has chord labels with surrounding whitespace: "
        f"{sorted(labels_with_whitespace)}"
    )

    invalid_labels = sorted(
        {
            chord_label
            for chord_label in chord_labels
            if not is_valid_chord_label(chord_label)
        }
    )
    assert not invalid_labels, (
        f"{csv_path} has chord labels that do not match the parser: "
        f"{invalid_labels}"
    )
