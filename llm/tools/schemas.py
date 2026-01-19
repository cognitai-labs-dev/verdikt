from typing import NamedTuple

from pydantic import BaseModel

from llm.common.schemas import LLMRole, ResponseStats, ContextMessage


class ToolDefinition(NamedTuple):
    name: str
    description: str


class ToolResult(NamedTuple):
    contents: str
    metadata: dict


class ToolMessage(ResponseStats):
    contents: str
    role: LLMRole = LLMRole.ASSISTANT
    model_name: str


class ToolCall(BaseModel):
    context_messages: list[ContextMessage]
    tool_messages: list[ToolMessage]
