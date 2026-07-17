"""
ACP-DRP C1：產生純數位靜音 wav 與獨立 manifest。

  python scripts/prep/make_silence.py
  python scripts/prep/make_silence.py --copies-per-duration 25

預設產生 3/5/8/10 秒各 25 段，共 100 段；不覆蓋舊 pilot。
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

from config import DATA_DIR, SAMPLE_RATE  # noqa: E402

DURATIONS_SEC = [3, 5, 8, 10]
COPIES_PER_DURATION = 25
NOISE_DB = -60  # 僅在 --noise 時加入，C1 預設為純數位靜音


def _make_silence_wav(path: Path, duration_sec: float, *, add_noise: bool) -> None:
    n = int(SAMPLE_RATE * duration_sec)
    audio = np.zeros(n, dtype=np.float32)
    if add_noise:
        amplitude = 10 ** (NOISE_DB / 20)
        audio += np.random.default_rng(42).normal(0, amplitude, n).astype(np.float32)
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), audio, SAMPLE_RATE)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate E3 C1 silence clips")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DATA_DIR / "acp_drp" / "C1_silence",
    )
    parser.add_argument(
        "--copies-per-duration",
        type=int,
        default=COPIES_PER_DURATION,
    )
    parser.add_argument(
        "--noise",
        action="store_true",
        help="加入 -60 dB 極低底噪；C1 預設不加入",
    )
    parser.add_argument(
        "--manifest-out",
        type=Path,
        default=DATA_DIR / "manifests" / "c1_silence.csv",
    )
    args = parser.parse_args()
    if args.copies_per_duration < 1:
        parser.error("--copies-per-duration must be >= 1")

    manifest_rows: list[dict] = []
    idx = 1

    for dur in DURATIONS_SEC:
        for _ in range(args.copies_per_duration):
            fname = f"silence_{idx:02d}_{dur}s.wav"
            wav_path = args.output_dir / fname
            _make_silence_wav(wav_path, dur, add_noise=args.noise)
            rel_from_manifest = Path("..") / "acp_drp" / "C1_silence" / fname
            manifest_rows.append({
                "audio_path": rel_from_manifest.as_posix(),
                "reference_text": "",
                "language": "zh-tw",
                "condition": "C1",
            })
            print(f"Created {wav_path}")
            idx += 1

    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest_out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["audio_path", "reference_text", "language", "condition"],
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(f"\n{len(manifest_rows)} clips → {args.output_dir}")
    print(f"Manifest → {args.manifest_out}")
    print("合併至 data/manifests/acp_drp.csv 後執行 ACP-DRP 實驗。")


if __name__ == "__main__":
    main()
