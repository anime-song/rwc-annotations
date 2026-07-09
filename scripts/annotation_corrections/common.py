from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ORIGINAL_DIR = Path("00_annotations_original")
PREPROCESSED_DIR = Path("01_annotations_preprocessed")
VOCAL_MAPPING = Path("MIDI_aligned") / "metadata_mapping_vocals.csv"


@dataclass(frozen=True)
class VocalShiftTarget:
    rwcid: str
    track_index: int
    track_name: str
    semitone_offset: int
    preserve_measure_ranges: tuple[tuple[int, int], ...] = ()


@dataclass(frozen=True)
class TrackShiftStats:
    shifted_events: int
    preserved_events: int
    min_pitch_before: int | None
    max_pitch_before: int | None
    min_pitch_after: int | None
    max_pitch_after: int | None


def rwc_collection_dir(rwcid: str) -> str:
    return f"RWC-{rwcid.split('_', maxsplit=1)[1][0]}"


def midi_path_for_id(root: Path, rwcid: str) -> Path:
    return root / "MIDI_aligned" / rwc_collection_dir(rwcid) / f"{rwcid}.mid"


def read_vlq(data: bytes | bytearray, index: int) -> tuple[int, int]:
    value = 0
    while True:
        if index >= len(data):
            raise ValueError(
                "Unexpected end of MIDI data while reading variable length value"
            )
        byte = data[index]
        index += 1
        value = (value << 7) | (byte & 0x7F)
        if not byte & 0x80:
            return value, index


def channel_data_length(status: int) -> int:
    event_type = status & 0xF0
    if event_type in (0xC0, 0xD0):
        return 1
    if 0x80 <= event_type <= 0xE0:
        return 2
    raise ValueError(f"Unsupported running status byte: 0x{status:02X}")


def system_data_length(status: int) -> int:
    if status in (0xF1, 0xF3):
        return 1
    if status == 0xF2:
        return 2
    if status in (0xF6, 0xF8, 0xF9, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE):
        return 0
    raise ValueError(f"Unsupported MIDI system status byte: 0x{status:02X}")


def iter_midi_tracks(data: bytes) -> list[tuple[int, int, int]]:
    if data[:4] != b"MThd":
        raise ValueError("Missing MThd header")
    header_length = int.from_bytes(data[4:8], "big")
    track_count = int.from_bytes(data[10:12], "big")
    index = 8 + header_length

    tracks = []
    for track_index in range(track_count):
        if data[index : index + 4] != b"MTrk":
            raise ValueError(f"Missing MTrk header for track {track_index}")
        length = int.from_bytes(data[index + 4 : index + 8], "big")
        start = index + 8
        end = start + length
        if end > len(data):
            raise ValueError(f"Track {track_index} extends beyond end of file")
        tracks.append((start, end, length))
        index = end

    return tracks


def midi_ticks_per_quarter(data: bytes) -> int:
    division = int.from_bytes(data[12:14], "big")
    if division & 0x8000:
        raise ValueError("SMPTE MIDI time divisions are not supported")
    return division


def extract_track_names(track_data: bytes | bytearray) -> list[str]:
    names: list[str] = []
    index = 0
    running_status: int | None = None

    while index < len(track_data):
        _, index = read_vlq(track_data, index)
        status_or_data = track_data[index]

        if status_or_data == 0xFF:
            index += 1
            meta_type = track_data[index]
            index += 1
            length, index = read_vlq(track_data, index)
            payload = bytes(track_data[index : index + length])
            index += length
            if meta_type in (0x03, 0x04):
                names.append(payload.decode("latin1", errors="replace"))
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
                index += channel_data_length(status)
            else:
                index += system_data_length(status)
            continue

        if running_status is None:
            raise ValueError("MIDI running status used before any channel status")
        index += channel_data_length(running_status)

    return names


