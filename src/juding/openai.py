from src.config import settings
from src.constants import JudgeType
from src.depedencies import instructor_client
from src.juding.base import BaseJudgeService, JudgeResult
from llm import Client

JUDGE_SYSTEM_PROMPT = """You are an expert judge tasked with evaluating the quality of an AI assistant's response to a user question.

Your evaluation should consider the following criteria:
1. Correctness: Is the answer factually accurate? Does it contain any errors or misleading information?
2. Completeness: Does the answer fully address all aspects of the question? Are there any important points missing?
3. Clarity: Is the answer well-structured, easy to understand, and appropriately concise?
4. Relevance: Does the answer stay on topic and directly address what was asked?

Scoring guidelines:
- 90-100: Excellent response, fully correct and comprehensive
- 70-89: Good response, mostly correct with minor issues
- 50-69: Acceptable response, but has notable gaps or errors
- 30-49: Poor response, significant issues with accuracy or completeness
- 0-29: Unacceptable response, fails to address the question or is largely incorrect

A score of 70 or above is considered a "pass", below 70 is a "fail"."""

JUDGE_EVAL_PROMPT = (
    "Please evaluate the assistant's response to the user's question above."
)


class OpenAiJudge(BaseJudgeService):
    def __init__(self):
        super().__init__(JudgeType.LLM, settings.LLM_MODEL)

        self.system_prompt = JUDGE_SYSTEM_PROMPT
        self.eval_prompt = JUDGE_EVAL_PROMPT
        self.client = Client(
            log_strategies=[],
            instructor_client=instructor_client,
            model_name=settings.LLM_MODEL,
        )

    def _get_judge_result(self, question: str, answer: str) -> JudgeResult:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
            {"role": "user", "content": self.eval_prompt},
        ]
        return self.client.structured_response(JudgeResult, messages, None)
