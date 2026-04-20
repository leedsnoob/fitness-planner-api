from __future__ import annotations

import html
import re
from collections import defaultdict
from collections.abc import Iterable
from typing import Optional

PATTERN_ORDER = [
    "horizontal_push",
    "vertical_push",
    "horizontal_pull",
    "vertical_pull",
    "squat",
    "hinge",
    "lunge",
    "core",
]

HOME_COMPATIBLE_EQUIPMENT = {
    "bodyweight",
    "dumbbell",
    "gym_mat",
    "kettlebell",
    "pull_up_bar",
    "resistance_band",
    "swiss_ball",
}

GYM_ONLY_EQUIPMENT = {"barbell", "bench", "incline_bench", "sz_bar"}

ADVANCED_KEYWORDS = {
    "1 leg",
    "clean",
    "dragon flag",
    "handstand",
    "muscle up",
    "pistol",
    "planche",
    "single leg",
    "snatch",
    "turkish get up",
}

BEGINNER_KEYWORDS = {
    "bodyweight squat",
    "dead bug",
    "glute bridge",
    "knee push up",
    "plank",
    "wall sit",
}

HIGH_IMPACT_KEYWORDS = {"box jump", "burpee", "jump", "snatch"}
MEDIUM_IMPACT_KEYWORDS = {"kettlebell swing", "lunge", "split squat", "step up"}
EXCLUDED_KEYWORDS = {
    "abduction",
    "adduction",
    "bag",
    "battle rope",
    "drill",
    "hackenschmitt",
    "jump rope",
    "mobility",
    "stretch",
    "warmup",
    "warm-up",
}
UNSUPPORTED_GYM_KEYWORDS = {"cable", "landmine", "lever", "machine", "smith", "sled"}

EQUIPMENT_ALIASES = {
    "bench": "bench",
    "barbell": "barbell",
    "dumbbell": "dumbbell",
    "gym mat": "gym_mat",
    "incline bench": "incline_bench",
    "kettlebell": "kettlebell",
    "none (bodyweight exercise)": "bodyweight",
    "pull-up bar": "pull_up_bar",
    "resistance band": "resistance_band",
    "swiss ball": "swiss_ball",
    "sz-bar": "sz_bar",
}

MUSCLE_ALIASES = {
    "abs": "abs",
    "biceps": "biceps",
    "calves": "calves",
    "chest": "chest",
    "glutes": "glutes",
    "hamstrings": "hamstrings",
    "lats": "lats",
    "quads": "quads",
    "shoulders": "shoulders",
    "triceps": "triceps",
}


def strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def slugify(value: str) -> str:
    lowered = value.lower().strip()
    lowered = re.sub(r"[^a-z0-9]+", "_", lowered)
    return re.sub(r"_+", "_", lowered).strip("_")


def normalize_equipment(value: str) -> str:
    slug = value.lower().strip()
    return EQUIPMENT_ALIASES.get(slug, slugify(value))


def normalize_muscle(value: str) -> str:
    slug = value.lower().strip()
    return MUSCLE_ALIASES.get(slug, slugify(value))


def unique_in_order(values: Iterable[str]) -> list[str]:
    seen = set()
    ordered: list[str] = []
    for item in values:
        if not item or item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def get_english_translation(record: dict) -> Optional[dict]:
    for translation in record.get("translations", []):
        if translation.get("language") == 2 and translation.get("name"):
            return translation
    return None


def infer_environment_tags(equipment_tags: list[str]) -> list[str]:
    equipment = set(equipment_tags)
    if not equipment:
        return ["both"]
    if equipment & GYM_ONLY_EQUIPMENT:
        return ["gym"]
    if equipment <= HOME_COMPATIBLE_EQUIPMENT:
        return ["both"]
    return ["both"]


def infer_movement_pattern(name: str, description: str, category: str, muscles: list[str]) -> str:
    text = f"{name} {description} {category}".lower()
    muscle_set = set(muscles)
    category_text = category.lower()

    if any(keyword in text for keyword in ("pull up", "chin up", "pulldown", "lat pulldown")):
        return "vertical_pull"
    if any(keyword in text for keyword in ("row", "face pull")) or "lats" in muscle_set:
        return "horizontal_pull"
    if any(keyword in text for keyword in ("lunge", "split squat", "step up")):
        return "lunge"
    if any(
        keyword in text
        for keyword in ("deadlift", "good morning", "hip thrust", "glute bridge", "kettlebell swing")
    ):
        return "hinge"
    if any(keyword in text for keyword in ("squat", "wall sit", "leg press")) or "quads" in muscle_set:
        return "squat"
    if any(keyword in text for keyword in ("plank", "crunch", "sit up", "leg raise", "twist")) or "abs" in muscle_set:
        return "core"
    if "chest" in muscle_set or any(keyword in text for keyword in ("bench press", "push up", "chest press", "fly")):
        return "horizontal_push"
    if any(keyword in text for keyword in ("overhead", "shoulder press", "push press", "lateral raise", "front raise")):
        return "vertical_push"
    if "shoulders" in muscle_set:
        return "vertical_push"
    if "chest" in category_text:
        return "horizontal_push"
    if "shoulder" in category_text:
        return "vertical_push"
    if "back" in category_text:
        return "horizontal_pull"
    if "leg" in category_text:
        return "squat"
    if "abs" in category_text or "core" in category_text:
        return "core"
    if "arm" in category_text:
        if "triceps" in muscle_set:
            return "horizontal_push"
        return "horizontal_pull"
    return "core"


