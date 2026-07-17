# ACP-DRP 資料集規格（決策紀錄）

> **狀態**：2026-07-17 更新；C1、C2A、C2B、C3、C4、C5 已建；C2A 待逐段人工聽檢；**擴充結果尚未全量重跑寫入主表**  
> **用途**：部署風險探針套件（Deployment Risk Probe），服務論文主角「Deployment Risk Probe Framework」  
> **論文代號**：ACP-DRP（ACP Deployment Risk Probe）  
> **對應主稿**：`paper/rocling2026_draft.tex`（現況結果仍為擴充前 pilot：$N{=}20$/條件）

---

## 一、敘事對齊（勿偏題）

| 要做 | 不要做 |
|------|--------|
| 用套件**操作化** deployment risk，讓別人可重測任意 ASR | 再講成「更大的 Cloud vs Edge 比較語料」 |
| C2 採雙軌：**公開可重現 DEMAND（C2B）** + 限制內部使用之醫院自錄（C2A） | 將未完成逐段人工聽檢的 C2A 原始／切段音檔公開 |
| C3／C4／C5 以**真人**為主結果 | 用合成音取代 C5 主結果 |

**論文主角**：Framework  
**Cloud／Edge**：Case study  
**效能數字**：主文僅 footnote（已定）

---

## 二、擴充目標規模

| 子集 | 定義 | 規模 | 來源 | 優先序 |
|------|------|------|------|--------|
| **C1** | 空靜音 | 100 段 | 電腦產生；長度分層（建議 3/5/8/10 s） | P3 |
| **C2A** | 醫院場域底噪 | 5 場域 × 20 = 100 | 自錄；已建 5 s、16 kHz mono 共 100 段；自動初篩完成、待人工聽檢 | 已建（限制內部使用） |
| **C2B** | 公開純環境噪音 | 5 場景 × 20 = 100 | **DEMAND**（CC BY-SA 3.0；Zenodo 1227121） | 已建、已重跑 |
| **C3** | 極短語音（1–3 字級） | 50 × 2 語者 = 100 | 1 男 + 1 女；同一腳本；**已裁切**前後長靜音 | 已建 |
| **C4** | 猶豫音 | 50 × 2 = 100 | 同上男女；同一腳本 | 已建 |
| **C5** | ACP 關鍵詞句 | 50 × 2 = 100 | 同上男女；現有 50 句腳本 | 已建 |
| **合計** | | **約 600 段** | | |

### C5 合成音決策（2026-07-16）

- **主 C5 = 真人（男女）**，不當合成。
- 合成 C5（C5-S）**僅可選**平行對照（可重現上限），且排在 P0 真人錄製與重跑之後；**不得取代** C5-H。
- 理由：國語 500 已是合成；C5 職責是部署情境關鍵詞對照，合成會低估錯誤、削弱「準確度看似可用、探針仍險」的論證；且須與真人 C3／C4 條件對齊。

### 計分角色（同一批音檔可多用）

| 指標 | 主要子集 |
|------|----------|
| (a) 靜音／純噪音仍輸出 | C1、C2A、C2B |
| (b1) 空輸出／漏接 | C3、C4 |
| (b2) 非空不符／高風險改寫 | C3、C4 |
| ACP 關鍵詞錯誤率 | C5 |
| 乾淨語音 CER 對照 | C5（可兼用） |

---

## 三、錄製與規格約束

1. **通道一致**：C3／C4／C5 建議同一批男女、同一麥克風／取樣設定（16 kHz、mono、wav）。
2. **C3 建構效度**：先裁切語音段再送 ASR；禁止再以「短內容 + 前後數秒靜音」混進 C1 效應。
3. **C3／C4 腳本**：見 `data/recording_scripts/c3_c4_recording_script.txt`（各 50；001–020 對齊 pilot）；短否定／確認／猶豫填充；男女念同一詞表。
4. **C2A 公開性**：研究團隊確認後已完成醫院純環境底噪採集；不以問診、叫號或可辨識人聲為收錄目標。音檔經 20 s 初切、Silero VAD／Whisper 初篩後，再建為 5 s 子集；自動篩查不能取代逐段人工聽檢，完成聽檢與合規確認前限制內部使用。
5. **C2B（本輪採用）**：**DEMAND** 五場景純環境噪音 → `data/acp_drp/C2B_public/`（PCAFETER、OHALLWAY、OOFFICE、PRESTO、DLIVING；各 20 段，共 100）。腳本 `python scripts/prep/build_c2b_demand.py`；manifest `data/manifests/c2b_demand.csv`；授權見同目錄 `SOURCES.md`。
6. **重跑**：擴充後至少重跑案例主比較（雲端 `lang-med`、邊緣）+ lang／VAD 消融；數字才能寫進主表。

