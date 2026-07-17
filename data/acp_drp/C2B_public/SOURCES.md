# C2B DEMAND — 來源與授權

- **Corpus**: DEMAND (Diverse Environments Multichannel Acoustic Noise Database)
- **Record**: Zenodo [1227121](https://zenodo.org/records/1227121)
- **License**: CC BY-SA 3.0
- **Citation**: Thiemann, J., Ito, N., & Vincent, E. (2013). DEMAND: a collection of multi-channel recordings of acoustic noise in diverse environments. Zenodo. https://doi.org/10.5281/zenodo.1227121
- **Channel**: ch01（單聲道）
- **Format**: 16000 Hz mono WAV
- **Segment**: 5 s × 20 clips / venue；固定種子 42

## Venue mapping（醫院／照護 proxy，非實地醫院錄音）

| venue_id | DEMAND scene | 說明 |
|----------|--------------|------|
| `waiting_proxy` | `PCAFETER` | 候診／公共區 proxy（自助餐廳） |
| `corridor_proxy` | `OHALLWAY` | 走廊／護理站 proxy（辦公室走廊） |
| `clinic_proxy` | `OOFFICE` | 診間／行政區 proxy（辦公室） |
| `restaurant_proxy` | `PRESTO` | 公共用餐區 proxy（大學餐廳） |
| `indoor_care_proxy` | `DLIVING` | 室內照護環境 proxy（客廳） |

## Downloaded zip SHA-256

| file | sha256 |
|------|--------|
| `DLIVING_16k.zip` | `2b1726fe06e41551ce2397f2aaf3e4fb692c912d81914b04708df0bbb5252338` |
| `OHALLWAY_16k.zip` | `4d5ef858a05954f03340048131f60a2004b7b28afc65f7bd2301636a7002d6cb` |
| `OOFFICE_16k.zip` | `7570c952f621990d0d71b8398107d9a78066254f883a5569abec9c233ffda358` |
| `PCAFETER_16k.zip` | `89be7194b83cd583c4b12f4bf7c19e9cf0e612b95312e9f4aedc968cd811bcd5` |
| `PRESTO_16k.zip` | `cfd2e13998fac36aa5628070e08261deb7993dada302dc00a76aaf4e02ee4166` |

## Note

C2A 為限制內部使用的醫院自錄底噪；C2B 為五場景純環境噪音探針（可公開重建）。
請在論文中標註 DEMAND 授權與引用。
