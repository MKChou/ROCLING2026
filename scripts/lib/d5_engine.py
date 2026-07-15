"""D5 Nemotron 3.5 ASR 0.6B 推論引擎（批次 + 可選串流首字／VAD）。"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from threading import Thread

import numpy as np
import psutil
import soundfile as sf
from transformers import AutoModelForRNNT, AutoProcessor, TextIteratorStreamer

from config import (
    LANGUAGE_D5,
    MODEL_ID_D5,
    PROFILE_D5,
    PROFILE_D5_VAD,
    SAMPLE_RATE,
    VAD_THRESHOLD,
)
from text_norm import to_traditional
from vad_gate import apply_vad_gate

_processor = None
_model = None
_device: str | None = None

# 論文表 1：80 ms chunk → lookahead=0；批次主臂沿用較大 context（1120 ms）
DEFAULT_BATCH_LOOKAHEAD = 13
DEFAULT_STREAM_LOOKAHEAD = 0


@dataclass
class TranscribeResult:
    audio: str
    ref: str
    hyp_simplified: str
    hyp_traditional: str
    decode_time_sec: float
    audio_duration_sec: float
    profile: str = PROFILE_D5
    condition: str = ""
    peak_mem_mb: float = 0.0
    first_token_sec: float | None = None
    vad_gated: bool = False
    vad_has_speech: bool | None = None

    def to_jsonl_dict(self) -> dict:
        rtf = (
            round(self.decode_time_sec / self.audio_duration_sec, 4)
            if self.audio_duration_sec > 0
            else None
        )
        row = {
            "audio": self.audio,
            "ref": self.ref,
            "hyp_simplified": self.hyp_simplified,
            "hyp": self.hyp_traditional,
            "decode_time_sec": round(self.decode_time_sec, 4),
            "audio_duration_sec": round(self.audio_duration_sec, 4),
            "rtf": rtf,
            "peak_mem_mb": round(self.peak_mem_mb, 1),
            "profile": self.profile,
        }
        if self.condition:
            row["condition"] = self.condition
        if self.first_token_sec is not None:
            row["first_token_sec"] = round(self.first_token_sec, 4)
        if self.vad_gated:
            row["vad_gated"] = True
            row["vad_has_speech"] = bool(self.vad_has_speech)
        return row


def _peak_mem_mb() -> float:
    return psutil.Process().memory_info().rss / (1024 * 1024)


def _resolve_device(device: str) -> str:
    import torch

    if device == "cpu":
        return "cpu"
    if device == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("Requested device=cuda but torch.cuda.is_available() is False")
        return "cuda"
    return "cuda" if torch.cuda.is_available() else "cpu"


def load_model(device: str = "auto", *, lookahead_tokens: int | None = None) -> tuple:
    global _processor, _model, _device
    resolved = _resolve_device(device)
    if _model is None or _device != resolved:
        print(f"Loading {MODEL_ID_D5} (device={resolved})...")
        _processor = AutoProcessor.from_pretrained(MODEL_ID_D5)
        la = DEFAULT_BATCH_LOOKAHEAD if lookahead_tokens is None else lookahead_tokens
        _processor.set_num_lookahead_tokens(la)
        if resolved == "cpu":
            _model = AutoModelForRNNT.from_pretrained(MODEL_ID_D5).to("cpu")
        else:
            _model = AutoModelForRNNT.from_pretrained(MODEL_ID_D5, device_map=resolved)
        _device = resolved
        print("Model ready.\n")
    elif lookahead_tokens is not None and _processor is not None:
        _processor.set_num_lookahead_tokens(lookahead_tokens)
    return _processor, _model


def set_lookahead(lookahead_tokens: int) -> None:
    processor, _ = load_model()
    processor.set_num_lookahead_tokens(lookahead_tokens)


def warmup(device: str = "auto") -> None:
    """E2：預熱模型，避免首次推論計入量測。"""
    silence = np.zeros(SAMPLE_RATE, dtype=np.float32)
    transcribe_array(silence, device=device)


def prepare_audio(wav_path: Path, *, allow_silent: bool = False) -> np.ndarray:
    audio, sr = sf.read(str(wav_path), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    if sr != SAMPLE_RATE:
        import librosa

        audio = librosa.resample(audio, orig_sr=sr, target_sr=SAMPLE_RATE)

    peak = float(np.max(np.abs(audio)))
    if peak < 0.01:
        if allow_silent:
            return audio.astype(np.float32)
        raise RuntimeError(f"Audio too quiet: {wav_path}")

    return (audio / peak * 0.95).astype(np.float32)


def transcribe_array(audio: np.ndarray, *, device: str = "auto") -> tuple[str, float, float]:
    processor, model = load_model(device=device)
    mem_before = _peak_mem_mb()

    start = time.perf_counter()
    inputs = processor(audio, sampling_rate=SAMPLE_RATE, language=LANGUAGE_D5)
    inputs = inputs.to(model.device, dtype=model.dtype)
    output = model.generate(**inputs, return_dict_in_generate=True)
    text = processor.decode(output.sequences, skip_special_tokens=True)
    if isinstance(text, list):
        text = text[0] if text else ""
    elapsed = time.perf_counter() - start
    mem_peak = max(mem_before, _peak_mem_mb())
    return text.strip(), elapsed, mem_peak


def _safe_audio_slice(audio: np.ndarray, start_idx: int, end_idx: int) -> np.ndarray:
    """HF 串流公式的 start_idx 可為負（n_fft/2 左 pad）；numpy 負索引不能直接切片。"""
    need = end_idx - start_idx
    if need <= 0:
        return np.zeros(0, dtype=np.float32)
    left_pad = max(0, -start_idx)
    right_pad = max(0, end_idx - audio.shape[0])
    lo = max(0, start_idx)
    hi = min(audio.shape[0], end_idx)
    body = audio[lo:hi]
    if left_pad or right_pad:
        return np.concatenate(
            [
                np.zeros(left_pad, dtype=np.float32),
                body,
                np.zeros(right_pad, dtype=np.float32),
            ]
        ).astype(np.float32)
    return body.astype(np.float32)


def _stream_feature_generator(processor, model, audio: np.ndarray, first_chunk_inputs):
    yield first_chunk_inputs.input_features[:, : processor.num_mel_frames_first_audio_chunk, :]

    mel_frame_idx = processor.num_mel_frames_first_audio_chunk
    hop_length = processor.feature_extractor.hop_length
    n_fft = processor.feature_extractor.n_fft
    chunk_samples = processor.num_samples_per_audio_chunk
    start_idx = mel_frame_idx * hop_length - n_fft // 2
    # 持續餵到音檔末端（含最後不足一 chunk 的補零）
    while start_idx < audio.shape[0]:
        end_idx = start_idx + chunk_samples
        chunk = _safe_audio_slice(audio, start_idx, end_idx)
        if chunk.shape[0] < n_fft:
            break
        inputs = processor(
            chunk,
            sampling_rate=SAMPLE_RATE,
            is_streaming=True,
            is_first_audio_chunk=False,
            language=LANGUAGE_D5,
            return_tensors="pt",
        )
        inputs = inputs.to(model.device, dtype=model.dtype)
        yield inputs.input_features
        mel_frame_idx += processor.num_mel_frames_per_audio_chunk
        start_idx = mel_frame_idx * hop_length - n_fft // 2


def transcribe_array_streaming(
    audio: np.ndarray,
    *,
    device: str = "auto",
    lookahead_tokens: int = DEFAULT_STREAM_LOOKAHEAD,
) -> tuple[str, float, float, float]:
    """
    串流解碼，回傳 (text, total_sec, first_token_sec, mem_mb)。
    first_token_sec：自 generate 啟動到第一個非空文字 chunk 的牆鐘時間。
    """
    processor, model = load_model(device=device, lookahead_tokens=lookahead_tokens)
    mem_before = _peak_mem_mb()

    # 過短音檔補零，避免小於 first chunk
    min_len = int(processor.num_samples_first_audio_chunk)
    if audio.shape[0] < min_len:
        audio = np.pad(audio, (0, min_len - audio.shape[0]))

    first_chunk_inputs = processor(
        audio[: processor.num_samples_first_audio_chunk],
        sampling_rate=SAMPLE_RATE,
        is_streaming=True,
        is_first_audio_chunk=True,
        language=LANGUAGE_D5,
        return_tensors="pt",
    )
    first_chunk_inputs = first_chunk_inputs.to(model.device, dtype=model.dtype)

    streamer = TextIteratorStreamer(processor.tokenizer, skip_special_tokens=True)
    generate_kwargs = {
        **first_chunk_inputs,
        "input_features": _stream_feature_generator(processor, model, audio, first_chunk_inputs),
        "streamer": streamer,
    }

    chunks: list[str] = []
    first_token_sec: float | None = None
    err: list[BaseException] = []

    def _run_generate() -> None:
        try:
            model.generate(**generate_kwargs)
        except BaseException as exc:  # noqa: BLE001 — 傳到主執行緒
            err.append(exc)
            streamer.end()

    t0 = time.perf_counter()
    thread = Thread(target=_run_generate)
    thread.start()
    for text_chunk in streamer:
        if first_token_sec is None and text_chunk and text_chunk.strip():
            first_token_sec = time.perf_counter() - t0
        chunks.append(text_chunk)
    thread.join()
    elapsed = time.perf_counter() - t0
    if err:
        raise RuntimeError(f"streaming generate failed: {err[0]}") from err[0]
    if first_token_sec is None:
        first_token_sec = elapsed
    text = "".join(chunks).strip()
    mem_peak = max(mem_before, _peak_mem_mb())
    return text, elapsed, first_token_sec, mem_peak


def transcribe_file(
    wav_path: Path,
    *,
    reference: str = "",
    condition: str = "",
    device: str = "auto",
    allow_silent: bool = False,
    use_vad: bool = False,
    vad_threshold: float = VAD_THRESHOLD,
    streaming: bool = False,
    lookahead_tokens: int = DEFAULT_STREAM_LOOKAHEAD,
) -> TranscribeResult:
    audio = prepare_audio(wav_path, allow_silent=allow_silent)
    duration = len(audio) / SAMPLE_RATE
    profile = PROFILE_D5_VAD if use_vad else PROFILE_D5
    vad_has_speech: bool | None = None
    first_token_sec: float | None = None

    if use_vad:
        gated, vad_has_speech = apply_vad_gate(
            audio, threshold=vad_threshold, sampling_rate=SAMPLE_RATE
        )
        if not vad_has_speech or gated is None:
            return TranscribeResult(
                audio=str(wav_path.resolve()),
                ref=reference,
                hyp_simplified="",
                hyp_traditional="",
                decode_time_sec=0.0,
                audio_duration_sec=duration,
                profile=profile,
                condition=condition,
                peak_mem_mb=_peak_mem_mb(),
                first_token_sec=None,
                vad_gated=True,
                vad_has_speech=False,
            )
        audio = gated

    if streaming:
        simplified, decode_time, first_token_sec, mem_mb = transcribe_array_streaming(
            audio, device=device, lookahead_tokens=lookahead_tokens
        )
    else:
        simplified, decode_time, mem_mb = transcribe_array(audio, device=device)

    return TranscribeResult(
        audio=str(wav_path.resolve()),
        ref=reference,
        hyp_simplified=simplified,
        hyp_traditional=to_traditional(simplified),
        decode_time_sec=decode_time,
        audio_duration_sec=duration,
        profile=profile,
        condition=condition,
        peak_mem_mb=mem_mb,
        first_token_sec=first_token_sec,
        vad_gated=use_vad,
        vad_has_speech=vad_has_speech,
    )


def model_size_gb() -> float:
    """估算 HF cache 中模型權重大小（GB）。"""
    try:
        from huggingface_hub import scan_cache_dir

        cache = scan_cache_dir()
        total = 0
        for repo in cache.repos:
            if MODEL_ID_D5.replace("/", "--") in repo.repo_id.replace("/", "--") or repo.repo_id.endswith(
                MODEL_ID_D5.split("/")[-1]
            ):
                for rev in repo.revisions:
                    total += rev.size_on_disk
        return round(total / (1024**3), 2) if total else 0.0
    except Exception:
        return 0.0
