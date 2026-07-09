# 2026-07-09 004 Note RWC P001 Missing Vocal Harmony

Status: noted

## Scope

- Annotation type: aligned MIDI vocal content
- RWCID: `RWC_P001`
- Files:
  - `docs/annotation_corrections/unresolved_annotation_notes.csv`

## Observation

Starting at measure 6, a vocal harmony is present but not transcribed in the aligned MIDI annotation.

## Decision

This is recorded as an unresolved observation, not an annotation correction.
No MIDI or preprocessed annotation file was changed for this note.

## Record

The observation was added to `unresolved_annotation_notes.csv` as:

```text
RWC_P001;MIDI_aligned;;;6;;missing_vocal_harmony;unresolved;Vocal harmony is not transcribed from measure 6 onward.
```

## Validation

- `git diff --check` passed.

## Follow-Up

- Review the source audio and MIDI around measure 6 before deciding whether to add or reconstruct the missing harmony.