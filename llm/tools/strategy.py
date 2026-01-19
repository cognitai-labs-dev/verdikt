from abc import ABC, abstractmethod

from pydantic import BaseModel

from llm.tools.schemas import ToolCall


class ToolLogStrategy(ABC):
    @abstractmethod
    def handle(self, call: ToolCall, context: BaseModel):
        pass
