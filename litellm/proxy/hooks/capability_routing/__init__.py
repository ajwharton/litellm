"""render.ai capability routing — pragma → LiteLLM model group."""

from litellm.proxy.hooks.capability_routing.main import (
    CapabilityRoutingHook,
    capability_routing_hook,
)
from litellm.proxy.hooks.capability_routing.pragma import (
    DEFAULT_FAIL_UP_CAPABILITY,
    DEFAULT_KNOWN_CAPABILITIES,
    extract_capability_from_messages,
    resolve_capability,
)

__all__ = [
    "CapabilityRoutingHook",
    "capability_routing_hook",
    "DEFAULT_FAIL_UP_CAPABILITY",
    "DEFAULT_KNOWN_CAPABILITIES",
    "extract_capability_from_messages",
    "resolve_capability",
]