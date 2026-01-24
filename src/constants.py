from enum import StrEnum


class JudgmentType(StrEnum):
    HUMAN = "HUMAN"
    LLM = "LLM"


class JudgmentStatus(StrEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
