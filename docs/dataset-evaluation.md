# Dataset Evaluation

## Goal

The project needs a public exercise data source that can seed a PostgreSQL-backed API for constraint-aware workout planning. The selected source must support a reproducible local workflow, fit a structured SQL schema, and provide enough metadata to derive exercise tags used later for filtering and substitutions.

## Sources Reviewed

### 1. wger API

- URL: https://wger.readthedocs.io/en/latest/api/api.html
- Project: https://github.com/wger-project/wger
- Access style: public API
- Notable strength: the official API documentation states that public endpoints such as the exercise list can be accessed without authentication.
- Relevant fields: exercise name, description, category, muscles, secondary muscles, equipment, image metadata, source identifiers, per-exercise license metadata.
- Fit for this project: strong. The API structure already exposes the core exercise entities needed for seeding a relational database, while still leaving room for project-specific enrichment such as movement pattern, difficulty, impact level, and contraindication tags.

### 2. free-exercise-db

- URL: https://github.com/yuhonas/free-exercise-db
- Access style: static JSON dataset hosted in a public GitHub repository
- Notable strength: simple file-based consumption and easy local inspection
- Limitation: weaker provenance and operational structure than `wger`; less suitable when the project needs a documented upstream API and richer source metadata.
- Fit for this project: useful as a comparison point and possible backup inspiration for naming or categorisation, but not selected as the primary upstream.

### 3. Kaggle-hosted exercise datasets

- URL: https://www.kaggle.com/datasets
- Access style: downloadable files from a public dataset portal
- Notable strength: many alternative fitness and gym datasets exist
- Limitations: download flow is less reproducible in an automated project pipeline, schema quality varies significantly across dataset authors, and some datasets require authentication before download.
- Fit for this project: useful for exploratory comparison, but not ideal as the main source for a repeatable seed-generation workflow.

## Selection Decision

`wger` is the primary upstream source for this coursework.

## Why `wger` Was Chosen

1. It offers a public, documented exercise API rather than an ad hoc file dump.
2. It provides stable source identifiers that can be stored in the local database.
3. It already exposes muscles and equipment, which reduces the amount of manual bootstrapping needed before enrichment.
4. It is easier to justify in the technical report because the data access method is clear, citable, and reproducible.
5. It supports a strong workflow for this project:
   - fetch public exercise data
   - save a raw local snapshot
   - clean and enrich it into a curated seed file
   - import the curated seed into PostgreSQL

## Why The Other Sources Were Not Selected

- `free-exercise-db` is useful, but the project benefits more from a documented upstream API with richer source metadata.
- Kaggle is valuable for discovery and comparison, but not as strong for an automated and reproducible seed pipeline in a coursework setting.

## Coursework Relevance

This decision supports several assessment goals:

- clear stack and data-source justification
- evidence of independent exploration
- high-level GenAI usage through alternative comparison
- reproducible database integration for the final demo and oral examination
