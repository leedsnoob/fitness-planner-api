from enum import Enum


class Goal(str, Enum):
    MUSCLE_GAIN = "MUSCLE_GAIN"
    STRENGTH = "STRENGTH"
    GENERAL_FITNESS = "GENERAL_FITNESS"


class TrainingLevel(str, Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class Environment(str, Enum):
    HOME = "HOME"
    GYM = "GYM"


class MovementPattern(str, Enum):
    HORIZONTAL_PUSH = "horizontal_push"
    VERTICAL_PUSH = "vertical_push"
    HORIZONTAL_PULL = "horizontal_pull"
    VERTICAL_PULL = "vertical_pull"
    SQUAT = "squat"
    HINGE = "hinge"
    LUNGE = "lunge"
    CORE = "core"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ImpactLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PlanSplit(str, Enum):
    FULL_BODY = "full_body"
    UPPER_LOWER = "upper_lower"
    PUSH_PULL_LEGS = "push_pull_legs"


class AdjustmentReason(str, Enum):
    DISLIKE = "DISLIKE"
    PAIN_OR_DISCOMFORT = "PAIN_OR_DISCOMFORT"
    EQUIPMENT_UNAVAILABLE = "EQUIPMENT_UNAVAILABLE"
    TOO_DIFFICULT = "TOO_DIFFICULT"
    ENVIRONMENT_MISMATCH = "ENVIRONMENT_MISMATCH"
    WANTS_VARIETY = "WANTS_VARIETY"


class WorkoutCompletionStatus(str, Enum):
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    SKIPPED = "SKIPPED"
