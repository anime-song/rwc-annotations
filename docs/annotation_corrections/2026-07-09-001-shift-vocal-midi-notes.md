# 2026-07-09 001 Shift Vocal MIDI Notes

Status: validated

## Scope

- Annotation type: aligned MIDI vocal tracks
- RWCID: 133 MIDI files listed in `metadata_mapping_vocals.csv`
- Input files:
  - `00_annotations_original/MIDI_aligned/metadata_mapping_vocals.csv`
  - `00_annotations_original/MIDI_aligned/RWC-*/RWC_*.mid`
- Output files:
  - `01_annotations_preprocessed/MIDI_aligned/RWC-*/RWC_*.mid`
- Script:
  - `scripts/annotation_corrections/apply_all.py`

## Problem

`MIDI_aligned/metadata_mapping_vocals.csv` contains vocal track mappings with `SemitoneOffset` values.
Rows without a `comment` are considered actionable global corrections.
For these rows, the specified MIDI vocal track needs to be shifted downward by the semitone offset.

## Evidence

- `metadata_mapping_vocals.csv` defines `RWCID`, `MIDITrackNo`, `MIDITrackName`, `SemitoneOffset`, and `comment`.
- `MIDITrackNo` was checked against MIDI track names before implementation:
  - `RWC_P001` track 5 is `MELODY`.
  - `RWC_G006` track 4 is `Vo Main`.
  - `RWC_R015` track 3 is `Melo`.
- Target row counts from the original mapping:
  - Total rows: 185
  - Rows with blank `comment`: 169
  - Blank-comment rows with nonzero `SemitoneOffset`: 133
  - Nonzero target offsets: 128 tracks at 12 semitones, 5 tracks at 24 semitones

## Decision

For each blank-comment row in `metadata_mapping_vocals.csv`:

- If `SemitoneOffset == 0`, leave the MIDI track unchanged.
- If `SemitoneOffset > 0`, shift the specified MIDI track downward by that number of semitones.
- Rows with non-empty `comment` are not changed in this correction, even when `SemitoneOffset` is nonzero.
- Only MIDI note-number fields are changed:
  - Note Off
  - Note On
  - Polyphonic Key Pressure
- MIDI timing, velocities, controller data, metadata, track order, and chunk lengths are preserved.

## Implementation

The script refreshes `01_annotations_preprocessed/` from `00_annotations_original/`, reads the original vocal mapping CSV, validates that the mapped track name matches the target MIDI track, then rewrites only the target track note numbers.

```powershell
python scripts\annotation_corrections\apply_all.py
```

## Change Summary

- 133 MIDI files were modified under `01_annotations_preprocessed/MIDI_aligned/`.
- `metadata_mapping_vocals.csv` was copied from the original snapshot and left unchanged.
- No beat, chord, melody, or metadata CSV content was intentionally changed.
- The script reported 133 nonzero vocal shift targets:
  - 128 tracks shifted down 12 semitones.
  - 5 tracks shifted down 24 semitones.

Example script output:

```text
Blank-comment mapping rows: 169
Nonzero vocal shift targets: 133
RWC_P001 track 5 'MELODY': down 24 semitones, 986 note events, pitch 75-91 -> 51-67
RWC_G069 track 4 'MELODY': down 24 semitones, 474 note events, pitch 72-89 -> 48-65
RWC_R015 track 3 'Melo': down 24 semitones, 118 note events, pitch 69-81 -> 45-57
```

## Validation

```powershell
uv run black scripts\annotation_corrections\apply_all.py tests\test_midi_vocal_shifts.py
uv run pytest
```

Results:

- `black`: passed; 2 changed-task files left unchanged after formatting.
- `pytest`: passed; 2592 tests passed in 12.00 seconds.
- Added MIDI-specific regression checks:
  - Target count is fixed at 169 blank-comment rows and 133 nonzero shift targets.
  - Each shifted MIDI file matches the expected note-number rewrite from `00_annotations_original/`.
  - MIDI files without shift targets match the original snapshot byte-for-byte.

## Risks And Follow-Up

- This correction assumes `SemitoneOffset` is a downward shift amount, as specified by the user.
- Rows with comments may still contain useful future corrections, but they were intentionally excluded here.
- Existing repository tests only checked MIDI file presence, so `tests/test_midi_vocal_shifts.py` was added to verify that generated MIDI files match the scripted shifts from the original snapshot.
