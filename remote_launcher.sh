#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-}"
REPO="Phinnito/Easy_Mensa"
BRANCH="main"
DEVCONTAINER=".devcontainer/devcontainer.json"
CODESPACE_DISPLAY_NAME="EasyMensa-v2"

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
  echo "☁️ 第一次使用新版启动器：正在创建 Easy_Mensa 云端环境..."

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

echo "🍳 正在等待 ${LABEL} 网页启动..."

URL=""
for _ in {1..60}; do
  URL="$(
    gh codespace ports -c "$CODESPACE" \
      --json sourcePort,browseUrl \
      --jq ".[] | select(.sourcePort == ${PORT}) | .browseUrl" 2>/dev/null \
      | head -n 1
  )"

  if [[ -n "$URL" && "$URL" != "null" ]]; then
    break
  fi
  sleep 2
done

if [[ -z "$URL" || "$URL" == "null" ]]; then
  URL="https://${CODESPACE}-${PORT}.app.github.dev"
fi

echo "✅ ${LABEL} 已启动"
echo "🌐 ${URL}"

if command -v open >/dev/null 2>&1; then
  open "$URL"
else
  echo "请在浏览器打开上面的地址。"
fi
