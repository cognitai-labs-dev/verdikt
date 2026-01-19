from pydantic import BaseModel

from llm.common.schemas import LLMRole, ResponseStats, ContextMessage


class ClientMessage(BaseModel):
    response: BaseModel
    role: LLMRole


class ClientCall(ResponseStats):
    context_messages: list[ContextMessage]
    client_message: ClientMessage
    model_name: str
