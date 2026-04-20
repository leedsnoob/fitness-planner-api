# Fitness Planner API

Constraint-aware fitness planning API for generating weekly workout plans and revising them based on equipment, pain/discomfort, difficulty, and user preference constraints.

## Planned Stack

- FastAPI
- PostgreSQL
- SQLAlchemy 2
- Alembic
- Pydantic Settings
- pytest

## Development Status

Project bootstrap is in progress.

- Phase 1 covers repository setup, local PostgreSQL, FastAPI app scaffolding, and authentication.
- Phase 2 adds public exercise data evaluation, cleaning, enrichment, and PostgreSQL seed import tooling.

## Phase 2 Data Workflow

```bash
PYTHONPATH=. .venv/bin/python scripts/fetch_wger_snapshot.py
PYTHONPATH=. .venv/bin/python scripts/build_exercise_seed.py --target-size 140
PYTHONPATH=. .venv/bin/python scripts/import_exercise_seed.py
```

## Phase 2 Documentation

- [Dataset Evaluation](docs/dataset-evaluation.md)
- [Data Design](docs/data-design.md)
- [GenAI Usage Log](docs/genai-usage.md)

## Current Data Artifacts

- `data/raw/wger_exercises_snapshot.json`
- `data/seeds/exercises_cleaned.json`
- `skills/exercise-constraint-enricher/`
