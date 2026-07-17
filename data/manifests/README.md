# 測試集 manifest 說明

每個測試集一個 CSV。`audio_path` 相對於本目錄（`data/manifests/`）。

## 通用欄位

```csv
audio_path,reference_text,language
../legacy_pilot/acp_wavs/acp_001.wav,我想要簽預立醫療決定。,zh-tw
```

## 各測試集檔名約定

| 檔案 | 用途 | 實驗 |
|------|------|------|
| `mandarin.csv` | 國語 500 句 | E1 |
| `taiwanese.csv` | 台語 500 句 | E1 |
| `e2_latency_50.csv` | 國語固定 50 句 | E2 |
| `acp.csv` | legacy 單一語者 ACP 50 | E1（舊） |
| `c5_acp.csv` | ACP-DRP C5 男女 100 | E1 擴充 |
| `hallucination.csv` | pilot 探針（含 condition） | E3 主表 |
| `c1_silence.csv` | ACP-DRP C1×100 | E3 擴充 |
| `c2a_hospital.csv` | ACP-DRP C2A×100 | E3 擴充 |
| `c2b_demand.csv` | ACP-DRP C2B×100 | E3 擴充 |
| `c3_short.csv` | ACP-DRP C3×100（男女各 50） | E3 擴充 |
| `c4_hesitation.csv` | ACP-DRP C4×100（男女各 50） | E3 擴充 |
| `c3_c4.csv` | C3+C4 合併×200（跑實驗用） | E3 擴充 |

## Pilot 幻覺診斷集（E3）

```csv
audio_path,reference_text,language,condition
../legacy_pilot/hallucination/C1/silence_01_3s.wav,,zh-tw,C1
../legacy_pilot/hallucination/C3/short_01.wav,好,zh-tw,C3
```

C2–C4 原始檔：`data/recordings/hallucination/`。  
正式擴充：`data/acp_drp/`（見 `data/README.md`、`docs/ACP-DRP資料集規格.md`）。
