"""E3 摘要：含 C3/C4 錯例與插入字數明細。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

from text_norm import char_len, normalize_for_cer  # noqa: E402

OUT = SCRIPT_DIR.parent.parent / "results" / "E3_outputs"


def load(profile: str, tag: str) -> list[dict]:
    path = OUT / f"{profile}_{tag}.jsonl"
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def summarize(profile: str, rows: list[dict]) -> None:
    print(f"\n{'='*50}\n[{profile}]")
    for cond in ("C1", "C2", "C2A", "C2B", "C3", "C4", "C5"):
        sub = [r for r in rows if r.get("condition") == cond]
        if not sub:
            continue
        if cond in ("C1", "C2", "C2A", "C2B"):
            nonempty = sum(1 for r in sub if char_len(r.get("hyp", "")) > 0)
            print(f"  {cond} 非空率: {nonempty/len(sub)*100:.1f}% ({nonempty}/{len(sub)})")
        elif cond in ("C3", "C4"):
            inserts = [
                max(0, char_len(r.get("hyp", "")) - char_len(r.get("ref", "")))
                for r in sub
            ]
            mismatches = [
                r for r in sub
                if normalize_for_cer(r.get("hyp", "")) != normalize_for_cer(r.get("ref", ""))
            ]
            print(
                f"  {cond} 平均插入字數: {sum(inserts)/len(inserts):.2f} | "
                f"辨識與參考不同: {len(mismatches)}/{len(sub)}"
            )
            for r in mismatches[:5]:
                print(f"    ref={r.get('ref')!r} -> hyp={r.get('hyp')!r}")
        else:
            import jiwer
            refs = [normalize_for_cer(r.get("ref", "")) for r in sub]
            hyps = [normalize_for_cer(r.get("hyp", "")) for r in sub]
            cer = jiwer.cer(refs, hyps) * 100 if refs else 0
            print(f"  {cond} CER: {cer:.2f}% ({len(sub)} 段)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize E3 / ACP-DRP outputs")
    parser.add_argument("--tag", default="hallucination")
    args = parser.parse_args()

    suffix = f"_{args.tag}"
    profiles = [
        p.stem.removesuffix(suffix)
        for p in sorted(OUT.glob(f"*{suffix}.jsonl"))
    ]
    if not profiles:
        raise SystemExit(f"No {args.tag} jsonl in {OUT}")
    for profile in profiles:
        summarize(profile, load(profile, args.tag))


if __name__ == "__main__":
    main()
