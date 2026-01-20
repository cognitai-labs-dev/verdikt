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
