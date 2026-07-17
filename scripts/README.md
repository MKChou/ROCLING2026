# ROCLING 2026 實驗腳本

對應論文案例管線：**D2 雲端 Whisper API**、**D5 邊緣 Nemotron**。  
探針套件規格：`docs/ACP-DRP資料集規格.md`。

## 目錄結構

```
scripts/
├── lib/           共用模組（config / manifest / text_norm / keywords / engines / vad）
├── prep/          資料準備（C1 silence、C2A/C2B、C3/C4、C5、manifest）
├── exp/           run_d5 / run_lab_api / run_whisper / score / error_analysis
├── analysis/      tw_keyword_recall / analyze_tw_e1 / summarize_e3 / compare_e3 / probe_d2_lang
├── env/           setup_env / verify_env / download_corpus
└── run_all.ps1    一鍵重跑
```

### C2B（DEMAND）

```powershell
python scripts/prep/build_c2b_demand.py
# 產出：data/acp_drp/C2B_public/ + data/manifests/c2b_demand.csv + SOURCES.md
```

### C3／C4（男女極短／猶豫）

```powershell
# 預設來源：../C3/{male,female}/、../C4/{male,female}/（Windows 錄音機「錄製.wav」命名）
python scripts/prep/build_c3_c4.py
# 產出：data/acp_drp/C3_short/、C4_hesitation/ + manifests/c3_short.csv、c4_hesitation.csv
# C3 轉檔時裁前後長靜音；原始檔備份至 data/recordings/c3_raw、c4_raw
```

## 一鍵重跑

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1
```

依序：E1（D2 國語/台語/ACP、D5 國語/ACP）→ E3 → E2 → 計分 → 錯誤分析。

## 安裝

```powershell
powershell -ExecutionPolicy Bypass -File scripts\env\setup_env.ps1
python scripts\env\verify_env.py
```

## 個別實驗

### E1 準確度

```powershell
python scripts/exp/run_d5.py e1 --testset mandarin --manifest data/manifests/mandarin.csv
python scripts/exp/run_d5.py e1 --testset acp --manifest data/manifests/acp.csv
python scripts/exp/run_lab_api.py e1 --testset mandarin --manifest data/manifests/mandarin.csv
python scripts/exp/run_lab_api.py e1 --testset taiwanese --manifest data/manifests/taiwanese.csv
python scripts/exp/run_lab_api.py e1 --testset acp --manifest data/manifests/acp.csv
python scripts/exp/score.py e1
```

### E2 延遲（footnote 用；非論文主角）

```powershell
python scripts/exp/run_d5.py e2 --manifest data/manifests/e2_latency_50.csv --device auto
python scripts/exp/run_d5.py e2 --manifest data/manifests/e2_latency_50.csv --device cpu
python scripts/exp/run_lab_api.py e2 --manifest data/manifests/e2_latency_50.csv
```

### E3 部署風險探針

```powershell
# C2A 醫院底噪建置（音檔限制內部使用）
python scripts/prep/build_c2a_hospital.py --source-dir <原始錄音目錄>

python scripts/exp/run_d5.py e3 --manifest data/manifests/hallucination.csv
python scripts/exp/run_d5.py e3 --manifest data/manifests/hallucination.csv --device cuda --vad
python scripts/exp/run_whisper.py e3 --manifest data/manifests/hallucination.csv --device cuda
python scripts/exp/run_whisper.py e3 --manifest data/manifests/hallucination.csv --device cuda --vad
python scripts/exp/run_lab_api.py e3 --manifest data/manifests/hallucination.csv
python scripts/exp/score.py e3
python scripts/analysis/compare_e3_profiles.py
```

### 錯誤分析

```powershell
python scripts/exp/error_analysis.py
python scripts/analysis/analyze_tw_e1.py
python scripts/analysis/tw_keyword_recall.py
```

## 備註

- D2：`lang=TA and ZH Medical V1`；伺服器 OpenCC s2twp；靜音 `<{silent}>`
- D5：`zh-CN` → OpenCC s2twp；無台語
- 本機語料：`E:\data\22k_corpus`（見 `docs/實驗室語料路徑.md`）
- 重建 manifest：`python scripts/prep/build_manifest.py`