### C2A 醫院自錄場域

| venue_id | 場景 | 段數 |
|----------|------|------|
| `lobby` | 入口大廳 | 20 |
| `waiting_area` | 候診區 | 20 |
| `elevator_area` | 電梯等候／乘梯環境 | 20 |
| `low_traffic_corridor` | 低人流走廊 | 20 |
| `service_counter` | 服務櫃檯周邊 | 20 |

重建：`python scripts/prep/build_c2a_hospital.py --source-dir <原始錄音目錄>`；manifest：`data/manifests/c2a_hospital.csv`。領藥區因初篩出現疑似人聲，不納入正式 100 段。

### C2B DEMAND 場域對照

| venue_id | DEMAND scene | proxy 說明 |
|----------|--------------|------------|
| `waiting_proxy` | `PCAFETER` | 候診／公共區 |
| `corridor_proxy` | `OHALLWAY` | 走廊／護理站 |
| `clinic_proxy` | `OOFFICE` | 診間／行政區 |
| `restaurant_proxy` | `PRESTO` | 公共用餐區 |
| `indoor_care_proxy` | `DLIVING` | 室內照護環境 |
---

## 四、與現況 pilot 的關係

| 項目 | 現況（論文已報） | 目標 ACP-DRP |
|------|------------------|--------------|
| C1–C4 | 各約 20 | 見上表 |
| C5／ACP | 單一成人 50 句（關鍵詞）；探針內 C5 對照 20 | 男女各 50 |
| 噪音 | 單一環境底噪（pilot C2） | **C2A 醫院自錄 + C2B DEMAND** 五場景純噪各 100；皆已重跑 |
| 結果表 | `tab:halluc` 等 | 全量錄製並重跑後替換 |

投稿若來不及全量：主文可寫「套件設計如下；本報告基於 pilot 子集」，擴充列未來工作或 camera-ready。

---

## 五、建議目錄（錄製完成後）

```
data/
  acp_drp/
    C1_silence/
    C2A_hospital/{venue_id}/
    C2B_public/{venue_id}/   # + SOURCES.md（授權）
    C3_short/{male,female}/
    C4_hesitation/{male,female}/
    C5_acp/{male,female}/
  recording_scripts/
    acp_recording_script.txt
    c3_c4_recording_script.txt
  recordings/
    hallucination/c*_raw/
    c5_raw/female_classmateB/
  legacy_pilot/              # 舊 pilot；勿刪
    hallucination/C1–C4
    acp_wavs/
  manifests/
    acp_drp.csv              # audio_path,reference_text,language,condition,speaker,venue,source
```

---

## 六、待辦勾選

- [x] C3／C4 腳本定稿（`data/recording_scripts/c3_c4_recording_script.txt`）
- [x] C3／C4 男女錄音＋建置（`acp_drp/C3_short`、`C4_hesitation`；C3 已裁靜音；`python scripts/prep/build_c3_c4.py`）
- [x] C5 男女錄音（沿用 `data/recording_scripts/acp_recording_script.txt`；已入 `acp_drp/C5_acp`）
- [x] C2B 公開源選定：**DEMAND** + `scripts/prep/build_c2b_demand.py`
- [x] C2A 建置：5 場域 × 20 段（5 s、16 kHz mono）
- [ ] C2A 逐段人工聽檢與對外使用合規確認
- [x] C1 合成 100（3/5/8/10 秒各 25；純數位靜音）
- [ ] 建 `acp_drp.csv` + 計分腳本對齊（含 C2B）
- [ ] 重跑 E3／ACP 關鍵詞主比較與消融
- [ ] （可選）C5-S 合成平行軌
- [ ] 主稿數字與 §4.1／圖 1 段數對齊更新
