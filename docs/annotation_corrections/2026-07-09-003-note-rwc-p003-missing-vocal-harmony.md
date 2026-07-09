# 2026-07-09 003 Note RWC P003 Missing Vocal Harmony

Status: noted

## Scope

- Annotation type: aligned MIDI vocal content
- RWCID: `RWC_P003`
- Files:
  - `docs/annotation_corrections/unresolved_annotation_notes.csv`

## Observation

Starting at measure 61, a vocal harmony is present but not transcribed in the aligned MIDI annotation.

## Decision

This is recorded as an unresolved observation, not an annotation correction.
No MIDI or preprocessed annotation file was changed for this note.

## Record

The observation was added to `unresolved_annotation_notes.csv` as:

```text
RWC_P003;MIDI_aligned;61;;missing_vocal_harmony;unresolved;Vocal harmony is not transcribed from measure 61 onward.
```

## Validation

- `git diff --check` passed.

## Follow-Up

- Review the source audio and MIDI around measure 61 before deciding whether to add or reconstruct the missing harmony.
