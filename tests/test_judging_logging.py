import pytest
from pydantic import BaseModel

from llm.clients.schemas import ClientCall, ClientMessage
from llm.common.schemas import LLMRole, ContextMessage
from src.judging.logging import JudgeClientLoggingStrategy
from src.schemas.judgment import JudgmentUpdateSchema


class DummyResponse(BaseModel):
    text: str = "response"


def make_client_call(
    input_tokens: int = 100,
    output_tokens: int = 50,
    input_tokens_cost: float = 0.01,
    output_tokens_cost: float = 0.02,
) -> ClientCall:
    return ClientCall(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_tokens_cost=input_tokens_cost,
        output_tokens_cost=output_tokens_cost,
        context_messages=[ContextMessage(message="test", role=LLMRole.USER)],
        client_message=ClientMessage(response=DummyResponse(), role=LLMRole.ASSISTANT),
        model_name="gpt-4",
    )


def test_handle_updates_context_with_token_info():
    strategy = JudgeClientLoggingStrategy()
    call = make_client_call(
        input_tokens=100,
        output_tokens=50,
        input_tokens_cost=0.01,
        output_tokens_cost=0.02,
    )
    context = JudgmentUpdateSchema(id=1)

    strategy.handle(call, context)

    assert context.input_tokens == 100
    assert context.output_tokens == 50
    assert context.input_tokens_cost == 0.01
    assert context.output_tokens_cost == 0.02


def test_handle_raises_when_context_is_none():
    strategy = JudgeClientLoggingStrategy()
    call = make_client_call()

    with pytest.raises(Exception, match="No context provided"):
        strategy.handle(call, None)
