#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH=.

alembic upgrade head
python scripts/import_exercise_seed.py

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-10000}"
