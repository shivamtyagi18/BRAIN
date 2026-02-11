
import os
from typing import Optional, Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.language_models import BaseChatModel

class LLMFactory:
    @staticmethod
    def create_llm(
        provider: Literal["gemini", "openai", "ollama"] = "gemini",
        model_name: Optional[str] = None,
        temperature: float = 0.7
    ) -> BaseChatModel:
        """
        Factory to create LLM instances based on provider.
        """
        if provider == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set.")
            return ChatGoogleGenerativeAI(
                model=model_name or "gemini-pro",
                temperature=temperature,
                google_api_key=api_key
            )
        
        elif provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set.")
            return ChatOpenAI(
                model=model_name or "gpt-4-turbo",
                temperature=temperature,
                api_key=api_key
            )
        
        elif provider == "ollama":
            return ChatOllama(
                model=model_name or "mistral",
                temperature=temperature,
                num_predict=-1,  # No output token limit
            )
        
        else:
            raise ValueError(f"Unsupported provider: {provider}")