def shift_track_notes(
    track_data: bytes,
    semitone_offset: int,
    preserve_tick_ranges: tuple[tuple[int, int], ...] = (),
) -> tuple[bytes, TrackShiftStats]:
    shifted = bytearray(track_data)
    index = 0
    absolute_tick = 0
    running_status: int | None = None
    shifted_events = 0
    preserved_events = 0
    pitches_before: list[int] = []
    pitches_after: list[int] = []
    active_shifted_notes: dict[tuple[int, int], int] = {}

    def should_preserve(tick: int) -> bool:
        return any(start <= tick < end for start, end in preserve_tick_ranges)

    def active_key(status: int, pitch: int) -> tuple[int, int]:
        return status & 0x0F, pitch

    def activate_shifted(status: int, pitch: int) -> None:
        key = active_key(status, pitch)
        active_shifted_notes[key] = active_shifted_notes.get(key, 0) + 1

    def deactivate_shifted(status: int, pitch: int) -> bool:
        key = active_key(status, pitch)
        count = active_shifted_notes.get(key, 0)
        if count <= 0:
            return False
        if count == 1:
            del active_shifted_notes[key]
        else:
            active_shifted_notes[key] = count - 1
        return True

    while index < len(shifted):
        delta, index = read_vlq(shifted, index)
        absolute_tick += delta
        status_or_data = shifted[index]

        if status_or_data == 0xFF:
            index += 1
            index += 1
            length, index = read_vlq(shifted, index)
            index += length
            continue

        if status_or_data in (0xF0, 0xF7):
            index += 1
            length, index = read_vlq(shifted, index)
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

        event_type = status & 0xF0
        if event_type in (0x80, 0x90, 0xA0):
            before = shifted[data_start]
            velocity = shifted[data_start + 1] if data_length == 2 else 0
            shift_event = False

            if event_type == 0x90 and velocity > 0:
                shift_event = not should_preserve(absolute_tick)
                if shift_event:
                    activate_shifted(status, before)
            elif event_type == 0x80 or (event_type == 0x90 and velocity == 0):
                shift_event = deactivate_shifted(status, before)
            elif event_type == 0xA0:
                shift_event = not should_preserve(absolute_tick)

            if shift_event:
                after = before - semitone_offset
                if not 0 <= after <= 127:
                    raise ValueError(
                        f"Pitch shift out of MIDI range: "
                        f"{before} - {semitone_offset} = {after}"
                    )
                shifted[data_start] = after
                shifted_events += 1
                pitches_before.append(before)
                pitches_after.append(after)
            else:
                preserved_events += 1

        index += data_length

    stats = TrackShiftStats(
        shifted_events=shifted_events,
        preserved_events=preserved_events,
        min_pitch_before=min(pitches_before) if pitches_before else None,
        max_pitch_before=max(pitches_before) if pitches_before else None,
        min_pitch_after=min(pitches_after) if pitches_after else None,
        max_pitch_after=max(pitches_after) if pitches_after else None,
    )
    return bytes(shifted), stats


def measure_ranges_to_ticks(
    measure_ranges: tuple[tuple[int, int], ...], ticks_per_quarter: int
) -> tuple[tuple[int, int], ...]:
    ticks_per_measure = ticks_per_quarter * 4
    return tuple(
        ((start_measure - 1) * ticks_per_measure, end_measure * ticks_per_measure)
        for start_measure, end_measure in measure_ranges
    )


def apply_vocal_shift_targets(
    original_root: Path, output_root: Path, targets: list[VocalShiftTarget]
) -> list[str]:
    messages: list[str] = []
    targets_by_rwcid: dict[str, list[VocalShiftTarget]] = {}
    for target in targets:
        targets_by_rwcid.setdefault(target.rwcid, []).append(target)

    for rwcid in sorted(targets_by_rwcid):
        destination_path = midi_path_for_id(output_root, rwcid)
        midi_data = destination_path.read_bytes()
        tracks = iter_midi_tracks(midi_data)
        ticks_per_quarter = midi_ticks_per_quarter(midi_data)
        updated_data = bytearray(midi_data)

        for target in sorted(
            targets_by_rwcid[rwcid], key=lambda item: item.track_index
        ):
            if target.track_index >= len(tracks):
                raise ValueError(
                    f"{rwcid} target track {target.track_index} does not exist "
                    f"({len(tracks)} tracks available)"
                )

            start, end, _ = tracks[target.track_index]
            track_data = bytes(updated_data[start:end])
            names = [name.strip() for name in extract_track_names(track_data)]
            if target.track_name.strip() not in names:
                raise ValueError(
                    f"{rwcid} track {target.track_index} name mismatch: "
                    f"expected {target.track_name!r}, found {names}"
                )

            preserve_tick_ranges = measure_ranges_to_ticks(
                target.preserve_measure_ranges, ticks_per_quarter
            )
            shifted_track, stats = shift_track_notes(
                track_data, target.semitone_offset, preserve_tick_ranges
            )
            updated_data[start:end] = shifted_track
            preserve_message = (
                f", preserved {stats.preserved_events} note events in "
                f"measures {target.preserve_measure_ranges}"
                if target.preserve_measure_ranges
                else ""
            )
            messages.append(
                f"{rwcid} track {target.track_index} {target.track_name!r}: "
                f"down {target.semitone_offset} semitones, "
                f"{stats.shifted_events} note events, "
                f"pitch {stats.min_pitch_before}-{stats.max_pitch_before} -> "
                f"{stats.min_pitch_after}-{stats.max_pitch_after}"
                f"{preserve_message}"
            )

        destination_path.write_bytes(updated_data)

    return messages
