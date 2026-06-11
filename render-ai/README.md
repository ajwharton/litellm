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

`render-ai/capability_registry.yaml` `model_list` entries sharing a `model_name` form a capability
group. Re-point models by editing this file only — prompts stay stable.

Pair with render.ai docs: `docs/capability-routing.md` in the render-ai repo.

## Fork

Upstream: [BerriAI/litellm](https://github.com/BerriAI/litellm)  
Fork: [ajwharton/litellm](https://github.com/ajwharton/litellm) — branch `render-ai`