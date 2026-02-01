from typing import Any, overload

import instructor
from pydantic import BaseModel

from llm.clients.schemas import ClientCall, ClientMessage
from llm.clients.strategy import ClientLogStrategy
from llm.common.pricing import PricingService
from llm.common.schemas import LLMModel, LLMProvider, LLMRole
from llm.common.utils import to_context_messages


class Client:
    def __init__(
        self,
        model: LLMModel,
        log_strategies: list[ClientLogStrategy] = [],
    ):
        self.log_strategies = log_strategies
        self.pricing_service = PricingService()

        self.instructor_client = instructor.from_provider(
            model.provider_string,
            async_client=True,
            mode=model.mode,
        )
        self.model = model

    @overload
    async def structured_response[T: BaseModel](
        self,
        response_type: type[T],
        messages: list[dict[str, str]],
        context: BaseModel,
    ) -> T: ...

    @overload
    async def structured_response[T: BaseModel](
        self,
        response_type: type[T],
        messages: list[dict[str, str]],
    ) -> tuple[T, BaseModel]: ...

    async def structured_response[T: BaseModel](
        self,
        response_type: type[T],
        messages: list[dict[str, str]],
        context: BaseModel | None = None,
    ) -> T | tuple[T, BaseModel]:
        """
        Provides a structured response via an LLM call

        Uses provided log strategies to log all the LLM messages
        """
        response, llm_call = await self._structured_response(
            response_type, messages
        )

        if context is not None:
            for strategy in self.log_strategies:
                strategy.handle(llm_call, context)
            return response

        return response, llm_call

    async def _structured_response[T: BaseModel](
        self,
        response_type: type[T],
        messages: list[dict[str, str]],
    ) -> tuple[T, ClientCall]:
        if self.model.provider == LLMProvider.OPENAI:
            parsed, response = await self._openai_response(
                response_type, messages
            )
        elif self.model.provider == LLMProvider.ANTHROPIC:
            parsed, response = await self._anthropic_response(
                response_type, messages
            )
        else:
            raise ValueError(
                f"Unsupported provider: {self.model.provider}"
            )

        llm_call = self._create_llm_call(messages, parsed, response)
        return parsed, llm_call

    async def _openai_response[T: BaseModel](
        self,
        response_type: type[T],
        messages: list[dict[str, str]],
    ) -> tuple[T, Any]:
        return await self.instructor_client.responses.create_with_completion(  # type: ignore
            model=self.model.value,
            response_model=response_type,
            max_retries=3,
            input=messages,  # type: ignore
        )

    async def _anthropic_response[T: BaseModel](
        self,
        response_type: type[T],
        messages: list[dict[str, str]],
    ) -> tuple[T, Any]:
        return await self.instructor_client.messages.create_with_completion(  # type: ignore
            model=self.model.value,
            response_model=response_type,
            max_retries=3,
            messages=messages,  # type: ignore
        )

    def _create_llm_call(
        self,
        messages: list[dict[str, str]],
        parsed: BaseModel,
        response: Any,
    ) -> ClientCall:
        context_messages = to_context_messages(messages)
        client_message = self._parse_client_message(parsed)

        return ClientCall(
            context_messages=context_messages,
            client_message=client_message,
            model_name=self.model.value,
            **self.pricing_service.get_response_stats(
                response, self.model.value
            ).model_dump(),
        )

    @staticmethod
    def _parse_client_message(parsed: BaseModel) -> ClientMessage:
        return ClientMessage(response=parsed, role=LLMRole.ASSISTANT)
