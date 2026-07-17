"""本機公開 Whisper large-v3-turbo 推論（可覆核對照臂）。"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import psutil
import soundfile as sf
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

from config import (
    LANGUAGE_WHISPER_PUBLIC,
    MODEL_ID_WHISPER_PUBLIC,
    PROFILE_WSP_PUBLIC,
    PROFILE_WSP_PUBLIC_VAD,
    SAMPLE_RATE,
    VAD_THRESHOLD,
)
from text_norm import to_traditional
from vad_gate import apply_vad_gate

_processor = None
_model = None
_device: str | None = None
_torch_dtype = None


@dataclass
class TranscribeResult:
    audio: str
    ref: str
    hyp_raw: str
    hyp_traditional: str
    decode_time_sec: float
    audio_duration_sec: float
    profile: str = PROFILE_WSP_PUBLIC
    condition: str = ""
    peak_mem_mb: float = 0.0
    vad_gated: bool = False
    vad_has_speech: bool | None = None
    vad_threshold: float | None = None

    def to_jsonl_dict(self) -> dict:
        rtf = (
            round(self.decode_time_sec / self.audio_duration_sec, 4)
            if self.audio_duration_sec > 0
            else None
        )
        note = "public openai/whisper-large-v3-turbo; OpenCC s2twp post"
        if self.vad_gated:
            note += f"; Silero VAD threshold={self.vad_threshold}"
        row = {
            "audio": self.audio,
            "ref": self.ref,
            "hyp_raw": self.hyp_raw,
            "hyp": self.hyp_traditional,
            "decode_time_sec": round(self.decode_time_sec, 4),
            "audio_duration_sec": round(self.audio_duration_sec, 4),
            "rtf": rtf,
            "peak_mem_mb": round(self.peak_mem_mb, 1),
            "profile": self.profile,
            "note": note,
        }
        if self.condition:
            row["condition"] = self.condition
        if self.vad_gated:
            row["vad_gated"] = True
            row["vad_has_speech"] = bool(self.vad_has_speech)
            row["vad_threshold"] = self.vad_threshold
        return row


def _peak_mem_mb() -> float:
    return psutil.Process().memory_info().rss / (1024 * 1024)


def _resolve_device(device: str) -> str:
    if device == "cpu":
        return "cpu"
    if device == "cuda":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return "cuda" if torch.cuda.is_available() else "cpu"


def load_model(device: str = "auto") -> tuple:
    global _processor, _model, _device, _torch_dtype
    resolved = _resolve_device(device)
    if _model is None or _device != resolved:
        print(f"Loading {MODEL_ID_WHISPER_PUBLIC} (device={resolved})...")
        _torch_dtype = torch.float16 if resolved == "cuda" else torch.float32
        _processor = AutoProcessor.from_pretrained(MODEL_ID_WHISPER_PUBLIC)
        _model = AutoModelForSpeechSeq2Seq.from_pretrained(
            MODEL_ID_WHISPER_PUBLIC,
            torch_dtype=_torch_dtype,
            low_cpu_mem_usage=True,
        )
        _model.to(resolved)
        _model.eval()
        _device = resolved
        print("Model ready.\n")
    return _processor, _model


def prepare_audio(wav_path: Path) -> np.ndarray:
    audio, sr = sf.read(str(wav_path), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != SAMPLE_RATE:
        import librosa

        audio = librosa.resample(audio, orig_sr=sr, target_sr=SAMPLE_RATE)
    return audio.astype(np.float32)


def transcribe_array(audio: np.ndarray, *, device: str = "auto") -> tuple[str, float, float]:
    processor, model = load_model(device=device)
    resolved = _device or _resolve_device(device)
    mem_before = _peak_mem_mb()

    inputs = processor(
        audio,
        sampling_rate=SAMPLE_RATE,
        return_tensors="pt",
    )
    input_features = inputs.input_features.to(resolved, dtype=_torch_dtype)
    generate_kwargs: dict = {}
    try:
        generate_kwargs["forced_decoder_ids"] = processor.get_decoder_prompt_ids(
            language=LANGUAGE_WHISPER_PUBLIC, task="transcribe"
        )
    except Exception:
        generate_kwargs["language"] = LANGUAGE_WHISPER_PUBLIC
        generate_kwargs["task"] = "transcribe"

    start = time.perf_counter()
    with torch.inference_mode():
        generated = model.generate(input_features, **generate_kwargs)
    elapsed = time.perf_counter() - start
    text = processor.batch_decode(generated, skip_special_tokens=True)[0].strip()
    mem_peak = max(mem_before, _peak_mem_mb())
    return text, elapsed, mem_peak


def transcribe_file(
    wav_path: Path,
    *,
    reference: str = "",
    condition: str = "",
    device: str = "auto",
    use_vad: bool = False,
    vad_threshold: float = VAD_THRESHOLD,
) -> TranscribeResult:
    audio = prepare_audio(wav_path)
    duration = len(audio) / SAMPLE_RATE
    profile = PROFILE_WSP_PUBLIC_VAD if use_vad else PROFILE_WSP_PUBLIC
    vad_has_speech: bool | None = None

    if use_vad:
        gated, vad_has_speech = apply_vad_gate(
            audio, threshold=vad_threshold, sampling_rate=SAMPLE_RATE
        )
        if not vad_has_speech or gated is None:
            return TranscribeResult(
                audio=str(wav_path.resolve()),
                ref=reference,
                hyp_raw="",
                hyp_traditional="",
                decode_time_sec=0.0,
                audio_duration_sec=duration,
                profile=profile,
                condition=condition,
                peak_mem_mb=_peak_mem_mb(),
                vad_gated=True,
                vad_has_speech=False,
                vad_threshold=vad_threshold,
            )
        audio = gated

    raw, decode_time, mem_mb = transcribe_array(audio, device=device)
    return TranscribeResult(
        audio=str(wav_path.resolve()),
        ref=reference,
        hyp_raw=raw,
        hyp_traditional=to_traditional(raw),
        decode_time_sec=decode_time,
        audio_duration_sec=duration,
        profile=profile,
        condition=condition,
        peak_mem_mb=mem_mb,
        vad_gated=use_vad,
        vad_has_speech=vad_has_speech,
        vad_threshold=vad_threshold if use_vad else None,
    )
