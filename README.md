# ROCLING 2026 短論文專案

**主題**：面向安全關鍵部署的 ASR 風險探針框架（ACP-DRP），以預立醫療照護計畫語音為案例

投稿 ROCLING 2026 短論文。論文主角是 **Deployment Risk Probe Framework**；雲端／邊緣管線僅為 case study。

> **狀態（2026-07-17）**：敘事已收斂；C1／C2A／C2B／C3／C4／C5 均已建（主表數字仍待重跑替換）。  
> 交接見 **[docs/專案狀態與後續.md](docs/專案狀態與後續.md)**、資料規格見 **[docs/ACP-DRP資料集規格.md](docs/ACP-DRP資料集規格.md)**、資料目錄見 **[data/README.md](data/README.md)**。

## 專案結構

```
ROCLING2026/
├── paper/                         投稿 LaTeX（XeLaTeX／Overleaf）
│   ├── rocling2026_draft.tex      ★ 主稿
│   ├── rocling2026.bib
│   ├── rocling2026.sty
│   └── acl_natbib.bst
├── docs/
│   ├── 專案狀態與後續.md
│   ├── ACP-DRP資料集規格.md
│   ├── C2A實驗交接.md
│   └── …
├── data/                          見 data/README.md
│   ├── acp_drp/                   ★ 正式探針套件
│   ├── recording_scripts/         錄音稿（C3／C4／C5）
│   ├── recordings/                原始錄音（含 c5_raw/female_classmateB）
│   ├── legacy_pilot/              舊 pilot（不刪）
│   └── manifests/
├── scripts/                       見 scripts/README.md
├── results/                       實驗產出（gitignore）
├── reference/                     文獻 PDF
└── proposal/                      申請書（含個資 → 倉庫須 Private）
```

## 研究概要

- **框架**：分層部署風險探針（靜音幻覺／漏接／高風險改寫）+ ACP 關鍵詞與台語詞彙命中率對照
- **套件**：ACP-DRP；主表仍為先導試驗（C3／C4：$N{=}20$/條件）；C1／C2／C5 已擴充複核
- **底噪雙軌**：C2A 醫院自錄與 C2B DEMAND；C2A 待逐段人工聽檢
- **案例**：雲端 Whisper（`lang-med`）vs 邊緣 Nemotron 0.6B；另含 lang／VAD 消融
- **非主角**：GPU／CPU／延遲／記憶體（論文僅 footnote）

## 快速開始

```powershell
powershell -ExecutionPolicy Bypass -File scripts\env\setup_env.ps1
python scripts\env\verify_env.py
powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1
```

## 論文編譯（Overleaf）

- Compiler：**XeLaTeX**
- 四檔：`rocling2026_draft.tex`、`rocling2026.bib`、`rocling2026.sty`、`acl_natbib.bst`
- 投稿版：`\roclingfinalcopy` 保持註解（雙盲）

## 注意事項

- 倉庫含申請書個資，**請保持 Private**。
- `results/` 在 gitignore；重跑前 `run_all.ps1` 會備份至 `results_backup_*`。
- 整理原則：搬位歸檔、**不刪實驗音檔／結果**。
