import os
from typing import Any
from dotenv import load_dotenv, find_dotenv
from langchain_core.language_models.chat_models import BaseChatModel

# find_dotenv() searches from CWD upward, reliably finding .env regardless
# of which directory `uv run shinx` is invoked from.
load_dotenv(find_dotenv(usecwd=True))

def get_chat_model(
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.1,
    **kwargs: Any,
) -> BaseChatModel:
    """Universal LLM Factory for Shinx.
    
    Dynamically loads the appropriate LangChain model based on the provider.
    Switching between Google Gemini, OpenAI, or other providers is completely
    configuration-driven via environment variables (or direct arguments).
    
    Environment variables:
        SHINX_LLM_PROVIDER: "google_genai" (default) or "openai"
        SHINX_LLM_MODEL: e.g. "gemini-3.5-flash-lite", "gpt-4o", etc.
        GEMINI_API_KEY / GOOGLE_API_KEY: API key for Google GenAI
        OPENAI_API_KEY: API key for OpenAI
    """
    provider_name = (
        provider
        or os.getenv("SHINX_LLM_PROVIDER")
        or "google_genai"
    ).lower().strip()

    if provider_name in ("google", "google_genai", "gemini"):
        from langchain_google_genai import ChatGoogleGenerativeAI

        api_key = (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
        )
        model_name = model or os.getenv("SHINX_LLM_MODEL") or "gemini-3.5-flash"

        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temperature,
            **kwargs,
        )

    elif provider_name in ("openai", "chatgpt"):
        from langchain_openai import ChatOpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        model_name = model or os.getenv("SHINX_LLM_MODEL") or "gpt-4o-mini"

        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            temperature=temperature,
            **kwargs,
        )

    else:
        # Fallback to standard LangChain init_chat_model for any other provider
        from langchain.chat_models import init_chat_model

        model_name = model or os.getenv("SHINX_LLM_MODEL") or "gemini-3.8-flash"
        return init_chat_model(
            model=model_name,
            model_provider=provider_name,
            temperature=temperature,
            **kwargs,
        )
