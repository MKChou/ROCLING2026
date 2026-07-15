# 測試集 manifest 說明

每個測試集一個 CSV，欄位如下。

## 通用欄位

```csv
audio_path,reference_text,language
../acp_wavs/acp_001.wav,我想要簽預立醫療決定。,zh-tw
```

- `audio_path`：相對於本 CSV 所在目錄的路徑
- `reference_text`：標準答案（幻覺 C1/C2 留空）
- `language`：語言標記

## 各測試集檔名約定

| 檔案 | 用途 | 實驗 |
|------|------|------|
| `mandarin.csv` | Common Voice zh-TW 抽樣 500–1000 句 | E1 |
| `e2_latency_50.csv` | 從 mandarin 固定抽 50 句（同一批給所有系統） | E2 |
| `acp.csv` | ACP 錄音 30–50 句 | E1 |
| `hallucination.csv` | 幻覺診斷集 100 段，多一欄 `condition` | E3 |

## 幻覺診斷集（E3）額外欄位

```csv
audio_path,reference_text,language,condition
../hallucination/C1/silence_01_3s.wav,,zh-tw,C1
../hallucination/C3/short_01.wav,好,zh-tw,C3
```

| condition | 說明 | 段數 |
|-----------|------|------|
| C1 | 純靜音（`make_silence.py` 產生） | 20 |
| C2 | 環境噪音（手機錄製） | 20 |
| C3 | 極短語音 1–3 字 | 20 |
| C4 | 猶豫音 | 20 |
| C5 | 從 ACP 挑 20 句 | 20 |

C1 可先執行：`python scripts/prep/make_silence.py`，再手動合併 C2–C5 至 `hallucination.csv`。

C2–C4 手機原始檔與 `c4_refs.csv` 見 `data/recordings/hallucination/`；匯入用 `scripts/prep/import_c2_noise.py`、`scripts/prep/import_c3_c4.py`。
