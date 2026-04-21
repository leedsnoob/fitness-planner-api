# Fitness Planner API

Constraint-aware fitness planning API built with FastAPI and PostgreSQL. The system imports curated public exercise data, generates weekly plans, revises individual exercises when constraints change, records workout logs, exposes analytics, and can generate user-facing plan explanations through SiliconFlow + Qwen.

## Stack

- FastAPI
- PostgreSQL
- SQLAlchemy 2
- Alembic
- JWT authentication
- pytest
- SiliconFlow Chat Completions for explanation generation

## Quick Start

Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Copy `.env.example` to `.env` and fill the required values:

```bash
cp .env.example .env
```

Apply database migrations:

```bash
PYTHONPATH=. .venv/bin/alembic upgrade head
```

Import the cleaned exercise seed:

```bash
PYTHONPATH=. .venv/bin/python scripts/import_exercise_seed.py
```

Run the API locally:

```bash
PYTHONPATH=. .venv/bin/uvicorn app.main:app --reload
```

## Environment Variables

The project reads configuration from `.env`.

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `SILICONFLOW_API_KEY`
- `SILICONFLOW_BASE_URL`
- `SILICONFLOW_MODEL`
- `SILICONFLOW_CONNECT_TIMEOUT_SECONDS`
- `SILICONFLOW_READ_TIMEOUT_SECONDS`

See [.env.example](.env.example) for the full template.

## API Documentation

FastAPI exposes live API documentation while the service is running:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`
- Production Swagger UI: `https://fitness-planner-api-qrnh.onrender.com/docs`
- Submission PDF: [API Documentation PDF](docs/api-documentation.pdf)

Regenerate the submission PDF:

```bash
PYTHONPATH=. .venv/bin/python scripts/build_api_docs_pdf.py
```

## Deployment

- Production API: `https://fitness-planner-api-qrnh.onrender.com`
- Health check: `https://fitness-planner-api-qrnh.onrender.com/health`

## Submission Artifacts

- API documentation PDF: [docs/api-documentation.pdf](docs/api-documentation.pdf)
- Technical report PDF: [docs/technical-report.pdf](docs/technical-report.pdf)
- Presentation slides: [docs/presentation-slides-link.md](docs/presentation-slides-link.md)

## Data Artifacts

- `data/raw/wger_exercises_snapshot.json`: raw `wger` snapshot
- `data/seeds/exercises_cleaned.json`: cleaned and enriched exercise seed
- `skills/exercise-constraint-enricher/`: AI-assisted enrichment workflow artifact

## Tests

Run the full automated test suite:

```bash
PYTHONPATH=. .venv/bin/pytest -q
```

The test harness provisions an isolated PostgreSQL database per pytest worker/process.

## Supporting Project Notes

- [Dataset Evaluation](docs/dataset-evaluation.md)
- [Data Design](docs/data-design.md)
- [GenAI Usage Log](docs/genai-usage.md)
