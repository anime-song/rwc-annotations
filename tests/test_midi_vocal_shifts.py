from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.annotation_corrections.apply_all import (
    ORIGINAL_DIR,
    PREPROCESSED_DIR,
    VOCAL_MAPPING,
    VocalShiftTarget,
    iter_midi_tracks,
    load_vocal_shift_targets,
    midi_path_for_id,
    shift_track_notes,
)

ORIGINAL_ROOT = REPO_ROOT / ORIGINAL_DIR
PREPROCESSED_ROOT = REPO_ROOT / PREPROCESSED_DIR
TARGETS, BLANK_COMMENT_ROWS, SHIFTED_TARGET_COUNT = load_vocal_shift_targets(
    ORIGINAL_ROOT / VOCAL_MAPPING
)
TARGETS_BY_RWCID: dict[str, list[VocalShiftTarget]] = {}
for target in TARGETS:
    TARGETS_BY_RWCID.setdefault(target.rwcid, []).append(target)


def expected_shifted_midi_bytes(rwcid: str, targets: list[VocalShiftTarget]) -> bytes:
    source_path = midi_path_for_id(ORIGINAL_ROOT, rwcid)
    midi_data = bytearray(source_path.read_bytes())
    tracks = iter_midi_tracks(bytes(midi_data))

    for target in sorted(targets, key=lambda item: item.track_index):
        start, end, _ = tracks[target.track_index]
        shifted_track, _ = shift_track_notes(
            bytes(midi_data[start:end]), target.semitone_offset
        )
        midi_data[start:end] = shifted_track

    return bytes(midi_data)


def test_vocal_mapping_target_counts():
    assert BLANK_COMMENT_ROWS == 169
    assert SHIFTED_TARGET_COUNT == 133


@pytest.mark.parametrize("rwcid", sorted(TARGETS_BY_RWCID))
def test_midi_files_match_scripted_vocal_shifts(rwcid: str):
    expected = expected_shifted_midi_bytes(rwcid, TARGETS_BY_RWCID[rwcid])
    actual = midi_path_for_id(PREPROCESSED_ROOT, rwcid).read_bytes()
    assert actual == expected


def test_midi_files_without_shift_targets_match_original():
    shifted_rwcids = set(TARGETS_BY_RWCID)
    for source_path in sorted((ORIGINAL_ROOT / "MIDI_aligned").rglob("*.mid")):
        rwcid = source_path.stem
        if rwcid in shifted_rwcids:
            continue
        output_path = midi_path_for_id(PREPROCESSED_ROOT, rwcid)
        assert output_path.read_bytes() == source_path.read_bytes()
