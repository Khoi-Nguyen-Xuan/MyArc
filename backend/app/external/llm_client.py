"""
Creates the chat model every agent uses.

"""

from __future__ import annotations

from langchain.chat_models import BaseChatModel, init_chat_model

DEFAULT_MODEL = "openai:gpt-5-mini"

# HTTP statuses that mean the LLM is misconfigured, so retrying or moving on to the
# next item can't help: 401 bad or expired key, 403 no access, 404 unknown model name.
_SETUP_ERROR_STATUSES = {401, 403, 404}


def create_chat_model(
    model: str = DEFAULT_MODEL,
    *,
    api_key: str | None = None,
    timeout_seconds: float = 60.0,
) -> BaseChatModel:
    """
    Build a chat model from a "provider:model" string.
    """

    return init_chat_model(model, api_key=api_key, timeout=timeout_seconds, max_retries=2)


def is_setup_error(exc: Exception) -> bool:
    """True for errors no retry can fix. OpenAI's and Anthropic's errors both carry `status_code`."""
    return getattr(exc, "status_code", None) in _SETUP_ERROR_STATUSES
