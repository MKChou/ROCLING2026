"""將 acp_wavs 內音檔統一為 16 kHz 單聲道 wav（覆蓋原檔）。"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DIR = SCRIPT_DIR.parent / "data" / "acp_wavs"
SAMPLE_RATE = 16000


def find_ffmpeg() -> str:
    import shutil

    path = shutil.which("ffmpeg")
    if not path:
        raise SystemExit("ffmpeg not found. Install: winget install Gyan.FFmpeg")
    return path


def convert_file(ffmpeg: str, src: Path) -> None:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False, dir=src.parent) as tmp:
        tmp_path = Path(tmp.name)
    try:
        subprocess.run(
            [ffmpeg, "-y", "-i", str(src), "-ar", str(SAMPLE_RATE), "-ac", "1", str(tmp_path)],
            check=True,
            capture_output=True,
        )
        tmp_path.replace(src)
        print(f"  {src.name} → 16kHz mono")
    except subprocess.CalledProcessError as exc:
        tmp_path.unlink(missing_ok=True)
        raise SystemExit(f"Failed: {src.name}\n{exc.stderr.decode(errors='replace')}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize ACP wav to 16kHz mono")
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--pattern", default="acp_*.wav")
    args = parser.parse_args()

    ffmpeg = find_ffmpeg()
    files = sorted(args.dir.glob(args.pattern))
    if not files:
        raise SystemExit(f"No files: {args.dir / args.pattern}")

    print(f"Converting {len(files)} files in {args.dir}")
    for path in files:
        convert_file(ffmpeg, path)
    print("Done.")


if __name__ == "__main__":
    main()
