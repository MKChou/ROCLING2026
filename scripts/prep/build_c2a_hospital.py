"""從自錄醫院環境音建置 ACP-DRP C2A 子集。

預設產出 5 場景 × 20 段（5 s、不重疊）= 100 段，並避開初篩時
標記為疑似人聲的來源時窗。

用法：
  python scripts/prep/build_c2a_hospital.py --source-dir C:\\path\\to\\recordings
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
SAMPLE_RATE = 16_000


@dataclass(frozen=True)
class SourceSpec:
    filename: str
    clips: int
    excluded_ranges: tuple[tuple[float, float], ...] = ()


@dataclass(frozen=True)
class VenueSpec:
    description: str
    sources: tuple[SourceSpec, ...]


# 五類皆為公共或低侵入場域。領藥區因初篩出現疑似人聲，暫不納入。
VENUES: dict[str, VenueSpec] = {
    "lobby": VenueSpec(
        "入口大廳",
        (
            SourceSpec(
                "入口大廳.m4a",
                20,
                (
                    (20.0, 25.0),   # lobby_04 人工聽檢：遠處人聲
                    (45.0, 50.0),   # lobby_06 人工聽檢：有人聲
                    (135.0, 165.0),  # 初篩疑似人聲
                ),
            ),
        ),
    ),
    "waiting_area": VenueSpec(
        "候診區",
        (SourceSpec("候診區1+2.m4a", 20),),
    ),
    "elevator_area": VenueSpec(
        "電梯等候／乘梯環境",
        (
            SourceSpec("電梯1.m4a", 10),
            SourceSpec("電梯2.m4a", 10, ((25.0, 30.0),)),  # elevator_area_13 遠處人聲
        ),
    ),
    "low_traffic_corridor": VenueSpec(
        "低人流走廊",
        (
            SourceSpec("低人流走廊1.m4a", 10),
            SourceSpec("低人流走廊2.m4a", 10, ((75.0, 90.0),)),
        ),
    ),
    "service_counter": VenueSpec(
        "服務櫃檯周邊",
        (
            SourceSpec("櫃檯1+2.m4a", 20, ((140.0, 145.0),)),  # service_counter_11 遠處人聲
        ),
    ),
}


def find_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise SystemExit(f"{name} not found")
    return path


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


def overlaps_excluded(
    start: float,
    duration: float,
    excluded_ranges: tuple[tuple[float, float], ...],
) -> bool:
    end = start + duration
    return any(start < excluded_end and end > excluded_start for excluded_start, excluded_end in excluded_ranges)


def choose_starts(
    *,
    source_duration: float,
    clip_duration: float,
    count: int,
    excluded_ranges: tuple[tuple[float, float], ...],
    seed: int,
) -> list[float]:
    full_clips = math.floor(source_duration / clip_duration)
    candidates = [
        i * clip_duration
        for i in range(full_clips)
        if not overlaps_excluded(i * clip_duration, clip_duration, excluded_ranges)
    ]
    if len(candidates) < count:
        raise SystemExit(
            f"Only {len(candidates)} eligible clips after exclusions; need {count}"
        )

    # 固定種子的等機率抽樣，輸出依時間排序，與 C2B 建置原則一致。
    import numpy as np

    rng = np.random.default_rng(seed)
    return sorted(float(x) for x in rng.choice(candidates, size=count, replace=False))


def cut_clip(
    ffmpeg: str,
    source: Path,
    output: Path,
    *,
    start_sec: float,
    duration_sec: float,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{start_sec:.3f}",
            "-i",
            str(source),
            "-t",
            f"{duration_sec:.3f}",
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(output),
        ],
        check=True,
    )


def write_sources_md(
    path: Path,
    *,
    clips_per_venue: int,
    duration_sec: float,
    seed: int,
) -> None:
    lines = [
        "# C2A 醫院環境底噪 — 來源與使用限制",
        "",
        "- **Source**: 研究團隊實地自錄之醫院環境底噪",
        "- **Content policy**: 不以人聲、問診、叫號或個人資訊為收錄目標",
        "- **Distribution**: 限研究團隊內部使用；完成逐段人工聽檢與合規確認前不得公開原始音檔",
        f"- **Format**: {SAMPLE_RATE} Hz mono PCM WAV",
        f"- **Segment**: {duration_sec:g} s × {clips_per_venue} clips / venue；固定種子 {seed}",
        "- **Screening**: 來源先以 20 s 切段進行 Silero VAD／Whisper 初篩；疑似人聲時窗不納入",
        "- **Post-build check**: 100 段以 Silero VAD threshold 0.3 複查均為陰性；仍待逐段人工聽檢",
        "",
        "## Venue mapping",
        "",
        "| venue_id | 場景 | 來源檔數 |",
        "|----------|------|----------|",
    ]
    for venue_id, spec in VENUES.items():
        lines.append(f"| `{venue_id}` | {spec.description} | {len(spec.sources)} |")

    lines += [
        "",
        "## 注意事項",
        "",
        "- 自動 VAD／ASR 僅為初篩，不能取代逐段人工聽檢。",
        "- `reference_text` 留空；本子集用於量測純底噪下 ASR 是否產生非空輸出。",
        "- manifest 保留來源檔名與起始秒數，供內部追溯；對外釋出前應另製去識別版本。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build C2A hospital ambient-noise subset")
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "acp_drp" / "C2A_hospital",
    )
    parser.add_argument(
        "--manifest-out",
        type=Path,
        default=PROJECT_ROOT / "data" / "manifests" / "c2a_hospital.csv",
    )
    parser.add_argument("--clips-per-venue", type=int, default=20)
    parser.add_argument("--duration", type=float, default=5.0)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.clips_per_venue != 20:
        raise SystemExit("Current source quotas are defined for exactly 20 clips per venue")

    ffmpeg = find_tool("ffmpeg")
    ffprobe = find_tool("ffprobe")
    all_rows: list[dict[str, str]] = []
    selection_log: list[dict[str, object]] = []

    for venue_id, venue in VENUES.items():
        venue_dir = args.output_dir / venue_id
        venue_dir.mkdir(parents=True, exist_ok=True)
        for stale in venue_dir.glob("*.wav"):
            stale.unlink()

        clip_index = 1
        for source_index, source_spec in enumerate(venue.sources):
            source = args.source_dir / source_spec.filename
            if not source.is_file():
                raise SystemExit(f"Missing source recording: {source}")

            source_duration = probe_duration(ffprobe, source)
            source_seed = args.seed + int(
                hashlib.sha256(
                    f"{venue_id}:{source_index}:{source.name}".encode("utf-8")
                ).hexdigest()[:8],
                16,
            ) % 100_000
            starts = choose_starts(
                source_duration=source_duration,
                clip_duration=args.duration,
                count=source_spec.clips,
                excluded_ranges=source_spec.excluded_ranges,
                seed=source_seed,
            )

            for start_sec in starts:
                filename = f"{venue_id}_{clip_index:02d}.wav"
                output = venue_dir / filename
                cut_clip(
                    ffmpeg,
                    source,
                    output,
                    start_sec=start_sec,
                    duration_sec=args.duration,
                )
                rel = Path("..") / "acp_drp" / "C2A_hospital" / venue_id / filename
                all_rows.append(
                    {
                        "audio_path": rel.as_posix(),
                        "reference_text": "",
                        "language": "zh-tw",
                        "condition": "C2A",
                        "venue": venue_id,
                        "source": "hospital_self_recorded",
                        "source_scene": venue.description,
                        "source_file": source.name,
                        "start_sec": f"{start_sec:.3f}",
                        "duration_sec": f"{args.duration:.1f}",
                        "license": "restricted_internal",
                    }
                )
                selection_log.append(
                    {
                        "venue": venue_id,
                        "output_file": filename,
                        "source_file": source.name,
                        "start_sec": start_sec,
                        "duration_sec": args.duration,
                    }
                )
                clip_index += 1

        produced = clip_index - 1
        if produced != args.clips_per_venue:
            raise SystemExit(f"{venue_id}: produced {produced}, expected {args.clips_per_venue}")
        print(f"{venue_id}: {produced} clips")

    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "audio_path",
        "reference_text",
        "language",
        "condition",
        "venue",
        "source",
        "source_scene",
        "source_file",
        "start_sec",
        "duration_sec",
        "license",
    ]
    with args.manifest_out.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    write_sources_md(
        args.output_dir / "SOURCES.md",
        clips_per_venue=args.clips_per_venue,
        duration_sec=args.duration,
        seed=args.seed,
    )
    (args.output_dir / "selection_log.json").write_text(
        json.dumps(selection_log, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Manifest: {args.manifest_out} ({len(all_rows)} rows)")
    print(f"Output:   {args.output_dir}")


if __name__ == "__main__":
    main()
