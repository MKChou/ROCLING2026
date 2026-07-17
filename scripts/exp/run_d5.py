"""
D5 Nemotron 實驗執行器（對應論文 E1 / E2 / E3）

從專案根目錄執行：

  python scripts/run_d5.py e1 --testset mandarin --manifest data/manifests/mandarin.csv
  python scripts/run_d5.py e1 --testset acp --manifest data/manifests/acp.csv
  python scripts/run_d5.py e2 --manifest data/manifests/e2_latency_50.csv --device cpu
  python scripts/run_d5.py e3 --manifest data/manifests/hallucination.csv

跑完後彙總指標：

  python scripts/score.py e1 --profile D5
  python scripts/score.py e3 --profile D5
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

from config import (  # noqa: E402
    E2_REPEATS,
    PROFILE_D5,
    PROFILE_D5_VAD,
    RESULTS_DIR,
    TESTSET_ACP,
    TESTSET_HALLUCINATION,
    TESTSET_MANDARIN,
    VAD_THRESHOLD,
)
from d5_engine import (  # noqa: E402
    DEFAULT_STREAM_LOOKAHEAD,
    load_model,
    model_size_gb,
    transcribe_file,
    warmup,
)
from manifest import load_manifest  # noqa: E402
from vad_gate import load_vad  # noqa: E402


def _profile(use_vad: bool) -> str:
    return PROFILE_D5_VAD if use_vad else PROFILE_D5


def _write_jsonl(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {len(rows)} lines → {path}")


def _hardware_line(device: str) -> str:
    import torch

    cpu = platform.processor() or platform.machine()
    ram_gb = round(psutil_ram_gb(), 1)
    gpu = "none"
    vram = ""
    if device != "cpu" and torch.cuda.is_available():
        gpu = torch.cuda.get_device_name(0)
        props = torch.cuda.get_device_properties(0)
        vram = f", VRAM: {props.total_memory / (1024**3):.1f}GB"
    return f"CPU: {cpu}, RAM: {ram_gb}GB; GPU: {gpu}{vram}; device={device}"


def psutil_ram_gb() -> float:
    import psutil

    return psutil.virtual_memory().total / (1024**3)


def run_e1(args: argparse.Namespace) -> None:
    rows_manifest = load_manifest(args.manifest)
    if args.limit:
        rows_manifest = rows_manifest[: args.limit]

    if args.vad:
        load_vad()
    load_model(device=args.device)
    outputs: list[dict] = []
    profile = _profile(args.vad)

    for i, row in enumerate(rows_manifest, start=1):
        wav = row.resolved_audio
        print(f"[{i}/{len(rows_manifest)}] {wav.name}")
        try:
            result = transcribe_file(
                wav,
                reference=row.reference_text,
                device=args.device,
                allow_silent=False,
                use_vad=args.vad,
                vad_threshold=args.vad_threshold,
            )
            record = result.to_jsonl_dict()
            record["testset"] = args.testset
            outputs.append(record)
            print(f"  → {result.hyp_traditional or '(empty)'}")
        except Exception as exc:
            print(f"  ! {exc}", file=sys.stderr)

    suffix = f"{args.testset}_{args.tag}" if args.tag else args.testset
    out_path = RESULTS_DIR / "E1_outputs" / f"{profile}_{suffix}.jsonl"
    _write_jsonl(outputs, out_path)


def run_e2(args: argparse.Namespace) -> None:
    """E2：固定 50 句 × 3 輪（第 1 輪 warm-up 不計），輸出 E2_performance.csv。"""
    rows_manifest = load_manifest(args.manifest)
    if len(rows_manifest) < 1:
        raise SystemExit("E2 manifest is empty")

    if args.vad:
        load_vad()
    load_model(device=args.device)
    if not args.streaming:
        warmup(device=args.device)

    latencies: list[float] = []
    decode_times: list[float] = []
    audio_durations: list[float] = []
    peak_mems: list[float] = []
    first_tokens: list[float] = []

    measured_repeats = max(1, E2_REPEATS - 1)
    total_passes = E2_REPEATS
    profile = _profile(args.vad)

    for pass_idx in range(total_passes):
        is_warmup = pass_idx == 0
        label = "warm-up" if is_warmup else f"measure {pass_idx}"
        print(f"\n--- Pass {pass_idx + 1}/{total_passes} ({label}) ---")

        for row in rows_manifest:
            result = transcribe_file(
                row.resolved_audio,
                reference=row.reference_text,
                device=args.device,
                allow_silent=True,
                use_vad=args.vad,
                vad_threshold=args.vad_threshold,
                streaming=args.streaming,
                lookahead_tokens=args.lookahead,
            )
            if is_warmup:
                continue
            latencies.append(result.decode_time_sec)
            decode_times.append(result.decode_time_sec)
            audio_durations.append(result.audio_duration_sec)
            peak_mems.append(result.peak_mem_mb)
            if result.first_token_sec is not None:
                first_tokens.append(result.first_token_sec)

    total_audio = sum(audio_durations)
    total_decode = sum(decode_times)
    rtf = total_decode / total_audio if total_audio > 0 else 0.0
    lat_sorted = sorted(latencies)
    p95_idx = max(0, int(len(lat_sorted) * 0.95) - 1)
    peak_mem_gb = max(peak_mems) / 1024 if peak_mems else 0.0
    device_label = args.device
    if args.streaming:
        device_label = f"{args.device}_stream_la{args.lookahead}"

    perf_row = {
        "profile": profile,
        "device": device_label,
        "rtf": round(rtf, 4),
        "latency_avg_s": round(statistics.mean(latencies), 4) if latencies else 0,
        "latency_p95_s": round(lat_sorted[p95_idx], 4) if lat_sorted else 0,
        "first_token_s": (
            round(statistics.mean(first_tokens), 4) if first_tokens else ""
        ),
        "peak_mem_gb": round(peak_mem_gb, 2),
        "model_size_gb": model_size_gb(),
        "n_utts": len(rows_manifest),
        "measured_repeats": measured_repeats,
        "testset": "mandarin",
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    perf_path = RESULTS_DIR / "E2_performance.csv"
    _append_csv(perf_path, perf_row)

    hw_path = RESULTS_DIR / "E2_hardware.txt"
    hw_note = _hardware_line(args.device)
    if args.streaming:
        hw_note += f"; streaming lookahead={args.lookahead}"
    hw_path.write_text(hw_note + "\n", encoding="utf-8")
    ft = perf_row["first_token_s"]
    print(
        f"\nE2 summary: RTF={perf_row['rtf']}, avg_latency={perf_row['latency_avg_s']}s"
        + (f", first_token={ft}s" if ft != "" else "")
    )
    print(f"Wrote → {perf_path}")
    print(f"Wrote → {hw_path}")


def _append_csv(path: Path, row: dict) -> None:
    import csv

    write_header = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def run_e3(args: argparse.Namespace) -> None:
    rows_manifest = load_manifest(args.manifest)
    if args.limit:
        rows_manifest = rows_manifest[: args.limit]

    if args.vad:
        load_vad()
    load_model(device=args.device)
    outputs: list[dict] = []
    profile = _profile(args.vad)

    for i, row in enumerate(rows_manifest, start=1):
        wav = row.resolved_audio
        cond = row.condition or "?"
        print(f"[{i}/{len(rows_manifest)}] {cond} {wav.name}")
        try:
            result = transcribe_file(
                wav,
                reference=row.reference_text,
                condition=row.condition,
                device=args.device,
                allow_silent=True,
                use_vad=args.vad,
                vad_threshold=args.vad_threshold,
            )
            record = result.to_jsonl_dict()
            outputs.append(record)
            print(f"  → {result.hyp_traditional or '(empty)'}")
        except Exception as exc:
            print(f"  ! {exc}", file=sys.stderr)

    tag = getattr(args, "tag", None) or "hallucination"
    out_path = RESULTS_DIR / "E3_outputs" / f"{profile}_{tag}.jsonl"
    _write_jsonl(outputs, out_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ROCLING 2026 D5 Nemotron experiments")
    sub = parser.add_subparsers(dest="experiment", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
        p.add_argument("--vad", action="store_true", help="啟用 Silero VAD 閘控")
        p.add_argument("--vad-threshold", type=float, default=VAD_THRESHOLD)

    p_e1 = sub.add_parser("e1", help="E1 準確度：國語 CER / ACP 關鍵詞")
    p_e1.add_argument(
        "--testset",
        required=True,
        choices=[TESTSET_MANDARIN, TESTSET_ACP],
        help="mandarin 或 acp（台語 D5 標 N/A，不執行）",
    )
    p_e1.add_argument("--manifest", type=Path, required=True)
    add_common(p_e1)
    p_e1.add_argument("--limit", type=int)
    p_e1.add_argument("--tag", help="另存 E1 輸出後綴，避免覆蓋既有結果")
    p_e1.set_defaults(func=run_e1)

    p_e2 = sub.add_parser("e2", help="E2 延遲與資源：RTF / 延遲 / 記憶體")
    p_e2.add_argument("--manifest", type=Path, required=True, help="固定 50 句 manifest")
    add_common(p_e2)
    p_e2.add_argument(
        "--streaming",
        action="store_true",
        help="以 HF 串流 generate 量測首字延遲（first_token_s）",
    )
    p_e2.add_argument(
        "--lookahead",
        type=int,
        default=DEFAULT_STREAM_LOOKAHEAD,
        help="串流 num_lookahead_tokens（0=80ms, 預設 0）",
    )
    p_e2.set_defaults(func=run_e2)

    p_e3 = sub.add_parser("e3", help="E3 幻覺診斷測試")
    p_e3.add_argument("--manifest", type=Path, required=True)
    add_common(p_e3)
    p_e3.add_argument("--limit", type=int)
    p_e3.add_argument(
        "--tag",
        default="hallucination",
        help="輸出檔名後綴（預設 hallucination；C1 可用 c1_silence）",
    )
    p_e3.set_defaults(func=run_e3)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not hasattr(args, "vad"):
        args.vad = False
    profile = _profile(args.vad)
    print("=" * 55)
    print(f"  ROCLING 2026 · {profile} Nemotron + OpenCC s2twp")
    print(f"  experiment={args.experiment} | device={args.device} | vad={args.vad}")
    print("=" * 55 + "\n")
    args.func(args)


if __name__ == "__main__":
    main()
