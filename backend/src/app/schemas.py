from src.schemas.app import AppSchema


class AppWithPrompts(AppSchema):
    judge_prompt: str
    judge_prompt_hash: str
