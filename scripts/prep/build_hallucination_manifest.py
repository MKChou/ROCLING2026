"""從 ACP manifest 產生 E3 C5 對照組（預設 001–020）。"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

from manifest import load_manifest  # noqa: E402

PROJECT_ROOT = SCRIPT_DIR.parent.parent
ACP_MANIFEST = PROJECT_ROOT / "data" / "manifests" / "acp.csv"
C1_MANIFEST = PROJECT_ROOT / "data" / "manifests" / "hallucination_C1.csv"
OUT_MANIFEST = PROJECT_ROOT / "data" / "manifests" / "hallucination.csv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--c5-count", type=int, default=20, help="C5 句數（從 ACP 前 N 句）")
    args = parser.parse_args()

    rows: list[dict] = []

    if C1_MANIFEST.exists():
        with C1_MANIFEST.open(encoding="utf-8-sig", newline="") as f:
            rows.extend(list(csv.DictReader(f)))

    acp = load_manifest(ACP_MANIFEST)
    for item in acp[: args.c5_count]:
        rows.append({
            "audio_path": f"../legacy_pilot/acp_wavs/{item.resolved_audio.name}",
            "reference_text": item.reference_text,
            "language": item.language,
            "condition": "C5",
        })

    with OUT_MANIFEST.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["audio_path", "reference_text", "language", "condition"],
        )
        writer.writeheader()
        writer.writerows(rows)

    c5 = sum(1 for r in rows if r.get("condition") == "C5")
    c1 = sum(1 for r in rows if r.get("condition") == "C1")
    print(f"Wrote {OUT_MANIFEST}: C1={c1}, C5={c5}, total={len(rows)}")


if __name__ == "__main__":
    main()
