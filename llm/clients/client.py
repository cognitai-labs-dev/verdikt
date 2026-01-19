from instructor import Instructor
from openai.types.responses import Response
from pydantic import BaseModel

from llm.common.pricing import PricingService
from llm.common.schemas import LLMRole, ContextMessage
from llm.clients.schemas import ClientCall, ClientMessage
from llm.clients.strategy import ClientLogStrategy


class Client:
    def __init__(
        self,
        log_strategies: list[ClientLogStrategy],
        instructor_client: Instructor,
        model_name: str,
    ):
        self.log_strategies = log_strategies
        self.instructor_client = instructor_client
        self.model_name = model_name
        self.pricing_service = PricingService()

    def structured_response[T: BaseModel](
        self,
        response_type: type[T],
        messages: list[dict[str, str]],
        context: BaseModel | None,
    ) -> T:
        """
        Provides a structured response via an LLM call

        Uses provided log strategies to log all the LLM messages
        """
        parsed, response = self.instructor_client.responses.create_with_completion(
            model=self.model_name,
            response_model=response_type,
            max_retries=3,
            input=messages,
        )
        self._handle_log_strategies(messages, context, parsed, response)
        return parsed

    def _handle_log_strategies(
        self,
        messages: list[dict[str, str]],
        context: BaseModel | None,
        parsed: BaseModel,
        response: Response,
    ):
        context_messages = self._parse_context_messages(messages)
        client_message = self._parse_client_message(parsed)

        llm_call = ClientCall(
            context_messages=context_messages,
            client_message=client_message,
            model_name=self.model_name,
            **self.pricing_service.get_response_stats(
                response, self.model_name
            ).model_dump(),
        )
        for strategy in self.log_strategies:
            strategy.handle(llm_call, context)

    @staticmethod
    def _parse_client_message(parsed: BaseModel) -> ClientMessage:
        return ClientMessage(response=parsed, role=LLMRole.ASSISTANT)

    @staticmethod
    def _parse_context_messages(
        messages: list[dict[str, str]],
    ) -> list[ContextMessage]:
        return [
            ContextMessage(message=message["content"], role=LLMRole(message["role"]))
            for message in messages
        ]
