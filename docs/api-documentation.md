# Fitness Planner API Documentation

Production base URL: `https://fitness-planner-api-qrnh.onrender.com`

Local interactive documentation:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## 1. Purpose

Fitness Planner API is a constraint-aware training planning service built with FastAPI and PostgreSQL. It supports:

- user registration and login
- profile-based training constraints
- public exercise discovery and custom exercise CRUD
- weekly plan generation
- single-exercise replacement with revision history
- workout log CRUD
- analytics endpoints
- SiliconFlow + Qwen explanations for plans and revisions

This document lists every public endpoint with:
- method and path
- authentication requirement
- parameters
- example request
- expected response
- relevant error codes

## 2. Authentication

Protected endpoints use bearer token authentication.

1. Call `POST /auth/register` or `POST /auth/login`
2. Copy the returned `access_token`
3. Send it in the request header:

```http
Authorization: Bearer <access_token>
```

Example:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 3. Unified Error Response

Business and platform errors use a unified JSON envelope:

```json
{
  "code": "provider_timeout",
  "message": "SiliconFlow explanation request timed out.",
  "details": null
}
```

Field meanings:
- `code`: machine-readable error identifier
- `message`: human-readable explanation
- `details`: optional structured details

Common error codes:
- `unauthorized`
- `not_found`
- `conflict`
- `unprocessable_entity`
- `validation_error`
- `provider_timeout`
- `provider_unavailable`
- `provider_rate_limited`
- `provider_bad_response`
- `provider_not_configured`

## 4. Common Enums

### 4.1 `Environment`
- `HOME`
- `GYM`

### 4.2 `Goal`
- `MUSCLE_GAIN`
- `STRENGTH`
- `GENERAL_FITNESS`

### 4.3 `PlanSplit`
- `full_body`
- `upper_lower`
- `push_pull_legs`

### 4.4 `AdjustmentReason`
- `DISLIKE`
- `PAIN_OR_DISCOMFORT`
- `EQUIPMENT_UNAVAILABLE`
- `TOO_DIFFICULT`
- `ENVIRONMENT_MISMATCH`
- `WANTS_VARIETY`

### 4.5 `MovementPattern`
- `horizontal_push`
- `vertical_push`
- `horizontal_pull`
- `vertical_pull`
- `squat`
- `hinge`
- `lunge`
- `core`

### 4.6 `DifficultyLevel`
- `beginner`
- `intermediate`
- `advanced`

### 4.7 `ImpactLevel`
- `low`
- `medium`
- `high`

### 4.8 `WorkoutCompletionStatus`
- `COMPLETED`
- `PARTIAL`
- `SKIPPED`

### 4.9 `ExplanationScope`
- `PLAN`
- `REVISION`

## 5. Endpoint Reference

### 5.1 `GET /health`

- Auth: none
- Purpose: health check and deployment verification

Example request:

```http
GET /health
```

Expected response: `200 OK`

```json
{
  "status": "ok",
  "service": "Fitness Planner API",
  "environment": "production"
}
```

Relevant errors: none

---

### 5.2 `POST /auth/register`

- Auth: none
- Purpose: register a new user and return a bearer token

Request body:
- `email`: required email
- `password`: required password, minimum length 8
- `display_name`: optional display name

Example request:

```json
{
  "email": "alice@example.com",
  "password": "StrongPass123!",
  "display_name": "Alice"
}
```

