"""產出論文圖 1：準確度—延遲權衡散點圖（paper/tradeoff.pdf）。"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

from config import RESULTS_DIR  # noqa: E402


def _read_e1_cer(profile: str, testset: str) -> float:
    path = RESULTS_DIR / "E1_accuracy.csv"
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["profile"] == profile and row["testset"] == testset:
                return float(row["cer"])
    raise KeyError(f"{profile}/{testset} not in E1_accuracy.csv")


def _read_e2_latency(profile: str, device: str) -> float:
    path = RESULTS_DIR / "E2_performance.csv"
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["profile"] == profile and row["device"] == device:
                return float(row["latency_avg_s"])
    raise KeyError(f"{profile}/{device} not in E2_performance.csv")


def _halluc_rate(profile: str) -> float:
    path = RESULTS_DIR / "E3_hallucination.csv"
    subset = []
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["profile"] == profile and row["condition"] in ("C1", "C2"):
                subset.append(int(row["is_nonempty"]))
    if not subset:
        return 0.0
    return sum(subset) / len(subset) * 100


def main() -> None:
    import matplotlib.pyplot as plt

    points = [
        {
            "label": "D2 Whisper API",
            "cer": _read_e1_cer("D2", "mandarin"),
            "latency": _read_e2_latency("D2", "remote-api (network incl.)"),
            "halluc": _halluc_rate("D2"),
            "color": "#2563eb",
        },
        {
            "label": "D5 Nemotron (GPU)",
            "cer": _read_e1_cer("D5", "mandarin"),
            "latency": _read_e2_latency("D5", "auto"),
            "halluc": _halluc_rate("D5"),
            "color": "#16a34a",
        },
        {
            "label": "D5 Nemotron (CPU)",
            "cer": _read_e1_cer("D5", "mandarin"),
            "latency": _read_e2_latency("D5", "cpu"),
            "halluc": _halluc_rate("D5"),
            "color": "#86efac",
        },
    ]

    fig, ax = plt.subplots(figsize=(4.2, 3.2))
    for pt in points:
        size = 80 + pt["halluc"] * 12
        ax.scatter(
            pt["latency"],
            pt["cer"],
            s=size,
            c=pt["color"],
            edgecolors="black",
            linewidths=0.6,
            zorder=3,
            label=pt["label"],
        )
        ax.annotate(
            pt["label"].replace(" ", "\n"),
            (pt["latency"], pt["cer"]),
            textcoords="offset points",
            xytext=(6, 6),
            fontsize=7,
        )

    ax.set_xlabel("平均延遲 (s) — 國語 50 句 E2")
    ax.set_ylabel("國語 CER (%)")
    ax.set_title("準確度—延遲權衡（點越大＝幻覺率越高）")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    out = PROJECT_ROOT / "paper" / "tradeoff.pdf"
    fig.savefig(out, bbox_inches="tight")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
