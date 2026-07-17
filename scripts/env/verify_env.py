"""驗證實驗室環境是否就緒（依賴、GPU、模型、ffmpeg）。"""

from __future__ import annotations

import platform
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

PASS = "OK"
FAIL = "FAIL"


def check(label: str, ok: bool, detail: str = "") -> bool:
    status = PASS if ok else FAIL
    msg = f"[{status}] {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return ok


def main() -> int:
    print("=" * 55)
    print("ROCLING 2026 實驗環境檢查")
    print("=" * 55)

    ok = True
    ok &= check("Python", sys.version_info >= (3, 10), sys.version.split()[0])

    for pkg in ("torch", "transformers", "soundfile", "librosa", "opencc", "jiwer", "psutil", "numpy"):
        try:
            __import__(pkg if pkg != "opencc" else "opencc")
            check(f"import {pkg}", True)
        except ImportError as exc:
            ok &= check(f"import {pkg}", False, str(exc))

    ffmpeg = shutil.which("ffmpeg")
    ok &= check("ffmpeg", ffmpeg is not None, ffmpeg or "winget install Gyan.FFmpeg")

    try:
        import torch

        cuda = torch.cuda.is_available()
        if cuda:
            gpu = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            check("CUDA GPU", True, f"{gpu}, {vram:.1f} GB VRAM")
        else:
            check("CUDA GPU", False, "不可用，D5 將用 CPU")
    except Exception as exc:
        ok &= check("CUDA GPU", False, str(exc))

    import psutil

    ram_gb = psutil.virtual_memory().total / (1024**3)
    cpu = platform.processor() or platform.machine()
    print(f"\n[INFO] CPU: {cpu}")
    print(f"[INFO] RAM: {ram_gb:.1f} GB")

    # 模型載入 smoke test
    print("\n--- D5 模型載入測試 ---")
    try:
        from d5_engine import load_model, model_size_gb

        load_model(device="auto")
        size = model_size_gb()
        check("Nemotron 0.6B", True, f"cache ~{size} GB" if size else "已載入")
    except Exception as exc:
        ok &= check("Nemotron 0.6B", False, str(exc))

    # ACP 錄音檔（legacy pilot 男聲；擴充版見 data/acp_drp/C5_acp）
    project_root = SCRIPT_DIR.parent.parent
    acp_dir = project_root / "data" / "legacy_pilot" / "acp_wavs"
    wavs = sorted(acp_dir.glob("acp_*.wav"))
    c5_dir = project_root / "data" / "acp_drp" / "C5_acp"
    c5_wavs = list(c5_dir.rglob("*.wav")) if c5_dir.exists() else []
    check("ACP 錄音（legacy）", len(wavs) > 0, f"{len(wavs)} 個 acp_*.wav")
    check("ACP-DRP C5", len(c5_wavs) > 0, f"{len(c5_wavs)} 個 wav")

    print("\n" + ("環境就緒，可開始實驗。" if ok else "有項目未通過，請先執行 setup_env.ps1"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
