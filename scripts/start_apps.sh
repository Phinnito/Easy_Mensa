#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

git pull --ff-only >/dev/null 2>&1 || true
python -m pip install -q -r requirements.txt >/dev/null 2>&1 || true

pkill -f '[s]treamlit run apps/admin_app.py' >/dev/null 2>&1 || true
pkill -f '[s]treamlit run apps/user_app.py' >/dev/null 2>&1 || true

nohup python -m streamlit run apps/admin_app.py   --server.address 0.0.0.0   --server.port 8501   --server.headless true   >/tmp/easy_mensa_admin.log 2>&1 </dev/null &

nohup python -m streamlit run apps/user_app.py   --server.address 0.0.0.0   --server.port 8502   --server.headless true   >/tmp/easy_mensa_user.log 2>&1 </dev/null &
