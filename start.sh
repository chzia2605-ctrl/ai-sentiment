#!/usr/bin/env bash
set -e
# Load .env if present
if [ -f .env ]; then
  echo "Loading .env"
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

# Start the Flask app
python app.py
