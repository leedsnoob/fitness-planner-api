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

