# Technical Report: Constraint-Aware Fitness Planning API

## Submission Links

- Public GitHub repository: https://github.com/leedsnoob/fitness-planner-api
- API documentation PDF: https://github.com/leedsnoob/fitness-planner-api/blob/main/docs/api-documentation.pdf
- Presentation slides link: https://github.com/leedsnoob/fitness-planner-api/blob/main/docs/presentation-slides-link.md
- Production API: https://fitness-planner-api-qrnh.onrender.com
- Production Swagger UI: https://fitness-planner-api-qrnh.onrender.com/docs

## 1. Project Overview

This project implements a constraint-aware fitness planning API rather than a generic exercise CRUD application. A typical user journey is: register, complete a profile, generate a weekly plan, replace an exercise when constraints change, log actual training, inspect analytics, and optionally request natural-language explanations. The system therefore combines database-backed CRUD, workflow-oriented planning, analytics, and a non-critical GenAI explanation layer in one deployed web API.

The coursework minimum was exceeded in three ways. First, the system includes more than one full CRUD resource: custom exercises and workout logs both support create, read, update, and delete operations. Second, the API contains workflow resources such as adjustment requests, revision history, analytics, and explanations, which go beyond static data storage. Third, the project is deployed publicly on Render with production smoke-test evidence.

## 2. Stack and Architectural Choices

- **Python** was chosen because the project mixes API design, heuristic scoring, data cleaning, testing, and external provider integration. Python supports all of these cleanly within one codebase.
- **FastAPI** was selected because it is API-first, generates OpenAPI/Swagger automatically, and integrates well with Pydantic validation and SQLAlchemy models. This was more suitable than Django/DRF for a service-centric project where the main complexity sits in planning logic rather than server-rendered application structure.
- **PostgreSQL** was used because plans, sessions, revisions, logs, explanations, and owner-scoped resources form a strongly relational model. A NoSQL design would have weakened integrity and made analytics and revision tracking harder to explain and maintain.
- **SQLAlchemy 2** provides an explicit model layer and readable query construction. **Alembic** was added once the schema stabilized so that the system no longer depended on `create_all()` as a deployment mechanism.
- **JWT bearer authentication** was used instead of session-based auth because the project is a stateless API deployed on Render. It fits external hosting and owner-scoped resource protection more naturally.
- **Render** was chosen because it supports Python web services, managed PostgreSQL, environment variables, and blueprint-based deployment with low setup overhead.
- **SiliconFlow + Qwen** were integrated only for explanations, not for core planning decisions. This preserves deterministic business logic while still adding user-facing explainability.

At a high level, the project follows a layered design:

- `routes` expose HTTP endpoints;
- `services` contain planning, adjustment, analytics, logging, and explanation logic;
- `models` define relational entities;
- `schemas` define request/response contracts;
- `migrations` manage schema evolution;
- `tests` cover integration, migrations, concurrency, resilience, and online verification.

## 3. Data Source, Enrichment, and Database Design

The exercise dataset was not written manually. Instead, the project uses a reproducible pipeline:

1. compare candidate public exercise sources;
2. capture a raw snapshot;
3. clean and normalize records;
4. enrich records with project-specific semantics;
5. import the curated seed into PostgreSQL.

`wger` was selected as the primary upstream source because it offered better provenance, a clearer public API, and enough structure to support later enrichment. Alternatives such as `free-exercise-db` and generic Kaggle files were explored but not used as the main source because they were less suitable for a reproducible API-first import pipeline.

The cleaned dataset is not just a reformatted raw dump. It strips HTML, extracts usable English records, normalizes equipment and muscle fields, removes unsuitable drills or ambiguous records, and adds semantic tags needed for planning. The enrichment layer adds:

- `movement_pattern`
- `difficulty`
- `impact_level`
- `contraindication_tags`
- environment and equipment tags

This enrichment matters because raw exercise metadata is not enough for constraint-aware recommendation. The planner needs to know not only what muscle an exercise targets, but also what movement it represents, whether it is beginner-friendly, whether it fits home or gym contexts, and whether it should be treated conservatively for discomfort-related filtering.

The repository also contains `skills/exercise-constraint-enricher`, which documents the AI-assisted enrichment workflow. This is important evidence of methodological GenAI use: the prompting logic, manual review boundary, and tagging rules are explicit artifacts rather than hidden ad hoc interactions.