Expected response: `201 Created`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "email": "alice@example.com",
    "profile": {
      "display_name": "Alice",
      "training_level": null,
      "preferred_environment": null,
      "primary_goal": null,
      "training_days_per_week": null,
      "available_equipment": [],
      "discomfort_tags": [],
      "blocked_exercise_ids": []
    }
  }
}
```

Relevant errors:
- `409 conflict`: email already registered
- `422 validation_error`: invalid email or weak/short password

---

### 5.3 `POST /auth/login`

- Auth: none
- Purpose: authenticate an existing user

Request body:
- `email`
- `password`

Example request:

```json
{
  "email": "alice@example.com",
  "password": "StrongPass123!"
}
```

Expected response: `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "email": "alice@example.com",
    "profile": {
      "display_name": "Alice",
      "training_level": "INTERMEDIATE",
      "preferred_environment": "HOME",
      "primary_goal": "MUSCLE_GAIN",
      "training_days_per_week": 3,
      "available_equipment": ["dumbbell", "resistance_band"],
      "discomfort_tags": [],
      "blocked_exercise_ids": []
    }
  }
}
```

Relevant errors:
- `401 unauthorized`: invalid email or password
- `422 validation_error`

---

### 5.4 `GET /exercises`

- Auth: optional
- Purpose: list public exercises and, when authenticated with `include_custom=true`, the current user's custom exercises

Query parameters:
- `movement_pattern`
- `difficulty`
- `environment` (`home` or `gym`)
- `equipment_tag`
- `include_custom` (default `true`)
- `limit`
- `offset`

Example request:

```http
GET /exercises?movement_pattern=horizontal_push&difficulty=intermediate&limit=5&offset=0
```

Expected response: `200 OK`

```json
{
  "items": [
    {
      "id": 1,
      "source_id": "1295",
      "source_name": "wger",
      "name": "Barbell Bench Press - NB",
      "description": "Gym chest press.",
      "primary_muscles": ["chest"],
      "secondary_muscles": ["shoulders", "triceps"],
      "movement_pattern": "horizontal_push",
      "equipment_tags": ["barbell"],
      "environment_tags": ["gym"],
      "difficulty": "intermediate",
      "impact_level": "low",
      "contraindication_tags": ["shoulder_discomfort"],
      "is_custom": false
    }
  ],
  "total": 1,
  "limit": 5,
  "offset": 0
}
```

Response format notes:
- `items[]`: exercise records
- `total`: total matching records
- `limit` / `offset`: pagination echo

Relevant errors:
- `422 validation_error`
- `unprocessable_entity`: invalid `environment` filter

---

### 5.5 `GET /exercises/{exercise_id}`

- Auth: optional
- Purpose: fetch one public exercise or one custom exercise owned by the current user

Path parameters:
- `exercise_id`

Example request:

```http
GET /exercises/1
```

Expected response: `200 OK`

```json
{
  "id": 1,
  "source_id": "1295",
  "source_name": "wger",
  "name": "Barbell Bench Press - NB",
  "description": "Gym chest press.",
  "primary_muscles": ["chest"],
  "secondary_muscles": ["shoulders", "triceps"],
  "movement_pattern": "horizontal_push",
  "equipment_tags": ["barbell"],
  "environment_tags": ["gym"],
  "difficulty": "intermediate",
  "impact_level": "low",
  "contraindication_tags": ["shoulder_discomfort"],
  "is_custom": false
}
```

Relevant errors:
- `404 not_found`
- `422 validation_error`

---

### 5.6 `GET /me/profile`

- Auth: bearer token required
- Purpose: get the current user's profile

Example request:

```http
GET /me/profile
Authorization: Bearer <token>
```

Expected response: `200 OK`

```json
{
  "email": "alice@example.com",
  "profile": {
    "display_name": "Alice",
    "training_level": "INTERMEDIATE",
    "preferred_environment": "HOME",
    "primary_goal": "MUSCLE_GAIN",
    "training_days_per_week": 3,
    "available_equipment": ["dumbbell", "resistance_band"],
    "discomfort_tags": [],
    "blocked_exercise_ids": []
  }
}
```

Relevant errors:
- `401 unauthorized`

---

### 5.7 `PUT /me/profile`

- Auth: bearer token required
- Purpose: update the current user's profile

Request body:
- `display_name`
- `training_level`
- `preferred_environment`
- `primary_goal`
- `training_days_per_week`
- `available_equipment`
- `discomfort_tags`
- `blocked_exercise_ids`

Example request:

```json
{
  "display_name": "Alice",
  "training_level": "INTERMEDIATE",
  "preferred_environment": "HOME",
  "primary_goal": "MUSCLE_GAIN",
  "training_days_per_week": 3,
  "available_equipment": ["dumbbell", "resistance_band"],
  "discomfort_tags": [],
  "blocked_exercise_ids": []
}
```

Expected response: `200 OK`

```json
{
  "email": "alice@example.com",
  "profile": {
    "display_name": "Alice",
    "training_level": "INTERMEDIATE",
    "preferred_environment": "HOME",
    "primary_goal": "MUSCLE_GAIN",
    "training_days_per_week": 3,
    "available_equipment": ["dumbbell", "resistance_band"],
    "discomfort_tags": [],
    "blocked_exercise_ids": []
  }
}
```

Relevant errors:
- `401 unauthorized`
- `422 validation_error`

---

### 5.8 `POST /me/custom-exercises`

- Auth: bearer token required
- Purpose: create a user-owned custom exercise

Request body:
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

Example request:

```json
{
  "name": "Band Chest Press",
  "description": "Custom home chest press.",
  "primary_muscles": ["chest"],
  "secondary_muscles": ["triceps"],
  "movement_pattern": "horizontal_push",
  "equipment_tags": ["resistance_band"],
  "environment_tags": ["both"],
  "difficulty": "beginner",
  "impact_level": "low",
  "contraindication_tags": []
}
```

Expected response: `201 Created`

```json
{
  "id": 201,
  "source_id": null,
  "source_name": "custom",
  "name": "Band Chest Press",
  "description": "Custom home chest press.",
  "primary_muscles": ["chest"],
  "secondary_muscles": ["triceps"],
  "movement_pattern": "horizontal_push",
  "equipment_tags": ["resistance_band"],
  "environment_tags": ["both"],
  "difficulty": "beginner",
  "impact_level": "low",
  "contraindication_tags": [],
  "is_custom": true
}
```

Relevant errors:
- `401 unauthorized`
- `422 validation_error`

---

### 5.9 `PATCH /me/custom-exercises/{exercise_id}`

- Auth: bearer token required
- Purpose: partially update a custom exercise

Path parameters:
- `exercise_id`

Request body: all fields optional
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

Example request:

```json
{
  "description": "Updated home chest press.",
  "difficulty": "intermediate"
}
```

Expected response: `200 OK`

```json
{
  "id": 201,
  "source_id": null,
  "source_name": "custom",
  "name": "Band Chest Press",
  "description": "Updated home chest press.",
  "primary_muscles": ["chest"],
  "secondary_muscles": ["triceps"],
  "movement_pattern": "horizontal_push",
  "equipment_tags": ["resistance_band"],
  "environment_tags": ["both"],
  "difficulty": "intermediate",
  "impact_level": "low",
  "contraindication_tags": [],
  "is_custom": true
}
```

Relevant errors:
- `401 unauthorized`
- `404 not_found`
- `422 validation_error`

---

### 5.10 `DELETE /me/custom-exercises/{exercise_id}`

- Auth: bearer token required
- Purpose: delete a custom exercise

Path parameters:
- `exercise_id`

Example request:

```http
DELETE /me/custom-exercises/201
Authorization: Bearer <token>
```

Expected response: `204 No Content`

Response body: none

Relevant errors:
- `401 unauthorized`
- `404 not_found`
- `422 validation_error`

---

### 5.11 `POST /plans/generate`

- Auth: bearer token required
- Purpose: generate a weekly plan from the current profile constraints

Request body:
- `split`: `full_body`, `upper_lower`, or `push_pull_legs`
- `goal`: `MUSCLE_GAIN`, `STRENGTH`, or `GENERAL_FITNESS`
- `training_days_per_week`: currently `3` or `4`
- `environment`: `HOME` or `GYM`
- `note`: optional

Example request:

```json
{
  "split": "full_body",
  "goal": "MUSCLE_GAIN",
  "training_days_per_week": 3,
  "environment": "HOME",
  "note": null
}
```

Expected response: `201 Created`

```json
{
  "id": 3,
  "goal": "MUSCLE_GAIN",
  "split": "full_body",
  "training_days_per_week": 3,
  "environment": "HOME",
  "generation_mode": "rule_based_v1",
  "status": "active",
  "current_revision_number": 0,
  "session_count": 3,
  "created_at": "2026-04-21T13:46:09.731690Z",
  "request_snapshot": {
    "request": {
      "split": "full_body",
      "goal": "MUSCLE_GAIN",
      "training_days_per_week": 3,
      "environment": "HOME",
      "note": null
    },
    "profile_constraints": {
      "training_level": "INTERMEDIATE",
      "available_equipment": ["dumbbell", "resistance_band"],
      "discomfort_tags": [],
      "blocked_exercise_ids": []
    }
  },
  "sessions": [
    {
      "id": 7,
      "day_index": 1,
      "session_name": "Full Body A",
      "focus_summary": "Push, squat, pull, hinge, core",
      "exercises": [
        {
          "id": 31,
          "slot_type": "main_push",
          "selection_score": 100.0,
          "score_breakdown": {
            "pattern_match": 30.0,
            "muscle_match": 20.0,
            "difficulty_fit": 18.0,
            "environment_fit": 10.0,
            "equipment_fit": 12.0,
            "total": 100.0
          },
          "sets": 4,
          "reps": "8-12",
          "rest_seconds": 90,
          "notes": "Selected by rule-based planner for main_push."
        }
      ]
    }
  ]
}
```

Relevant errors:
- `401 unauthorized`
- `422 validation_error`
- `unprocessable_entity`: unsupported split/day combination or invalid constraints
- `409 conflict`

---

### 5.12 `GET /plans`

- Auth: bearer token required
- Purpose: list plans owned by the current user

Query parameters:
- `limit`
- `offset`

Example request:

```http
GET /plans?limit=20&offset=0
Authorization: Bearer <token>
```

Expected response: `200 OK`

```json
{
  "items": [
    {
      "id": 3,
      "goal": "MUSCLE_GAIN",
      "split": "full_body",
      "training_days_per_week": 3,
      "environment": "HOME",
      "generation_mode": "rule_based_v1",
      "status": "active",
      "current_revision_number": 1,
      "session_count": 3,
      "created_at": "2026-04-21T13:46:09.731690Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

Relevant errors:
- `401 unauthorized`
- `422 validation_error`

---

### 5.13 `GET /plans/{plan_id}`

- Auth: bearer token required
- Purpose: fetch one plan with sessions and exercises

Path parameters:
- `plan_id`

Example request:

```http
GET /plans/3
Authorization: Bearer <token>
```

Expected response: `200 OK`

```json
{
  "id": 3,
  "goal": "MUSCLE_GAIN",
  "split": "full_body",
  "training_days_per_week": 3,
  "environment": "HOME",
  "generation_mode": "rule_based_v1",
  "status": "active",
  "current_revision_number": 1,
  "session_count": 3,
  "created_at": "2026-04-21T13:46:09.731690Z",
  "request_snapshot": {
    "request": {
      "split": "full_body",
      "goal": "MUSCLE_GAIN",
      "training_days_per_week": 3,
      "environment": "HOME",
      "note": null
    },
    "profile_constraints": {
      "training_level": "INTERMEDIATE",
      "available_equipment": ["dumbbell", "resistance_band"],
      "discomfort_tags": [],
      "blocked_exercise_ids": []
    }
  },
  "sessions": [
    {
      "id": 7,
      "day_index": 1,
      "session_name": "Full Body A",
      "focus_summary": "Push, squat, pull, hinge, core",
      "exercises": []
    }
  ]
}
```

Relevant errors:
- `401 unauthorized`
- `404 not_found`
- `422 validation_error`

---

### 5.14 `DELETE /plans/{plan_id}`

- Auth: bearer token required
- Purpose: delete one plan

Path parameters:
- `plan_id`

Example request:

```http
DELETE /plans/3
Authorization: Bearer <token>
```

Expected response: `204 No Content`

Response body: none

Relevant errors:
- `401 unauthorized`
- `404 not_found`
- `422 validation_error`

---

### 5.15 `POST /plans/{plan_id}/adjustments`

- Auth: bearer token required
- Purpose: replace one planned exercise and create a revision

Path parameters:
- `plan_id`

Request body:
- `session_exercise_id`
- `reason`
- `detail_note`
- `override_environment`
- `temporary_unavailable_equipment`
- `temporary_discomfort_tags`

Example request:

```json
{
  "session_exercise_id": 31,
  "reason": "DISLIKE",
  "detail_note": null,
  "override_environment": null,
  "temporary_unavailable_equipment": [],
  "temporary_discomfort_tags": []
}
```

Expected response: `200 OK`

```json
{
  "revision_number": 1,
  "old_exercise": {
    "id": 115,
    "source_id": "1556",
    "source_name": "wger",
    "name": "Devil's Press",
    "description": "Previous movement.",
    "primary_muscles": ["chest"],
    "secondary_muscles": ["triceps"],
    "movement_pattern": "horizontal_push",
    "equipment_tags": ["dumbbell"],
    "environment_tags": ["both"],
    "difficulty": "intermediate",
    "impact_level": "low",
    "contraindication_tags": [],
    "is_custom": false
  },
  "new_exercise": {
    "id": 49,
    "source_id": "1554",
    "source_name": "wger",
    "name": "Clap Push-UP",
    "description": "Replacement movement.",
    "primary_muscles": ["chest"],
    "secondary_muscles": ["shoulders", "triceps"],
    "movement_pattern": "horizontal_push",
    "equipment_tags": ["bodyweight"],
    "environment_tags": ["both"],
    "difficulty": "intermediate",
    "impact_level": "low",
    "contraindication_tags": [],
    "is_custom": false
  },
  "score_breakdown": {
    "pattern_match": 30.0,
    "muscle_match": 20.0,
    "difficulty_fit": 18.0,
    "environment_fit": 10.0,
    "equipment_fit": 12.0,
    "total": 100.0,
    "replacement_reason_bonus": 6.0
  },
  "explanation": "Replaced Devil's Press with Clap Push-UP due to dislike.",
  "updated_plan": {
    "id": 3,
    "current_revision_number": 1,
    "sessions": []
  }
}
```

Relevant errors:
- `401 unauthorized`
- `404 not_found`
- `409 conflict`
- `422 unprocessable_entity`

---

### 5.16 `GET /plans/{plan_id}/revisions`

- Auth: bearer token required
- Purpose: list revision history for one plan

Path parameters:
- `plan_id`

Example request:

```http
GET /plans/3/revisions
Authorization: Bearer <token>
```

Expected response: `200 OK`

```json
{
  "items": [
    {
      "revision_number": 1,
      "reason": "DISLIKE",
      "detail_note": "",
      "old_exercise": {
        "id": 115,
        "name": "Devil's Press",
        "movement_pattern": "horizontal_push",
        "is_custom": false
      },
      "new_exercise": {
        "id": 49,
        "name": "Clap Push-UP",
        "movement_pattern": "horizontal_push",
        "is_custom": false
      },
      "created_at": "2026-04-21T13:46:21.336806Z"
    }
  ],
  "total": 1
}
```

Relevant errors:
- `401 unauthorized`
- `404 not_found`
- `422 validation_error`

---

### 5.17 `GET /plans/{plan_id}/revisions/{revision_number}`

- Auth: bearer token required
- Purpose: fetch a single revision in detail

Path parameters:
- `plan_id`
- `revision_number`

Example request:

```http
GET /plans/3/revisions/1
Authorization: Bearer <token>
```

Expected response: `200 OK`

```json
{
  "revision_number": 1,
  "reason": "DISLIKE",
  "detail_note": "",
  "old_exercise": {
    "id": 115,
    "name": "Devil's Press",
    "movement_pattern": "horizontal_push",
    "is_custom": false
  },
  "new_exercise": {
    "id": 49,
    "name": "Clap Push-UP",
    "movement_pattern": "horizontal_push",
    "is_custom": false
  },
  "created_at": "2026-04-21T13:46:21.336806Z",
  "score_breakdown": {
    "pattern_match": 30.0,
    "muscle_match": 20.0,
    "difficulty_fit": 18.0,
    "environment_fit": 10.0,
    "equipment_fit": 12.0,
    "total": 100.0,
    "replacement_reason_bonus": 6.0
  },
  "explanation": "Replaced Devil's Press with Clap Push-UP due to dislike.",
  "before_snapshot": {},
  "after_snapshot": {}
}
```

Relevant errors:
- `401 unauthorized`
- `404 not_found`
- `422 validation_error`

---

### 5.18 `POST /plans/{plan_id}/explain`

- Auth: bearer token required
- Purpose: generate and store a plan-level explanation

Path parameters:
- `plan_id`

Example request:

```http
POST /plans/3/explain
Authorization: Bearer <token>
```

Expected response: `201 Created`

```json
{
  "id": 3,
  "explanation_scope": "PLAN",
  "plan_id": 3,
  "revision_id": null,
  "revision_number": null,
  "provider": "siliconflow",
  "model_name": "Qwen/Qwen3.6-35B-A3B",
  "input_snapshot": {
    "scope": "PLAN",
    "plan": {
      "id": 3,
      "goal": "MUSCLE_GAIN"
    }
  },
  "output_text": "This plan uses a three-day full-body split with muscle gain as the primary goal.",
  "created_at": "2026-04-21T13:46:52.178028Z"
}
```

Relevant errors:
- `401 unauthorized`
- `404 not_found`
- `503 provider_timeout`
- `503 provider_unavailable`
- `503 provider_rate_limited`
- `503 provider_not_configured`
- `502 provider_bad_response`

---

### 5.19 `GET /plans/{plan_id}/explanations`

- Auth: bearer token required
- Purpose: list plan-level explanation history

Path parameters:
- `plan_id`

Example request:

```http
GET /plans/3/explanations
Authorization: Bearer <token>
```

Expected response: `200 OK`

```json
{
  "items": [
    {
      "id": 3,
      "explanation_scope": "PLAN",
      "plan_id": 3,
      "revision_id": null,
      "revision_number": null,
      "provider": "siliconflow",
      "model_name": "Qwen/Qwen3.6-35B-A3B",
      "input_snapshot": {
        "scope": "PLAN"
      },
      "output_text": "This plan uses a three-day full-body split with muscle gain as the primary goal.",
      "created_at": "2026-04-21T13:46:52.178028Z"
    }
  ],
  "total": 1
}
```

Relevant errors:
- `401 unauthorized`
- `404 not_found`
- `422 validation_error`

---

### 5.20 `POST /plans/{plan_id}/revisions/{revision_number}/explain`

- Auth: bearer token required
- Purpose: generate and store a revision-level explanation

Path parameters:
- `plan_id`
- `revision_number`

Example request:

```http
POST /plans/3/revisions/1/explain
Authorization: Bearer <token>
```

Expected response: `201 Created`

```json
{
  "id": 4,
  "explanation_scope": "REVISION",
  "plan_id": 3,
  "revision_id": 3,
  "revision_number": 1,
  "provider": "siliconflow",
  "model_name": "Qwen/Qwen3.6-35B-A3B",
  "input_snapshot": {
    "scope": "REVISION",
    "plan": {
      "id": 3
    },
    "revision": {
      "revision_number": 1
    }
  },
  "output_text": "The replacement was triggered by a dislike preference while preserving the same horizontal push training intent.",
  "created_at": "2026-04-21T13:47:10.000000Z"
}
```

Relevant errors:
- `401 unauthorized`
- `404 not_found`
- `503 provider_timeout`
- `503 provider_unavailable`
- `503 provider_rate_limited`
- `503 provider_not_configured`
- `502 provider_bad_response`

---

### 5.21 `GET /plans/{plan_id}/revisions/{revision_number}/explanations`

- Auth: bearer token required
- Purpose: list explanation history for one revision

Path parameters:
- `plan_id`
- `revision_number`

Example request:

```http
GET /plans/3/revisions/1/explanations
Authorization: Bearer <token>
```

Expected response: `200 OK`

```json
{
  "items": [
    {
      "id": 4,
      "explanation_scope": "REVISION",
      "plan_id": 3,
      "revision_id": 3,
      "revision_number": 1,
      "provider": "siliconflow",
      "model_name": "Qwen/Qwen3.6-35B-A3B",
      "input_snapshot": {
        "scope": "REVISION"
      },
      "output_text": "The replacement was triggered by a dislike preference while preserving the same horizontal push training intent.",
      "created_at": "2026-04-21T13:47:10.000000Z"
    }
  ],
  "total": 1
}
```

Relevant errors:
- `401 unauthorized`
- `404 not_found`
- `422 validation_error`

---

### 5.22 `POST /workout-logs`

- Auth: bearer token required
- Purpose: create a workout log for a planned exercise

Request body:
- `plan_id`
- `session_id`
- `session_exercise_id`
- `completion_status`
- `completed_sets`
- `completed_reps_total`
- `effort_rating`
- `note`
- `performed_on`

Example request:

```json
{
  "plan_id": 3,
  "session_id": 7,
  "session_exercise_id": 31,
  "completion_status": "COMPLETED",
  "completed_sets": 4,
  "completed_reps_total": 40,
  "effort_rating": 7,
  "note": "Good session.",
  "performed_on": "2026-04-21"
}
```

Expected response: `201 Created`

```json
{
  "id": 1,
  "plan_id": 3,
  "session_id": 7,
  "session_exercise_id": 31,
  "exercise_id": 49,
  "exercise_name_snapshot": "Clap Push-UP",
  "slot_type_snapshot": "main_push",
  "movement_pattern_snapshot": "horizontal_push",
  "planned_sets": 4,
  "planned_reps": "8-12",
  "planned_rest_seconds": 90,
  "completed_sets": 4,
  "completed_reps_total": 40,
  "completion_status": "COMPLETED",
  "effort_rating": 7,
  "note": "Good session.",
  "performed_on": "2026-04-21",
  "created_at": "2026-04-21T13:48:00.000000Z",
  "updated_at": "2026-04-21T13:48:00.000000Z"
}
```

Relevant errors:
- `401 unauthorized`
- `404 not_found`
- `409 conflict`
- `422 unprocessable_entity`

---

### 5.23 `GET /workout-logs`

- Auth: bearer token required
- Purpose: list workout logs with filters and pagination

Query parameters:
- `plan_id`
- `session_id`
- `performed_from`
- `performed_to`
- `completion_status`
- `limit`
- `offset`

Example request:

```http
GET /workout-logs?plan_id=3&limit=20&offset=0
Authorization: Bearer <token>
```

Expected response: `200 OK`

```json
{
  "items": [
    {
      "id": 1,
      "plan_id": 3,
      "session_id": 7,
      "session_exercise_id": 31,
      "exercise_id": 49,
      "exercise_name_snapshot": "Clap Push-UP",
      "slot_type_snapshot": "main_push",
      "movement_pattern_snapshot": "horizontal_push",
      "planned_sets": 4,
      "planned_reps": "8-12",
      "planned_rest_seconds": 90,
      "completed_sets": 4,
      "completed_reps_total": 40,
      "completion_status": "COMPLETED",
      "effort_rating": 7,
      "note": "Good session.",
      "performed_on": "2026-04-21",
      "created_at": "2026-04-21T13:48:00.000000Z",
      "updated_at": "2026-04-21T13:48:00.000000Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

Relevant errors:
- `401 unauthorized`
- `422 validation_error`

---

### 5.24 `GET /workout-logs/{log_id}`

- Auth: bearer token required
- Purpose: fetch one workout log

Path parameters:
- `log_id`

Example request:

```http
GET /workout-logs/1
Authorization: Bearer <token>
```

Expected response: `200 OK`

```json
{
  "id": 1,
  "plan_id": 3,
  "session_id": 7,
  "session_exercise_id": 31,
  "exercise_id": 49,
  "exercise_name_snapshot": "Clap Push-UP",
  "slot_type_snapshot": "main_push",
  "movement_pattern_snapshot": "horizontal_push",
  "planned_sets": 4,
  "planned_reps": "8-12",
  "planned_rest_seconds": 90,
  "completed_sets": 4,
  "completed_reps_total": 40,
  "completion_status": "COMPLETED",
  "effort_rating": 7,
  "note": "Good session.",
  "performed_on": "2026-04-21",
  "created_at": "2026-04-21T13:48:00.000000Z",
  "updated_at": "2026-04-21T13:48:00.000000Z"
}
```

Relevant errors:
- `401 unauthorized`
- `404 not_found`
- `422 validation_error`

---

### 5.25 `PATCH /workout-logs/{log_id}`

- Auth: bearer token required
- Purpose: update workout log completion fields

Path parameters:
- `log_id`

Request body: all fields optional
- `completion_status`
- `completed_sets`
- `completed_reps_total`
- `effort_rating`
- `note`
- `performed_on`

Example request:

```json
{
  "completion_status": "PARTIAL",
  "completed_sets": 3,
  "completed_reps_total": 30,
  "effort_rating": 8,
  "note": "Reduced volume.",
  "performed_on": "2026-04-21"
}
```

Expected response: `200 OK`

```json
{
  "id": 1,
  "plan_id": 3,
  "session_id": 7,
  "session_exercise_id": 31,
  "exercise_id": 49,
  "exercise_name_snapshot": "Clap Push-UP",
  "slot_type_snapshot": "main_push",
  "movement_pattern_snapshot": "horizontal_push",
  "planned_sets": 4,
  "planned_reps": "8-12",
  "planned_rest_seconds": 90,
  "completed_sets": 3,
  "completed_reps_total": 30,
  "completion_status": "PARTIAL",
  "effort_rating": 8,
  "note": "Reduced volume.",
  "performed_on": "2026-04-21",
  "created_at": "2026-04-21T13:48:00.000000Z",
  "updated_at": "2026-04-21T13:49:00.000000Z"
}
```

Relevant errors:
- `401 unauthorized`
- `404 not_found`
- `422 unprocessable_entity`

---

### 5.26 `DELETE /workout-logs/{log_id}`

- Auth: bearer token required
- Purpose: delete one workout log

Path parameters:
- `log_id`

Example request:

```http
DELETE /workout-logs/1
Authorization: Bearer <token>
```

Expected response: `204 No Content`

Response body: none

Relevant errors:
- `401 unauthorized`
- `404 not_found`
- `422 validation_error`

---

### 5.27 `GET /analytics/volume`

- Auth: bearer token required
- Purpose: return workout volume analytics

Query parameters:
- `days`: reporting range, default `30`

Example request:

```http
GET /analytics/volume?days=30
Authorization: Bearer <token>
```

Expected response: `200 OK`

```json
{
  "total_logged_sessions": 1,
  "total_completed_sets": 4,
  "total_completed_reps": 40,
  "daily_points": [
    {
      "date": "2026-04-21",
      "completed_sets": 4,
      "completed_reps": 40,
      "logged_exercises": 1
    }
  ]
}
```

Relevant errors:
- `401 unauthorized`
- `422 validation_error`

---

### 5.28 `GET /analytics/adherence`

- Auth: bearer token required
- Purpose: return adherence analytics

Query parameters:
- `plan_id`: optional plan filter

Example request:

```http
GET /analytics/adherence?plan_id=3
Authorization: Bearer <token>
```

Expected response: `200 OK`

```json
{
  "planned_exercises": 15,
  "logged_exercises": 1,
  "completed_exercises": 1,
  "partial_exercises": 0,
  "skipped_exercises": 0,
  "adherence_rate": 0.0667
}
```

Relevant errors:
- `401 unauthorized`
- `404 not_found`
- `422 validation_error`

---

### 5.29 `GET /analytics/replacements`

- Auth: bearer token required
- Purpose: return replacement analytics

Query parameters:
- `plan_id`: optional plan filter

Example request:

```http
GET /analytics/replacements?plan_id=3
Authorization: Bearer <token>
```

Expected response: `200 OK`

```json
{
  "total_revisions": 1,
  "by_reason": {
    "DISLIKE": 1
  },
  "latest_revisions": [
    {
      "revision_number": 1,
      "reason": "DISLIKE",
      "old_exercise_name": "Devil's Press",
      "new_exercise_name": "Clap Push-UP",
      "created_at": "2026-04-21T13:46:21.336806Z"
    }
  ]
}
```

Relevant errors:
- `401 unauthorized`
- `404 not_found`
- `422 validation_error`

## 6. Notes

- Explanation endpoints are non-critical enhancement endpoints. If the provider fails or times out, plan, revision, workout log, and analytics data remain intact.
- This English document is the submission version referenced by `README.md`.
