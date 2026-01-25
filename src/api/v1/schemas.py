from pydantic import BaseModel


class JudgmentRequest(BaseModel):
    reasoning: str
    passed: bool
    score: int


class EvaluationSummaryResponse(BaseModel):
    """
    TODO: for only for 1 LLM type, later expand to a map of llm statistics
    """

    id: int
    samples_count: int
    judgments_count: int
    average_score: float
    pass_rate: int


class GoldenComparisonResponse(BaseModel):
    """
    TODO: for only for 1 LLM type, later expand to a map of llm statistics
    """

    id: int
    samples_count: int
    llm_judgments_count: int
    average_human_score: float
    average_llm_score: float
    agreement_ratio: float
