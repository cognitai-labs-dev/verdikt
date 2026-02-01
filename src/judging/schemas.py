from pydantic import BaseModel


class JudgmentResult(BaseModel):
    reasoning: str
    passed: bool


class PricingSchema(BaseModel):
    input_tokens: int
    output_tokens: int
    input_tokens_cost: float
    output_tokens_cost: float
