from enum import StrEnum
from typing import NamedTuple

from pydantic import BaseModel


class LLMRole(StrEnum):
    ASSISTANT = "assistant"
    USER = "user"
    SYSTEM = "system"
    TOOL = "tool"


class ResponseStats(BaseModel):
    input_tokens: int
    output_tokens: int
    input_tokens_cost: float
    output_tokens_cost: float


class ContextMessage(BaseModel):
    message: str
    role: LLMRole

class TokensPricing(NamedTuple):
    input_cost_per_token: float
    output_cost_per_token: float