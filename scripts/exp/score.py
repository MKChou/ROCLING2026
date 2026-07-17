"""
彙總實驗指標 → results/E1_accuracy.csv、results/E3_hallucination.csv

  python scripts/score.py e1            # 自動掃描所有 profile
  python scripts/score.py e1 --profile D5
  python scripts/score.py e3
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

from config import RESULTS_DIR, TESTSET_ACP, TESTSET_MANDARIN, TESTSET_TAIWANESE  # noqa: E402
from keywords import has_keyword_hallucination, keyword_error_stats  # noqa: E402
from text_norm import char_len, is_nonempty_hypothesis, normalize_for_cer  # noqa: E402

E1_TESTSETS = (TESTSET_MANDARIN, TESTSET_ACP, TESTSET_TAIWANESE)


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _cer(references: list[str], hypotheses: list[str]) -> float:
    import jiwer

    refs = [normalize_for_cer(r) for r in references]
    hyps = [normalize_for_cer(h) for h in hypotheses]
    if not refs:
        return 0.0
    return round(jiwer.cer(refs, hyps) * 100, 2)


def _discover_profiles(out_dir: Path, suffix: str) -> list[str]:
    profiles = set()
    for p in out_dir.glob(f"*_{suffix}.jsonl"):
        profiles.add(p.name[: -len(f"_{suffix}.jsonl")])
    return sorted(profiles)


def score_e1(profiles: list[str] | None, tag: str | None = None) -> None:
    out_dir = RESULTS_DIR / "E1_outputs"
    if not out_dir.exists():
        raise SystemExit(f"No outputs: {out_dir}")

    if not profiles:
        if tag:
            suffix = f"_acp_{tag}.jsonl"
            profiles = sorted(
                p.name[: -len(suffix)] for p in out_dir.glob(f"*{suffix}")
            )
        else:
            profiles = sorted({p.name.rsplit("_", 1)[0] for p in out_dir.glob("*.jsonl")})
    summary_rows: list[dict] = []

    for profile in profiles:
        for testset in E1_TESTSETS:
            suffix = f"{testset}_{tag}" if tag else testset
            path = out_dir / f"{profile}_{suffix}.jsonl"
            if not path.exists():
                continue

            records = _load_jsonl(path)
            refs = [r.get("ref", "") for r in records]
            hyps = [r.get("hyp", "") for r in records]
            avg_rtf = _avg([r.get("rtf") for r in records])

            row = {
                "profile": profile,
                "testset": testset,
                "n_utts": len(records),
                "cer": _cer(refs, hyps),
                "avg_rtf": avg_rtf,
                "keyword_total": "",
                "keyword_err": "",
                "keyword_err_rate": "",
            }
            if testset == TESTSET_ACP:
                row.update(keyword_error_stats(refs, hyps))
            summary_rows.append(row)

            # D5 額外比較 OpenCC 前後（僅 mandarin）
            if testset == TESTSET_MANDARIN and any(r.get("hyp_simplified") for r in records):
                hyps_simp = [r.get("hyp_simplified", "") for r in records]
                summary_rows.append({
                    "profile": profile,
                    "testset": f"{testset}_raw_simplified",
                    "n_utts": len(records),
                    "cer": _cer(refs, hyps_simp),
                    "avg_rtf": avg_rtf,
                    "keyword_total": "",
                    "keyword_err": "",
                    "keyword_err_rate": "",
                })

    if not summary_rows:
        raise SystemExit("No E1 jsonl files to score")

    out_name = f"E1_accuracy_{tag}.csv" if tag else "E1_accuracy.csv"
    out_path = RESULTS_DIR / out_name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "profile", "testset", "n_utts", "cer", "avg_rtf",
        "keyword_total", "keyword_err", "keyword_err_rate",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"Wrote {len(summary_rows)} rows → {out_path}")
    for row in summary_rows:
        print(f"  [{row['profile']}] {row['testset']}: CER={row['cer']}%", end="")
        if row.get("keyword_err_rate") != "":
            print(f", keyword_err={row['keyword_err_rate']}%", end="")
        print()


def _avg(values: list) -> float | str:
    nums = [v for v in values if isinstance(v, (int, float))]
    return round(sum(nums) / len(nums), 4) if nums else ""


def score_e3(profiles: list[str] | None, *, tag: str = "hallucination") -> None:
    out_dir = RESULTS_DIR / "E3_outputs"
    if not profiles:
        profiles = _discover_profiles(out_dir, tag)
    if not profiles:
        raise SystemExit(f"No {tag} jsonl in {out_dir}")

    out_rows: list[dict] = []
    for profile in profiles:
        path = out_dir / f"{profile}_{tag}.jsonl"
        if not path.exists():
            print(f"Skip (not found): {path}")
            continue
        for r in _load_jsonl(path):
            ref = r.get("ref", "")
            hyp = r.get("hyp", "")
            # JSONL 可能存 hyp 或 hyp_traditional
            if not hyp:
                hyp = r.get("hyp_traditional", "")
            out_rows.append({
                "profile": profile,
                "condition": r.get("condition", ""),
                "audio_path": r.get("audio", ""),
                "ref_text": ref,
                "hyp_text": hyp,
                "hyp_len": char_len(hyp),
                "is_nonempty": int(is_nonempty_hypothesis(hyp)),
                "keyword_hallucinated": int(has_keyword_hallucination(ref, hyp)),
            })

    if not out_rows:
        raise SystemExit(f"No rows scored for tag={tag}")

    out_name = "E3_hallucination.csv" if tag == "hallucination" else f"E3_{tag}.csv"
    out_path = RESULTS_DIR / out_name
    fields = list(out_rows[0].keys())
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Wrote {len(out_rows)} rows → {out_path}")

    for profile in profiles:
        print(f"\n[{profile}]")
        prof_rows = [r for r in out_rows if r["profile"] == profile]
        for cond in ("C1", "C2", "C2A", "C2B", "C3", "C4", "C5"):
            subset = [r for r in prof_rows if r["condition"] == cond]
            if not subset:
                continue
            if cond in ("C1", "C2", "C2A", "C2B"):
                n_nonempty = sum(r["is_nonempty"] for r in subset)
                rate = n_nonempty / len(subset) * 100
                print(f"  {cond} 非空: {n_nonempty}/{len(subset)} ({rate:.1f}%)")
            elif cond in ("C3", "C4"):
                inserts = [
                    max(0, r["hyp_len"] - char_len(r["ref_text"])) for r in subset
                ]
                avg_ins = sum(inserts) / len(inserts) if inserts else 0
                print(f"  {cond} 平均插入字數: {avg_ins:.2f}")
            else:  # C5
                cer = _cer([r["ref_text"] for r in subset], [r["hyp_text"] for r in subset])
                kw_rate = sum(r["keyword_hallucinated"] for r in subset) / len(subset) * 100
                print(f"  {cond} 正常語音: CER={cer}%, 關鍵詞幻覺率={kw_rate:.1f}% ({len(subset)} 段)")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="experiment", required=True)

    p1 = sub.add_parser("e1")
    p1.add_argument("--profile", nargs="*", default=None)
    p1.add_argument("--tag", help="計分帶有相同後綴的 E1 輸出")
    p1.set_defaults(func=lambda a: score_e1(a.profile, a.tag))

    p3 = sub.add_parser("e3")
    p3.add_argument("--profile", nargs="*", default=None)
    p3.add_argument("--tag", default="hallucination")
    p3.set_defaults(func=lambda a: score_e3(a.profile, tag=a.tag))

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
