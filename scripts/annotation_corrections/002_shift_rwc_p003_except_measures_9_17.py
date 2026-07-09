from __future__ import annotations

from pathlib import Path

from scripts.annotation_corrections.common import (
    VocalShiftTarget,
    apply_vocal_shift_targets,
)

TARGETS = [
    VocalShiftTarget(
        rwcid="RWC_P003",
        track_index=4,
        track_name="MELODY",
        semitone_offset=12,
        preserve_measure_ranges=((9, 17),),
    )
]


def apply(original_root: Path, output_root: Path) -> list[str]:
    return [
        f"Comment-specific vocal shift targets: {len(TARGETS)}",
        *apply_vocal_shift_targets(original_root, output_root, TARGETS),
    ]
