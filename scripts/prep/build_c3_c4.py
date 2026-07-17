"""建立 ACP-DRP C3（極短）／C4（猶豫）男女真人資料集。

來源檔依 Windows 錄音機命名：
  錄製.wav -> 第 1 句
  錄製 (2).wav -> 第 2 句
  ...
  錄製 (50).wav -> 第 50 句

C3 轉檔時裁切前後長靜音（建構效度），再輸出 16 kHz mono wav。
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
SCRIPT_PATH = DATA_DIR / "recording_scripts" / "c3_c4_recording_script.txt"
DEFAULT_C3_SRC = PROJECT_ROOT.parent / "C3"
DEFAULT_C4_SRC = PROJECT_ROOT.parent / "C4"
C3_OUT = DATA_DIR / "acp_drp" / "C3_short"
C4_OUT = DATA_DIR / "acp_drp" / "C4_hesitation"
C3_RAW_ARCHIVE = DATA_DIR / "recordings" / "c3_raw"
C4_RAW_ARCHIVE = DATA_DIR / "recordings" / "c4_raw"
C3_MANIFEST = DATA_DIR / "manifests" / "c3_short.csv"
C4_MANIFEST = DATA_DIR / "manifests" / "c4_hesitation.csv"
SAMPLE_RATE = 16_000

# 裁切前後長靜音，但保留約 50 ms 邊距，避免切掉字頭／字尾
C3_TRIM_FILTER = (
    "silenceremove=start_periods=1:start_silence=0.05:start_threshold=-40dB:detection=peak,"
    "aformat=dblp,areverse,"
    "silenceremove=start_periods=1:start_silence=0.05:start_threshold=-40dB:detection=peak,"
    "aformat=dblp,areverse"
)


def recording_number(stem: str) -> int | None:
    if stem == "錄製":
        return 1
    match = re.fullmatch(r"錄製 \((\d+)\)", stem)
    return int(match.group(1)) if match else None


def parse_section(path: Path, marker: str) -> dict[int, str]:
    """從腳本解析 【C3】或 【C4】區塊的編號→參考文字。"""
    lines = path.read_text(encoding="utf-8").splitlines()
    in_section = False
    texts: dict[int, str] = {}
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"【{marker}】"):
            in_section = True
            continue
        if in_section and stripped.startswith("【") and not stripped.startswith(f"【{marker}】"):
            break
        if in_section and stripped.startswith("=" * 10) and texts:
            break
        match = re.match(r"^(\d{3})\s+(\S+)", stripped)
        if in_section and match:
            texts[int(match.group(1))] = match.group(2)
    return texts


def collect_sources(src_dir: Path) -> dict[int, Path]:
    sources: dict[int, Path] = {}
    if not src_dir.is_dir():
        raise SystemExit(f"Source dir not found: {src_dir}")
    for path in src_dir.glob("*.wav"):
        number = recording_number(path.stem)
        if number is None:
            continue
        if number in sources:
            raise SystemExit(f"Duplicate recording #{number} in {src_dir}")
        sources[number] = path
    if sorted(sources) != list(range(1, 51)):
        missing = sorted(set(range(1, 51)) - set(sources))
        extra = sorted(set(sources) - set(range(1, 51)))
        raise SystemExit(f"{src_dir}: missing={missing}, extra={extra}")
    return sources


def archive_raw(sources: dict[int, Path], archive_dir: Path) -> None:
    archive_dir.mkdir(parents=True, exist_ok=True)
    for src in sources.values():
        dst = archive_dir / src.name
        if dst.resolve() == src.resolve():
            continue
        shutil.copy2(src, dst)


def convert(
    ffmpeg: str,
    source: Path,
    destination: Path,
    *,
    trim_silence: bool,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
    ]
    if trim_silence:
        cmd.extend(["-af", C3_TRIM_FILTER])
    cmd.extend(
        [
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(destination),
        ]
    )
    subprocess.run(cmd, check=True)


def probe_duration(ffprobe: str, path: Path) -> float:
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def build_condition(
    *,
    ffmpeg: str,
    ffprobe: str,
    condition: str,
    texts: dict[int, str],
    male_src: Path,
    female_src: Path,
    out_dir: Path,
    raw_archive: Path | None,
    manifest_path: Path,
    filename_prefix: str,
    trim_silence: bool,
) -> None:
    if sorted(texts) != list(range(1, 51)):
        raise SystemExit(f"{condition} script expected 1-50; got {sorted(texts)}")

    gender_sources = {
        "male": ("classmate_a", collect_sources(male_src)),
        "female": ("classmate_b", collect_sources(female_src)),
    }

    rows: list[dict[str, str]] = []
    short_after_trim: list[str] = []
    durations: list[float] = []

    for gender, (speaker, sources) in gender_sources.items():
        if raw_archive is not None:
            archive_raw(sources, raw_archive / gender)
        for number in range(1, 51):
            filename = f"{filename_prefix}_{number:03d}.wav"
            destination = out_dir / gender / filename
            convert(ffmpeg, sources[number], destination, trim_silence=trim_silence)
            duration = probe_duration(ffprobe, destination)
            durations.append(duration)
            if duration < 0.05:
                short_after_trim.append(f"{condition}/{gender}/{filename} ({duration:.3f}s)")
            rel = Path("..") / "acp_drp" / out_dir.name / gender / filename
            rows.append(
                {
                    "audio_path": rel.as_posix(),
                    "reference_text": texts[number],
                    "language": "zh-tw",
                    "condition": condition,
                    "speaker": speaker,
                    "gender": gender,
                    "sentence_id": f"{number:03d}",
                }
            )

    if short_after_trim:
        raise SystemExit(
            "Trimmed clips too short (likely silence-only or over-trimmed):\n  "
            + "\n  ".join(short_after_trim)
        )

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(
        f"{condition} ready: {len(rows)} clips | "
        f"dur min/mean/max = {min(durations):.2f}/{sum(durations)/len(durations):.2f}/{max(durations):.2f}s"
    )
    print(f"  Output:   {out_dir}")
    print(f"  Manifest: {manifest_path}")
    if raw_archive is not None:
        print(f"  Raw:      {raw_archive}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build ACP-DRP C3/C4 male/female sets")
    parser.add_argument("--c3-src", type=Path, default=DEFAULT_C3_SRC)
    parser.add_argument("--c4-src", type=Path, default=DEFAULT_C4_SRC)
    parser.add_argument("--c3-out", type=Path, default=C3_OUT)
    parser.add_argument("--c4-out", type=Path, default=C4_OUT)
    parser.add_argument("--c3-manifest", type=Path, default=C3_MANIFEST)
    parser.add_argument("--c4-manifest", type=Path, default=C4_MANIFEST)
    parser.add_argument("--no-archive", action="store_true", help="Skip copying raw into recordings/")
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise SystemExit("ffmpeg/ffprobe not found")

    c3_texts = parse_section(SCRIPT_PATH, "C3")
    c4_texts = parse_section(SCRIPT_PATH, "C4")

    build_condition(
        ffmpeg=ffmpeg,
        ffprobe=ffprobe,
        condition="C3",
        texts=c3_texts,
        male_src=args.c3_src / "male",
        female_src=args.c3_src / "female",
        out_dir=args.c3_out,
        raw_archive=None if args.no_archive else C3_RAW_ARCHIVE,
        manifest_path=args.c3_manifest,
        filename_prefix="c3",
        trim_silence=True,
    )
    build_condition(
        ffmpeg=ffmpeg,
        ffprobe=ffprobe,
        condition="C4",
        texts=c4_texts,
        male_src=args.c4_src / "male",
        female_src=args.c4_src / "female",
        out_dir=args.c4_out,
        raw_archive=None if args.no_archive else C4_RAW_ARCHIVE,
        manifest_path=args.c4_manifest,
        filename_prefix="c4",
        trim_silence=False,
    )
    print("Done.")


if __name__ == "__main__":
    main()
