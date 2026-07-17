"""
本機公開 Whisper large-v3-turbo 對照臂（WspPublic / WspPublic_VAD）

  python scripts/exp/run_whisper.py e3 --manifest data/manifests/hallucination.csv --device cuda
  python scripts/exp/run_whisper.py e3 --manifest data/manifests/hallucination.csv --device cuda --vad
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

from config import (  # noqa: E402
    MODEL_ID_WHISPER_PUBLIC,
    PROFILE_WSP_PUBLIC,
    PROFILE_WSP_PUBLIC_VAD,
    RESULTS_DIR,
    TESTSET_ACP,
    TESTSET_MANDARIN,
    VAD_THRESHOLD,
)
from manifest import load_manifest  # noqa: E402
from vad_gate import load_vad  # noqa: E402
from whisper_engine import load_model, transcribe_file  # noqa: E402


def _write_jsonl(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {len(rows)} lines → {path}")


def _profile(use_vad: bool) -> str:
    return PROFILE_WSP_PUBLIC_VAD if use_vad else PROFILE_WSP_PUBLIC


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
                use_vad=args.vad,
                vad_threshold=args.vad_threshold,
            )
            outputs.append(result.to_jsonl_dict())
            print(f"  → {result.hyp_traditional or '(empty)'}")
        except Exception as exc:
            print(f"  ! {exc}", file=sys.stderr)

    tag = getattr(args, "tag", None) or "hallucination"
    out_path = RESULTS_DIR / "E3_outputs" / f"{profile}_{tag}.jsonl"
    _write_jsonl(outputs, out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Public Whisper large-v3-turbo baseline")
    sub = parser.add_subparsers(dest="experiment", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
        p.add_argument("--limit", type=int)
        p.add_argument("--vad", action="store_true", help="啟用 Silero VAD 閘控")
        p.add_argument("--vad-threshold", type=float, default=VAD_THRESHOLD)

    p_e1 = sub.add_parser("e1")
    p_e1.add_argument("--testset", required=True, choices=[TESTSET_MANDARIN, TESTSET_ACP])
    p_e1.add_argument("--manifest", type=Path, required=True)
    add_common(p_e1)
    p_e1.add_argument("--tag", help="另存 E1 輸出後綴，避免覆蓋既有結果")
    p_e1.set_defaults(func=run_e1)

    p_e3 = sub.add_parser("e3")
    p_e3.add_argument("--manifest", type=Path, required=True)
    add_common(p_e3)
    p_e3.add_argument(
        "--tag",
        default="hallucination",
        help="輸出檔名後綴（預設 hallucination；C1 可用 c1_silence）",
    )
    p_e3.set_defaults(func=run_e3)

    args = parser.parse_args()
    profile = _profile(args.vad)
    print("=" * 55)
    print(f"  ROCLING 2026 · {profile} {MODEL_ID_WHISPER_PUBLIC}")
    print(f"  experiment={args.experiment} | device={args.device} | vad={args.vad}")
    print("=" * 55 + "\n")
    args.func(args)


if __name__ == "__main__":
    main()
