"""比較 E3 探針：非空／不符／服藥改寫等（多 profile）。"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

from text_norm import char_len, is_nonempty_hypothesis, normalize_for_cer  # noqa: E402

RESULTS = SCRIPT_DIR.parent.parent / "results"
OUT_DIR = RESULTS / "E3_outputs"
ANALYSIS = RESULTS / "analysis"


def load_profile(profile: str, tag: str) -> list[dict]:
    path = OUT_DIR / f"{profile}_{tag}.jsonl"
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def summarize(profile: str, rows: list[dict]) -> dict:
    c12 = [r for r in rows if r.get("condition") in ("C1", "C2")]
    c2a = [r for r in rows if r.get("condition") == "C2A"]
    c2b = [r for r in rows if r.get("condition") == "C2B"]
    c34 = [r for r in rows if r.get("condition") in ("C3", "C4")]
    c3 = [r for r in rows if r.get("condition") == "C3"]
    c5 = [r for r in rows if r.get("condition") == "C5"]

    def mismatch(r: dict) -> bool:
        return normalize_for_cer(r.get("hyp", "")) != normalize_for_cer(r.get("ref", ""))

    empty = [r for r in c34 if char_len(r.get("hyp", "")) == 0 and mismatch(r)]
    nonempty_mm = [r for r in c34 if char_len(r.get("hyp", "")) > 0 and mismatch(r)]
    fuyao = [
        r
        for r in c3
        if "服藥" in (r.get("hyp") or "")
        and ("不要" in (r.get("ref") or ""))
    ]
    c5_cer = None
    if c5:
        import jiwer

        refs = [normalize_for_cer(r.get("ref", "")) for r in c5]
        hyps = [normalize_for_cer(r.get("hyp", "")) for r in c5]
        c5_cer = round(jiwer.cer(refs, hyps) * 100, 2)

    def nonempty_fraction(items: list[dict]) -> str:
        if not items:
            return ""
        count = sum(1 for r in items if is_nonempty_hypothesis(r.get("hyp", "")))
        return f"{count}/{len(items)}"

    stats = {
        "profile": profile,
        "nonempty_c12": nonempty_fraction(c12),
        "nonempty_c2a": nonempty_fraction(c2a),
        "nonempty_c2b": nonempty_fraction(c2b),
        "mismatch_c34": f"{sum(1 for r in c34 if mismatch(r))}/{len(c34)}" if c34 else "",
        "empty_c34": f"{len(empty)}/{len(c34)}" if c34 else "",
        "nonempty_mismatch_c34": f"{len(nonempty_mm)}/{len(c34)}" if c34 else "",
        "fuyao_c3": f"{len(fuyao)}/{len(c3)}" if c3 else "",
        "c5_cer_pct": c5_cer if c5_cer is not None else "",
    }
    print(f"\n[{profile}]")
    if c12:
        print(f"  非語音非空 C1+C2 (pilot): {stats['nonempty_c12']}")
    if c2a:
        print(f"  非語音非空 C2A: {stats['nonempty_c2a']}")
    if c2b:
        print(f"  非語音非空 C2B: {stats['nonempty_c2b']}")
    if c34:
        print(
            f"  極短+猶豫不符: {stats['mismatch_c34']} "
            f"(空 {stats['empty_c34']}, 非空不符 {stats['nonempty_mismatch_c34']})"
        )
    if c3:
        print(f"  C3 不要→服藥: {stats['fuyao_c3']}")
    if fuyao:
        for r in fuyao:
            print(f"    {r.get('ref')!r} → {r.get('hyp')!r}")
    if c5_cer is not None:
        print(f"  C5 CER: {c5_cer}%")
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare E3 / ACP-DRP profiles")
    parser.add_argument("--tag", default="hallucination")
    args = parser.parse_args()

    suffix = f"_{args.tag}"
    profiles = [
        p.stem.removesuffix(suffix)
        for p in sorted(OUT_DIR.glob(f"*{suffix}.jsonl"))
    ]
    if not profiles:
        raise SystemExit(f"No {args.tag} jsonl in {OUT_DIR}")
    rows_out = []
    for profile in profiles:
        rows_out.append(summarize(profile, load_profile(profile, args.tag)))
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    out_name = "e3_profile_compare.csv" if args.tag == "hallucination" else f"e3_{args.tag}_compare.csv"
    out_csv = ANALYSIS / out_name
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        writer.writeheader()
        writer.writerows(rows_out)
    print(f"\nWrote → {out_csv}")


if __name__ == "__main__":
    main()
