#!/usr/bin/env bash
set -euo pipefail

ZSHRC="$HOME/.zshrc"
START_MARKER="# >>> Easy_Mensa commands >>>"
END_MARKER="# <<< Easy_Mensa commands <<<"

touch "$ZSHRC"

if grep -Fq "$START_MARKER" "$ZSHRC"; then
  awk -v start="$START_MARKER" -v end="$END_MARKER" '
    $0 == start {skip=1; next}
    $0 == end {skip=0; next}
    !skip {print}
  ' "$ZSHRC" > "${ZSHRC}.tmp"
  mv "${ZSHRC}.tmp" "$ZSHRC"
fi

cat >> "$ZSHRC" <<'EOF'

# >>> Easy_Mensa commands >>>
ChefHuang() {
  gh api     -H "Accept: application/vnd.github.raw+json"     repos/Phinnito/Easy_Mensa/contents/remote_launcher.sh     | bash -s -- admin
}

Chaetzli() {
  open "https://phinnito.github.io/Easy_Mensa/"
}
# <<< Easy_Mensa commands <<<
EOF

echo "✅ 已安装：ChefHuang 和 Chaetzli"
echo "运行下面这句让当前 Terminal 立即生效："
echo "source ~/.zshrc"
