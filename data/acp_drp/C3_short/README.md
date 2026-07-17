# C3_short

極短語音（確認／否定／短答），男女各 50 = 100 段。

```
C3_short/{male,female}/c3_001.wav … c3_050.wav
```

- 規格：16 kHz mono pcm_s16le；建置時已裁前後長靜音
- 腳本：`../../recording_scripts/c3_c4_recording_script.txt`
- Manifest：`../../manifests/c3_short.csv`
- 原始檔：`../../recordings/c3_raw/{male,female}/`
- 重建：`python scripts/prep/build_c3_c4.py`
