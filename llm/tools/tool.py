# mypy: ignore-errors
import json
import logging
from abc import ABC, abstractmethod
from typing import Type

from openai import OpenAI
from openai.types.responses import (
    Response,
)
from pydantic import BaseModel

from llm.common.pricing import PricingService
from llm.common.utils import to_context_messages
from llm.tools.prompts import DEFAULT_TOOL_PROMPT
from llm.tools.schemas import (
    ToolDefinition,
    ToolResult,
    LLMRole,
    ToolMessage,
    ToolCall,
)
from llm.common.schemas import ContextMessage
from llm.tools.strategy import ToolLogStrategy


class Tool[T: BaseModel](ABC):
    """
    TODO: This class needs improvement for clarification purposes
    """

    tool_definition: ToolDefinition

    def __init__(
        self,
        parameters_model: Type[BaseModel],
        client: OpenAI,
        model_name: str,
        log_strategies: list[ToolLogStrategy],
        system_prompt: str | None = None,
    ):
        self.system_prompt = system_prompt or DEFAULT_TOOL_PROMPT
        self.model_name = model_name
        self.client = client

        self.pricing_service = PricingService()
        self.parameters_model = parameters_model
        self.context_messages: list[dict] = []

        self.logger = logging.getLogger(__name__)
        self.logging_messages: list[ToolMessage | ContextMessage] = []
        self.log_strategies = log_strategies

    def execute(self, question: str, context: BaseModel) -> ToolResult:
        self.context_messages = []

        response = self._ask_for_arguments(question)
        metadata = self._call_tool(response)
        result = self._ask_for_result()

        self._call_log_strategies(context)

        return ToolResult(result, metadata)

    def _call_log_strategies(self, context: BaseModel):
        context_messages = []
        response_messages = []
        for message in self.logging_messages:
            if isinstance(message, ContextMessage):
                context_messages.append(message)
            else:
                response_messages.append(message)

        for strategy in self.log_strategies:
            strategy.handle(
                ToolCall(
                    context_messages=context_messages,
                    tool_messages=response_messages,
                ),
                context,
            )

    def _ask_for_arguments(self, question: str) -> Response:
        messages = [
            {
                "role": "system",
                "content": self.system_prompt,
            },
            {"role": "user", "content": question},
        ]
        self.context_messages.extend(messages)
        self.logging_messages.extend(to_context_messages(messages))

        response: Response = self.client.responses.create(
            model=self.model_name,
            tools=self._openai_json(),  # noqa
            input=self.context_messages,  # noqa
        )
        return response

    def _call_tool(self, response: Response) -> dict:
        if len(response.output) != 1:
            self.logger.error(
                "Tool call must have exactly one response, it has %d, tool %s",
                len(response.output),
                self.tool_definition.name,
            )
            return {}

        item = response.output[0]
        if not hasattr(item, "arguments"):
            self._handle_missing_argument(item)
            return {}

        params_str = item.arguments
        tool_params = self.parameters_model(**json.loads(params_str))
        self.logging_messages.append(
            ToolMessage(
                contents=params_str,
                model_name=self.model_name,
                **self.pricing_service.get_response_stats(
                    response, self.model_name
                ).model_dump(),
            )
        )
        tool_result = self._call(tool_params)

        self._append_tool_response(item, response, tool_result.contents)
        return tool_result.metadata

    def _handle_missing_argument(self, item):
        error_text = item.content[0].text
        self.logger.error(
            "Tool call must have at least one argument, reason: %s", error_text
        )
        # Continue so that there is a chance of success and log for debugging purposes
        self.context_messages.append({"role": "assistant", "content": error_text})

    def _append_tool_response(self, item, response: Response, tool_response: str):
        self.logging_messages.append(
            ContextMessage(message=tool_response, role=LLMRole.TOOL)
        )
        self.context_messages += response.output
        self.context_messages.append(
            {
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": json.dumps({"tool_result": tool_response}),
            }
        )

    def _ask_for_result(self) -> str:
        response: Response = self.client.responses.create(
            model=self.model_name,
            tools=self._openai_json(),  # noqa
            input=self.context_messages,  # noqa
        )

        self.logging_messages.append(
            ToolMessage(
                contents=response.output_text,
                model_name=self.model_name,
                **self.pricing_service.get_response_stats(
                    response, self.model_name
                ).model_dump(),
            )
        )
        return response.output_text

    def _openai_json(self) -> list[dict]:
        """
        Based on

        https://platform.openai.com/docs/guides/function-calling
        """
        parameters = self.parameters_model.model_json_schema()
        parameters["additionalProperties"] = False
        return [
            {
                "type": "function",
                "name": self.tool_definition.name,
                "description": self.tool_definition.description,
                "parameters": parameters,
                "strict": True,
            }
        ]

    @abstractmethod
    def _call(self, tool_param: T) -> ToolResult:
        pass
