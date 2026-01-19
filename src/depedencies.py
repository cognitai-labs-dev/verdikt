import instructor
from openai import OpenAI

from src.config import settings

instructor_client = instructor.from_openai(
    OpenAI(api_key=settings.OPENAI_API_KEY), mode=instructor.Mode.RESPONSES_TOOLS
)

