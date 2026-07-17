"""台語詞彙覆蓋分析（keyword recall + 多餘輸出粗估）。

台語參考句為逗號分隔之詞彙標註（非逐字稿），直接算 CER 會因格式不匹配而
高估錯誤。本腳本以「參考詞彙是否出現在系統輸出中」計算命中率，並以貪婪移除
命中詞彙後的殘餘字元比例，粗估多餘輸出（非嚴格 insertion／precision）：

  recall = 命中詞彙數 / 參考詞彙總數
  leftover_rate = 移除命中詞彙後殘餘字元數 / 輸出字元數

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


def leftover_after_hits(hyp_norm: str, keywords: list[str]) -> tuple[int, int]:
    """Greedily remove matched keywords (longest first); return (leftover, hyp_len)."""
    remaining = hyp_norm
    matched = []
    for kw in keywords:
        kw_n = normalize_for_cer(kw)
        if kw_n and kw_n in remaining:
            matched.append(kw_n)
    for kw_n in sorted(matched, key=len, reverse=True):
        remaining = remaining.replace(kw_n, "", 1)
    return len(remaining), len(hyp_norm)


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
    hyp_chars = 0
    leftover_chars = 0
    ref_kw_chars = 0
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
            hits = [
                kw
                for kw in keywords
                if normalize_for_cer(kw) and normalize_for_cer(kw) in hyp_norm
            ]
            total_kw += len(keywords)
            hit_kw += len(hits)
            ref_kw_chars += sum(len(normalize_for_cer(kw)) for kw in keywords)
            left, hlen = leftover_after_hits(hyp_norm, keywords)
            leftover_chars += left
            hyp_chars += hlen
            if hits:
                utt_any_hit += 1
                if len(examples_hit) < args.samples:
                    examples_hit.append((row["ref"], row["hyp"]))
            else:
                if len(examples_miss) < args.samples:
                    examples_miss.append((row["ref"], row["hyp"]))
            if len(hits) == len(keywords):
                utt_all_hit += 1

    recall = hit_kw / total_kw if total_kw else 0.0
    leftover_rate = leftover_chars / hyp_chars if hyp_chars else 0.0
    covered_rate = 1.0 - leftover_rate

    print(f"輸入：{args.input}")
    print(f"語句數：{utt_total}")
    print(f"參考詞彙總數：{total_kw}")
    print(f"命中詞彙數：{hit_kw}")
    print(f"詞彙命中率（keyword recall）：{recall * 100:.2f}%")
    print(f"至少命中一詞之語句：{utt_any_hit}/{utt_total}（{utt_any_hit / utt_total * 100:.1f}%）")
    print(f"全部詞彙命中之語句：{utt_all_hit}/{utt_total}（{utt_all_hit / utt_total * 100:.1f}%）")
    print(f"參考詞彙字元總數：{ref_kw_chars}")
    print(f"輸出字元總數：{hyp_chars}")
    print(f"移除命中詞後殘餘字元：{leftover_chars}")
    print(f"殘餘字元比例（多餘輸出粗估）：{leftover_rate * 100:.2f}%")
    print(f"命中詞覆蓋輸出比例（粗估）：{covered_rate * 100:.2f}%")

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
