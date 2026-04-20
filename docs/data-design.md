# Data Design

## Purpose

The API is not a generic exercise catalogue. It must eventually generate weekly plans and revise them when constraints change, such as equipment availability, discomfort, training environment, and exercise preference. Because of that, the seed data must be shaped for reasoning, not just storage.

## Design Approach

The project uses a single enhanced `Exercise` table in PostgreSQL for phase 2.

This is an intentional trade-off:

- it keeps the first production-ready schema small enough for fast implementation and testing
- it preserves the fields needed by later planning and substitution logic
- it avoids premature fragmentation into many tag tables before the public API for exercises is even implemented

## Core Exercise Fields

Each curated exercise record should store:

- `name`
- `source_id`
- `source_name`
- `description`
- `primary_muscles`
- `secondary_muscles`
- `movement_pattern`
- `equipment_tags`
- `environment_tags`
- `difficulty`
- `impact_level`
- `contraindication_tags`
- `is_custom`
- `created_at`

## Why Enrichment Is Required

The upstream source does not provide enough project-specific semantics for constraint-aware replacement logic. The project therefore adds a second layer of metadata.

Examples:

- `Bench Press` may arrive with chest and triceps information, but the API also needs to know that it is a `horizontal_push`, usually `gym` oriented, usually `intermediate`, and may be unsuitable for some users with shoulder discomfort.
- `Bodyweight Squat` needs environment and impact tags even if the upstream record does not explicitly frame it that way.

## Controlled Enumerations

### Movement Pattern

The initial controlled list is:

- `horizontal_push`
- `vertical_push`
- `horizontal_pull`
- `vertical_pull`
- `squat`
- `hinge`
- `lunge`
- `core`

### Difficulty

- `beginner`
- `intermediate`
- `advanced`

### Environment

- `home`
- `gym`
- `both`

### Impact Level

- `low`
- `medium`
- `high`

### Contraindication Tags

The first conservative tag set is:

- `shoulder_discomfort`
- `knee_discomfort`
- `lower_back_discomfort`

## Cleaning Rules

The seed-building pipeline follows two layers.

### Layer 1: Basic Cleaning

- remove empty or obviously unusable records
- strip HTML from descriptions
- normalize naming and list formatting
- normalize equipment and muscle labels
- deduplicate records by stable source identity and normalized name

### Layer 2: Semantic Enrichment

- derive `movement_pattern`
- derive `difficulty`
- derive `environment_tags`
- derive `impact_level`
- derive `contraindication_tags`

The second layer is where the project moves beyond a basic public exercise library into a reasoning-ready dataset.

## Review Policy

GenAI may propose semantic labels, but final project rules are not fully delegated to AI.

Manual review policy:

- `difficulty`: full review
- `contraindication_tags`: full review
- other semantic fields: category-based sampling review

This keeps the workflow efficient without weakening the project’s ability to justify risk-sensitive decisions in the oral examination.
