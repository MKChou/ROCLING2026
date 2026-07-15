"""Silero VAD 閘控：無語音 → 空輸出；有語音 → 拼接語音段後再送 ASR。"""

from __future__ import annotations

import numpy as np
import torch

SAMPLE_RATE = 16000
DEFAULT_THRESHOLD = 0.5

_model = None
_get_speech_timestamps = None


def load_vad() -> None:
    global _model, _get_speech_timestamps
    if _model is not None:
        return
    print("Loading Silero VAD (torch.hub snakers4/silero-vad)...")
    model, utils = torch.hub.load(
        repo_or_dir="snakers4/silero-vad",
        model="silero_vad",
        trust_repo=True,
    )
    _model = model
    _get_speech_timestamps = utils[0]
    print("Silero VAD ready.\n")


def speech_segments(
    audio: np.ndarray,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    sampling_rate: int = SAMPLE_RATE,
) -> list[dict]:
    """回傳 Silero 時間戳列表（單位：樣本）。無語音則空列表。"""
    load_vad()
    assert _model is not None and _get_speech_timestamps is not None
    wav = torch.from_numpy(np.asarray(audio, dtype=np.float32))
    if wav.ndim > 1:
        wav = wav.mean(dim=-1)
    return _get_speech_timestamps(
        wav,
        _model,
        sampling_rate=sampling_rate,
        threshold=threshold,
    )


def apply_vad_gate(
    audio: np.ndarray,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    sampling_rate: int = SAMPLE_RATE,
) -> tuple[np.ndarray | None, bool]:
    """
    Returns
    -------
    gated_audio :
        有語音時為拼接後的語音段；無語音時為 None（呼叫端應輸出空字串）。
    has_speech :
        是否偵測到語音。
    """
    stamps = speech_segments(audio, threshold=threshold, sampling_rate=sampling_rate)
    if not stamps:
        return None, False
    chunks = [audio[int(s["start"]) : int(s["end"])] for s in stamps]
    return np.concatenate(chunks).astype(np.float32), True
