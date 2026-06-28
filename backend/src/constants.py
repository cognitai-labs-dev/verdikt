from enum import StrEnum

# Token / credential prefixes for Verdikt's own machine-auth issuer.
TOKEN_PREFIX = "vkt_"
CLIENT_ID_PREFIX = "mc_"
CLIENT_SECRET_PREFIX = "secret_"


class JudgmentType(StrEnum):
    HUMAN = "HUMAN"
    LLM = "LLM"


class JudgmentStatus(StrEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"


class EvaluationType(StrEnum):
    LLM_ONLY = "LLM_ONLY"
    HUMAN_AND_LLM = "HUMAN_AND_LLM"


class SubjectType(StrEnum):
    EMAIL = "email"
    CLIENT = "client"
