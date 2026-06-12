# render.ai LiteLLM gateway (fork)

Capability-based routing for the render.ai **Route** pillar. Stages declare cognition
need via pragma; this proxy maps capability → governed model group.

## Pragma convention

```
#pragma capability: high-coding
Implement the fenced diff for TICKET-1234 …
```

- Capability names only — never model names in prompts
- Unknown capability **fails up** to `high-reasoning` (configurable)
- Hook strips pragma before the provider sees the message

## Quick start (local)

```bash
cd /path/to/litellm
python -m venv .venv && source .venv/bin/activate
pip install -e ".[proxy]"

cp render-ai/.env.example render-ai/.env
# edit render-ai/.env

set -a && source render-ai/.env && set +a
litellm --config render-ai/capability_registry.yaml --port 4000
```

Smoke test:

```bash
curl -s http://127.0.0.1:4000/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ignored-when-pragma-present",
    "messages": [{"role": "user", "content": "#pragma capability: cheap-deterministic\nSay hello in one word."}]
  }'
```

Check proxy logs for `CapabilityRoutingHook: model=cheap-deterministic`.

## Deploy on forge

```bash
bash render-ai/scripts/deploy_forge.sh
```

Requires `sshpass` and SSH access as `vulcan@forge`. Syncs this fork and starts the
proxy under systemd user service `render-litellm`.

## Registry governance

`render-ai/capability_registry.yaml` maps capabilities to **direct provider APIs** (no OpenRouter):

| Capability | Models (fallback order) |
|------------|-------------------------|
| `default` | Grok Composer 2.5 Fast (no-pragma harness traffic) |
| `high-reasoning` | Grok Composer 2.5 Fast → Grok 4.3 → Kimi K2.6 → Claude Sonnet 4.5 |
| `high-coding` | Kimi K2.6 → Claude Sonnet 4.5 → GPT-4.1 mini |
| `cheap-deterministic` | Grok 3 mini → GPT-5 mini → Grok 4.1 fast (non-reasoning) |
| `multimodal` | Kimi K2.6 → Grok 2 vision → Claude Sonnet 4.5 |

Re-point models by editing the registry only — prompts stay stable.

Pair with render.ai docs: `docs/capability-routing.md` in the render-ai repo.

## Fork

Upstream: [BerriAI/litellm](https://github.com/BerriAI/litellm)  
Fork: [ajwharton/litellm](https://github.com/ajwharton/litellm) — branch `render-ai`