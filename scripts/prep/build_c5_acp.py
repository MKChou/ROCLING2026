"""建立 ACP-DRP C5 男女真人關鍵詞句資料集。

女生來源檔依 Windows 錄音機命名：
  錄製.wav -> 第 1 句
  錄製 (2).wav -> 第 2 句
  ...
  錄製 (50).wav -> 第 50 句
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
SCRIPT_PATH = DATA_DIR / "recording_scripts" / "acp_recording_script.txt"
MALE_SOURCE = DATA_DIR / "legacy_pilot" / "acp_wavs"
OUTPUT_DIR = DATA_DIR / "acp_drp" / "C5_acp"
MANIFEST_PATH = DATA_DIR / "manifests" / "c5_acp.csv"
SAMPLE_RATE = 16_000
FEMALE_SOURCE_DEFAULT = DATA_DIR / "recordings" / "c5_raw" / "female_classmateB"


def parse_script(path: Path) -> dict[int, str]:
    texts: dict[int, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^(\d{3})\s+(.+?)\s*$", line.strip())
        if match:
            texts[int(match.group(1))] = match.group(2).strip()
    return texts


def recording_number(stem: str) -> int | None:
    if stem == "錄製":
        return 1
    match = re.fullmatch(r"錄製 \((\d+)\)", stem)
    return int(match.group(1)) if match else None


def convert(ffmpeg: str, source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(destination),
        ],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build ACP-DRP C5 male/female set")
    parser.add_argument("--female-source", type=Path, default=FEMALE_SOURCE_DEFAULT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--manifest-out", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg not found")

    texts = parse_script(SCRIPT_PATH)
    if sorted(texts) != list(range(1, 51)):
        raise SystemExit(f"Expected script sentences 1-50; got {sorted(texts)}")

    female_sources: dict[int, Path] = {}
    for path in args.female_source.glob("*.wav"):
        number = recording_number(path.stem)
        if number is not None:
            if number in female_sources:
                raise SystemExit(f"Duplicate female recording #{number}")
            female_sources[number] = path
    if sorted(female_sources) != list(range(1, 51)):
        missing = sorted(set(range(1, 51)) - set(female_sources))
        extra = sorted(set(female_sources) - set(range(1, 51)))
        raise SystemExit(f"Female recordings mismatch: missing={missing}, extra={extra}")

    male_sources = {i: MALE_SOURCE / f"acp_{i:03d}.wav" for i in range(1, 51)}
    missing_male = [i for i, path in male_sources.items() if not path.is_file()]
    if missing_male:
        raise SystemExit(f"Missing male recordings: {missing_male}")

    rows: list[dict[str, str]] = []
    for gender, speaker, sources in (
        ("male", "classmate_a", male_sources),
        ("female", "classmate_b", female_sources),
    ):
        for number in range(1, 51):
            filename = f"acp_{number:03d}.wav"
            destination = args.output_dir / gender / filename
            convert(ffmpeg, sources[number], destination)
            rows.append(
                {
                    "audio_path": (Path("..") / "acp_drp" / "C5_acp" / gender / filename).as_posix(),
                    "reference_text": texts[number],
                    "language": "zh-tw",
                    "condition": "C5",
                    "speaker": speaker,
                    "gender": gender,
                    "sentence_id": f"{number:03d}",
                }
            )

    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest_out.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(f"C5 ready: 100 clips (male=50, female=50)")
    print(f"Manifest: {args.manifest_out}")
    print(f"Output: {args.output_dir}")


if __name__ == "__main__":
    main()
