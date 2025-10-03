import json

import httpx

from src.core.config import Settings
from src.core.exceptions import LLMException
from src.infrastructure.llm.base import BaseLLM


class OpenRouterLLM(BaseLLM):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = httpx.AsyncClient(
            base_url=settings.openrouter_base_url,
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.settings.openrouter_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPError as e:
            raise LLMException(f"OpenRouter API error: {e}") from e
        except (KeyError, IndexError) as e:
            raise LLMException(f"Unexpected response format: {e}") from e

    async def generate_structured(
        self,
        prompt: str,
        schema: dict,
        temperature: float = 0.7,
    ) -> dict:
        try:
            structured_prompt = f"{prompt}\n\nОтветь в формате JSON согласно схеме: {json.dumps(schema, ensure_ascii=False)}"
            response_text = await self.generate(structured_prompt, temperature)
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            raise LLMException(f"Failed to parse LLM response as JSON: {e}") from e

    async def close(self) -> None:
        await self.client.aclose()

