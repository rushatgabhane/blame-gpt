import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Global LLM instances - initialized lazily
_llm_reasoning_cheap = None
_llm_reasoning = None
_llm_cheap = None
_embedding_model = None


def _get_llm_config() -> Dict[str, Any]:
    """Get LLM configuration from environment variables."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    config = {
        "provider": provider,
        "base_url": os.getenv("LLM_BASE_URL"),
        "reasoning_model": os.getenv("LLM_REASONING_MODEL", "o3-2025-04-16"),
        "reasoning_cheap_model": os.getenv("LLM_REASONING_CHEAP_MODEL", "o3-mini-2025-01-31"),
        "cheap_model": os.getenv("LLM_CHEAP_MODEL", "gpt-4.1-mini"),
        "embedding_model": os.getenv("LLM_EMBEDDING_MODEL", "text-embedding-3-large"),
    }

    # Get API key based on provider
    if provider == "openai":
        config["api_key"] = os.getenv("OPENAI_API_KEY")
    elif provider == "anthropic":
        config["api_key"] = os.getenv("ANTHROPIC_API_KEY")
    elif provider == "custom":
        config["api_key"] = os.getenv("CUSTOM_API_KEY")

    # Parse custom headers if provided
    custom_headers = os.getenv("LLM_CUSTOM_HEADERS", "{}")
    try:
        config["custom_headers"] = json.loads(custom_headers)
    except json.JSONDecodeError:
        logger.warning("Invalid LLM_CUSTOM_HEADERS format, using empty dict")
        config["custom_headers"] = {}

    return config


def _create_chat_model(model_name: str, temperature: float = 0.0):
    """Create a chat model based on configuration."""
    config = _get_llm_config()
    provider = config["provider"]

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        kwargs = {
            "model": model_name,
            "api_key": config["api_key"],
            "temperature": temperature,
        }

        if config["base_url"]:
            kwargs["base_url"] = config["base_url"]

        return ChatOpenAI(**kwargs)

    elif provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            logger.error("langchain_anthropic not installed. Install with: pip install langchain-anthropic")
            raise

        kwargs = {
            "model": model_name,
            "api_key": config["api_key"],
            "temperature": temperature,
        }

        if config["base_url"]:
            kwargs["base_url"] = config["base_url"]

        return ChatAnthropic(**kwargs)

    elif provider == "custom":
        from langchain_openai import ChatOpenAI

        kwargs = {
            "model": model_name,
            "api_key": config["api_key"],
            "temperature": temperature,
            "base_url": config["base_url"],
        }

        # Add custom headers if provided
        if config["custom_headers"]:
            kwargs["default_headers"] = config["custom_headers"]

        return ChatOpenAI(**kwargs)

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def _create_embedding_model():
    """Create an embedding model based on configuration."""
    config = _get_llm_config()
    provider = config["provider"]

    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        kwargs = {
            "model": config["embedding_model"],
            "api_key": config["api_key"],
        }

        if config["base_url"]:
            kwargs["base_url"] = config["base_url"]

        return OpenAIEmbeddings(**kwargs)

    elif provider == "anthropic":
        # Anthropic doesn't have embeddings, fallback to OpenAI
        logger.warning("Anthropic doesn't support embeddings, falling back to OpenAI")
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=config["embedding_model"],
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    elif provider == "custom":
        from langchain_openai import OpenAIEmbeddings

        kwargs = {
            "model": config["embedding_model"],
            "api_key": config["api_key"],
            "base_url": config["base_url"],
        }

        # Add custom headers if provided
        if config["custom_headers"]:
            kwargs["default_headers"] = config["custom_headers"]

        return OpenAIEmbeddings(**kwargs)

    else:
        raise ValueError(f"Unsupported LLM provider for embeddings: {provider}")


def get_llm_reasoning_cheap():
    """Get the cheap reasoning LLM instance (lazy initialization)."""
    global _llm_reasoning_cheap
    if _llm_reasoning_cheap is None:
        config = _get_llm_config()
        _llm_reasoning_cheap = _create_chat_model(config["reasoning_cheap_model"])
    return _llm_reasoning_cheap


def get_llm_reasoning():
    """Get the reasoning LLM instance (lazy initialization)."""
    global _llm_reasoning
    if _llm_reasoning is None:
        config = _get_llm_config()
        _llm_reasoning = _create_chat_model(config["reasoning_model"])
    return _llm_reasoning


def get_llm_cheap():
    """Get the cheap LLM instance (lazy initialization)."""
    global _llm_cheap
    if _llm_cheap is None:
        config = _get_llm_config()
        _llm_cheap = _create_chat_model(config["cheap_model"], temperature=0.2)
    return _llm_cheap


def get_embedding_model():
    """Get the embedding model instance (lazy initialization)."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = _create_embedding_model()
    return _embedding_model


# Lazy properties for backward compatibility
class _LazyLLM:
    """Lazy wrapper for LLM instances."""

    def __init__(self, getter_func):
        self._getter = getter_func
        self._instance = None

    def __getattr__(self, name):
        if self._instance is None:
            self._instance = self._getter()
        return getattr(self._instance, name)

    def __call__(self, *args, **kwargs):
        if self._instance is None:
            self._instance = self._getter()
        return self._instance(*args, **kwargs)


def validate_llm_config() -> bool:
    """Validate LLM configuration and return True if valid."""
    try:
        config = _get_llm_config()
        provider = config["provider"]

        if not config["api_key"]:
            logger.error(f"API key not set for provider: {provider}")
            return False

        if provider == "custom" and not config["base_url"]:
            logger.error("LLM_BASE_URL is required for custom provider")
            return False

        return True
    except Exception as e:
        logger.error(f"Invalid LLM configuration: {e}")
        return False


def get_llm_config_info() -> dict:
    """Get current LLM configuration info for debugging."""
    config = _get_llm_config()
    return {
        "provider": config["provider"],
        "has_api_key": bool(config["api_key"]),
        "base_url": config["base_url"],
        "reasoning_model": config["reasoning_model"],
        "reasoning_cheap_model": config["reasoning_cheap_model"],
        "cheap_model": config["cheap_model"],
        "embedding_model": config["embedding_model"],
        "has_custom_headers": bool(config["custom_headers"]),
    }


# Backward compatibility - expose the models as module-level attributes
llmReasoningCheap = _LazyLLM(get_llm_reasoning_cheap)
llmReasoning = _LazyLLM(get_llm_reasoning)
llmCheap = _LazyLLM(get_llm_cheap)
embedding_model = _LazyLLM(get_embedding_model)
