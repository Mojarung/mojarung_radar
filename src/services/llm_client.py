from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from openai import OpenAI, AsyncOpenAI
from src.core.config import get_settings
from src.core.logging_config import log
import asyncio

settings = get_settings()


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """Generate text from a prompt"""
        pass

    @abstractmethod
    def generate_json(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate structured JSON from a prompt"""
        pass

    @abstractmethod
    async def agenerate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """Async version: Generate text from a prompt"""
        pass

    @abstractmethod
    async def agenerate_json(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """Async version: Generate structured JSON from a prompt"""
        pass


class NvidiaClient(BaseLLMClient):
    """NVIDIA API client implementation using Qwen model"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key or settings.nvidia_api_key
        self.model = model or settings.nvidia_model
        self.base_url = base_url or settings.nvidia_base_url
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        self.async_client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

    def generate(
        self,
        prompt: str,
        temperature: float = 0.58,
        max_tokens: int = 4096,
        top_p: float = 0.7,
        **kwargs
    ) -> str:
        """Generate text from a prompt"""
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                stream=False,
                **kwargs
            )
            
            message = completion.choices[0].message
            content = message.content if message.content else ""
            
            log.info(f"LLM generation successful (model: {self.model})")
            return content
        except Exception as e:
            log.error(f"LLM generation failed: {e}")
            raise

    def generate_json(
        self,
        prompt: str,
        temperature: float = 0.58,
        max_tokens: int = 4096,
        top_p: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate structured JSON from a prompt"""
        import json
        
        try:
            # Add JSON formatting instruction to prompt
            json_prompt = f"{prompt}\n\nОтветь ТОЛЬКО валидным JSON, без дополнительного текста."
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": json_prompt}],
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                stream=False,
                **kwargs
            )
            
            message = completion.choices[0].message
            content = message.content if message.content else ""
            
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            parsed = json.loads(content)
            log.info(f"LLM JSON generation successful (model: {self.model})")
            return parsed
        except Exception as e:
            log.error(f"LLM JSON generation failed: {e}")
            raise

    async def agenerate(
        self,
        prompt: str,
        temperature: float = 0.58,
        max_tokens: int = 4096,
        top_p: float = 0.7,
        **kwargs
    ) -> str:
        """Async version: Generate text from a prompt"""
        try:
            completion = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                stream=False,
                **kwargs
            )

            message = completion.choices[0].message
            content = message.content if message.content else ""

            log.info(f"LLM async generation successful (model: {self.model})")
            return content
        except Exception as e:
            log.error(f"LLM async generation failed: {e}")
            raise

    async def agenerate_json(
        self,
        prompt: str,
        temperature: float = 0.58,
        max_tokens: int = 4096,
        top_p: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Async version: Generate structured JSON from a prompt"""
        import json

        try:
            # Add JSON formatting instruction to prompt
            json_prompt = f"{prompt}\n\nОтветь ТОЛЬКО валидным JSON, без дополнительного текста."

            completion = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": json_prompt}],
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                stream=False,
                **kwargs
            )

            message = completion.choices[0].message
            content = message.content if message.content else ""

            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            parsed = json.loads(content)
            log.info(f"LLM async JSON generation successful (model: {self.model})")
            return parsed
        except Exception as e:
            log.error(f"LLM async JSON generation failed: {e}")
            raise


# Singleton instance
_llm_client: Optional[BaseLLMClient] = None


def get_llm_client() -> BaseLLMClient:
    """Get singleton LLM client instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = NvidiaClient()
    return _llm_client

