# ROCLING 2026 短論文專案

**主題**：面向高齡語音互動應用之 ASR 部署方案比較——準確度、延遲與幻覺穩健性之權衡

本專案為國科會計畫「運用人工智慧語音互動平台（VOICE）提升多重共病高齡者參與預立醫療照護計畫」之前置研究，目標投稿 ROCLING 2026 短論文（4–8 頁正文）。

> **專案狀態（2026-07-07）**：Phase 1（實驗 + 論文初稿）已完成，**暫停至 7/13 與指導老師討論**。  
> 後續步驟見 **[docs/專案狀態與後續.md](docs/專案狀態與後續.md)**。

## 專案結構

```
ROCLING2026/
├── paper/                        論文（XeLaTeX，建議 Overleaf 編譯）
│   ├── rocling2026_draft.tex     論文稿（D2 vs D5，數據已填）
│   ├── rocling2026.bib           參考文獻
│   ├── rocling2026.sty            官方樣式
│   └── acl_natbib.bst            ★ 書目樣式（Overleaf 必須上傳）
├── docs/
│   ├── 專案狀態與後續.md           ★ 交接文件（7/13 後從這裡接續）
│   ├── 論文規劃_v2.md             論文架構與數據對照
│   ├── 實驗紀錄.md                實驗結果日誌
│   ├── 實驗交付手冊.md            E1–E3 細節（初版，部分過時）
│   ├── 實驗室環境.md / 實驗室語料路徑.md
│   └── ROCLING2026_研究規劃.md    初版五系統規劃（歷史保留）
├── data/manifests/               測試集 manifest
├── scripts/                      實驗腳本（詳見 scripts/README.md）
│   └── run_all.ps1               ★ 一鍵重跑全部實驗
├── results/                      實驗產出（gitignore，本機保留）
└── proposal/                     國科會申請書（含個資，倉庫必須 Private）
```

## 研究概要

- **實測比較**（Phase 1 完成）：
  - **D2**：Whisper large-v3-turbo 雲端 API（`lang=TA and ZH Medical V1`，與 app 一致；伺服器 OpenCC s2twp + 靜音標記）
  - **D5**：Nemotron 0.6B 本機串流（簡體 → app 端 OpenCC s2twp；不支援台語）
- **未實測**（論文未來工作）：D1 / D3+VAD / D4 Kaldi
- **評估維度**：CER、ACP 關鍵詞、RTF/延遲、幻覺穩健性（100 段）、語言覆蓋、可部署性
- **場景定位**：語音互動 **app** 的 ASR 後端選型（雲端 API vs 裝置端內嵌）

## 主要結果（Medical V1，2026-07-07）

| 指標 | D2 Whisper API | D5 Nemotron |
|------|----------------|-------------|
| 國語 CER（500 句） | 6.48% | **5.57%** |
| 台語 CER（500 句） | **9.0%** | N/A |
| 台語詞彙命中率 recall | **86.06%** | N/A |
| ACP 關鍵詞錯誤率 | **31.88%** | 39.13% |
| E2 平均延遲 | **0.23 s**（含網路） | **0.18 s**（GPU）/ 0.42 s（CPU） |
| 幻覺率（靜音+噪音 40 段） | **0%** | **0%** |

> 舊 `lang=Chinese & Taiwanese` 整合錯誤基線：台語 CER 88.35%、recall 11.22%（非主結果）。

## 快速開始

```powershell
# 環境（首次）
powershell -ExecutionPolicy Bypass -File scripts\env\setup_env.ps1
python scripts\env\verify_env.py

# 一鍵重跑（約 18 分鐘；需 API + HF 快取）
powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1
```

## 論文編譯（Overleaf）

- Compiler：**XeLaTeX**
- 必備四檔：`rocling2026_draft.tex`、`rocling2026.bib`、`rocling2026.sty`、`acl_natbib.bst`
- 順序：`\bibliographystyle{acl_natbib}` → `\bibliography{rocling2026}`
- 投稿版：`\roclingfinalcopy` 保持註解（雙盲）

## 時程

| 日期 | 事項 |
|------|------|
| **7/07** | Phase 1 完成（實驗 + 論文初稿） |
| **7/13** | 與指導老師討論 |
| **7/14–18** | 依老師意見修稿 |
| **7/20** | **EasyChair 投稿截止** |

## 待辦（7/13 後）

見 [docs/專案狀態與後續.md](docs/專案狀態與後續.md) 第六節。摘要：

- [ ] 7/13 師生討論、修稿
- [ ] Overleaf 最終 PDF
- [ ] 7/20 EasyChair 投稿

## 重要連結

- 會議：[ROCLING 2026](https://rocling2026.github.io/NTHU_rocling_2026/)
- 投稿：[EasyChair](https://easychair.org/conferences/?conf=rocling2026)（雙盲）

## 注意事項

- 本倉庫含國科會申請書（個資），**請保持 Private**。
- `results/` 在 gitignore；重跑前 `run_all.ps1` 會自動備份至 `results_backup_*`。
