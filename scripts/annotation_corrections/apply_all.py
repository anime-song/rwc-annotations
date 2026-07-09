from __future__ import annotations

import argparse
import importlib
import shutil
import sys
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.annotation_corrections.common import ORIGINAL_DIR, PREPROCESSED_DIR

CORRECTION_MODULES = (
    "scripts.annotation_corrections.001_shift_blank_comment_vocals",
    "scripts.annotation_corrections.002_shift_rwc_p003_except_measures_9_17",
)


def repo_root() -> Path:
    return REPO_ROOT


def refresh_preprocessed_from_original(original_root: Path, output_root: Path) -> None:
    if not original_root.exists():
        raise FileNotFoundError(
            f"Original annotation directory not found: {original_root}"
        )
    output_root.mkdir(parents=True, exist_ok=True)

    for source in sorted(original_root.rglob("*")):
        relative_path = source.relative_to(original_root)
        destination = output_root / relative_path
        if source.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)


def load_correction(module_name: str) -> Callable[[Path, Path], list[str]]:
    module = importlib.import_module(module_name)
    return module.apply


def apply_all(root: Path) -> list[str]:
    original_root = root / ORIGINAL_DIR
    output_root = root / PREPROCESSED_DIR
    refresh_preprocessed_from_original(original_root, output_root)

    messages: list[str] = []
    for module_name in CORRECTION_MODULES:
        messages.append(f"Applying {module_name}")
        messages.extend(load_correction(module_name)(original_root, output_root))

    return messages


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenerate preprocessed annotations and apply scripted corrections."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=repo_root(),
        help="Repository root. Defaults to the root containing this script.",
    )
    args = parser.parse_args()

    for message in apply_all(args.repo_root.resolve()):
        print(message)


if __name__ == "__main__":
    main()
