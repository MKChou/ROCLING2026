"""Quick analysis of D2 taiwanese E1 outputs."""

from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

import jiwer

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

from text_norm import normalize_for_cer  # noqa: E402

PROJECT_ROOT = SCRIPT_DIR.parent.parent
JSONL = PROJECT_ROOT / "results" / "E1_outputs" / "D2_taiwanese.jsonl"
OUT = PROJECT_ROOT / "results" / "analysis" / "tw_samples.txt"


def main() -> None:
    rows = [json.loads(line) for line in JSONL.read_text(encoding="utf-8").splitlines() if line.strip()]
    rep = sum(1 for r in rows if re.search(r"(.{2,})\1{5,}", r.get("hyp") or ""))
    empty = sum(1 for r in rows if not normalize_for_cer(r.get("hyp", "")))
    silent = sum(1 for r in rows if "<{silent}>" in (r.get("hyp") or ""))

    cers: list[float] = []
    for r in rows:
        ref = normalize_for_cer(r.get("ref", ""))
        hyp = normalize_for_cer(r.get("hyp", ""))
        if ref:
            cers.append(jiwer.cer(ref, hyp))

    cers_excl = [c for c in cers if c <= 1.0]
    print(f"n={len(rows)} repetition={rep} empty={empty} silent={silent}")
    print(f"overall CER={sum(cers)/len(cers)*100:.2f}%")
    print(f"median CER={statistics.median(cers)*100:.2f}%")
    print(f"mean CER (excl rep>100%)={statistics.mean(cers_excl)*100:.2f}% n={len(cers_excl)}")

    lines: list[str] = []
    for r in rows[:15]:
        lines.append(f"REF: {r['ref']}\nHYP: {r['hyp']}\n")
    lines.append("--- worst ---\n")
    scored = sorted(
        (
            (jiwer.cer(normalize_for_cer(r["ref"]), normalize_for_cer(r["hyp"])), r)
            for r in rows
            if normalize_for_cer(r["ref"])
        ),
        key=lambda x: x[0],
        reverse=True,
    )
    for cer, r in scored[:10]:
        lines.append(f"CER {cer * 100:.1f}%\nREF: {r['ref']}\nHYP: {r['hyp']}\n")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
