# C2A 醫院環境底噪 — 來源與使用限制

- **Source**: 研究團隊實地自錄之醫院環境底噪
- **Content policy**: 不以人聲、問診、叫號或個人資訊為收錄目標
- **Distribution**: 限研究團隊內部使用；完成逐段人工聽檢與合規確認前不得公開原始音檔
- **Format**: 16000 Hz mono PCM WAV
- **Segment**: 5 s × 20 clips / venue；固定種子 42
- **Screening**: 來源先以 20 s 切段進行 Silero VAD／Whisper 初篩；疑似人聲時窗不納入
- **Post-build check**: 100 段以 Silero VAD threshold 0.3 複查均為陰性；仍待逐段人工聽檢
- **Manual replacement (2026-07-17)**: 人工聽檢發現 4 段含遠處人聲後，改以同來源未使用時窗替換：`lobby_04`→105 s、`lobby_06`→200 s、`elevator_area_13`→110 s、`service_counter_11`→10 s；原時窗已加入建置腳本排除清單

## Venue mapping

| venue_id | 場景 | 來源檔數 |
|----------|------|----------|
| `lobby` | 入口大廳 | 1 |
| `waiting_area` | 候診區 | 1 |
| `elevator_area` | 電梯等候／乘梯環境 | 2 |
| `low_traffic_corridor` | 低人流走廊 | 2 |
| `service_counter` | 服務櫃檯周邊 | 1 |

## 注意事項

- 自動 VAD／ASR 僅為初篩，不能取代逐段人工聽檢。
- `reference_text` 留空；本子集用於量測純底噪下 ASR 是否產生非空輸出。
- manifest 保留來源檔名與起始秒數，供內部追溯；對外釋出前應另製去識別版本。