The current schema contains ten tables:

- `users`: account identity, email, password hash, timestamps.
- `user_profiles`: goal, training days, environment, available equipment, contraindications, and profile timestamps.
- `exercises`: cleaned/enriched canonical exercise records including source metadata and semantic tags.
- `training_plans`: plan version root with user ownership, goal, split, request snapshot, and current revision number.
- `workout_sessions`: per-plan sessions such as A/B/C, session ordering, and labels.
- `workout_session_exercises`: concrete planned exercises with slot type, movement pattern, score breakdown, and prescribed sets/reps/rest.
- `adjustment_requests`: the reason and context for a single-exercise replacement attempt.
- `plan_revisions`: before/after snapshots and revision metadata for replacements.
- `workout_logs`: plan-linked execution logs with completion status, performance values, and historical snapshots.
- `plan_explanations`: stored plan or revision explanations with provider, model, input snapshot, and output text.

Full CRUD is intentionally limited to resources where end-user mutation makes sense, especially custom exercises and workout logs. Plans, revisions, and explanations are more workflow-driven: some are created by the system and only exposed through controlled read or create paths.

## 4. Planning, Replacement, and Explanation Logic

The planning pipeline is rule-based and transparent. It selects a split based on goal and training days, creates session templates, fills session slots with candidate exercises, applies hard filters, scores viable candidates, and finally assigns goal-specific sets, reps, and rest values. This design was preferred over collaborative filtering because there is not yet a large user-behavior matrix, and a defensible rule-based system is easier to test and explain in an oral exam.

The planner avoids producing "the same workout every day" because sessions are template-driven and slot-based. Each session has different slot intentions, movement patterns, and scoring constraints, so even in the same weekly split, the candidate search space differs across sessions.

Single-exercise adjustment is implemented as a first-class workflow rather than by regenerating the whole plan. A user submits an adjustment request for one planned exercise, the service applies constraint-aware replacement logic, and the result is written as a new revision with before/after snapshots. This makes the system more realistic and easier to audit.

On top of base rule scoring, the project adds context-aware reranking:

- adherence bonus from historical completion behavior,
- effort penalty from past high-effort or poorly completed movements,
- revision-reason penalty for previously disliked or discomfort-related replacements,
- novelty bonus to reduce repetition,
- context override bonus when the current request explicitly changes environment or discomfort context.

The explanation layer uses SiliconFlow + Qwen to generate plan-level and revision-level explanations from structured snapshots. It is intentionally non-critical: if explanation generation fails, the core plan, revision, logs, and analytics remain valid. Timeout, retry, and error-isolation behavior are handled separately from the main planning transaction.

## 5. Authentication and Security Design

The API uses JWT bearer authentication with `Authorization: Bearer <token>`. Tokens carry a subject claim and expiry, and they are signed with `HS256`. Passwords are never stored in plaintext; the database stores `hashed_password`, produced through Passlib using `pbkdf2_sha256`.

Protected resources include profile, custom exercises, plans, revisions, workout logs, analytics, and explanations. The system applies owner-scoped access control so that one user cannot access another user's private training data. In practice this means:

- unauthenticated requests return `401`,
- invalid tokens return `401`,
- missing underlying users also return `401`,
- owner-scope failures generally return `404` to avoid leaking another user's resource details.

The API also standardizes error responses as `code`, `message`, and `details`. Secrets are managed through environment variables rather than committed credentials, including `DATABASE_URL`, `JWT_SECRET_KEY`, and `SILICONFLOW_API_KEY`.

This is appropriate for coursework scope and public deployment, but it is not positioned as a full enterprise-grade security model. The current system does not implement refresh tokens, rate limiting, RBAC, or audit trails, and these are acknowledged as future hardening areas rather than hidden omissions.

## 6. Testing and Verification

The testing strategy combines automated regression with deployed verification instead of relying on manual Swagger or Postman-only testing. The project currently has `62` passing pytest cases, and those tests cover:

- authentication and profile behavior,
- custom exercise CRUD,
- plan generation,
- single-exercise adjustment and revision history,
- workout log CRUD,
- analytics endpoints,
- explanation endpoint resilience,
- unified error responses,
- Alembic migrations,
- concurrency behavior.

