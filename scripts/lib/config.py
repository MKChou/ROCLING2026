"""ROCLING 2026 實驗共用設定（D5 與後續系統共用路徑/詞表）。"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MANIFEST_DIR = DATA_DIR / "manifests"
RESULTS_DIR = PROJECT_ROOT / "results"
RECORDINGS_DIR = DATA_DIR / "recordings"
HALLUC_RAW_DIR = RECORDINGS_DIR / "hallucination"

# 本機大型語料（147 下載解壓後：E:\data\22k_corpus\{trandition_zh,tw_clean,metadata.csv}）
CORPUS_ROOT = Path(os.environ.get("ROCLING_CORPUS_ROOT", r"E:\data\22k_corpus"))

# 部署方案
PROFILE_D2 = "D2"  # 實驗室 Whisper API（149:5002；國語與台語為不同 lang/路由）
PROFILE_D2_LLEGACY = "D2_Llegacy"  # D2 + 舊 lang（Chinese & Taiwanese），E3 對照
PROFILE_D5 = "D5"
PROFILE_D5_VAD = "D5_VAD"  # D5 + Silero VAD 閘控
PROFILE_WSP_PUBLIC = "WspPublic"  # 本機公開 openai/whisper-large-v3-turbo 對照臂
PROFILE_WSP_PUBLIC_VAD = "WspPublic_VAD"  # WspPublic + Silero VAD（對應交付手冊 D3）
MODEL_ID_D5 = "nvidia/nemotron-3.5-asr-streaming-0.6b"
VAD_THRESHOLD = 0.5
MODEL_ID_WHISPER_PUBLIC = "openai/whisper-large-v3-turbo"
LANGUAGE_D5 = "zh-CN"
LANGUAGE_WHISPER_PUBLIC = "zh"
SAMPLE_RATE = 16000
LAB_API_LANG_LEGACY = "Chinese & Taiwanese"

# 測試集代號（對應 E1_accuracy.csv 的 testset 欄）
TESTSET_MANDARIN = "mandarin"
TESTSET_TAIWANESE = "taiwanese"
TESTSET_ACP = "acp"
TESTSET_HALLUCINATION = "hallucination"

# 實驗室 Whisper API（D2）：openai/whisper-large-v3-turbo
# lang 對照（app STT 與實測一致，2026-07-07 探測）：
#   TA and ZH Medical V1 → 台語/中文漢字（國台語雙語整合設定；台語 E1 應使用此 lang）
#   TA_toned             → 台羅拼音（帶調）
#   Chinese & Taiwanese  → 舊 lang；台語常偏國語同音改寫，勿再用於台語 E1
LAB_API_URL = "http://140.116.245.149:5002/proxy"
LAB_API_URL_TAIWANESE = None
LAB_API_LANG_MANDARIN = "TA and ZH Medical V1"
LAB_API_LANG_TAIWANESE = "TA and ZH Medical V1"
LAB_API_LANG_TAIWANESE_ROMAN = "TA_toned"
LAB_API_TOKEN = "2025@mi2s_asr@tai"

# 依 testset 選 API（run_lab_api.py 使用）
LAB_API_LANG_BY_TESTSET = {
    TESTSET_MANDARIN: LAB_API_LANG_MANDARIN,
    TESTSET_ACP: LAB_API_LANG_MANDARIN,
    TESTSET_TAIWANESE: LAB_API_LANG_TAIWANESE,
}
LAB_API_URL_BY_TESTSET = {
    TESTSET_MANDARIN: LAB_API_URL,
    TESTSET_ACP: LAB_API_URL,
    TESTSET_TAIWANESE: LAB_API_URL_TAIWANESE or LAB_API_URL,
}
# 向後相容
LAB_API_LANG = LAB_API_LANG_MANDARIN

# 語料伺服器 SSH（147，FRP 轉發埠）
LAB_SSH_HOST = "140.116.245.147"
LAB_SSH_PORT = 24680

# E2：國語固定 50 句子集（manifest 檔名約定）
E2_MANIFEST = MANIFEST_DIR / "e2_latency_50.csv"
E2_REPEATS = 3  # 第 1 次 warm-up 不計

# E3 幻覺條件
HALLUC_CONDITIONS = ("C1", "C2", "C3", "C4", "C5")

# 附錄 A：ACP 關鍵詞表
ACP_KEYWORDS = [
  # 文件與制度類
    "預立醫療決定",
    "預立醫療照護諮商",
    "病人自主權利法",
    "醫療委任代理人",
    "意願書",
    "簽署",
    # 處置類
    "心肺復甦術",
    "CPR",
    "DNR",
    "插管",
    "氣切",
    "洗腎",
    "鼻胃管",
    "葉克膜",
    "輸血",
    "抗生素",
    "維生醫療",
    # 照護類
    "安寧緩和",
    "緩和醫療",
    "善終",
    "末期",
    "臨終",
    "舒適照護",
    "居家安寧",
    # 對話類
    "急救",
    "放棄",
    "拒絕",
    "同意",
    "家屬",
    "討論",
    "意願",
]
