#!/bin/bash
# Double-click this file in Finder to start the Journal Lookup app.
# Keep this Terminal window open while using the app; close it to stop the server.

cd "$(dirname "$0")"
APP_DIR="$(pwd)"

# Prefer conda env if available (change env name below if you use another)
if command -v conda &>/dev/null; then
  if conda env list 2>/dev/null | grep -q "llamaparse"; then
    echo "Using conda env: llamaparse"
    RUN_CMD="conda run -n llamaparse streamlit run journal_lookup_app.py"
  elif conda env list 2>/dev/null | grep -q "llama-parse-env"; then
    echo "Using conda env: llama-parse-env"
    RUN_CMD="conda run -n llama-parse-env streamlit run journal_lookup_app.py"
  fi
fi

if [ -z "$RUN_CMD" ]; then
  RUN_CMD="python3 -m streamlit run journal_lookup_app.py"
fi

echo "Starting Journal Lookup at: $APP_DIR"
echo "Browser will open at http://localhost:8501"
echo "Close this window to stop the app."
echo ""

$RUN_CMD

read -n 1 -p "Press any key to close..."
