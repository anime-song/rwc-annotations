# 2026-07-09 007 Note RWC P005 Vocal Harmony Issues

Status: noted

## Scope

- Annotation type: aligned MIDI vocal and CHORUS content
- RWCID: `RWC_P005`
- MIDI tracks:
  - 4 MELODY
  - 5 CHO
- Files:
  - `docs/annotation_corrections/unresolved_annotation_notes.csv`

## Observation

`RWC_P005` has multiple unresolved vocal harmony annotation issues across the MELODY and CHORUS tracks.

CHORUS/CHO issues:

- Measures 16-17 and 54-55: CHORUS is one octave too low, and the harmony one octave above the original track around F4 is not transcribed.
- Measures 18-19: CHORUS contains harmony that should not exist.
- Measures 20 and 58: CHORUS is one octave too low, and the harmony one octave above the original track around F4 is not transcribed.
- Measures 21 and 59: two CHORUS harmonies are present, but the lower harmony is one octave too low.
- Measures 22-27 and 60-65: CHORUS contains harmony that should not exist.
- Measure 51: CHORUS harmony is not transcribed.

MELODY issues:

- Measures 30-31, 34-35, 38-39, 42-43, 68-69, 72-73, 76-77, 80-81, 104-105, 108-109, 112-113, and 116-117: lower harmony part is written in the MELODY track.
- Measures 36-37, 74-75, and 110-111: MELODY is one octave too low relative to the corrected MELODY reference.
- Measures 97-98 and 101-102: MELODY contains harmony, and the harmony does not actually exist.

Missing harmony without a known target track:

- Measures 32-33, 40-41, 70-71, 78-79, 106-107, and 114-115: harmony is not transcribed.

## Decision

This is recorded as an unresolved observation, not an annotation correction.
No MIDI or preprocessed annotation file was changed for this note.

## Record

The observations were added to `unresolved_annotation_notes.csv` as one row per measure range.
Track-specific rows use `MIDITrackNo`/`MIDITrackName`; missing harmony rows without a clear target track leave those fields blank.

## Validation

- `git diff --check` passed.

## Follow-Up

- Review the listed ranges against audio before deciding whether to remove spurious harmony notes, shift octave errors, move lower harmony out of MELODY, or add missing harmony notes.