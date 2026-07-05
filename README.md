# ROCLING 2026 短論文專案

**主題**：面向高齡語音互動應用之 ASR 部署方案比較——準確度、延遲與幻覺穩健性之權衡

本專案為國科會計畫「運用人工智慧語音互動平台（VOICE）提升多重共病高齡者參與預立醫療照護計畫」之前置研究，目標投稿 ROCLING 2026 短論文（4–6 頁）。

## 專案結構

```
├── paper/                        論文與 LaTeX 模板
│   ├── rocling2026_draft.tex     論文初稿（實驗數據待補，【待補】處為填入位置）
│   ├── rocling2026.bib           參考文獻
│   ├── rocling2026.tex           ROCLING 2026 官方模板（原始說明文件）
│   ├── rocling2026.sty           官方樣式檔
│   └── acl_natbib.bst            書目樣式檔
├── docs/                         研究文件
│   ├── ROCLING2026_研究規劃.md    研究計畫（定位、貢獻、實驗設計、時程）
│   └── 實驗交付手冊.md            實驗步驟與資料交付格式（E1–E5）
├── data/
│   └── dict.xlsx                 台語漢字↔國語對照詞典（編寫 ACP 測試句用）
├── reference/                    參考文獻 PDF
│   ├── 2025_ACP and DNR.pdf                  羅醫師 JFMA 論文
│   ├── J AGS 2009 Schickedanz ...pdf         ACP 階段性框架
│   ├── J AGS 2021 Scheerens ...pdf           高齡 eHealth 工具設計
│   └── 2605.17640v1.pdf                      MARQUIS：Video RAG 三階段管線（盧老師提供）
└── proposal/
    └── 申請書115_送國科會版_全.pdf  國科會計畫申請書（含個資，僅限私人倉庫）
```

## 研究概要

- **比較對象（五種部署方案）**：
  - D1：Whisper large-v3（GPU 伺服器）
  - D2：Whisper small（本地端）
  - D3：Whisper small + Silero VAD 門控
  - D4：Kaldi 混合式系統（實驗室既有）
  - D5：Nemotron 3.5 ASR 0.6B + OpenCC 簡繁轉換
- **評估維度**：CER（國語／台語）、ACP 醫療關鍵詞錯誤率、RTF／延遲／記憶體、**幻覺穩健性**（靜音／噪音／極短語音／猶豫音診斷集）、可部署性
- **核心賣點**：在醫療敏感對話場景，輸出穩健性（不幻覺）應與字錯誤率並列為 ASR 選型的第一級指標

## 論文編譯

使用 **XeLaTeX** 編譯（建議 Overleaf，需 AR PL UKai TW 標楷體字型）：

```bash
cd paper
xelatex rocling2026_draft.tex
bibtex rocling2026_draft
xelatex rocling2026_draft.tex
xelatex rocling2026_draft.tex
```

## 待辦事項

- [ ] 向盧老師確認台語測試集（TAT 或實驗室既有）
- [ ] 下載 Common Voice zh-TW 測試集（國語 CER 用）
- [ ] 建置幻覺診斷集（約 100 段音檔）
- [ ] 編寫並錄製 ACP 測試句（30–50 句，可用 `data/dict.xlsx` 輔助）
- [ ] 執行實驗 E1–E5（詳見 `docs/實驗交付手冊.md`）
- [ ] 實驗數據回填論文（`paper/rocling2026_draft.tex` 中【待補】處）

## 重要日期

- **投稿截止**：2026/07/20
- 會議官網：[ROCLING 2026](https://rocling2026.github.io/NTHU_rocling_2026/)
- 投稿系統：[EasyChair](https://easychair.org/conferences/?conf=rocling2026)（雙盲審查，投稿版不可含作者資訊）

## 注意事項

- 本倉庫含國科會申請書（個人資料），**請務必保持 Private**。
- 論文投稿版須匿名：`\roclingfinalcopy` 保持註解、不可出現機構與作者名稱。
