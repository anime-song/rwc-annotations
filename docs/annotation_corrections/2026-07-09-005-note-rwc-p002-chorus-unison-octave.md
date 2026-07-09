# 2026-07-09 005 Note RWC P002 Chorus Unison Octave

Status: noted

## Scope

- Annotation type: aligned MIDI CHORUS track content
- MIDI track: 15 CHORUS
- RWCID: `RWC_P002`
- Files:
  - `docs/annotation_corrections/unresolved_annotation_notes.csv`

## Observation

In the CHORUS track, the unison octave passage has three issues in measures 5-7, 9-11, 52-54, 83-85, and 87-89:

- the octave is one octave too low;
- it duplicates the melody;
- it includes an unnecessary upper octave.

## Decision

This is recorded as an unresolved observation, not an annotation correction.
No MIDI or preprocessed annotation file was changed for this note.

## Record

The observation was added to `unresolved_annotation_notes.csv` as one row per measure range with `MIDITrackNo` set to `15`, `MIDITrackName` set to `CHORUS`, and `IssueType` set to `chorus_unison_octave_error`.

## Validation

- `git diff --check` passed.

## Follow-Up

- Review the CHORUS track and corresponding audio in the listed measure ranges before deciding whether to remove, shift, or otherwise rewrite the affected notes.