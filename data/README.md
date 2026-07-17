# data/ 目錄說明（2026-07-17 整理）

> 原則：**搬位歸檔，不刪檔**。正式探針以 `acp_drp/` 為主；舊 pilot 在 `legacy_pilot/`。

```
data/
├── acp_drp/                    ★ ACP-DRP 正式套件
│   ├── C1_silence/
│   ├── C2A_hospital/           （限制內部使用；wav 見 .gitignore）
│   ├── C2B_public/
│   ├── C3_short/{male,female}/ （已建 100；裁靜音）
│   ├── C4_hesitation/{male,female}/ （已建 100）
│   ├── C5_acp/{male,female}/
│   └── _cache/                 DEMAND zip 快取
├── recording_scripts/          錄音稿
│   ├── acp_recording_script.txt
│   └── c3_c4_recording_script.txt
├── recordings/                 匯入前原始錄音
│   ├── hallucination/c*_raw/   pilot C2–C4 原始檔
│   ├── c3_raw/{male,female}/   C3 擴充原始（48 kHz）
│   ├── c4_raw/{male,female}/   C4 擴充原始（48 kHz）
│   └── c5_raw/female_classmateB/  C5 女聲原始（原 classmateB/）
├── legacy_pilot/               舊 pilot 實驗音檔（保留可重跑）
│   ├── hallucination/C1–C4
│   └── acp_wavs/               舊單一語者 ACP 50 句
├── manifests/                  CSV 清單
└── dict.xlsx
```

## 路徑對照（舊 → 新）

| 舊位置 | 新位置 |
|--------|--------|
| `classmateB/` | `recordings/c5_raw/female_classmateB/` |
| `data/hallucination/` | `legacy_pilot/hallucination/` |
| `data/acp_wavs/` | `legacy_pilot/acp_wavs/` |
| `data/acp_recording_script.txt` | `recording_scripts/acp_recording_script.txt` |
| `data/c3_c4_recording_script.txt` | `recording_scripts/c3_c4_recording_script.txt` |

Manifest 相對路徑已改為 `../legacy_pilot/...`。
