import httpx
from typing import Optional
import json

from app.llm.base import BaseLLMProvider
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenRouterProvider(BaseLLMProvider):
    """Провайдер для OpenRouter API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or settings.openrouter_api_key
        self.base_url = base_url or settings.openrouter_base_url
        self.model = model or settings.default_llm_model
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """Генерация текста через OpenRouter."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        **kwargs
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"Error calling OpenRouter API: {e}")
                raise
    
    async def generate_structured(
        self,
        prompt: str,
        response_format: dict,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> dict:
        """Генерация структурированного JSON ответа."""
        format_instruction = f"\nОтветь в формате JSON со следующей структурой: {json.dumps(response_format, ensure_ascii=False)}"
        full_prompt = prompt + format_instruction
        
        response_text = await self.generate(
            full_prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            **kwargs
        )
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start != -1 and end != 0:
                return json.loads(response_text[start:end])
            raise

