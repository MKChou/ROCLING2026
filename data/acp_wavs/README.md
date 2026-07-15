# ACP 錄音資料

## 語者 A（classmate_a）— 2026-07-06

- **句數**：50 / 50（完整）
- **原始檔**：`raw/classmate_a/recording_001.wav` … `recording_050.wav`
- **實驗用**：`acp_001.wav` … `acp_050.wav`（16 kHz 單聲道）
- **manifest**：`../manifests/acp.csv`（含 `speaker=classmate_a`）

## 舊版錄音

已刪除（先前 12 句測試錄音與 mp3）；正式資料以 A 同學 50 句為準。

## 整理指令（新錄音放入 acp_wavs 後）

```powershell
python scripts/organize_acp_wavs.py --speaker <語者代號>
python scripts/exp/run_d5.py e1 --testset acp --manifest data/manifests/acp.csv
python scripts/exp/score.py e1 --profile D5
```

檔名規則：`錄製.wav` = 001，`錄製 (2).wav` = 002，…，`錄製 (50).wav` = 050。
