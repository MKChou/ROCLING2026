"""
從 DEMAND（Zenodo）建 ACP-DRP C2B 公開底噪子集。

預設 5 場景 × 20 段（5 s、不重疊）= 100 段純環境噪音：
  PCAFETER / OHALLWAY / OOFFICE / PRESTO / DLIVING

用法：
  python scripts/prep/build_c2b_demand.py
  python scripts/prep/build_c2b_demand.py --skip-download   # 已下載 zip 時
  python scripts/prep/build_c2b_demand.py --duration 5 --clips-per-venue 20

授權：DEMAND CC BY-SA 3.0（Thiemann, Ito, Vincent；Zenodo 1227121）
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import sys
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import soundfile as sf

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

from config import DATA_DIR, SAMPLE_RATE  # noqa: E402

ZENODO_RECORD = "1227121"
ZENODO_FILES_BASE = f"https://zenodo.org/records/{ZENODO_RECORD}/files"

# venue_id -> (DEMAND scene code, 對應場域 proxy 說明)
VENUES: dict[str, tuple[str, str]] = {
    "waiting_proxy": ("PCAFETER", "候診／公共區 proxy（自助餐廳）"),
    "corridor_proxy": ("OHALLWAY", "走廊／護理站 proxy（辦公室走廊）"),
    "clinic_proxy": ("OOFFICE", "診間／行政區 proxy（辦公室）"),
    "restaurant_proxy": ("PRESTO", "公共用餐區 proxy（大學餐廳）"),
    "indoor_care_proxy": ("DLIVING", "室內照護環境 proxy（客廳）"),
}

LICENSE = "CC BY-SA 3.0"
CITATION = (
    "Thiemann, J., Ito, N., & Vincent, E. (2013). "
    "DEMAND: a collection of multi-channel recordings of acoustic noise "
    f"in diverse environments. Zenodo. https://doi.org/10.5281/zenodo.{ZENODO_RECORD}"
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download_zip(scene: str, dest: Path, *, force: bool = False) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0 and not force:
        print(f"  keep {dest.name}")
        return dest
    url = f"{ZENODO_FILES_BASE}/{scene}_16k.zip?download=1"
    print(f"  download {url}")
    req = Request(url, headers={"User-Agent": "ROCLING2026-ACP-DRP/1.0"})
    with urlopen(req, timeout=120) as resp:
        data = resp.read()
    dest.write_bytes(data)
    print(f"  wrote {dest.name} ({len(data) / 1e6:.1f} MB)")
    return dest


def extract_ch01(zip_path: Path, extract_dir: Path) -> Path:
    """解壓並回傳 ch01（或排序後第一個）wav。"""
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".wav")]
        if not names:
            raise SystemExit(f"No wav in {zip_path}")
        # Prefer channel 01 / ch01
        preferred = [
            n
            for n in names
            if "ch01" in Path(n).stem.lower()
            or Path(n).stem.lower() in {"01", "1", "ch1"}
        ]
        pick = sorted(preferred or names)[0]
        target = extract_dir / Path(pick).name
        if not target.exists():
            with zf.open(pick) as src, target.open("wb") as dst:
                dst.write(src.read())
        print(f"  extract {pick} -> {target.name}")
        return target


def cut_clips(
    wav_path: Path,
    out_dir: Path,
    *,
    venue_id: str,
    n_clips: int,
    duration_sec: float,
    seed: int,
) -> list[dict]:
    audio, sr = sf.read(str(wav_path), always_2d=False)
    if audio.ndim > 1:
        audio = audio[:, 0]
    if sr != SAMPLE_RATE:
        raise SystemExit(f"{wav_path}: expected {SAMPLE_RATE} Hz, got {sr}")

    clip_n = int(duration_sec * SAMPLE_RATE)
    max_start = len(audio) - clip_n
    if max_start < 0:
        raise SystemExit(f"{wav_path}: too short for {duration_sec}s clips")

    # Non-overlapping grid, then subsample with fixed seed if more than needed
    starts = list(range(0, max_start + 1, clip_n))
    if len(starts) < n_clips:
        raise SystemExit(
            f"{wav_path}: only {len(starts)} non-overlap clips, need {n_clips}"
        )
    rng = np.random.default_rng(seed)
    chosen = sorted(rng.choice(starts, size=n_clips, replace=False).tolist())

    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for i, start in enumerate(chosen, 1):
        clip = np.asarray(audio[start : start + clip_n], dtype=np.float32)
        fname = f"{venue_id}_{i:02d}.wav"
        out_path = out_dir / fname
        sf.write(str(out_path), clip, SAMPLE_RATE)
        rel = Path("..") / "acp_drp" / "C2B_public" / venue_id / fname
        rows.append(
            {
                "audio_path": rel.as_posix(),
                "reference_text": "",
                "language": "zh-tw",
                "condition": "C2B",
                "venue": venue_id,
                "source": "DEMAND",
                "source_scene": "",  # filled by caller
                "source_file": wav_path.name,
                "start_sec": f"{start / SAMPLE_RATE:.3f}",
                "duration_sec": f"{duration_sec:.1f}",
                "license": LICENSE,
            }
        )
    return rows


def write_sources_md(
    path: Path,
    *,
    venues: dict[str, tuple[str, str]],
    zip_hashes: dict[str, str],
    n_clips: int,
    duration_sec: float,
    seed: int,
) -> None:
    lines = [
        "# C2B DEMAND — 來源與授權",
        "",
        f"- **Corpus**: DEMAND (Diverse Environments Multichannel Acoustic Noise Database)",
        f"- **Record**: Zenodo [{ZENODO_RECORD}](https://zenodo.org/records/{ZENODO_RECORD})",
        f"- **License**: {LICENSE}",
        f"- **Citation**: {CITATION}",
        f"- **Channel**: ch01（單聲道）",
        f"- **Format**: {SAMPLE_RATE} Hz mono WAV",
        f"- **Segment**: {duration_sec:g} s × {n_clips} clips / venue；固定種子 {seed}",
        "",
        "## Venue mapping（醫院／照護 proxy，非實地醫院錄音）",
        "",
        "| venue_id | DEMAND scene | 說明 |",
        "|----------|--------------|------|",
    ]
    for vid, (scene, desc) in venues.items():
        lines.append(f"| `{vid}` | `{scene}` | {desc} |")
    lines += [
        "",
        "## Downloaded zip SHA-256",
        "",
        "| file | sha256 |",
        "|------|--------|",
    ]
    for name, digest in sorted(zip_hashes.items()):
        lines.append(f"| `{name}` | `{digest}` |")
    lines += [
        "",
        "## Note",
        "",
        "C2A 為限制內部使用的醫院自錄底噪；C2B 為五場景純環境噪音探針（可公開重建）。",
        "請在論文中標註 DEMAND 授權與引用。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build C2B from DEMAND")
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=DATA_DIR / "acp_drp" / "_cache" / "demand",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DATA_DIR / "acp_drp" / "C2B_public",
    )
    parser.add_argument(
        "--manifest-out",
        type=Path,
        default=DATA_DIR / "manifests" / "c2b_demand.csv",
    )
    parser.add_argument("--clips-per-venue", type=int, default=20)
    parser.add_argument("--duration", type=float, default=5.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--force-download", action="store_true")
    args = parser.parse_args()

    all_rows: list[dict] = []
    zip_hashes: dict[str, str] = {}

    for venue_id, (scene, _desc) in VENUES.items():
        print(f"\n== {venue_id} ({scene}) ==")
        zip_path = args.cache_dir / f"{scene}_16k.zip"
        if not args.skip_download:
            download_zip(scene, zip_path, force=args.force_download)
        elif not zip_path.exists():
            raise SystemExit(f"Missing {zip_path}; omit --skip-download")
        zip_hashes[zip_path.name] = _sha256(zip_path)

        ch01 = extract_ch01(zip_path, args.cache_dir / scene)
        venue_dir = args.output_dir / venue_id
        venue_seed = args.seed + int(
            hashlib.sha256(venue_id.encode("utf-8")).hexdigest()[:8], 16
        ) % 10_000
        rows = cut_clips(
            ch01,
            venue_dir,
            venue_id=venue_id,
            n_clips=args.clips_per_venue,
            duration_sec=args.duration,
            seed=venue_seed,
        )
        for r in rows:
            r["source_scene"] = scene
        all_rows.extend(rows)
        print(f"  wrote {len(rows)} clips -> {venue_dir}")

    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "audio_path",
        "reference_text",
        "language",
        "condition",
        "venue",
        "source",
        "source_scene",
        "source_file",
        "start_sec",
        "duration_sec",
        "license",
    ]
    with args.manifest_out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    sources = args.output_dir / "SOURCES.md"
    write_sources_md(
        sources,
        venues=VENUES,
        zip_hashes=zip_hashes,
        n_clips=args.clips_per_venue,
        duration_sec=args.duration,
        seed=args.seed,
    )

    print(f"\nManifest -> {args.manifest_out} ({len(all_rows)} rows)")
    print(f"Sources  -> {sources}")
    print("Done.")


if __name__ == "__main__":
    main()
