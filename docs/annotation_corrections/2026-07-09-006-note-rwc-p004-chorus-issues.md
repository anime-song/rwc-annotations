# 2026-07-09 006 Note RWC P004 Chorus Issues

Status: noted

## Scope

- Annotation type: aligned MIDI CHORUS track content
- RWCID: `RWC_P004`
- MIDI track: 16 CHORUS
- Files:
  - `docs/annotation_corrections/unresolved_annotation_notes.csv`

## Observation

The CHORUS track has several unresolved annotation issues:

- Measures 9-14, 37-42, 65-70, and 77-82 duplicate the melody.
- Measures 16-17 are one octave above, but it is difficult to determine whether the vocal or chorus should be higher.
- Measures 44-45 and 72-73 are missing the CHORUS harmony transcription.

## Decision

This is recorded as an unresolved observation, not an annotation correction.
No MIDI or preprocessed annotation file was changed for this note.

## Record

The observations were added to `unresolved_annotation_notes.csv` as one row per measure range with `MIDITrackNo` set to `16` and `MIDITrackName` set to `CHORUS`.

Issue types used:

- `chorus_duplicates_melody`
- `chorus_octave_ambiguous`
- `missing_chorus_harmony`

## Validation

- `git diff --check` passed.

## Follow-Up

- Review the CHORUS track and corresponding audio in the listed measure ranges before deciding whether to remove duplicates, shift octaves, or add missing harmony notes.