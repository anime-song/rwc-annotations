from __future__ import annotations

import csv
from pathlib import Path

from scripts.annotation_corrections.common import (
    VOCAL_MAPPING,
    VocalShiftTarget,
    apply_vocal_shift_targets,
)


def load_targets(mapping_path: Path) -> tuple[list[VocalShiftTarget], int, int]:
    targets: list[VocalShiftTarget] = []
    blank_comment_rows = 0

    with mapping_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")
        for row in reader:
            if row["comment"].strip():
                continue
            blank_comment_rows += 1
            semitone_offset = int(row["SemitoneOffset"])
            if semitone_offset == 0:
                continue
            targets.append(
                VocalShiftTarget(
                    rwcid=row["RWCID"],
                    track_index=int(row["MIDITrackNo"]),
                    track_name=row["MIDITrackName"],
                    semitone_offset=semitone_offset,
                )
            )

    return targets, blank_comment_rows, len(targets)


def apply(original_root: Path, output_root: Path) -> list[str]:
    targets, blank_comment_rows, shifted_target_count = load_targets(
        original_root / VOCAL_MAPPING
    )
    return [
        f"Blank-comment mapping rows: {blank_comment_rows}",
        f"Nonzero vocal shift targets: {shifted_target_count}",
        *apply_vocal_shift_targets(original_root, output_root, targets),
    ]
