"""快速檢查 C3/C4 錄音檔數量、格式與長度。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

from config import HALLUC_RAW_DIR  # noqa: E402

C3_REFS = [
    "好", "不要", "是", "對", "可以", "不行", "嗯好", "好喔", "不要了", "是的",
    "沒有", "有", "好嗎", "不是", "對啊", "好啊", "不要啊", "可以啊", "嗯", "喔",
]
C4_REFS = [
    "嗯", "嗯", "啊", "啊", "呃", "呃", "嗯", "啊", "唔", "嗯",
    "啊", "呃", "嗯", "啊", "嗯", "呃", "唔", "嗯", "啊呃", "嗯啊",
]


def sort_key(path: Path) -> int:
    stem = path.stem
    match = re.search(r"\((\d+)\)$", stem)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d+)$", stem)
    if match:
        return int(match.group(1))
    return 1


def probe(path: Path) -> dict:
    import soundfile as sf

    info = sf.info(str(path))
    return {
        "duration_sec": info.duration,
        "sample_rate": info.samplerate,
        "channels": info.channels,
    }


def inspect(label: str, folder: Path, refs: list[str]) -> list[str]:
    issues: list[str] = []
    files = sorted(folder.glob("*.wav"), key=sort_key)
    print(f"\n=== {label}: {len(files)} files (expected 20) ===")
    if len(files) != 20:
        issues.append(f"{label}: 檔案數 {len(files)}，預期 20")

    durations: list[float] = []
    for i, path in enumerate(files, 1):
        info = probe(path)
        dur = info["duration_sec"]
        durations.append(dur)
        ref = refs[i - 1] if i <= len(refs) else "?"
        flags: list[str] = []
        if info["sample_rate"] not in (16000, 48000, 44100):
            flags.append("unusual_sr")
        if dur < 2.0:
            flags.append("too_short")
        if label == "C4" and dur < 2.5:
            flags.append("C4_may_be_short")
        if label == "C3" and dur > 10.0:
            flags.append("C3_may_be_long")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        print(
            f"  {i:02d} {path.name:18s} "
            f"dur={dur:5.2f}s sr={info['sample_rate']} ch={info['channels']} "
            f"ref={ref}{flag_str}"
        )

    if durations:
        print(
            f"  summary: min={min(durations):.2f}s "
            f"max={max(durations):.2f}s avg={sum(durations)/len(durations):.2f}s"
        )
    return issues


def main() -> None:
    all_issues: list[str] = []
    all_issues.extend(inspect("C3", HALLUC_RAW_DIR / "c3_raw", C3_REFS))
    all_issues.extend(inspect("C4", HALLUC_RAW_DIR / "c4_raw", C4_REFS))
    if all_issues:
        print("\n=== Issues ===")
        for item in all_issues:
            print(f"  - {item}")
        sys.exit(1)
    print("\nOK: 20+20 files, format looks acceptable for import.")


if __name__ == "__main__":
    main()
