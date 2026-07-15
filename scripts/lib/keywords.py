"""ACP 關鍵詞比對（E1 關鍵詞錯誤率、E3 關鍵詞幻覺）。"""

from __future__ import annotations

from config import ACP_KEYWORDS
from text_norm import normalize_for_cer


def _norm_keyword(kw: str) -> str:
    return normalize_for_cer(kw)


NORMALIZED_KEYWORDS = [_norm_keyword(k) for k in ACP_KEYWORDS]


def keywords_in_text(text: str) -> list[str]:
    """回傳文本中出現的關鍵詞（原始詞表用語）。"""
    norm_text = normalize_for_cer(text)
    found: list[str] = []
    for raw, normed in zip(ACP_KEYWORDS, NORMALIZED_KEYWORDS, strict=True):
        if normed and normed in norm_text:
            found.append(raw)
    return found


def keyword_error_stats(references: list[str], hypotheses: list[str]) -> dict:
    """
  E1 ACP：參考句中應出現的關鍵詞，是否在辨識結果中正確出現。
  回傳 total, errors, error_rate（百分比）。
  """
    total = 0
    errors = 0
    for ref, hyp in zip(references, hypotheses, strict=True):
        expected = keywords_in_text(ref)
        hyp_norm = normalize_for_cer(hyp)
        for kw in expected:
            total += 1
            if _norm_keyword(kw) not in hyp_norm:
                errors += 1
    rate = (errors / total * 100) if total else 0.0
    return {"keyword_total": total, "keyword_err": errors, "keyword_err_rate": round(rate, 2)}


def has_keyword_hallucination(reference: str, hypothesis: str) -> bool:
    """輸出含關鍵詞，但參考文本沒有 → 關鍵詞幻覺。"""
    ref_kws = set(keywords_in_text(reference))
    hyp_kws = keywords_in_text(hypothesis)
    return any(kw not in ref_kws for kw in hyp_kws)
