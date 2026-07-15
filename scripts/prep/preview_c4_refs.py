"""用 D5 預聽 C4 各段內容，協助建立 reference_text 對照。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

from d5_engine import load_model, transcribe_file  # noqa: E402

from config import HALLUC_RAW_DIR  # noqa: E402

C4_SRC = HALLUC_RAW_DIR / "c4_raw"


def sort_key(path: Path) -> int:
    stem = path.stem
    match = re.search(r"\((\d+)\)$", stem)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d+)$", stem)
    if match:
        return int(match.group(1))
    return 1


def main() -> None:
    files = sorted(C4_SRC.glob("*.wav"), key=sort_key)
    if not files:
        raise SystemExit(f"No wav in {C4_SRC}")

    load_model(device="auto")
    print(f"{'#':>3}  {'file':18s}  {'D5_hyp':30s}")
    print("-" * 60)
    for i, path in enumerate(files, 1):
        result = transcribe_file(path, device="auto")
        print(f"{i:3d}  {path.name:18s}  {result.hyp_traditional!r}")


if __name__ == "__main__":
    main()
