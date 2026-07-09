# Annotation Correction Records

このディレクトリは、RWCアノテーション修正作業のMarkdown記録を保存する場所です。
アノテーションデータの変更は、必ず対応するMarkdown記録と再現スクリプトを持たせます。

## ファイル命名

- `000-baseline.md`
  - `00_annotations_original/` を作成したときの記録。
- `YYYY-MM-DD-NNN-short-title.md`
  - 個別修正の記録。
  - 例: `2026-07-09-001-fix-rwc-p001-beat-offset.md`

## 記録テンプレート

````markdown
# YYYY-MM-DD NNN Short Title

Status: draft | applied | validated | needs-review

## Scope

- Annotation type:
- RWCID:
- Input files:
- Output files:
- Script:

## Problem

Describe the suspected annotation issue.

## Evidence

List the evidence used to decide the correction.
Include commands, visual checks, audio checks, cross-annotation comparisons, or references.

## Decision

Describe the exact correction policy.
If the decision is uncertain, mark the record as `needs-review` and do not apply the change yet.

## Implementation

Record the script path and the commands used.

```bash
uv run python scripts/annotation_corrections/apply_all.py
```

## Change Summary

Summarize changed files and the important before/after values.
Do not paste large generated files; summarize the meaningful differences.

## Validation

Record validation commands and results.

```bash
uv run pytest
```

## Risks And Follow-Up

List remaining uncertainty, review needs, or future cleanup.
````

## Baseline Record Template

````markdown
# Baseline Snapshot

Status: validated

## Source

- Source directory: `01_annotations_preprocessed/`
- Baseline directory: `00_annotations_original/`
- Created on:
- Created by:

## Commands

```bash
# Record the exact copy and verification commands here.
```

## Verification

- `git status --short` before snapshot:
- File count comparison:
- Spot checks:
- Notes:
````
