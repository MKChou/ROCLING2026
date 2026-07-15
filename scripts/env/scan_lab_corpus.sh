#!/usr/bin/env bash
# 在已 SSH 登入的 147 上執行，掃描 22k 語料位置。
# 用法：
#   bash scan_lab_corpus.sh
#   bash scan_lab_corpus.sh > ~/rocling_corpus_scan.txt

set -euo pipefail

BASE="${HOME}/Linux_DATA"
OUT="${1:-}"

log() {
  echo "$@"
}

section() {
  log ""
  log "======================================================================"
  log "== $1"
  log "======================================================================"
}

section "HOST"
hostname
whoami
pwd
df -h "$BASE" 2>/dev/null | tail -1 || true

section "Linux_DATA top (size)"
du -sh "$BASE"/* 2>/dev/null | sort -hr | head -25 || true

section "Find 22k_corpus directories"
find "$BASE" -maxdepth 6 -type d -name '22k_corpus' 2>/dev/null || true
find "$BASE" -maxdepth 6 -type d -name '22k_corpus_processed' 2>/dev/null || true

CANDIDATES=(
  "$BASE/synthesis/corpus/corpus_manager/22k_corpus"
  "$BASE/synthesis/corpus/corpus_manager/22k_corpus_processed"
  "$BASE/synthesis/corpus/corpus_manager/148_kaldi_tw_corpus"
)

section "Candidate paths"
for p in "${CANDIDATES[@]}"; do
  if [[ -d "$p" ]]; then
    log "OK  $p"
    du -sh "$p" 2>/dev/null || true
    ls "$p" 2>/dev/null | head -15 | sed 's/^/    /' || true
  else
    log "MISS $p"
  fi
done

CORPUS_ROOT="$BASE/synthesis/corpus/corpus_manager/22k_corpus"
if [[ -d "$CORPUS_ROOT" ]]; then
  section "22k_corpus subfolders"
  du -sh "$CORPUS_ROOT"/* 2>/dev/null | sort -hr | head -20 || true

  section "Taiwanese (tw)"
  TW_ROOT="$CORPUS_ROOT/tw/corpus"
  if [[ -d "$TW_ROOT" ]]; then
    ls "$TW_ROOT" 2>/dev/null | head -20 | sed 's/^/  /' || true
    log "wav count (tw): $(find "$TW_ROOT" -name '*.wav' 2>/dev/null | wc -l)"
    TW_SAMPLE=$(find "$TW_ROOT" -name '*.wav' 2>/dev/null | head -1)
    if [[ -n "$TW_SAMPLE" ]]; then
      log "sample wav: $TW_SAMPLE"
      STEM="${TW_SAMPLE%.wav}"
      for ext in txt json ctl trn; do
        [[ -f "${STEM}.${ext}" ]] && log "  + ${STEM}.${ext}" && head -3 "${STEM}.${ext}" && break
      done
      # same dir text files
      DIR=$(dirname "$TW_SAMPLE")
      find "$DIR" -maxdepth 1 \( -name '*.txt' -o -name '*.json' \) 2>/dev/null | head -3 | while read -r f; do
        log "text file: $f"
        head -5 "$f"
      done
    fi
  else
    log "No $TW_ROOT"
  fi

  section "Traditional Chinese (trandition_zh)"
  ZH_ROOT="$CORPUS_ROOT/trandition_zh"
  if [[ -d "$ZH_ROOT" ]]; then
    ls "$ZH_ROOT" 2>/dev/null | head -20 | sed 's/^/  /' || true
    log "wav count (trandition_zh): $(find "$ZH_ROOT" -name '*.wav' 2>/dev/null | wc -l)"
    ZH_SAMPLE=$(find "$ZH_ROOT" -name '*.wav' 2>/dev/null | head -1)
    if [[ -n "$ZH_SAMPLE" ]]; then
      log "sample wav: $ZH_SAMPLE"
      DIR=$(dirname "$ZH_SAMPLE")
      find "$DIR" -maxdepth 1 \( -name '*.txt' -o -name '*.json' -o -name '*.ctl' \) 2>/dev/null | head -3 | while read -r f; do
        log "text file: $f"
        head -5 "$f"
      done
    fi
  else
    log "No $ZH_ROOT"
  fi

  section "metadata.csv"
  find "$CORPUS_ROOT" -maxdepth 2 -name 'metadata.csv' 2>/dev/null | while read -r f; do
    log "$f ($(wc -l < "$f") lines)"
    head -3 "$f"
  done
fi

section "whisper_test / hakka_data"
ls -la "$BASE/whisper_test" 2>/dev/null | head -10 || true
ls -la "$BASE/hakka_data" 2>/dev/null | head -10 || true

section "DONE"
log "Scan complete. Copy this output back to ROCLING project."
