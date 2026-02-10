from pydantic import BaseModel


class PromptSummary(BaseModel):
    llm_passed_count: int = 0
    llm_total_count: int = 0
    human_and_llm_matched_count: int = 0
    human_and_llm_total_count: int = 0
    evaluations_count: int = 0
