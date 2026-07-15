"""CER / 幻覺判定用文字正規化。"""

from __future__ import annotations

import re
import unicodedata

try:
    from opencc import OpenCC

    _opencc = OpenCC("s2twp")
except ImportError:
    _opencc = None


def to_traditional(text: str) -> str:
    if not text or _opencc is None:
        return text
    return _opencc.convert(text)


def strip_special_markers(text: str) -> str:
    """移除 ASR 特殊標記，如實驗室 API 的 <{silent}>。"""
    if not text:
        return ""
    return re.sub(r"<\{[^}]*\}>", "", text).strip()


def normalize_for_cer(text: str) -> str:
    """全形→半形、去標點空白、統一繁體。"""
    if not text:
        return ""
    text = strip_special_markers(text)
    text = unicodedata.normalize("NFKC", text)
    text = to_traditional(text)
    text = "".join(
        c
        for c in text
        if not c.isspace() and not unicodedata.category(c).startswith("P")
    )
    return text


def char_len(text: str) -> int:
    return len(normalize_for_cer(text))


def is_nonempty_hypothesis(text: str) -> bool:
    return char_len(text) > 0
