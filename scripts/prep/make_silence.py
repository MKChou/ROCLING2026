"""
E3 幻覺診斷集 C1：產生純靜音 wav + manifest 片段

  python scripts/make_silence.py
  python scripts/make_silence.py --output-dir data/hallucination/C1
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
COPIES_PER_DURATION = 5
NOISE_DB = -60  # 極低底噪，模擬真實靜音


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
        default=DATA_DIR / "hallucination" / "C1",
    )
    parser.add_argument("--noise", action="store_true", default=True)
    parser.add_argument("--manifest-out", type=Path, default=DATA_DIR / "manifests" / "hallucination_C1.csv")
    args = parser.parse_args()

    manifest_rows: list[dict] = []
    idx = 1

    for dur in DURATIONS_SEC:
        for _ in range(COPIES_PER_DURATION):
            fname = f"silence_{idx:02d}_{dur}s.wav"
            wav_path = args.output_dir / fname
            _make_silence_wav(wav_path, dur, add_noise=args.noise)
            rel_from_manifest = Path("..") / "hallucination" / "C1" / fname
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
    print("合併至 data/manifests/hallucination.csv 後執行：")
    print("  python scripts/run_d5.py e3 --manifest data/manifests/hallucination.csv")


if __name__ == "__main__":
    main()
