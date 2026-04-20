---
name: exercise-constraint-enricher
description: Use when normalizing public exercise records into the fitness planner schema and assigning deterministic movement, difficulty, environment, impact, and contraindication tags.
---

# Exercise Constraint Enricher

## Overview

This skill standardizes raw public exercise records for the fitness planner project.

It is designed for the phase 2 data workflow:

- inspect upstream exercise records
- normalize fields into the local schema
- propose deterministic semantic tags
- flag high-risk fields for manual review

## When To Use

Use this skill when:

- a public exercise source needs to be converted into the local `Exercise` model
- records need `movement_pattern`, `difficulty`, `environment_tags`, `impact_level`, or `contraindication_tags`
- an AI-assisted pass should follow the project’s fixed labeling rules rather than free-form guessing

Do not use it for:

- end-user workout planning
- medical advice
- runtime HTTP request handling

## Input Contract

Expect a raw exercise record with as many of these fields as possible:

- upstream identifier
- exercise name
- description
- category
- equipment
- primary muscles
- secondary muscles

## Output Contract

Produce a normalized record containing:

- `source_id`
- `source_name`
- `name`
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

## Workflow

1. Normalize names, description text, muscles, and equipment.
2. Reject records that match project exclusion rules or have too little signal.
3. Derive `movement_pattern` using deterministic keyword and category heuristics.
4. Derive `difficulty`, `environment_tags`, and `impact_level`.
5. Derive conservative `contraindication_tags`.
6. Mark `difficulty` and `contraindication_tags` as mandatory manual-review fields.

## Review Rules

- Always require manual review for `difficulty`.
- Always require manual review for `contraindication_tags`.
- For other semantic fields, sampling review is acceptable after the rules stabilise.
- If the record is ambiguous, exclude it rather than inventing a confident label.

## References

- For project-specific tagging rules, read `references/tagging-rules.md`.
