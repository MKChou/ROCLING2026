"""台語詞彙命中率（keyword recall）分析。

台語參考句為逗號分隔之詞彙標註（非逐字稿），直接算 CER 會因格式不匹配而
高估錯誤。本腳本改以「參考詞彙是否出現在系統輸出中」計算命中率：

  recall = 命中詞彙數 / 參考詞彙總數

詞彙與輸出均經 normalize_for_cer 正規化（繁體統一、去標點空白）後，
以子字串比對判定命中。

用法：
  python scripts/analysis/tw_keyword_recall.py
  python scripts/analysis/tw_keyword_recall.py --input results/E1_outputs/D2_taiwanese.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.text_norm import normalize_for_cer  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def split_keywords(ref: str) -> list[str]:
    parts = [p.strip() for p in ref.replace("，", ",").split(",")]
    return [p for p in parts if p]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default=str(PROJECT_ROOT / "results" / "E1_outputs" / "D2_taiwanese.jsonl"),
    )
    parser.add_argument(
        "--samples", type=int, default=5, help="列出前 N 筆命中/未命中範例"
    )
    args = parser.parse_args()

    total_kw = 0
    hit_kw = 0
    utt_total = 0
    utt_any_hit = 0
    utt_all_hit = 0
    examples_hit: list[tuple[str, str]] = []
    examples_miss: list[tuple[str, str]] = []

    with open(args.input, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            keywords = split_keywords(row["ref"])
            if not keywords:
                continue
            hyp_norm = normalize_for_cer(row["hyp"])
            utt_total += 1
            hits = [kw for kw in keywords if normalize_for_cer(kw) and normalize_for_cer(kw) in hyp_norm]
            total_kw += len(keywords)
            hit_kw += len(hits)
            if hits:
                utt_any_hit += 1
                if len(examples_hit) < args.samples:
                    examples_hit.append((row["ref"], row["hyp"]))
            else:
                if len(examples_miss) < args.samples:
                    examples_miss.append((row["ref"], row["hyp"]))
            if len(hits) == len(keywords):
                utt_all_hit += 1

    print(f"輸入：{args.input}")
    print(f"語句數：{utt_total}")
    print(f"參考詞彙總數：{total_kw}")
    print(f"命中詞彙數：{hit_kw}")
    print(f"詞彙命中率（keyword recall）：{hit_kw / total_kw * 100:.2f}%")
    print(f"至少命中一詞之語句：{utt_any_hit}/{utt_total}（{utt_any_hit / utt_total * 100:.1f}%）")
    print(f"全部詞彙命中之語句：{utt_all_hit}/{utt_total}（{utt_all_hit / utt_total * 100:.1f}%）")

    if examples_hit:
        print("\n-- 有命中範例 --")
        for ref, hyp in examples_hit:
            print(f"  ref: {ref}\n  hyp: {hyp}\n")
    if examples_miss:
        print("-- 全未命中範例 --")
        for ref, hyp in examples_miss:
            print(f"  ref: {ref}\n  hyp: {hyp}\n")


if __name__ == "__main__":
    main()
