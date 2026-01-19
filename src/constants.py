from enum import StrEnum


class JudgeType(StrEnum):
    HUMAN = "HUMAN"
    LLM = "LLM"


class JudgeStatus(StrEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
