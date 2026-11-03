#!/usr/bin/env bash
set -e
python -m streamlit run apps/user_app.py --server.address 0.0.0.0 --server.port 8502
