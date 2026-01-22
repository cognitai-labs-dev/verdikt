from llm import ClientLogStrategy, ClientCall
from src.judging.schemas import PricingSchema


class JudgeClientLoggingStrategy(ClientLogStrategy):
    def handle(self, call: ClientCall, context: PricingSchema | None):
        if context is None:
            raise RuntimeError("No context provided in logging strategy")

        context.input_tokens = call.input_tokens
        context.output_tokens = call.output_tokens
        context.input_tokens_cost = call.input_tokens_cost
        context.output_tokens_cost = call.output_tokens_cost
