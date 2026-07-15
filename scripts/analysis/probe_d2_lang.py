"""Quick probe: compare D2 API lang values on a few Taiwanese wavs."""

from __future__ import annotations

import argparse
import base64
import csv
import sys
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

from config import LAB_API_TOKEN, LAB_API_URL, MANIFEST_DIR  # noqa: E402

DEFAULT_LANGS = [
    "TA and ZH Medical V1",
    "TA_toned",
    "Chinese & Taiwanese",
    "TW",
]


def probe(wav: Path, langs: list[str]) -> None:
    b64 = base64.b64encode(wav.read_bytes()).decode()
    for lang in langs:
        try:
            resp = requests.post(
                LAB_API_URL,
                data={"lang": lang, "token": LAB_API_TOKEN, "audio": b64},
                timeout=60,
            )
            if resp.status_code != 200:
                print(f"    lang={lang!r:22} -> HTTP {resp.status_code}: {resp.text[:120]}")
                continue
            hyp = resp.json().get("sentence", "").strip()
            print(f"    lang={lang!r:22} -> {hyp or '(empty)'}")
        except Exception as exc:
            print(f"    lang={lang!r:22} -> ERROR: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST_DIR / "taiwanese.csv")
    parser.add_argument("-n", type=int, default=5, help="number of utterances")
    parser.add_argument("--langs", nargs="+", default=DEFAULT_LANGS)
    args = parser.parse_args()

    rows = list(csv.DictReader(args.manifest.open(encoding="utf-8")))[: args.n]

    print("=" * 70)
    print("D2 API lang probe (Taiwanese samples)")
    print(f"URL: {LAB_API_URL}")
    print(f"langs: {args.langs}")
    print("=" * 70)

    for i, row in enumerate(rows, start=1):
        wav = Path(row["audio_path"])
        ref = row["reference_text"]
        print(f"\n[{i}] {wav.name}")
        print(f"    ref: {ref}")
        if not wav.exists():
            print("    ! wav missing, skip")
            continue
        probe(wav, args.langs)


if __name__ == "__main__":
    main()
