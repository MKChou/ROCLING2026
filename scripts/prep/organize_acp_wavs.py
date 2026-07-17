"""整理 ACP 錄音：錄製.wav / 錄製 (N).wav → acp_XXX.wav + 更新 manifest。"""

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
ACP_DIR = PROJECT_ROOT / "data" / "legacy_pilot" / "acp_wavs"
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifests" / "acp.csv"
SCRIPT_PATH = PROJECT_ROOT / "data" / "recording_scripts" / "acp_recording_script.txt"
SAMPLE_RATE = 16000


def parse_recording_script(path: Path) -> dict[int, str]:
    texts: dict[int, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\d{3})\s+(.+?)\s*$", line.strip())
        if m:
            texts[int(m.group(1))] = m.group(2).strip()
    return texts


def recording_number(stem: str) -> int | None:
    if stem == "錄製":
        return 1
    m = re.match(r"錄製 \((\d+)\)$", stem)
    return int(m.group(1)) if m else None


def find_ffmpeg() -> str:
    import shutil as sh

    path = sh.which("ffmpeg")
    if not path:
        raise SystemExit("ffmpeg not found")
    return path


def convert_wav(ffmpeg: str, src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [ffmpeg, "-y", "-i", str(src), "-ar", str(SAMPLE_RATE), "-ac", "1", str(dst)],
        check=True,
        capture_output=True,
    )


def archive_old_files(acp_dir: Path, archive_dir: Path) -> None:
    archive_dir.mkdir(parents=True, exist_ok=True)
    for pattern in ("*.mp3", "acp_*.wav"):
        for f in acp_dir.glob(pattern):
            if f.is_file():
                shutil.move(str(f), str(archive_dir / f.name))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--speaker", default="classmate_a", help="語者代號（存檔用）")
    parser.add_argument("--no-archive", action="store_true")
    args = parser.parse_args()

    texts = parse_recording_script(SCRIPT_PATH)
    if len(texts) < 50:
        raise SystemExit(f"Recording script has only {len(texts)} sentences")

    raw_dir = ACP_DIR / "raw" / args.speaker
    raw_dir.mkdir(parents=True, exist_ok=True)

    sources: list[tuple[int, Path]] = []
    for wav in ACP_DIR.glob("*.wav"):
        num = recording_number(wav.stem)
        if num is not None:
            sources.append((num, wav))

    if not sources:
        raise SystemExit(f"No 錄製*.wav files in {ACP_DIR}")

    sources.sort(key=lambda x: x[0])
    nums = [n for n, _ in sources]
    missing = [i for i in range(1, 51) if i not in nums]
    extra = [n for n in nums if n < 1 or n > 50]

    print(f"Found {len(sources)} recordings: #{nums[0]}–#{nums[-1]}")
    if missing:
        print(f"Warning: missing sentence numbers: {missing}")
    if extra:
        print(f"Warning: out of range: {extra}")

    if not args.no_archive:
        archive = ACP_DIR / "_archive" / f"before_{args.speaker}"
        archive_old_files(ACP_DIR, archive)
        print(f"Archived old acp_*.wav / *.mp3 → {archive}")

    ffmpeg = find_ffmpeg()
    manifest_rows: list[dict] = []

    for num, src in sources:
        if num not in texts:
            print(f"Skip #{num}: no script text")
            continue

        # 保留原始檔到 raw/
        raw_copy = raw_dir / f"recording_{num:03d}.wav"
        if src.resolve() != raw_copy.resolve():
            shutil.copy2(src, raw_copy)

        dst = ACP_DIR / f"acp_{num:03d}.wav"
        convert_wav(ffmpeg, src, dst)
        manifest_rows.append({
            "audio_path": f"../legacy_pilot/acp_wavs/acp_{num:03d}.wav",
            "reference_text": texts[num],
            "language": "zh-tw",
            "speaker": args.speaker,
        })
        print(f"  {src.name} → acp_{num:03d}.wav")

    # 刪除已處理的錄製*.wav（原始已在 raw/）
    for num, src in sources:
        if src.exists() and src.parent == ACP_DIR:
            src.unlink()

    manifest_rows.sort(key=lambda r: r["audio_path"])
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["audio_path", "reference_text", "language", "speaker"],
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(f"\nManifest: {MANIFEST_PATH} ({len(manifest_rows)} rows)")
    print("Done.")


if __name__ == "__main__":
    main()
