"""E5 質性錯誤分析：漏掉的關鍵詞排行 + CER 最差句 → results/error_analysis.txt"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

import jiwer  # noqa: E402

from config import RESULTS_DIR  # noqa: E402
from keywords import keywords_in_text  # noqa: E402
from text_norm import normalize_for_cer  # noqa: E402


def analyze(profile: str, lines: list[str]) -> None:
    path = RESULTS_DIR / "E1_outputs" / f"{profile}_acp.jsonl"
    if not path.exists():
        return
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]

    lines.append(f"===== {profile} (ACP {len(rows)} 句) =====")
    failed: dict[str, list[str]] = {}
    scored = []
    for r in rows:
        ref, hyp = r["ref"], r["hyp"]
        refn, hypn = normalize_for_cer(ref), normalize_for_cer(hyp)
        cer = jiwer.cer(refn, hypn) if refn else 0.0
        scored.append((cer, ref, hyp))
        for kw in keywords_in_text(ref):
            if normalize_for_cer(kw) not in hypn:
                failed.setdefault(kw, []).append(hyp)

    lines.append("\n漏掉的關鍵詞（次數）:")
    for kw, hyps in sorted(failed.items(), key=lambda x: -len(x[1])):
        lines.append(f"  {kw} ×{len(hyps)}")
        for h in hyps:
            lines.append(f"      hyp: {h}")

    scored.sort(reverse=True)
    lines.append("\nCER 最差 10 句:")
    for cer, ref, hyp in scored[:10]:
        lines.append(f"  {cer * 100:5.1f}%  REF: {ref}")
        lines.append(f"          HYP: {hyp}")
    lines.append("")


def main() -> None:
    lines: list[str] = []
    for profile in ("D5", "D2"):
        analyze(profile, lines)
    out = RESULTS_DIR / "analysis" / "error_analysis.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
