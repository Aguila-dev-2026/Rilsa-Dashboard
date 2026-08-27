#!/usr/bin/env bash
set -euo pipefail

exec python -m streamlit run app.py \
  --server.address=0.0.0.0 \
  --server.port="${PORT:-8000}" \
  --server.headless=true \
  --server.runOnSave=false
