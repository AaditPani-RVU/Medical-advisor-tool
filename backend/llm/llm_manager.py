"""
Unified LLM Manager handling API calls with local fallback.
Supports Google Gemini (Primary) and Ollama (Fallback).
"""

import logging
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from backend.core.settings import settings
from backend.llm.ollama_client import get_ollama_client

logger = logging.getLogger(__name__)

# Configure Gemini if key is available
_gemini_configured = False
if settings.gemini_api_key:
    try:
        genai.configure(api_key=settings.gemini_api_key)
        _gemini_configured = True
    except Exception as e:
        logger.error(f"Failed to configure Gemini: {e}")

class LLMManager:
    """Manages LLM generation with primary API and local fallback."""
    
    def __init__(self):
        self.provider = settings.llm_provider
        self.ollama_client = get_ollama_client()
        
        # Safety settings for Gemini to prevent false positive blocks on health info
        self.gemini_safety = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

    def generate(self, prompt: str, system_prompt: str | None = None, temperature: float = 0.1, max_tokens: int = 2048) -> str:
        """
        Generate completion, falling back to Ollama if Gemini fails or is disabled.
        """
        if self.provider == "gemini" and _gemini_configured:
            try:
                # Use gemini-2.5-flash as default fast model
                model = genai.GenerativeModel('gemini-2.5-flash',
                                             system_instruction=system_prompt)
                
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    ),
                    safety_settings=self.gemini_safety
                )
                return response.text
            except Exception as e:
                logger.warning(f"Gemini generation failed, falling back to Ollama. Error: {e}")
                
        # Fallback / Default
        return self.ollama_client.generate(
            prompt, 
            temperature=temperature, 
            system_prompt=system_prompt, 
            max_tokens=max_tokens
        )

    def chat(self, messages: list[dict], temperature: float = 0.3, max_tokens: int = 2048) -> str:
        """
        Chat completion with history mapping.
        """
        if self.provider == "gemini" and _gemini_configured:
            try:
                system_instruction = None
                gemini_history = []
                
                for msg in messages:
                    if msg["role"] == "system":
                        system_instruction = msg["content"]
                    elif msg["role"] == "assistant":
                        gemini_history.append({"role": "model", "parts": [msg["content"]]})
                    elif msg["role"] == "user":
                        gemini_history.append({"role": "user", "parts": [msg["content"]]})
                
                model = genai.GenerativeModel(
                    'gemini-2.5-flash',
                    system_instruction=system_instruction
                )
                
                if gemini_history:
                    # Pop the last user message to use as the actual prompt
                    last_msg = gemini_history.pop()
                    if last_msg["role"] == "user":
                        chat_session = model.start_chat(history=gemini_history)
                        response = chat_session.send_message(
                            last_msg["parts"][0],
                            generation_config=genai.types.GenerationConfig(
                                temperature=temperature,
                                max_output_tokens=max_tokens,
                            ),
                            safety_settings=self.gemini_safety
                        )
                        return response.text

            except Exception as e:
                logger.warning(f"Gemini chat failed, falling back to Ollama. Error: {e}")
                
        # Fallback to Ollama
        return self.ollama_client.chat(messages, temperature=temperature, max_tokens=max_tokens)


# Singleton
_manager: LLMManager | None = None

def get_llm() -> LLMManager:
    global _manager
    if _manager is None:
        _manager = LLMManager()
    return _manager
