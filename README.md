# Fitness Planner API

Constraint-aware fitness planning API for generating weekly workout plans and revising them around equipment limits, discomfort, difficulty, and user preferences.

## Current Stack

- FastAPI
- PostgreSQL
- SQLAlchemy 2
- Pydantic Settings
- JWT authentication
- pytest

## Current Project Status

The project is implemented through Phase 5.

- Phase 1: repository setup, local PostgreSQL, authentication, user profile
- Phase 2: public exercise data evaluation, cleaning, enrichment, and seed import
- Phase 3: exercise listing, filtering, and custom exercise CRUD
- Phase 4: rule-based weekly plan generation with persisted plans, sessions, and session exercises
- Phase 5: single-exercise adjustment requests with revision history and before/after plan snapshots

## Current Tables

- `users`
- `user_profiles`
- `exercises`
- `training_plans`
- `workout_sessions`
- `workout_session_exercises`
- `adjustment_requests`
- `plan_revisions`

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Set environment variables:

```bash
export DATABASE_URL="postgresql+psycopg://tomchen@localhost:5432/fitness_planner"
export JWT_SECRET_KEY="replace-with-a-long-secret"
```

Run the API:

```bash
PYTHONPATH=. .venv/bin/uvicorn app.main:app --reload
```

## API Documentation

FastAPI generates the live API documentation automatically:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

The final submission version will also include an exported API documentation PDF referenced from this README.

## Current Endpoint Groups

- `POST /auth/register`
- `POST /auth/login`
- `GET /me/profile`
- `PUT /me/profile`
- `GET /exercises`
- `GET /exercises/{id}`
- `POST /me/custom-exercises`
- `PATCH /me/custom-exercises/{id}`
- `DELETE /me/custom-exercises/{id}`
- `POST /plans/generate`
- `GET /plans`
- `GET /plans/{id}`
- `DELETE /plans/{id}`
- `POST /plans/{id}/adjustments`
- `GET /plans/{id}/revisions`
- `GET /plans/{id}/revisions/{revision_number}`

## Data Workflow

Fetch, clean, and import exercise seed data:

```bash
PYTHONPATH=. .venv/bin/python scripts/fetch_wger_snapshot.py
PYTHONPATH=. .venv/bin/python scripts/build_exercise_seed.py --target-size 140
PYTHONPATH=. .venv/bin/python scripts/import_exercise_seed.py
```

## Current Data Artifacts

- `data/raw/wger_exercises_snapshot.json`: raw `wger` snapshot
- `data/seeds/exercises_cleaned.json`: cleaned and enriched seed dataset
- `skills/exercise-constraint-enricher/`: AI-assisted enrichment workflow artifact

## Tests

Run the current automated test suite:

```bash
PYTHONPATH=. .venv/bin/pytest -q
```

## Supporting Documentation

- [Dataset Evaluation](docs/dataset-evaluation.md)
- [Data Design](docs/data-design.md)
- [GenAI Usage Log](docs/genai-usage.md)
