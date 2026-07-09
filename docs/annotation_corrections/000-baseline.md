# Baseline Snapshot

Status: validated

## Source

- Source directory: `01_annotations_preprocessed/`
- Baseline directory: `00_annotations_original/`
- Created on: 2026-07-09
- Created by: Codex

## Commands

```powershell
git status --short
Copy-Item -LiteralPath 01_annotations_preprocessed -Destination 00_annotations_original -Recurse
(Get-ChildItem -Recurse -File 01_annotations_preprocessed | Measure-Object).Count
(Get-ChildItem -Recurse -File 00_annotations_original | Measure-Object).Count
```

## Verification

- `git status --short` before snapshot:
  - `M .gitignore`
  - `?? docs/`
- File count comparison:
  - `01_annotations_preprocessed/`: 863 files
  - `00_annotations_original/`: 863 files
- Spot checks:
  - `00_annotations_original/` contains `beats/`, `chords/`, `melody/`, and `MIDI_aligned/`.
  - `00_annotations_original/MIDI_aligned/metadata_mapping_vocals.csv` is present.
- Notes:
  - The existing `.gitignore` modification was not made as part of the baseline copy and was left untouched.
