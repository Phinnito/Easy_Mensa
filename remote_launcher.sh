#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-}"
REPO="Phinnito/Easy_Mensa"
BRANCH="main"
DEVCONTAINER=".devcontainer/devcontainer.json"
CODESPACE_DISPLAY_NAME="EasyMensa-v3"

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
  echo "🧹 正在停止这个仓库之前留下的旧 Codespace..."

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

  echo "☁️ 正在创建唯一的 Easy_Mensa 云端环境..."

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
for attempt in {1..36}; do
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
  echo "❌ Codespace 等待超过 3 分钟仍未就绪。"
  echo "请到 GitHub → Code → Codespaces 检查 EasyMensa-v3。"
  exit 1
fi

# Streamlit apps are started automatically by devcontainer postStartCommand.
# Codespaces forwarded-port URLs use a deterministic format.
echo "🍳 云端环境已就绪，正在打开 ${LABEL} ..."
sleep 8

URL="https://${CODESPACE}-${PORT}.app.github.dev"

echo "✅ ${LABEL}"
echo "🌐 ${URL}"

if command -v open >/dev/null 2>&1; then
  open "$URL"
else
  echo "请在浏览器打开上面的地址。"
fi
