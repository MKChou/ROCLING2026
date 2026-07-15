# ROCLING 2026 實驗腳本

對應 `docs/實驗交付手冊.md` 的 E1–E3 流程。目前實作 **D2 Whisper large-v3-turbo**（實驗室 API）、**D5 Nemotron**（本機）；D1/D3/D4 待後續擴充。

## 目錄結構

```
scripts/
├── lib/                      共用模組（被其他腳本 import，不直接執行）
│   ├── config.py             路徑、API 設定、ACP 詞表、實驗常數
│   ├── manifest.py           讀取 manifest.csv
│   ├── text_norm.py          CER 正規化、OpenCC 轉繁、靜音標記處理
│   ├── keywords.py           ACP 關鍵詞比對
│   └── d5_engine.py          D5 Nemotron 推論引擎
├── prep/                     資料準備（一次性）
│   ├── build_manifest.py             mandarin / taiwanese / e2_latency_50
│   ├── build_hallucination_manifest.py
│   ├── make_silence.py               E3 C1 靜音檔
│   ├── import_c2_noise.py            C2 噪音錄音匯入
│   ├── import_c3_c4.py               C3/C4 錄音匯入（C4 需 c4_refs.csv）
│   ├── inspect_c3_c4.py              匯入前檢查
│   ├── preview_c4_refs.py
│   ├── convert_acp_wavs.py
│   └── organize_acp_wavs.py
├── exp/                      實驗執行與計分
│   ├── run_d5.py             D5：e1 / e2 / e3 子命令
│   ├── run_lab_api.py        D2：e1 / e2 / e3 子命令（實驗室 API）
│   ├── score.py              彙總 E1/E3 → results/*.csv
│   └── error_analysis.py     質性錯例 → results/analysis/error_analysis.txt
├── analysis/                 分析與圖表
│   ├── analyze_tw_e1.py      台語 E1 錯誤分佈 → results/analysis/tw_samples.txt
│   ├── tw_keyword_recall.py  台語詞彙命中率 → 論文 5.3（Medical V1：86.06%）
│   ├── summarize_e3.py
│   └── plot_tradeoff.py      圖 1（需 matplotlib；論文亦有 pgfplots 內嵌版）
├── env/                      環境與語料下載
│   ├── setup_env.ps1 / verify_env.py
│   ├── download_corpus.py / .ps1 / _scp.ps1
│   └── scan_lab_corpus.sh
└── run_all.ps1               一鍵重跑全部實驗（見下）
```

## 一鍵重跑

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1
```

依序執行：E1（D2 國語/台語/ACP、D5 國語/ACP）→ E3（兩系統）→ E2（D2、D5 CPU/GPU）→ 計分 → 錯誤分析。
全程約 1.5–2 小時（D5 國語 500 句最耗時）。個別步驟見下。

## 安裝（實驗室電腦）

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

### E2 延遲與資源（國語固定 50 句）

```powershell
python scripts/exp/run_d5.py e2 --manifest data/manifests/e2_latency_50.csv --device auto
python scripts/exp/run_d5.py e2 --manifest data/manifests/e2_latency_50.csv --device cpu
python scripts/exp/run_lab_api.py e2 --manifest data/manifests/e2_latency_50.csv
```

### E3 幻覺診斷

```powershell
python scripts/exp/run_d5.py e3 --manifest data/manifests/hallucination.csv
python scripts/exp/run_d5.py e3 --manifest data/manifests/hallucination.csv --device cuda --vad
python scripts/exp/run_whisper.py e3 --manifest data/manifests/hallucination.csv --device cuda
python scripts/exp/run_whisper.py e3 --manifest data/manifests/hallucination.csv --device cuda --vad
python scripts/exp/run_lab_api.py e3 --manifest data/manifests/hallucination.csv
python scripts/exp/score.py e3
python scripts/analysis/compare_e3_profiles.py
```

### E2 串流首字（邊緣 GPU）

```powershell
python scripts/exp/run_d5.py e2 --manifest data/manifests/e2_latency_50.csv --device cuda --streaming --lookahead 0
```

### 錯誤分析

```powershell
python scripts/exp/error_analysis.py
python scripts/analysis/analyze_tw_e1.py
python scripts/analysis/tw_keyword_recall.py
```

## D2 實驗室 API 備註

- 引擎：**Whisper large-v3-turbo**（`openai/whisper-large-v3-turbo`），論文 profile **D2**
- API（D2）：`http://140.116.245.149:5002/proxy`；lang=`TA and ZH Medical V1`（漢字）；台羅=`TA_toned`；token 見 `config.py`
- 伺服器端解碼後套用 **OpenCC s2twp** 統一為台灣正體（與 D5 相同套件，但 Whisper 解碼起點多為繁體/混雜）
- 靜音回 `<{silent}>`，`text_norm.strip_special_markers` 計分時移除
- E2 延遲含網路來回，與本機 D5 分開報告

## D5 技術備註

- Hugging Face Transformers 載入 `nvidia/nemotron-3.5-asr-streaming-0.6b`
- 語言 `zh-CN` → OpenCC `s2twp` 轉繁；**不跑台語**（論文標 N/A）
- 離線環境需設 `$env:HF_HUB_OFFLINE="1"` 用本機快取

## 本機語料（E:\data\22k_corpus）

- 國語：`trandition_zh/azure_synthesis_with_vad/`（wav + txt）
- 台語：`tw/corpus/148_kaldi_tw_corpus_300_corpus/`（wav + json[text] + wav.trn）
- 重建 manifest：`python scripts/prep/build_manifest.py`
