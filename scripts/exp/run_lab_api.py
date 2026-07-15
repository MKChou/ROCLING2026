"""
實驗室 Whisper API（D2）批次辨識 — 依 testset 選國語或台語 API 設定

  python scripts/run_lab_api.py e1 --testset acp --manifest data/manifests/acp.csv
  python scripts/run_lab_api.py e2 --manifest data/manifests/e2_latency_50.csv
  python scripts/run_lab_api.py e3 --manifest data/manifests/hallucination.csv

輸出格式與 run_d5.py 相同，預設 profile=D2（Whisper）。
若確認 API 為 large-v3-turbo 伺服器版，加 --profile D1。
注意：延遲含網路來回，非本機部署延遲。
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import statistics
import sys
import time
from pathlib import Path

import requests
import soundfile as sf

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

from config import (  # noqa: E402
    E2_REPEATS,
    LAB_API_LANG_BY_TESTSET,
    LAB_API_LANG_MANDARIN,
    LAB_API_TOKEN,
    LAB_API_URL,
    LAB_API_URL_BY_TESTSET,
    PROFILE_D2,
    RESULTS_DIR,
    TESTSET_MANDARIN,
)
from manifest import load_manifest  # noqa: E402

API_TOKEN = LAB_API_TOKEN
DEFAULT_PROFILE = PROFILE_D2


def api_settings_for_testset(testset: str | None) -> tuple[str, str]:
    """依 testset 回傳 (url, lang)；E2/E3 預設走國語 API。"""
    key = testset or TESTSET_MANDARIN
    url = LAB_API_URL_BY_TESTSET.get(key, LAB_API_URL)
    lang = LAB_API_LANG_BY_TESTSET.get(key, LAB_API_LANG_MANDARIN)
    return url, lang


def transcribe_via_api(
    wav_path: Path,
    *,
    api_url: str,
    api_lang: str,
    timeout: float = 30.0,
) -> tuple[str, float]:
    audio_b64 = base64.b64encode(wav_path.read_bytes()).decode()
    data = {"lang": api_lang, "token": API_TOKEN, "audio": audio_b64}

    start = time.perf_counter()
    response = requests.post(api_url, data=data, timeout=timeout)
    elapsed = time.perf_counter() - start

    response.raise_for_status()
    sentence = response.json().get("sentence", "").strip()
    return sentence, elapsed


def audio_duration_sec(wav_path: Path) -> float:
    info = sf.info(str(wav_path))
    return info.frames / info.samplerate


def run(args: argparse.Namespace) -> None:
    rows = load_manifest(args.manifest)
    if args.limit:
        rows = rows[: args.limit]

    testset = getattr(args, "testset", None)
    api_url, api_lang = api_settings_for_testset(testset)
    if getattr(args, "lang", None):
        api_lang = args.lang
    print(f"API: {api_url} | lang={api_lang}\n")

    outputs: list[dict] = []
    for i, row in enumerate(rows, start=1):
        wav = row.resolved_audio
        cond = f" {row.condition}" if row.condition else ""
        print(f"[{i}/{len(rows)}]{cond} {wav.name}")
        try:
            hyp, latency = transcribe_via_api(wav, api_url=api_url, api_lang=api_lang)
            duration = audio_duration_sec(wav)
            record = {
                "audio": str(wav),
                "ref": row.reference_text,
                "hyp": hyp,
                "decode_time_sec": round(latency, 4),
                "audio_duration_sec": round(duration, 4),
                "rtf": round(latency / duration, 4) if duration > 0 else None,
                "profile": args.profile,
                "note": "latency includes network round-trip",
            }
            if row.condition:
                record["condition"] = row.condition
            if args.experiment == "e1":
                record["testset"] = args.testset
            outputs.append(record)
            print(f"  → {hyp or '(empty)'}")
        except Exception as exc:
            print(f"  ! {exc}", file=sys.stderr)

    if args.experiment == "e1":
        out_path = RESULTS_DIR / "E1_outputs" / f"{args.profile}_{args.testset}.jsonl"
    else:
        out_path = RESULTS_DIR / "E3_outputs" / f"{args.profile}_hallucination.jsonl"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for record in outputs:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"\nWrote {len(outputs)} lines → {out_path}")


def _append_csv(path: Path, row: dict) -> None:
    write_header = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def run_e2(args: argparse.Namespace) -> None:
    """E2：固定 50 句 × 3 輪（第 1 輪 warm-up 不計），含網路往返延遲。"""
    rows = load_manifest(args.manifest)
    if not rows:
        raise SystemExit("E2 manifest is empty")

    api_url, api_lang = api_settings_for_testset(TESTSET_MANDARIN)
    print(f"API: {api_url} | lang={api_lang}\n")

    latencies: list[float] = []
    audio_durations: list[float] = []
    measured_repeats = max(1, E2_REPEATS - 1)

    for pass_idx in range(E2_REPEATS):
        is_warmup = pass_idx == 0
        label = "warm-up" if is_warmup else f"measure {pass_idx}"
        print(f"\n--- Pass {pass_idx + 1}/{E2_REPEATS} ({label}) ---")
        for i, row in enumerate(rows, start=1):
            wav = row.resolved_audio
            print(f"[{i}/{len(rows)}] {wav.name}")
            hyp, latency = transcribe_via_api(wav, api_url=api_url, api_lang=api_lang)
            duration = audio_duration_sec(wav)
            if is_warmup:
                continue
            latencies.append(latency)
            audio_durations.append(duration)

    total_audio = sum(audio_durations)
    total_decode = sum(latencies)
    rtf = total_decode / total_audio if total_audio > 0 else 0.0
    lat_sorted = sorted(latencies)
    p95_idx = max(0, int(len(lat_sorted) * 0.95) - 1)

    perf_row = {
        "profile": args.profile,
        "device": "remote-api (network incl.)",
        "rtf": round(rtf, 4),
        "latency_avg_s": round(statistics.mean(latencies), 4) if latencies else 0,
        "latency_p95_s": round(lat_sorted[p95_idx], 4) if lat_sorted else 0,
        "first_token_s": "",
        "peak_mem_gb": "",
        "model_size_gb": "",
        "n_utts": len(rows),
        "measured_repeats": measured_repeats,
        "testset": "mandarin",
    }
    perf_path = RESULTS_DIR / "E2_performance.csv"
    _append_csv(perf_path, perf_row)
    print(f"\nE2 summary: RTF={perf_row['rtf']}, avg_latency={perf_row['latency_avg_s']}s")
    print(f"Wrote → {perf_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Lab ASR API batch experiments")
    sub = parser.add_subparsers(dest="experiment", required=True)

    p_e1 = sub.add_parser("e1")
    p_e1.add_argument("--testset", required=True, choices=["mandarin", "acp", "taiwanese"])
    p_e1.add_argument("--manifest", type=Path, required=True)
    p_e1.add_argument("--profile", default=DEFAULT_PROFILE)
    p_e1.add_argument("--limit", type=int)
    p_e1.add_argument(
        "--lang",
        default=None,
        help='覆寫 API lang（例："Chinese & Taiwanese"）；預設依 testset',
    )

    p_e3 = sub.add_parser("e3")
    p_e3.add_argument("--manifest", type=Path, required=True)
    p_e3.add_argument("--profile", default=DEFAULT_PROFILE)
    p_e3.add_argument("--limit", type=int)
    p_e3.add_argument(
        "--lang",
        default=None,
        help='覆寫 API lang（例："Chinese & Taiwanese"）；預設依 config',
    )

    p_e2 = sub.add_parser("e2")
    p_e2.add_argument("--manifest", type=Path, required=True)
    p_e2.add_argument("--profile", default=DEFAULT_PROFILE)

    args = parser.parse_args()
    print("=" * 55)
    print(f"  ROCLING 2026 · {args.profile} Whisper（實驗室 API）")
    if args.experiment == "e1":
        url, lang = api_settings_for_testset(args.testset)
    else:
        url, lang = api_settings_for_testset(TESTSET_MANDARIN)
    if getattr(args, "lang", None):
        lang = args.lang
    print(f"  experiment={args.experiment} | {url} | lang={lang}")
    print("=" * 55 + "\n")
    if args.experiment == "e2":
        run_e2(args)
    else:
        run(args)


if __name__ == "__main__":
    main()
