"""匯入 C3/C4 錄音：轉 16 kHz mono、寫入 data/hallucination/、更新 manifest。"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

from config import HALLUC_RAW_DIR, PROJECT_ROOT  # noqa: E402

C3_SRC = HALLUC_RAW_DIR / "c3_raw"
C4_SRC = HALLUC_RAW_DIR / "c4_raw"
C4_REFS_CSV = C4_SRC / "c4_refs.csv"
C3_OUT = PROJECT_ROOT / "data" / "hallucination" / "C3"
C4_OUT = PROJECT_ROOT / "data" / "hallucination" / "C4"
MANIFEST = PROJECT_ROOT / "data" / "manifests" / "hallucination.csv"
SAMPLE_RATE = 16000

C3_REFS = [
    "好", "不要", "是", "對", "可以", "不行", "嗯好", "好喔", "不要了", "是的",
    "沒有", "有", "好嗎", "不是", "對啊", "好啊", "不要啊", "可以啊", "嗯", "喔",
]


def sort_key(path: Path) -> int:
    stem = path.stem
    match = re.search(r"\((\d+)\)$", stem)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d+)$", stem)
    if match:
        return int(match.group(1))
    return 1


def normalize_ref(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"\s+", "", text)
    return text


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


def load_c4_refs(path: Path) -> list[str]:
    """讀 c4_refs.csv；支援 reference_text 或 note 欄。"""
    refs: dict[int, str] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if not row or not row[0].strip().isdigit():
                continue
            idx = int(row[0].strip())
            ref_raw = ""
            if len(row) > 1 and row[1].strip():
                ref_raw = row[1].strip()
            elif len(row) > 2 and row[2].strip():
                ref_raw = row[2].strip()
            refs[idx] = normalize_ref(ref_raw)

    missing = [i for i in range(1, 21) if i not in refs or not refs[i]]
    if missing:
        raise SystemExit(f"Missing C4 reference_text for index: {missing}")
    return [refs[i] for i in range(1, 21)]


def import_folder(
    ffmpeg: str,
    src_dir: Path,
    out_dir: Path,
    prefix: str,
    refs: list[str],
) -> list[dict]:
    files = sorted(src_dir.glob("*.wav"), key=sort_key)
    if len(files) != 20:
        raise SystemExit(f"Expected 20 wav in {src_dir}, got {len(files)}")
    if len(refs) != 20:
        raise SystemExit(f"Expected 20 references, got {len(refs)}")

    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    condition = "C3" if prefix == "short" else "C4"
    print(f"Import {src_dir.name} -> {out_dir.name}")
    for i, (src, ref) in enumerate(zip(files, refs), 1):
        dst = out_dir / f"{prefix}_{i:02d}.wav"
        convert(ffmpeg, src, dst)
        rows.append({
            "audio_path": f"../hallucination/{condition}/{dst.name}",
            "reference_text": ref,
            "language": "zh-tw",
            "condition": condition,
        })
        print(f"  {src.name} -> {dst.name}  ref={ref!r}")
    return rows


def update_manifest(c3_rows: list[dict], c4_rows: list[dict]) -> None:
    with MANIFEST.open(encoding="utf-8-sig", newline="") as f:
        existing = list(csv.DictReader(f))

    by_cond: dict[str, list[dict]] = {c: [] for c in ("C1", "C2", "C3", "C4", "C5")}
    for row in existing:
        cond = row.get("condition", "")
        if cond in by_cond and cond not in ("C3", "C4"):
            by_cond[cond].append(row)

    merged = (
        by_cond["C1"] + by_cond["C2"] + c3_rows + c4_rows + by_cond["C5"]
    )
    with MANIFEST.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["audio_path", "reference_text", "language", "condition"],
        )
        writer.writeheader()
        writer.writerows(merged)

    counts = {c: sum(1 for r in merged if r["condition"] == c) for c in by_cond}
    print(
        f"Updated {MANIFEST}: "
        + ", ".join(f"{k}={v}" for k, v in counts.items())
        + f", total={len(merged)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--c3-src", type=Path, default=C3_SRC)
    parser.add_argument("--c4-src", type=Path, default=C4_SRC)
    parser.add_argument("--c4-refs", type=Path, default=C4_REFS_CSV)
    args = parser.parse_args()

    ffmpeg = find_ffmpeg()
    c4_refs = load_c4_refs(args.c4_refs)
    c3_rows = import_folder(ffmpeg, args.c3_src, C3_OUT, "short", C3_REFS)
    c4_rows = import_folder(ffmpeg, args.c4_src, C4_OUT, "hesitation", c4_refs)
    update_manifest(c3_rows, c4_rows)
    print("Done.")


if __name__ == "__main__":
    main()
