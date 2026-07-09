from pathlib import Path
import importlib
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.annotation_corrections.common import (
    ORIGINAL_DIR,
    PREPROCESSED_DIR,
    VocalShiftTarget,
    channel_data_length,
    iter_midi_tracks,
    measure_ranges_to_ticks,
    midi_path_for_id,
    midi_ticks_per_quarter,
    read_vlq,
    shift_track_notes,
    system_data_length,
)

BLANK_COMMENT_CORRECTION = importlib.import_module(
    "scripts.annotation_corrections.001_shift_blank_comment_vocals"
)
RWC_P003_CORRECTION = importlib.import_module(
    "scripts.annotation_corrections.002_shift_rwc_p003_except_measures_9_17"
)

ORIGINAL_ROOT = REPO_ROOT / ORIGINAL_DIR
PREPROCESSED_ROOT = REPO_ROOT / PREPROCESSED_DIR
TARGETS, BLANK_COMMENT_ROWS, SHIFTED_TARGET_COUNT = (
    BLANK_COMMENT_CORRECTION.load_targets(
        ORIGINAL_ROOT / BLANK_COMMENT_CORRECTION.VOCAL_MAPPING
    )
)
ALL_TARGETS = [*TARGETS, *RWC_P003_CORRECTION.TARGETS]
TARGETS_BY_RWCID: dict[str, list[VocalShiftTarget]] = {}
for target in ALL_TARGETS:
    TARGETS_BY_RWCID.setdefault(target.rwcid, []).append(target)


def expected_shifted_midi_bytes(rwcid: str, targets: list[VocalShiftTarget]) -> bytes:
    source_path = midi_path_for_id(ORIGINAL_ROOT, rwcid)
    midi_data = bytearray(source_path.read_bytes())
    tracks = iter_midi_tracks(bytes(midi_data))
    ticks_per_quarter = midi_ticks_per_quarter(bytes(midi_data))

    for target in sorted(targets, key=lambda item: item.track_index):
        start, end, _ = tracks[target.track_index]
        shifted_track, _ = shift_track_notes(
            bytes(midi_data[start:end]),
            target.semitone_offset,
            measure_ranges_to_ticks(target.preserve_measure_ranges, ticks_per_quarter),
        )
        midi_data[start:end] = shifted_track

    return bytes(midi_data)


def note_on_events(track_data: bytes) -> list[tuple[int, int]]:
    events: list[tuple[int, int]] = []
    index = 0
    absolute_tick = 0
    running_status: int | None = None

    while index < len(track_data):
        delta, index = read_vlq(track_data, index)
        absolute_tick += delta
        status_or_data = track_data[index]

        if status_or_data == 0xFF:
            index += 1
            index += 1
            length, index = read_vlq(track_data, index)
            index += length
            continue

        if status_or_data in (0xF0, 0xF7):
            index += 1
            length, index = read_vlq(track_data, index)
            index += length
            continue

        if status_or_data & 0x80:
            status = status_or_data
            index += 1
            if 0x80 <= status <= 0xEF:
                running_status = status
                data_start = index
                data_length = channel_data_length(status)
            else:
                index += system_data_length(status)
                continue
        else:
            if running_status is None:
                raise ValueError("MIDI running status used before any channel status")
            status = running_status
            data_start = index
            data_length = channel_data_length(status)

        if (status & 0xF0) == 0x90 and track_data[data_start + 1] > 0:
            events.append((absolute_tick, track_data[data_start]))

        index += data_length

    return events


def track_bytes(root: Path, rwcid: str, track_index: int) -> bytes:
    midi_data = midi_path_for_id(root, rwcid).read_bytes()
    start, end, _ = iter_midi_tracks(midi_data)[track_index]
    return midi_data[start:end]


def test_vocal_mapping_target_counts():
    assert BLANK_COMMENT_ROWS == 169
    assert SHIFTED_TARGET_COUNT == 133
    assert len(RWC_P003_CORRECTION.TARGETS) == 1


@pytest.mark.parametrize("rwcid", sorted(TARGETS_BY_RWCID))
def test_midi_files_match_scripted_vocal_shifts(rwcid: str):
    expected = expected_shifted_midi_bytes(rwcid, TARGETS_BY_RWCID[rwcid])
    actual = midi_path_for_id(PREPROCESSED_ROOT, rwcid).read_bytes()
    assert actual == expected


def test_rwc_p003_preserves_measures_9_to_17():
    target = RWC_P003_CORRECTION.TARGETS[0]
    assert target.rwcid == "RWC_P003"
    assert target.preserve_measure_ranges == ((9, 17),)

    original_events = note_on_events(
        track_bytes(ORIGINAL_ROOT, target.rwcid, target.track_index)
    )
    shifted_events = note_on_events(
        track_bytes(PREPROCESSED_ROOT, target.rwcid, target.track_index)
    )
    assert len(shifted_events) == len(original_events)

    preserve_ranges = measure_ranges_to_ticks(
        target.preserve_measure_ranges,
        midi_ticks_per_quarter(
            midi_path_for_id(ORIGINAL_ROOT, target.rwcid).read_bytes()
        ),
    )

    preserved_note_count = 0
    shifted_note_count = 0
    for (original_tick, original_pitch), (shifted_tick, shifted_pitch) in zip(
        original_events, shifted_events
    ):
        assert shifted_tick == original_tick
        should_preserve = any(
            start <= original_tick < end for start, end in preserve_ranges
        )
        if should_preserve:
            assert shifted_pitch == original_pitch
            preserved_note_count += 1
        else:
            assert shifted_pitch == original_pitch - target.semitone_offset
            shifted_note_count += 1

    assert preserved_note_count > 0
    assert shifted_note_count > 0


def test_midi_files_without_shift_targets_match_original():
    shifted_rwcids = set(TARGETS_BY_RWCID)
    for source_path in sorted((ORIGINAL_ROOT / "MIDI_aligned").rglob("*.mid")):
        rwcid = source_path.stem
        if rwcid in shifted_rwcids:
            continue
        output_path = midi_path_for_id(PREPROCESSED_ROOT, rwcid)
        assert output_path.read_bytes() == source_path.read_bytes()
