#!/usr/bin/env bash
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
cd "$(dirname "$0")"
if curl --silent --fail http://127.0.0.1:8700/health >/dev/null 2>&1; then
  echo '이미 실행 중입니다: http://localhost:8700'
  exit 0
fi
echo '이 터미널을 열어 두고 http://localhost:8700 에 접속하세요.'
if command -v ollama >/dev/null 2>&1; then
  if ! curl --silent --fail http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    mkdir -p var
    ollama serve >var/ollama-start.log 2>&1 &
  fi
  export SEMI_LLM_ENABLED="${SEMI_LLM_ENABLED:-1}"
fi
exec bash start.sh
