"""從本機 22k 語料產生 E1 manifest（mandarin / taiwanese / e2_latency_50）。"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

from config import CORPUS_ROOT, MANIFEST_DIR  # noqa: E402

# 16 kHz 繁中合成語料（wav + 同目錄 .txt 第一行為參考句）
MANDARIN_SUBDIRS = (
    "trandition_zh/azure_synthesis_with_vad/22khz_male_trad",
    "trandition_zh/azure_synthesis_with_vad/22khz_female_trad",
)

# 台語 Kaldi 語料：wav + 同 stem 之 .json（text）與 .wav.trn
TAIWANESE_ROOT = "tw/corpus/148_kaldi_tw_corpus_300_corpus"

TAG_RE = re.compile(r"\[[^\]]+\]")


def clean_reference(text: str) -> str:
    line = text.splitlines()[0].strip() if text else ""
    return TAG_RE.sub("", line).strip()


def collect_pairs(corpus_root: Path) -> list[tuple[Path, str]]:
    pairs: list[tuple[Path, str]] = []
    for rel in MANDARIN_SUBDIRS:
        root = corpus_root / rel
        if not root.is_dir():
            print(f"Skip missing: {root}")
            continue
        for wav in sorted(root.glob("*.wav")):
            txt = wav.with_suffix(".txt")
            if not txt.is_file():
                continue
            ref = clean_reference(txt.read_text(encoding="utf-8", errors="replace"))
            if ref:
                pairs.append((wav.resolve(), ref))
    return pairs


def load_taiwanese_reference(wav: Path) -> str:
    json_path = wav.with_suffix(".json")
    if json_path.is_file():
        data = json.loads(json_path.read_text(encoding="utf-8"))
        text = (data.get("text") or "").strip()
        if text:
            return TAG_RE.sub("", text).strip()
    trn_path = Path(str(wav) + ".trn")
    if trn_path.is_file():
        line = trn_path.read_text(encoding="utf-8", errors="replace").splitlines()[0].strip()
        return TAG_RE.sub("", line).strip()
    return ""


def collect_taiwanese_pairs(corpus_root: Path) -> list[tuple[Path, str]]:
    root = corpus_root / TAIWANESE_ROOT
    if not root.is_dir():
        raise SystemExit(f"Taiwanese corpus not found: {root}")
    pairs: list[tuple[Path, str]] = []
    for wav in sorted(root.rglob("*.wav")):
        ref = load_taiwanese_reference(wav)
        if ref:
            pairs.append((wav.resolve(), ref))
    return pairs


def write_manifest(path: Path, rows: list[tuple[Path, str]], language: str = "zh-tw") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["audio_path", "reference_text", "language"],
        )
        writer.writeheader()
        for audio, ref in rows:
            writer.writerow({
                "audio_path": str(audio),
                "reference_text": ref,
                "language": language,
            })
    print(f"Wrote {len(rows)} rows → {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-root", type=Path, default=CORPUS_ROOT)
    parser.add_argument("--mandarin-count", type=int, default=500)
    parser.add_argument("--taiwanese-count", type=int, default=500)
    parser.add_argument("--e2-count", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--skip-mandarin", action="store_true")
    parser.add_argument("--skip-taiwanese", action="store_true")
    args = parser.parse_args()

    rng = random.Random(args.seed)

    if not args.skip_mandarin:
        mandarin_pairs = collect_pairs(args.corpus_root)
        if len(mandarin_pairs) < args.mandarin_count:
            raise SystemExit(
                f"Only {len(mandarin_pairs)} mandarin pairs found, need {args.mandarin_count}"
            )
        sampled = mandarin_pairs.copy()
        rng.shuffle(sampled)
        mandarin = sampled[: args.mandarin_count]
        e2_rows = mandarin[: args.e2_count]
        write_manifest(MANIFEST_DIR / "mandarin.csv", mandarin)
        write_manifest(MANIFEST_DIR / "e2_latency_50.csv", e2_rows)
        print(
            f"Mandarin pool: {len(mandarin_pairs)} | sampled: {len(mandarin)} | e2: {len(e2_rows)}"
        )

    if not args.skip_taiwanese:
        tw_pairs = collect_taiwanese_pairs(args.corpus_root)
        if len(tw_pairs) < args.taiwanese_count:
            raise SystemExit(
                f"Only {len(tw_pairs)} taiwanese pairs found, need {args.taiwanese_count}"
            )
        tw_sampled = tw_pairs.copy()
        rng.shuffle(tw_sampled)
        taiwanese = tw_sampled[: args.taiwanese_count]
        write_manifest(MANIFEST_DIR / "taiwanese.csv", taiwanese, language="nan")
        print(f"Taiwanese pool: {len(tw_pairs)} | sampled: {len(taiwanese)}")


if __name__ == "__main__":
    main()