This approach was chosen because different risks appear at different layers. Integration tests verify endpoint behavior against a real PostgreSQL-backed app. Migration tests confirm a blank database can be upgraded to the current schema. Concurrency tests check that simultaneous actions do not corrupt plan revision behavior. Explanation resilience tests verify that provider failures do not pollute core business data.

User-story testing was also made explicit. Representative stories include:

- a full golden path: register, update profile, generate a plan, replace an exercise, log a workout, inspect analytics, and create explanations;
- a plan explanation failure that still leaves the plan readable and adjustable;
- a revision explanation failure that still leaves logging and analytics working;
- a two-user isolation story proving owner-scoped data protection.

The deployed system was additionally verified on Render through online smoke testing. Production checks confirmed `/health`, `/docs`, registration/login, profile updates, exercise listing, plan generation, adjustment, workout logging, analytics, and explanation requests against the live service.

## 7. Deployment

The project is deployed on Render using one web service and one managed PostgreSQL instance. Render was selected because it provides a simple hosted target for a Python API project and supports blueprint-based deployment through `render.yaml`.

The startup path is explicit:

1. apply Alembic migrations;
2. import the cleaned exercise seed;
3. launch Uvicorn.

This flow is encoded in `scripts/render_start.sh`, so the deployed environment stays aligned with the local schema and seed setup. The production service is available at `https://fitness-planner-api-qrnh.onrender.com`, and its Swagger UI is available at `https://fitness-planner-api-qrnh.onrender.com/docs`.

Core deployment environment variables include:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `SILICONFLOW_API_KEY`
- `SILICONFLOW_BASE_URL`
- `SILICONFLOW_MODEL`
- timeout configuration for the explanation provider

Two deployment limitations are documented honestly: Render free-tier cold starts can delay the first request, and explanation latency depends on an external provider rather than only local business logic.

## 8. Challenges, Lessons Learned, and Limitations

The main engineering challenges were schema evolution, unified error handling, pagination fixes, deployment setup, and concurrency safety. The project started with prototype-style database creation but later moved to Alembic to make schema evolution explainable and deployable. Owner-scoped error handling also had to be normalized so that validation and business errors did not produce inconsistent response formats.

The main data challenges came from the public exercise source itself. Upstream records were useful but not directly recommendation-ready, so cleaning, filtering, and semantic tagging were necessary. This led to an important design lesson: in recommendation-style APIs, data preparation is often as important as endpoint implementation.

The main AI/provider challenge was explanation latency. The final design lesson was not to make explanations part of the critical transaction path. They are useful, user-facing enhancements, but the planner itself should remain deterministic and testable even if the provider times out.

Current limitations include the absence of a more advanced progression model, relatively simple analytics, and synchronous explanation calls. Future work could add richer progression science, smaller explanation payloads or async explanation jobs, and possibly an MCP adapter as an extension rather than a current requirement.

## 9. GenAI Declaration, Evidence, and Appendix

GenAI was used throughout the project, but not only for low-level code completion. It was used for dataset exploration, schema and enrichment reasoning, AI-workflow design, documentation structuring, and the explanation layer itself. The main tools were Codex and SiliconFlow-hosted Qwen models. Human review remained the final decision point for source selection, schema boundaries, enrichment rules, security design, and algorithm choices.

Evidence of GenAI use is already present in the repository:

- `docs/genai-usage.md`
- `docs/dataset-evaluation.md`
- `skills/exercise-constraint-enricher/`
- `skills/exercise-constraint-enricher/references/tagging-rules.md`

This is high-level GenAI usage because the project uses AI to explore alternatives, shape the methodology, and create reusable workflow artifacts rather than merely asking for isolated code snippets.

### Appendix A. Representative GenAI Conversation Excerpts

- **Dataset selection**: GenAI was used to compare `wger`, `free-exercise-db`, and Kaggle-based options. The outcome was not blindly accepted; the final choice favored provenance, API accessibility, and reproducibility for a seed-import pipeline.
- **Enrichment workflow**: GenAI helped surface useful semantic fields such as `movement_pattern`, `difficulty`, `impact_level`, and `contraindication_tags`, but the final tagging rules were constrained into a repository skill plus explicit human review.
- **Explanation integration**: GenAI support was used to evaluate whether explanation should directly drive planning. The final system intentionally rejected that design and kept Qwen as a non-critical explanation layer with timeout and failure isolation.

Full exported conversation logs will be attached as supplementary material at submission time, as required by the assessment brief.
