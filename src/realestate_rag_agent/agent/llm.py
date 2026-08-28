from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from realestate_rag_agent.core.config import get_settings

# Overridable in tests via set_chat_model().
_override: BaseChatModel | None = None


def set_chat_model(model: BaseChatModel | None) -> None:
    global _override
    _override = model
    get_chat_model.cache_clear()


@lru_cache
def get_chat_model() -> BaseChatModel:
    if _override is not None:
        return _override

    from langchain_anthropic import ChatAnthropic

    settings = get_settings()
    if not settings.anthropic_api_key:
        raise RuntimeError("APP_ANTHROPIC_API_KEY is required to run the agent")

    return ChatAnthropic(
        model=settings.agent_model,
        temperature=0,
        max_tokens=1024,
        timeout=60,
        api_key=settings.anthropic_api_key,
    )
