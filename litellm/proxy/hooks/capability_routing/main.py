"""
render.ai capability routing hook for LiteLLM Proxy.

Parses `#pragma capability: <name>` from request messages, strips it, and sets
`model=<capability>` so LiteLLM resolves the governed model group from config.
Unknown capabilities fail up (default: high-reasoning).
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Set, Union

import litellm
from litellm._logging import verbose_proxy_logger
from litellm.caching.caching import DualCache
from litellm.integrations.custom_logger import CustomLogger
from litellm.proxy._types import UserAPIKeyAuth
from litellm.types.utils import CallTypesLiteral

from .pragma import (
    default_capability_from_env,
    extract_capability_from_messages,
    fail_up_capability_from_env,
    known_capabilities_from_env,
    resolve_capability,
)


class CapabilityRoutingHook(CustomLogger):
    """
    Pre-call hook: pragma in message → model group; unknown capability → fail up.
    """

    def __init__(
        self,
        known_capabilities: Optional[Set[str]] = None,
        fail_up_capability: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.known_capabilities = known_capabilities or known_capabilities_from_env()
        self.fail_up_capability = fail_up_capability or fail_up_capability_from_env()
        self.default_capability = default_capability_from_env()

    async def async_pre_call_hook(
        self,
        user_api_key_dict: UserAPIKeyAuth,
        cache: DualCache,
        data: dict,
        call_type: CallTypesLiteral,
    ) -> Optional[Union[Exception, str, dict]]:
        if call_type not in ("completion", "acompletion", "anthropic_messages"):
            return data

        messages = data.get("messages")
        if not messages or not isinstance(messages, list):
            return data

        requested_capability, cleaned_messages, pragma_found = (
            extract_capability_from_messages(messages)
        )
        if pragma_found:
            data["messages"] = cleaned_messages

        resolved, used_fail_up = resolve_capability(
            capability=requested_capability,
            model=data.get("model"),
            known_capabilities=self.known_capabilities,
            fail_up_capability=self.fail_up_capability,
            default_capability=self.default_capability,
        )
        if resolved is None:
            return data

        previous_model = data.get("model")
        data["model"] = resolved

        metadata: Dict[str, Any] = dict(data.get("metadata") or {})
        metadata["render_capability"] = resolved
        if requested_capability:
            metadata["render_capability_requested"] = requested_capability
        if pragma_found:
            metadata["render_pragma_source"] = "message"
        elif previous_model in self.known_capabilities:
            metadata["render_pragma_source"] = "model"
        if used_fail_up:
            metadata["render_capability_fail_up"] = True
        data["metadata"] = metadata

        verbose_proxy_logger.debug(
            "CapabilityRoutingHook: model=%s requested=%s pragma=%s fail_up=%s",
            resolved,
            requested_capability,
            pragma_found,
            used_fail_up,
        )
        return data


capability_routing_hook = CapabilityRoutingHook()

litellm.logging_callback_manager.add_litellm_callback(capability_routing_hook)