from abc import ABC, abstractmethod

from pydantic import BaseModel

from llm.clients.schemas import ClientCall


class ClientLogStrategy(ABC):
    @abstractmethod
    def handle(self, call: ClientCall, context: BaseModel | None):
        pass

