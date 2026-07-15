"""
從實驗室 147 下載 22k 語料到本機（預設 E:\\data\\22k_corpus）。

  # 建議先下載 ROCLING 實驗用子集（約 139 GB：繁中 + 台語 clean + metadata）
  set LAB_SSH_PASSWORD=你的密碼
  python scripts/download_corpus.py --subset rocling

  # 較完整（再加 zh，約 332 GB）
  python scripts/download_corpus.py --subset rocling-plus-zh

  # 整包 22k_corpus（約 550+ GB，需 E: 足夠空間）
  python scripts/download_corpus.py --subset full

環境變數（可選）：
  LAB_SSH_HOST=140.116.245.147
  LAB_SSH_PORT=24680
  LAB_SSH_USER=an4096750
  LAB_SSH_PASSWORD=...
  ROCLING_CORPUS_ROOT=E:/data/22k_corpus
"""

from __future__ import annotations

import argparse
import os
import stat
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

REMOTE_BASE = "Linux_DATA/synthesis/corpus/corpus_manager/22k_corpus"

SUBSETS: dict[str, list[str]] = {
    # trandition_zh ~12G + tw_clean ~127G + metadata
    "rocling": ["trandition_zh", "tw_clean", "metadata.csv"],
    # 再加 zh ~193G（MAGIC 等，國語未必適用 zh-TW）
    "rocling-plus-zh": ["trandition_zh", "tw_clean", "zh", "metadata.csv"],
    # 台語含文字檔（tw 整包約 212G；tw_clean 僅 wav）
    "tw": ["tw"],
    # 僅 tw/corpus（建議先 SSH 執行 du -sh tw/corpus 確認大小）
    "tw-corpus": ["tw/corpus"],
    # 整個 22k_corpus 目錄（含 tw 212G 等）
    "full": ["."],
}


def _connect():
    import paramiko

    host = os.environ.get("LAB_SSH_HOST", "140.116.245.147")
    port = int(os.environ.get("LAB_SSH_PORT", "24680"))
    user = os.environ.get("LAB_SSH_USER", "an4096750")
    pwd = os.environ.get("LAB_SSH_PASSWORD", "")
    if not pwd:
        pwd = input(f"SSH password for {user}@{host}:{port}: ").strip()

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting {user}@{host}:{port} ...")
    client.connect(
        host, port=port, username=user, password=pwd,
        timeout=30, banner_timeout=120, auth_timeout=30,
        allow_agent=False, look_for_keys=False,
    )
    return client, client.open_sftp()


def _remote_path(*parts: str) -> str:
    home = f"/home/{os.environ.get('LAB_SSH_USER', 'an4096750')}"
    rel = "/".join(p.strip("/") for p in parts if p and p != ".")
    return f"{home}/{REMOTE_BASE}/{rel}" if rel else f"{home}/{REMOTE_BASE}"


def _download_file(sftp, remote: str, local: Path, skip_existing: bool) -> None:
    if skip_existing and local.exists() and local.stat().st_size > 0:
        return
    local.parent.mkdir(parents=True, exist_ok=True)
    sftp.get(remote, str(local))


def _download_tree(sftp, remote_dir: str, local_dir: Path, skip_existing: bool, stats: dict) -> None:
    try:
        entries = sftp.listdir_attr(remote_dir)
    except FileNotFoundError:
        print(f"  SKIP (not found): {remote_dir}")
        return

    local_dir.mkdir(parents=True, exist_ok=True)
    for ent in entries:
        rname = ent.filename
        if rname in (".", ".."):
            continue
        remote = f"{remote_dir.rstrip('/')}/{rname}"
        local = local_dir / rname

        if stat.S_ISDIR(ent.st_mode):
            _download_tree(sftp, remote, local, skip_existing, stats)
        else:
            if skip_existing and local.exists() and local.stat().st_size == ent.st_size:
                stats["skipped"] += 1
                continue
            try:
                t0 = time.perf_counter()
                _download_file(sftp, remote, local, skip_existing=False)
                stats["files"] += 1
                stats["bytes"] += ent.st_size
                if stats["files"] % 500 == 0:
                    mb = stats["bytes"] / (1024**2)
                    print(f"  ... {stats['files']} files, {mb:.0f} MB", flush=True)
            except Exception as exc:
                stats["errors"] += 1
                print(f"  ERR {remote}: {exc}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download lab 22k_corpus to local disk")
    parser.add_argument(
        "--subset",
        choices=list(SUBSETS.keys()),
        default="rocling",
        help="rocling=繁中+tw_clean (~139GB); full=整包",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=Path(os.environ.get("ROCLING_CORPUS_ROOT", r"E:\data\22k_corpus")),
        help="Local destination root",
    )
    parser.add_argument("--no-skip-existing", action="store_true", help="Re-download all files")
    args = parser.parse_args()

    dest: Path = args.dest.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    skip = not args.no_skip_existing

    print("=" * 60)
    print(f"  Destination: {dest}")
    print(f"  Subset: {args.subset}")
    print(f"  Items: {SUBSETS[args.subset]}")
    print("=" * 60)

    client, sftp = _connect()
    stats = {"files": 0, "bytes": 0, "skipped": 0, "errors": 0}
    try:
        for item in SUBSETS[args.subset]:
            if item == ".":
                remote = _remote_path()
                local = dest
            elif item.endswith(".csv"):
                remote = _remote_path(item)
                local = dest / item
                print(f"\n>> {item}")
                _download_file(sftp, remote, local, skip)
                stats["files"] += 1
                continue
            else:
                remote = _remote_path(item)
                local = dest / item
            print(f"\n>> {item}\n   remote: {remote}\n   local:  {local}")
            _download_tree(sftp, remote, local, skip, stats)
    finally:
        sftp.close()
        client.close()

    print("\n" + "=" * 60)
    print(f"Done. downloaded={stats['files']} skipped={stats['skipped']} errors={stats['errors']}")
    print(f"Total bytes: {stats['bytes'] / (1024**3):.2f} GB")
    print(f"Corpus root: {dest}")


if __name__ == "__main__":
    main()
