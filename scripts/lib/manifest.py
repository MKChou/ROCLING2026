"""讀取與解析實驗 manifest.csv。"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ManifestRow:
    audio_path: str
    reference_text: str
    language: str = "zh-tw"
    condition: str = ""  # E3 幻覺診斷集用（C1–C5）

    @property
    def resolved_audio(self) -> Path:
        return resolve_audio_path(self._manifest_dir, self.audio_path)

    def bind_manifest_dir(self, manifest_dir: Path) -> ManifestRow:
        self._manifest_dir = manifest_dir
        return self

    _manifest_dir: Path = Path(".")


def resolve_audio_path(manifest_dir: Path, audio_path: str) -> Path:
    raw = Path(audio_path)
    candidates = [
        raw,
        manifest_dir / raw,
        manifest_dir.parent / raw,
        manifest_dir.parent.parent / raw,
    ]
    for path in candidates:
        if path.is_file():
            return path.resolve()
    raise FileNotFoundError(f"Audio not found: {audio_path} (manifest dir: {manifest_dir})")


def load_manifest(manifest_path: Path) -> list[ManifestRow]:
    manifest_path = manifest_path.resolve()
    manifest_dir = manifest_path.parent
    rows: list[ManifestRow] = []

    with manifest_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            audio = (row.get("audio_path") or row.get("audio") or "").strip()
            if not audio:
                raise ValueError(f"Row {i}: missing audio_path in {manifest_path}")

            item = ManifestRow(
                audio_path=audio,
                reference_text=(row.get("reference_text") or row.get("ref") or "").strip(),
                language=(row.get("language") or "zh-tw").strip(),
                condition=(row.get("condition") or "").strip(),
            ).bind_manifest_dir(manifest_dir)
            rows.append(item)

    if not rows:
        raise ValueError(f"Manifest is empty: {manifest_path}")
    return rows
