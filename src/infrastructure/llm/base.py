from abc import ABC, abstractmethod


class BaseLLM(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: dict,
        temperature: float = 0.7,
    ) -> dict:
        pass

