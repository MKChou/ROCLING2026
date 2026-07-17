# C2A 醫院底噪實驗交接

## 已備妥

- Manifest：`data/manifests/c2a_hospital.csv`
- 音檔：`data/acp_drp/C2A_hospital/{venue_id}/`
- 規模：5 場景 × 20 段 = 100 段
- 格式：每段 5 秒、16 kHz、mono PCM WAV
- 條件：`C2A`；`reference_text` 留空
- 建置腳本：`scripts/prep/build_c2a_hospital.py`
- 一鍵實驗：`scripts/run_c2a_hospital.ps1`

五場景為入口大廳、候診區、電梯區、低人流走廊與服務櫃檯。領藥區及自動初篩標記的疑似人聲時窗未納入。正式 100 段以 Silero VAD threshold 0.3 複查均為陰性；自動篩查不能取代逐段人工聽檢。

## 先驗證，不跑模型

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_c2a_hospital.ps1 -ValidateOnly
```

## 跑本機四臂

以下會依序執行 D5、D5+VAD、公開 Whisper、公開 Whisper+VAD，最後自動計分與彙總：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_c2a_hospital.ps1 -Device cuda
```

預設不呼叫實驗室 API，避免在未確認資料使用條件前外送 C2A 音檔。

## 確認許可後才跑實驗室 API

若要連同預設國語 API 一起跑：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_c2a_hospital.ps1 `
  -Device cuda `
  -IncludeLabApi `
  -LabProfile D2
```

若需指定語言設定，再加：

```powershell
-LabLang "<實際 API lang 值>"
```

論文中的 `lang-med`／`lang-base` 是匿名代號；執行時須傳入對應的實際 API `lang` 值，不應直接使用匿名代號。

## 個別執行

```powershell
python scripts/exp/run_d5.py e3 --manifest data/manifests/c2a_hospital.csv --device cuda --tag c2a_hospital
python scripts/exp/run_d5.py e3 --manifest data/manifests/c2a_hospital.csv --device cuda --vad --tag c2a_hospital
python scripts/exp/run_whisper.py e3 --manifest data/manifests/c2a_hospital.csv --device cuda --tag c2a_hospital
python scripts/exp/run_whisper.py e3 --manifest data/manifests/c2a_hospital.csv --device cuda --vad --tag c2a_hospital
python scripts/exp/score.py e3 --tag c2a_hospital
python scripts/analysis/summarize_e3.py --tag c2a_hospital
python scripts/analysis/compare_e3_profiles.py --tag c2a_hospital
```

## 輸出

- 原始辨識：`results/E3_outputs/*_c2a_hospital.jsonl`
- 逐段計分：`results/E3_c2a_hospital.csv`
- 跨 profile 摘要：`results/analysis/e3_c2a_hospital_compare.csv`

論文應將 C2A 與 C2B 分開報告。C2A 的主要指標為無目標語音時的非空輸出率，不使用 CER。

## 投稿前狀態

1. [x] 逐段人工聽完 100 段（約 8 分 20 秒）：確認無可理解人聲／姓名／叫號／個資；先前 4 段遠處人聲已替換。
2. [ ] 確認院方／研究計畫的資料使用及對外呈現範圍。
3. [ ] 完成各實驗臂後才將 C2A 數字寫入論文主表；不得把 VAD 初篩結果當成正式模型結果。

