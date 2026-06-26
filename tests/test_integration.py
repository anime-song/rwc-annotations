from collections import Counter
from pathlib import Path

import pandas as pd
import pytest

ANNOTATIONS_DIR = Path("01_annotations_preprocessed")
METADATA_PATH = Path("metadata.csv")

METADATA = pd.read_csv(METADATA_PATH, sep=";")

ANNOTATION_SPECS = {
    "beats": {
        "extension": ".csv",
        "end_column": "t",
        "expected_ids": lambda metadata: set(metadata["RWCID"]),
    },
    "chords": {
        "extension": ".csv",
        "end_column": "t_end",
        "expected_ids": lambda metadata: set(
            metadata.loc[metadata["CollID"] == "P", "RWCID"]
        ),
    },
    "melody": {
        "extension": ".csv",
        "end_column": "t",
        "expected_ids": lambda metadata: set(
            metadata.loc[metadata["CollID"] == "P", "RWCID"]
        ),
    },
    "MIDI_aligned": {
        "extension": ".mid",
        "expected_ids": lambda metadata: set(metadata["RWCID"]),
    },
}

CSV_ANNOTATION_KINDS = ("beats", "chords", "melody")
DURATION_END_TOLERANCE_SECONDS = 5.0
CROSS_ANNOTATION_END_TOLERANCE_SECONDS = 20.0


def annotation_files(kind: str) -> list[Path]:
    """Return annotation files for one annotation family.

    Parameters
    ----------
    kind
        Annotation family key from ``ANNOTATION_SPECS``.

    Returns
    -------
    list[pathlib.Path]
        Sorted annotation files below the collection subdirectories.

    Examples
    --------
    ``annotation_files("beats")`` is expected to return paths such as
    ``01_annotations_preprocessed/beats/RWC-P/RWC_P001.csv`` and to exclude
    CSV files placed directly in the annotation root, such as mapping tables.
    """
    spec = ANNOTATION_SPECS[kind]
    annotation_dir = ANNOTATIONS_DIR / kind
    return sorted(
        path
        for path in annotation_dir.rglob(f"*{spec['extension']}")
        if path.parent != annotation_dir
    )


def annotation_end_time(kind: str, path: Path) -> float:
    """Read the final annotated time from one CSV annotation file.

    Parameters
    ----------
    kind
        Annotation family key from ``ANNOTATION_SPECS``.
    path
        CSV annotation file to inspect.

    Returns
    -------
    float
        Maximum value in the annotation's configured end-time column.

    Examples
    --------
    A beat file with ``t`` values ``[0.50, 1.00, 1.50]`` is expected to
    return ``1.50``. A chord file uses ``t_end`` instead, so the final chord
    boundary is the expected return value.
    """
    df = pd.read_csv(path, sep=";")
    values = pd.to_numeric(df[ANNOTATION_SPECS[kind]["end_column"]], errors="coerce")
    assert values.notna().all(), f"{path} has non-numeric end-time values"
    return float(values.max())


def test_metadata_integrity():
    """Check that ``metadata.csv`` is internally consistent.

    The metadata table is the reference index for all annotation files, so it
    must have stable identifiers, valid collection labels, and usable timing
    fields.

    Examples
    --------
    ``RWC_P001`` is expected to have ``CollID == "P"``. For each row,
    ``0 <= audio_start < audio_end <= duration`` is expected to hold.
    """
    required_columns = {
        "RWCID",
        "CollID",
        "CDNo",
        "TrackNo",
        "Title",
        "audio_start",
        "audio_end",
        "duration",
    }
    missing_columns = required_columns - set(METADATA.columns)
    assert not missing_columns, f"metadata.csv is missing columns: {missing_columns}"

    assert METADATA["RWCID"].is_unique, "metadata.csv has duplicate RWCID values"
    assert METADATA["RWCID"].str.match(r"^RWC_[CGJPR]\d{3}[A-Z]?$").all()

    expected_coll_id = METADATA["RWCID"].str.extract(r"^RWC_([CGJPR])", expand=False)
    assert (METADATA["CollID"] == expected_coll_id).all()

    audio_start = pd.to_numeric(METADATA["audio_start"], errors="coerce")
    audio_end = pd.to_numeric(METADATA["audio_end"], errors="coerce")
    duration = pd.to_numeric(METADATA["duration"], errors="coerce")

    assert audio_start.notna().all(), "metadata.csv has non-numeric audio_start values"
    assert audio_end.notna().all(), "metadata.csv has non-numeric audio_end values"
    assert duration.notna().all(), "metadata.csv has non-numeric duration values"
    assert (audio_start >= 0).all(), "metadata.csv has negative audio_start values"
    assert (audio_end > audio_start).all(), "metadata.csv has audio_end <= audio_start"
    assert (duration >= audio_end).all(), "metadata.csv has audio_end > duration"


