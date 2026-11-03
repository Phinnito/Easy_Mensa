#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-}"
REPO="Phinnito/Easy_Mensa"
BRANCH="main"

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
  APP="apps/admin_app.py"
  PORT="8501"
  LABEL="ChefHuang"
  LOG="/tmp/easy_mensa_admin.log"
else
  APP="apps/user_app.py"
  PORT="8502"
  LABEL="Chaetzli"
  LOG="/tmp/easy_mensa_user.log"
fi

echo "🐱 正在打开 ${LABEL} ..."

CODESPACE="$(
  gh codespace list -R "$REPO" --json name,lastUsedAt \
    --jq 'sort_by(.lastUsedAt) | reverse | .[0].name' 2>/dev/null || true
)"

if [[ -z "$CODESPACE" || "$CODESPACE" == "null" ]]; then
  echo "☁️ 第一次使用：正在为 Easy_Mensa 创建云端环境..."
  CODESPACE="$(
    gh codespace create \
      -R "$REPO" \
      -b "$BRANCH" \
      -d "EasyMensa" \
      --idle-timeout 30m \
      --retention-period 168h
  )"
fi

if [[ -z "$CODESPACE" ]]; then
  echo "❌ 没有找到或创建 Codespace。"
  exit 1
fi

REMOTE_CMD="cd /workspaces/Easy_Mensa && git pull --ff-only >/dev/null 2>&1 || true; pkill -f '[s]treamlit run ${APP}' >/dev/null 2>&1 || true; nohup python -m streamlit run ${APP} --server.address 0.0.0.0 --server.port ${PORT} --server.headless true >${LOG} 2>&1 </dev/null &"

gh codespace ssh -c "$CODESPACE" "bash -lc $(printf '%q' "$REMOTE_CMD")" >/dev/null

URL=""
for _ in {1..30}; do
  URL="$(
    gh codespace ports -c "$CODESPACE" \
      --json sourcePort,browseUrl \
      --jq ".[] | select(.sourcePort == ${PORT}) | .browseUrl" 2>/dev/null \
      | head -n 1
  )"

  if [[ -n "$URL" && "$URL" != "null" ]]; then
    break
  fi
  sleep 1
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
