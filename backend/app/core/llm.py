"""
LLM client factory.
Builds a ChatOpenAI-compatible client pointed at OpenRouter.
"""
from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.core.config import settings


@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    """
    Return a cached LangChain LLM client configured for OpenRouter.

    OpenRouter accepts the OpenAI Chat Completions API schema, so we use
    ChatOpenAI with a custom base_url and the openrouter_api_key.
    """
    return ChatOpenAI(
        model=settings.openrouter_model,
        openai_api_key=settings.openrouter_api_key,
        openai_api_base=settings.openrouter_base_url,
        temperature=settings.llm_temperature,
        streaming=True,
        default_headers={
            # OpenRouter recommends these headers for attribution
            "HTTP-Referer": "https://github.com/nl2sql-agent",
            "X-Title": "NL2SQL Agent",
        },
    )


# Singleton exported for convenience
llm = get_llm()
