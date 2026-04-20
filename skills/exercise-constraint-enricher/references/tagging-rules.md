# Tagging Rules

## Purpose

These rules define the first deterministic enrichment pass for the fitness planner project.

## Movement Pattern

Use the following controlled list:

- `horizontal_push`
- `vertical_push`
- `horizontal_pull`
- `vertical_pull`
- `squat`
- `hinge`
- `lunge`
- `core`

### Heuristic Notes

- chest press and push-up style movements map to `horizontal_push`
- overhead press and raise style movements map to `vertical_push`
- rows map to `horizontal_pull`
- pull-up and pulldown style movements map to `vertical_pull`
- squat and leg-press style movements map to `squat`
- deadlift, hip hinge, bridge, and swing style movements map to `hinge`
- lunge, split-squat, and step-up style movements map to `lunge`
- crunch, plank, and leg-raise style movements map to `core`

## Difficulty

- `beginner`
- `intermediate`
- `advanced`

Conservative rule:

- beginner for basic bodyweight squats, planks, glute bridges, and similarly simple patterns
- advanced for clearly technical or high-skill movements such as handstand, snatch, pistol squat, or single-leg variants
- otherwise default to intermediate unless there is a strong reason not to

## Environment

- `gym` when barbell/bench style setup is required
- `both` for bodyweight, dumbbell, band, kettlebell, mat, and similar flexible setups

## Impact Level

- `high` for jumping or explosive conditioning movements
- `medium` for lunges, swings, and similar moderate-load dynamic lower-body movements
- `low` otherwise

## Contraindication Tags

Use only the current conservative set:

- `shoulder_discomfort`
- `knee_discomfort`
- `lower_back_discomfort`

### Conservative Mapping

- pushing and raise-heavy upper-body movements can trigger `shoulder_discomfort`
- squat and lunge patterns can trigger `knee_discomfort`
- hinge patterns and bent-over loading can trigger `lower_back_discomfort`

## Exclusions

Exclude records when they are closer to drills, warmups, mobility work, unsupported machine-specific variants, or otherwise too ambiguous for the current schema.
