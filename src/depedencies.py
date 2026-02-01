import instructor
from openai import AsyncOpenAI

from src.config import settings

async_instructor_client = instructor.from_openai(
    AsyncOpenAI(api_key=settings.OPENAI_API_KEY),
    mode=instructor.Mode.RESPONSES_TOOLS,
)