@pytest.mark.parametrize("kind", sorted(ANNOTATION_SPECS))
def test_annotation_filenames_match_metadata(kind: str):
    """Check that annotation filenames match the metadata index.

    Each annotation filename stem is treated as an ``RWCID``. Beat and aligned
    MIDI annotations are expected for all tracks, while chords and melody are
    expected for the RWC-P subset currently present in this repository.

    Parameters
    ----------
    kind
        Annotation family under test.

    Examples
    --------
    ``01_annotations_preprocessed/beats/RWC-P/RWC_P001.csv`` is expected
    because ``RWC_P001`` appears in ``metadata.csv`` and belongs in the
    ``RWC-P`` subdirectory. ``RWC_X001.csv`` would fail because its stem is not
    a known metadata identifier.
    """
    metadata_ids = set(METADATA["RWCID"])
    expected_ids = ANNOTATION_SPECS[kind]["expected_ids"](METADATA)
    paths = annotation_files(kind)
    actual_ids = [path.stem for path in paths]

    duplicate_ids = sorted(
        annotation_id
        for annotation_id, count in Counter(actual_ids).items()
        if count > 1
    )
    assert not duplicate_ids, f"{kind} has duplicate annotation files: {duplicate_ids}"

    unknown_ids = sorted(set(actual_ids) - metadata_ids)
    assert (
        not unknown_ids
    ), f"{kind} has files not listed in metadata.csv: {unknown_ids}"

    missing_ids = sorted(expected_ids - set(actual_ids))
    assert not missing_ids, f"{kind} is missing expected files: {missing_ids}"

    wrong_subdirs = [
        path
        for path in paths
        if path.parent.name != f"RWC-{path.stem.split('_')[1][0]}"
    ]
    assert (
        not wrong_subdirs
    ), f"{kind} files are in the wrong collection folder: {wrong_subdirs}"


def test_aligned_midi_available_for_every_metadata_rwcid():
    """Check that each metadata track has an aligned MIDI file.

    The aligned MIDI collection is expected to cover the full repository track
    index, not only a subset such as RWC-P.

    Examples
    --------
    If ``metadata.csv`` contains ``RWC_P001`` and ``RWC_C001``, files named
    ``RWC_P001.mid`` and ``RWC_C001.mid`` are expected under
    ``01_annotations_preprocessed/MIDI_aligned``. Missing either file is
    expected to fail this test.
    """
    metadata_ids = set(METADATA["RWCID"])
    midi_ids = {path.stem for path in annotation_files("MIDI_aligned")}

    missing_ids = sorted(metadata_ids - midi_ids)
    assert not missing_ids, (
        f"MIDI_aligned is missing files for metadata RWCID values: {missing_ids}"
    )


@pytest.mark.parametrize("kind", CSV_ANNOTATION_KINDS)
def test_annotation_durations_are_consistent_with_metadata(kind: str):
    """Check that annotation end times do not exceed metadata durations.

    This is a broad integration check, not a demand that annotation boundaries
    equal the audio duration exactly. A small tolerance allows for frame grids,
    trailing musical events, and conversion precision.

    Parameters
    ----------
    kind
        CSV annotation family under test.

    Examples
    --------
    If ``metadata.csv`` lists ``duration == 100.0`` and the tolerance is
    ``5.0`` seconds, an annotation ending at ``104.0`` is expected to pass.
    An annotation ending at ``106.0`` is expected to fail.
    """
    metadata_by_id = METADATA.set_index("RWCID")

    for path in annotation_files(kind):
        annotation_id = path.stem
        end_time = annotation_end_time(kind, path)
        duration = float(metadata_by_id.loc[annotation_id, "duration"])

        assert end_time <= duration + DURATION_END_TOLERANCE_SECONDS, (
            f"{path} ends at {end_time:.3f}s, beyond metadata duration "
            f"{duration:.3f}s + {DURATION_END_TOLERANCE_SECONDS:.1f}s"
        )


def test_annotation_end_times_agree_across_annotation_types():
    """Check that annotation families for the same track end in the same region.

    Tracks with multiple CSV annotation types should have broadly compatible
    timelines. The tolerance is intentionally wider than the metadata-duration
    check because beats, chords, and melody can encode different musical
    endpoints.

    Examples
    --------
    For one track, end times ``{"beats": 98.0, "chords": 100.0,
    "melody": 99.5}`` are expected to pass with a ``20.0`` second tolerance.
    End times ``{"beats": 70.0, "melody": 100.0}`` are expected to fail.
    """
    end_times_by_id: dict[str, dict[str, float]] = {}

    for kind in CSV_ANNOTATION_KINDS:
        for path in annotation_files(kind):
            end_times_by_id.setdefault(path.stem, {})[kind] = annotation_end_time(
                kind, path
            )

    for annotation_id, end_times in end_times_by_id.items():
        if len(end_times) < 2:
            continue

        earliest_end = min(end_times.values())
        latest_end = max(end_times.values())
        assert latest_end - earliest_end <= CROSS_ANNOTATION_END_TOLERANCE_SECONDS, (
            f"{annotation_id} annotation end times disagree by "
            f"{latest_end - earliest_end:.3f}s: {end_times}"
        )
