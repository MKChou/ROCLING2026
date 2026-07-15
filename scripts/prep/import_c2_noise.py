"""將環境噪音錄音轉為 16 kHz 單聲道並寫入 data/hallucination/C2/。"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

from config import HALLUC_RAW_DIR  # noqa: E402

DEFAULT_SRC = HALLUC_RAW_DIR / "c2_raw"
OUT_DIR = PROJECT_ROOT / "data" / "hallucination" / "C2"
MANIFEST = PROJECT_ROOT / "data" / "manifests" / "hallucination.csv"
SAMPLE_RATE = 16000


def sort_key(path: Path) -> int:
    """錄製.wav=1, 錄製 (N)=N, 錄製20=20（不依賴中文檔名）。"""
    stem = path.stem
    match = re.search(r"\((\d+)\)$", stem)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d+)$", stem)
    if match:
        return int(match.group(1))
    return 1


def find_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise SystemExit("ffmpeg not found. Install: winget install Gyan.FFmpeg")
    return path


def convert(ffmpeg: str, src: Path, dst: Path) -> None:
    subprocess.run(
        [ffmpeg, "-y", "-i", str(src), "-ar", str(SAMPLE_RATE), "-ac", "1", str(dst)],
        check=True,
        capture_output=True,
    )


def update_manifest() -> None:
    c2_rows = [
        {
            "audio_path": f"../hallucination/C2/noise_{i:02d}.wav",
            "reference_text": "",
            "language": "zh-tw",
            "condition": "C2",
        }
        for i in range(1, 21)
    ]

    with MANIFEST.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    by_cond: dict[str, list[dict]] = {c: [] for c in ("C1", "C2", "C3", "C4", "C5")}
    for row in rows:
        cond = row.get("condition", "")
        if cond in by_cond:
            by_cond[cond].append(row)

    merged = by_cond["C1"] + c2_rows + by_cond["C3"] + by_cond["C4"] + by_cond["C5"]
    with MANIFEST.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["audio_path", "reference_text", "language", "condition"],
        )
        writer.writeheader()
        writer.writerows(merged)

    print(f"Updated {MANIFEST}: C1={len(by_cond['C1'])}, C2=20, "
          f"C3={len(by_cond['C3'])}, C4={len(by_cond['C4'])}, C5={len(by_cond['C5'])}, "
          f"total={len(merged)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", type=Path, default=DEFAULT_SRC)
    parser.add_argument("--no-manifest", action="store_true")
    args = parser.parse_args()

    files = sorted(args.src.glob("*.wav"), key=sort_key)
    if len(files) != 20:
        for i, path in enumerate(files, 1):
            print(f"  {i:2d}. {path.name}")
        raise SystemExit(f"Expected 20 wav files in {args.src}, got {len(files)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ffmpeg = find_ffmpeg()
    print(f"Converting {len(files)} files -> {OUT_DIR}")
    for i, src in enumerate(files, 1):
        dst = OUT_DIR / f"noise_{i:02d}.wav"
        convert(ffmpeg, src, dst)
        print(f"  {src.name} -> {dst.name}")

    if not args.no_manifest:
        update_manifest()
    print("Done.")


if __name__ == "__main__":
    main()
