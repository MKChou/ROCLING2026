# 錄音原始檔（手機匯出，未轉檔）

與實驗用 `data/hallucination/C*`（16 kHz mono）分開存放。

## 目錄

| 路徑 | 內容 | 匯入指令 |
|------|------|----------|
| `hallucination/c2_raw/` | C2 環境噪音原始檔（已匯入可空） | `python scripts/prep/import_c2_noise.py` |
| `hallucination/c3_raw/` | C3 極短語音 20 段（`錄製.wav` …） | `python scripts/prep/import_c3_c4.py` |
| `hallucination/c4_raw/` | C4 猶豫音 20 段 + `c4_refs.csv` | 同上 |

## 檔名規則

- `錄製.wav` = 第 1 段，`錄製 (2).wav` = 第 2 段，…，`錄製 (20).wav` = 第 20 段
- C4 參考文字以 `c4_refs.csv` 的 `reference_text` 為準（可與建議清單順序不同）

## ACP 錄音

見 `data/acp_wavs/README.md`（`raw/` 子目錄存原始檔）。
