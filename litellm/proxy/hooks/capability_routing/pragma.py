"""
render.ai capability pragma parsing.

Stages declare cognition need via a leading line in message content:
    #pragma capability: high-coding

Never a model name — the proxy maps capability → LiteLLM model group.
"""

from __future__ import annotations

import os
import re
from typing import Any, List, Optional, Set, Tuple

PRAGMA_PATTERN = re.compile(
    r"^\s*#pragma\s+capability:\s*([a-z][a-z0-9_-]*)\s*$",
    re.IGNORECASE,
)

DEFAULT_KNOWN_CAPABILITIES: Set[str] = {
    "high-reasoning",
    "high-coding",
    "cheap-deterministic",
    "multimodal",
}

DEFAULT_FAIL_UP_CAPABILITY = "high-reasoning"


def known_capabilities_from_env() -> Set[str]:
    raw = os.getenv("RENDER_KNOWN_CAPABILITIES", "")
    if not raw.strip():
        return set(DEFAULT_KNOWN_CAPABILITIES)
    return {part.strip() for part in raw.split(",") if part.strip()}


def fail_up_capability_from_env() -> str:
    return os.getenv("RENDER_CAPABILITY_FAIL_UP", DEFAULT_FAIL_UP_CAPABILITY).strip()


def _content_to_str(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "\n".join(parts)
    return str(content)


def _str_to_content(original: Any, text: str) -> Any:
    if isinstance(original, str) or original is None:
        return text
    if isinstance(original, list):
        rebuilt: List[Any] = []
        replaced = False
        for block in original:
            if (
                not replaced
                and isinstance(block, dict)
                and block.get("type") == "text"
            ):
                rebuilt.append({**block, "text": text})
                replaced = True
            else:
                rebuilt.append(block)
        if not replaced and text:
            rebuilt.insert(0, {"type": "text", "text": text})
        return rebuilt
    return text


def _strip_leading_pragma(text: str) -> Tuple[Optional[str], str]:
    if not text:
        return None, text

    lines = text.splitlines()
    if not lines:
        return None, text

    match = PRAGMA_PATTERN.match(lines[0])
    if not match:
        return None, text

    capability = match.group(1).lower()
    remainder = "\n".join(lines[1:])
    if remainder:
        remainder = remainder.lstrip("\n")
    return capability, remainder


def extract_capability_from_messages(
    messages: List[dict],
) -> Tuple[Optional[str], List[dict], bool]:
    """
    Scan messages in order for the first pragma line in text content.
    Returns (capability, updated_messages, pragma_found).
    """
    if not messages:
        return None, messages, False

    updated = [dict(m) for m in messages]
    for idx, message in enumerate(updated):
        if message.get("role") not in ("user", "system", "developer"):
            continue
        original_content = message.get("content")
        text = _content_to_str(original_content)
        capability, stripped = _strip_leading_pragma(text)
        if capability is None:
            continue
        message["content"] = _str_to_content(original_content, stripped)
        return capability, updated, True

    return None, updated, False


def resolve_capability(
    capability: Optional[str],
    model: Optional[str],
    known_capabilities: Set[str],
    fail_up_capability: str,
) -> Tuple[Optional[str], bool]:
    """
    Resolve the model group name to route to.
    Returns (resolved_capability, used_fail_up).
    """
    if capability and capability in known_capabilities:
        return capability, False

    if capability and capability not in known_capabilities:
        return fail_up_capability, True

    if model and model in known_capabilities:
        return model, False

    return None, False