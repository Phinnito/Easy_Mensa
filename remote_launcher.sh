#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-}"
REPO="Phinnito/Easy_Mensa"
BRANCH="main"
DEVCONTAINER=".devcontainer/devcontainer.json"
CODESPACE_DISPLAY_NAME="EasyMensa-v6"

if [[ "$MODE" != "admin" && "$MODE" != "user" ]]; then
  echo "Usage: remote_launcher.sh {admin|user}"
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "❌ 需要 GitHub CLI (gh)。请先安装并运行 gh auth login。"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "❌ GitHub CLI 尚未登录。请先运行：gh auth login"
  exit 1
fi

if [[ "$MODE" == "admin" ]]; then
  PORT="8501"
  LABEL="ChefHuang"
else
  PORT="8502"
  LABEL="Chaetzli"
fi

echo "🐱 正在打开 ${LABEL} ..."

CODESPACE="$(
  gh codespace list -R "$REPO" --json name,displayName,lastUsedAt \
    --jq "map(select(.displayName == \"${CODESPACE_DISPLAY_NAME}\")) | sort_by(.lastUsedAt) | reverse | .[0].name" \
    2>/dev/null || true
)"

if [[ -z "$CODESPACE" || "$CODESPACE" == "null" ]]; then
  echo "🧹 正在停止 Easy_Mensa 的旧云端环境..."

  while IFS= read -r OLD_CODESPACE; do
    if [[ -n "$OLD_CODESPACE" && "$OLD_CODESPACE" != "null" ]]; then
      echo "   停止：$OLD_CODESPACE"
      gh api -X POST "user/codespaces/${OLD_CODESPACE}/stop" >/dev/null 2>&1 || true
    fi
  done < <(
    gh codespace list -R "$REPO" --json name \
      --jq '.[].name' 2>/dev/null || true
  )

  sleep 3

  echo "☁️ 正在创建 Easy_Mensa 云端环境..."

  MACHINE="$(
    gh api "repos/${REPO}/codespaces/machines?ref=${BRANCH}" \
      --jq '.machines | sort_by(.cpus, .memory_in_bytes) | .[0].name' 2>/dev/null || true
  )"

  if [[ -z "$MACHINE" || "$MACHINE" == "null" ]]; then
    echo "❌ 无法自动读取 Codespaces 机器类型。"
    echo "请先运行：gh auth refresh -h github.com -s codespace"
    exit 1
  fi

  echo "🖥️ 使用最轻量可用机器：${MACHINE}"

  CODESPACE="$(
    gh codespace create \
      -R "$REPO" \
      -b "$BRANCH" \
      --devcontainer-path "$DEVCONTAINER" \
      --machine "$MACHINE" \
      --default-permissions \
      -d "$CODESPACE_DISPLAY_NAME" \
      --idle-timeout 30m \
      --retention-period 168h
  )"
else
  echo "☁️ 正在唤醒 Easy_Mensa 云端环境..."
  gh api -X POST "user/codespaces/${CODESPACE}/start" >/dev/null 2>&1 || true
fi

if [[ -z "$CODESPACE" || "$CODESPACE" == "null" ]]; then
  echo "❌ 没有找到或创建 Codespace。"
  exit 1
fi

echo "⏳ 正在等待云端环境就绪..."
READY=0
for attempt in {1..48}; do
  STATE="$(
    gh api "user/codespaces/${CODESPACE}" --jq '.state' 2>/dev/null || true
  )"

  if [[ "$STATE" == "Available" ]]; then
    READY=1
    break
  fi

  if (( attempt % 4 == 0 )); then
    echo "   当前状态：${STATE:-启动中} ..."
  fi
  sleep 5
done

if [[ "$READY" -ne 1 ]]; then
  echo "❌ Codespace 等待超过 4 分钟仍未就绪。"
  exit 1
fi

if [[ "$MODE" == "admin" ]]; then
  LOCAL_PORT="18501"
  LOCAL_URL="http://127.0.0.1:${LOCAL_PORT}"
  PID_FILE="/tmp/easymensa-chef-forward.pid"
  LOG_FILE="/tmp/easymensa-chef-forward.log"

  echo "🔒 正在建立黄师傅后台的本地安全通道..."

  if [[ -f "$PID_FILE" ]]; then
    OLD_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
    if [[ -n "$OLD_PID" ]] && kill -0 "$OLD_PID" >/dev/null 2>&1; then
      kill "$OLD_PID" >/dev/null 2>&1 || true
      sleep 1
    fi
    rm -f "$PID_FILE"
  fi

  # Clean up any older launcher-created forward that may still own the port.
  pkill -f "gh codespace ports forward 8501:${LOCAL_PORT}" >/dev/null 2>&1 || true
  sleep 1

  nohup gh codespace ports forward "8501:${LOCAL_PORT}" -c "$CODESPACE" \
    >"$LOG_FILE" 2>&1 &
  FORWARD_PID=$!
  echo "$FORWARD_PID" >"$PID_FILE"

  LOCAL_READY=0
  for attempt in {1..30}; do
    HTTP_CODE="$(
      curl -sS -o /dev/null \
        --connect-timeout 2 \
        --max-time 4 \
        -w '%{http_code}' \
        "$LOCAL_URL" 2>/dev/null || true
    )"

    if [[ -n "$HTTP_CODE" && "$HTTP_CODE" != "000" ]]; then
      LOCAL_READY=1
      break
    fi

    if ! kill -0 "$FORWARD_PID" >/dev/null 2>&1; then
      echo "❌ 本地安全通道启动失败。"
      cat "$LOG_FILE" 2>/dev/null || true
      exit 1
    fi

    sleep 1
  done

  if [[ "$LOCAL_READY" -ne 1 ]]; then
    echo "❌ 黄师傅后台没有通过本地安全通道启动。"
    echo "日志：$LOG_FILE"
    exit 1
  fi

  echo "✅ ChefHuang 已启动"
  echo "🌐 ${LOCAL_URL}"
  echo "🔒 这个地址只在你自己的电脑上可访问，不会公开到互联网。"

  if command -v open >/dev/null 2>&1; then
    open "$LOCAL_URL"
  fi

  exit 0
fi

# Legacy user-mode fallback. Chaetzli normally opens the public GitHub Pages site directly.
URL="https://${CODESPACE}-${PORT}.app.github.dev"

echo "🍳 云端正在准备 ${LABEL} ..."
WEB_READY=0
for attempt in {1..60}; do
  HTTP_CODE="$(
    curl -L -sS -o /dev/null \
      --connect-timeout 4 \
      --max-time 8 \
      -w '%{http_code}' \
      "$URL" 2>/dev/null || true
  )"

  if [[ -n "$HTTP_CODE" && "$HTTP_CODE" != "000" && "$HTTP_CODE" != "404" ]]; then
    WEB_READY=1
    break
  fi

  if (( attempt % 10 == 0 )); then
    echo "   网页还在启动（HTTP ${HTTP_CODE:-000}）..."
  fi
  sleep 2
done

if [[ "$WEB_READY" -ne 1 ]]; then
  echo "❌ ${LABEL} 的网页仍未启动成功（端口 ${PORT}）。"
  exit 1
fi

echo "✅ ${LABEL} 已启动"
echo "🌐 ${URL}"

if command -v open >/dev/null 2>&1; then
  open "$URL"
fi
