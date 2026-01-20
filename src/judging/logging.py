from llm import ClientLogStrategy, ClientCall
from src.schemas.judge import JudgeUpdateSchema


class JudgeClientLoggingStrategy(ClientLogStrategy):
    def handle(self, call: ClientCall, context: JudgeUpdateSchema | None):
        if context is None:
            raise Exception("No context provided in logging strategy")

        context.input_tokens = call.input_tokens
        context.output_tokens = call.output_tokens
        context.input_tokens_cost = call.input_tokens_cost
        context.output_tokens_cost = call.output_tokens_cost
