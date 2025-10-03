from abc import ABC, abstractmethod
from typing import Optional


class BaseLLMProvider(ABC):
    """Базовый класс для LLM провайдеров.
    
    Позволяет легко заменить OpenRouter на другой сервис.
    """
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """Генерация текста через LLM."""
        raise NotImplementedError
    
    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_format: dict,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> dict:
        """Генерация структурированного ответа."""
        raise NotImplementedError

