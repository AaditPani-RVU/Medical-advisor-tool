"""
Ollama client wrapper — HTTP interface to local Ollama instance.
Supports both single-prompt generation and chat-style conversations.
"""

import httpx
import json
import logging
from backend.core.settings import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for communicating with the Ollama API."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 120.0,
    ):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.timeout = timeout

    def generate(
        self,
        prompt: str,
        temperature: float = 0.1,
        system_prompt: str | None = None,
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate a completion from Ollama.
        Low temperature for deterministic, factual output.
        Returns the raw response text.
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "num_predict": max_tokens,
            },
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = httpx.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except httpx.ConnectError:
            logger.error(
                "Cannot connect to Ollama. Is it running? "
                f"Tried: {self.base_url}"
            )
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama HTTP error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """
        Chat-style completion with message history.
        Messages format: [{"role": "system"|"user"|"assistant", "content": "..."}]
        Returns the assistant's response text.
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "num_predict": max_tokens,
            },
        }

        try:
            response = httpx.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
        except httpx.ConnectError:
            logger.error(
                "Cannot connect to Ollama. Is it running? "
                f"Tried: {self.base_url}"
            )
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama HTTP error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise

    def is_available(self) -> bool:
        """Check if Ollama is running and the model is available."""
        try:
            response = httpx.get(
                f"{self.base_url}/api/tags", timeout=5.0
            )
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                # Check if our model (or a variant) is available
                for m in models:
                    if self.model.split(":")[0] in m:
                        return True
                logger.warning(
                    f"Model '{self.model}' not found. "
                    f"Available: {models}. "
                    f"Run: ollama pull {self.model}"
                )
                return False
            return False
        except Exception:
            return False


# Singleton instance
_client: OllamaClient | None = None


def get_ollama_client() -> OllamaClient:
    """Get or create the singleton Ollama client."""
    global _client
    if _client is None:
        _client = OllamaClient()
    return _client
