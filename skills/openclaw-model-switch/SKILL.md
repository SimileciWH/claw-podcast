---
name: openclaw-model-switch
description: Switch the active model for the current OpenClaw session and verify the result. Use when the user asks to change model (for example, MiniMax M2.1, MiniMax M2.5-highspeed, gpt-5.3-codex, gpt-5.4-codex), check whether a model is allowed, or troubleshoot model routing/allowlist issues.
---

# OpenClaw Model Switch

Use this workflow to switch model safely and report the exact active model.

## Switch workflow

1. Call `session_status(model=<target_model>)`.
2. If success, read back the returned model and report it to user.
3. If error contains `not allowed`, do not retry blindly.
   - Explain that the model is blocked by allowlist/routing config.
   - List the exact config areas to update.

## Canonical model ids used in this environment

- `minimax/MiniMax-M2.5-highspeed`
- `minimax/MiniMax-M2.1`
- `minimax/MiniMax-M2.5` (may be blocked unless explicitly allowlisted)
- `openai-codex/gpt-5.3-codex`
- `openai-codex/gpt-5.4-codex` (may be blocked unless explicitly allowlisted)

## If model is blocked (`not allowed`)

Check and update these settings (with user confirmation when changing config):

1. `agents.defaults.models` must include the target model id.
2. Provider model inventory under `models.providers.<provider>.models` must include the target model when provider-level allowlist is used.
3. Required auth profile/provider must exist under `auth.profiles`.

After config changes, restart is applied by gateway config actions automatically.

## Confirmation format

Always return:

- Requested model
- Effective model after switch
- Status: success/blocked
- If blocked: exact missing config item
