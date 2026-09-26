"""Creates the chat model every agent uses.

Agents receive a LangChain `BaseChatModel` and never import a provider SDK
directly, so switching providers is a one-string change:
"openai:gpt-5-mini" -> "anthropic:<model-name>" (plus that provider's package).
"""

from __future__ import annotations

from langchain.chat_models import BaseChatModel, init_chat_model

DEFAULT_MODEL = "openai:gpt-5-mini"


def create_chat_model(model: str = DEFAULT_MODEL, *, timeout_seconds: float = 60.0) -> BaseChatModel:
    """Build a chat model from a "provider:model" string.

    No `temperature` on purpose: GPT-5 models only accept the default, and the
    agents rely on structured output, not sampling settings, for consistency.
    """
    return init_chat_model(model, timeout=timeout_seconds, max_retries=2)
