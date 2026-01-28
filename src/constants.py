from enum import StrEnum


class JudgmentType(StrEnum):
    HUMAN = "HUMAN"
    LLM = "LLM"


class JudgmentStatus(StrEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"


class EvaluationType(StrEnum):
    LLM_ONLY = "LLM_ONLY"
    HUMAN_AND_LLM = "HUMAN_AND_LLM"
