import pytest

from litellm.proxy.hooks.capability_routing.pragma import (
    extract_capability_from_messages,
    resolve_capability,
)


def test_extract_pragma_from_user_message():
    messages = [
        {"role": "user", "content": "#pragma capability: high-coding\nImplement the diff."}
    ]
    capability, cleaned, found = extract_capability_from_messages(messages)
    assert found is True
    assert capability == "high-coding"
    assert cleaned[0]["content"] == "Implement the diff."


def test_extract_pragma_case_insensitive():
    messages = [
        {"role": "user", "content": "#pragma capability: High-Reasoning\nPlan the change."}
    ]
    capability, _, found = extract_capability_from_messages(messages)
    assert found is True
    assert capability == "high-reasoning"


def test_no_pragma_passthrough():
    messages = [{"role": "user", "content": "Hello"}]
    capability, cleaned, found = extract_capability_from_messages(messages)
    assert found is False
    assert capability is None
    assert cleaned == messages


def test_unknown_capability_fails_up():
    known = {"high-reasoning", "high-coding", "cheap-deterministic", "multimodal"}
    resolved, fail_up = resolve_capability(
        capability="unknown-thing",
        model=None,
        known_capabilities=known,
        fail_up_capability="high-reasoning",
    )
    assert resolved == "high-reasoning"
    assert fail_up is True


def test_model_already_capability():
    known = {"high-coding"}
    resolved, fail_up = resolve_capability(
        capability=None,
        model="high-coding",
        known_capabilities=known,
        fail_up_capability="high-reasoning",
    )
    assert resolved == "high-coding"
    assert fail_up is False


@pytest.mark.asyncio
async def test_pre_call_hook_sets_model():
    from litellm.proxy.hooks.capability_routing.main import CapabilityRoutingHook

    hook = CapabilityRoutingHook()
    data = {
        "model": "gpt-4",
        "messages": [
            {
                "role": "user",
                "content": "#pragma capability: cheap-deterministic\nFormat changelog.",
            }
        ],
    }
    result = await hook.async_pre_call_hook(
        user_api_key_dict=None,
        cache=None,
        data=data,
        call_type="acompletion",
    )
    assert result["model"] == "cheap-deterministic"
    assert result["metadata"]["render_capability"] == "cheap-deterministic"
    assert "Format changelog." in result["messages"][0]["content"]