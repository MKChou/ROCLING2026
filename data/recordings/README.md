# 錄音原始檔（手機匯出，未轉檔）

與實驗用音檔分開存放：
- 舊 pilot 處理後：`data/legacy_pilot/hallucination/`
- 正式 ACP-DRP：`data/acp_drp/`

## 目錄

| 路徑 | 內容 | 匯入指令 |
|------|------|----------|
| `hallucination/c2_raw/` | C2 環境噪音原始檔（已匯入可空） | `python scripts/prep/import_c2_noise.py` |
| `hallucination/c3_raw/` | C3 極短語音 pilot 20 段 | `python scripts/prep/import_c3_c4.py`（legacy） |
| `hallucination/c4_raw/` | C4 猶豫音 pilot 20 段 + `c4_refs.csv` | 同上 |
| `c3_raw/{male,female}/` | C3 擴充男女各 50（原始 48 kHz） | `python scripts/prep/build_c3_c4.py` |
| `c4_raw/{male,female}/` | C4 擴充男女各 50（原始 48 kHz） | 同上 |
| `c5_raw/female_classmateB/` | C5 女聲原始（原專案根目錄 `classmateB/`） | `python scripts/prep/build_c5_acp.py` |

## 檔名規則

- `錄製.wav` = 第 1 段，`錄製 (2).wav` = 第 2 段，…
- C4 參考文字以 `c4_refs.csv` 的 `reference_text` 為準

## 錄音稿

見 `data/recording_scripts/`。