def infer_difficulty(name: str, equipment_tags: list[str], movement_pattern: str) -> str:
    text = name.lower()
    if any(keyword in text for keyword in ADVANCED_KEYWORDS):
        return "advanced"
    if text in BEGINNER_KEYWORDS:
        return "beginner"
    if "bodyweight" in equipment_tags and movement_pattern in {"squat", "core", "lunge"}:
        return "beginner"
    if set(equipment_tags) & GYM_ONLY_EQUIPMENT:
        return "intermediate"
    return "intermediate"


def infer_impact_level(name: str, movement_pattern: str) -> str:
    text = name.lower()
    if any(keyword in text for keyword in HIGH_IMPACT_KEYWORDS):
        return "high"
    if movement_pattern in {"lunge", "hinge"} or any(keyword in text for keyword in MEDIUM_IMPACT_KEYWORDS):
        return "medium"
    return "low"


def infer_contraindication_tags(name: str, movement_pattern: str) -> list[str]:
    text = name.lower()
    tags = set()

    if movement_pattern in {"horizontal_push", "vertical_push"} or any(
        keyword in text for keyword in ("dip", "upright row", "raise", "press")
    ):
        tags.add("shoulder_discomfort")
    if movement_pattern in {"squat", "lunge"} or any(
        keyword in text for keyword in ("jump", "step up", "split squat")
    ):
        tags.add("knee_discomfort")
    if movement_pattern == "hinge" or any(keyword in text for keyword in ("bent over", "deadlift", "good morning")):
        tags.add("lower_back_discomfort")

    return sorted(tags)


def should_skip_exercise(
    name: str,
    description: str,
    equipment_tags: list[str],
    primary_muscles: list[str],
    secondary_muscles: list[str],
) -> bool:
    text = f"{name} {description}".lower()
    if not primary_muscles and not secondary_muscles:
        return True
    if any(keyword in text for keyword in EXCLUDED_KEYWORDS):
        return True
    if not equipment_tags and any(keyword in text for keyword in UNSUPPORTED_GYM_KEYWORDS):
        return True
    return False


def clean_wger_exercise(record: dict) -> Optional[dict]:
    translation = get_english_translation(record)
    if translation is None:
        return None

    name = translation["name"].strip()
    if not name:
        return None

    description = strip_html(translation.get("description", ""))
    primary_muscles = unique_in_order(
        normalize_muscle(item.get("name_en") or item.get("name") or "") for item in record.get("muscles", [])
    )
    secondary_muscles = unique_in_order(
        normalize_muscle(item.get("name_en") or item.get("name") or "")
        for item in record.get("muscles_secondary", [])
    )
    equipment_tags = unique_in_order(
        normalize_equipment(item.get("name", "")) for item in record.get("equipment", [])
    )
    if should_skip_exercise(name, description, equipment_tags, primary_muscles, secondary_muscles):
        return None

    movement_pattern = infer_movement_pattern(
        name=name,
        description=description,
        category=(record.get("category") or {}).get("name", ""),
        muscles=primary_muscles,
    )

    return {
        "source_id": str(record["id"]),
        "source_name": "wger",
        "name": name,
        "description": description,
        "primary_muscles": primary_muscles,
        "secondary_muscles": secondary_muscles,
        "movement_pattern": movement_pattern,
        "equipment_tags": equipment_tags,
        "environment_tags": infer_environment_tags(equipment_tags),
        "difficulty": infer_difficulty(name, equipment_tags, movement_pattern),
        "impact_level": infer_impact_level(name, movement_pattern),
        "contraindication_tags": infer_contraindication_tags(name, movement_pattern),
        "is_custom": False,
    }


def build_curated_seed(records: list[dict], target_size: int = 140) -> list[dict]:
    deduplicated: dict[str, dict] = {}

    for record in records:
        cleaned = clean_wger_exercise(record)
        if cleaned is None:
            continue
        dedupe_key = slugify(cleaned["name"])
        deduplicated.setdefault(dedupe_key, cleaned)

    buckets: dict[str, list[dict]] = defaultdict(list)
    for exercise in deduplicated.values():
        buckets[exercise["movement_pattern"]].append(exercise)

    for exercises in buckets.values():
        exercises.sort(key=lambda item: (item["name"].lower(), item["source_id"]))

    curated: list[dict] = []
    while len(curated) < target_size:
        added_any = False
        for pattern in PATTERN_ORDER:
            items = buckets.get(pattern, [])
            if not items:
                continue
            curated.append(items.pop(0))
            added_any = True
            if len(curated) >= target_size:
                break
        if not added_any:
            break

    return curated
