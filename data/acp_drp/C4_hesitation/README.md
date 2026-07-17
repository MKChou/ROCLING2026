# C4_hesitation

猶豫／填充音，男女各 50 = 100 段。

```
C4_hesitation/{male,female}/c4_001.wav … c4_050.wav
```

- 規格：16 kHz mono pcm_s16le（不裁靜音，保留自然猶豫長度）
- 腳本：`../../recording_scripts/c3_c4_recording_script.txt`
- Manifest：`../../manifests/c4_hesitation.csv`
- 原始檔：`../../recordings/c4_raw/{male,female}/`
- 重建：`python scripts/prep/build_c3_c4.py`
