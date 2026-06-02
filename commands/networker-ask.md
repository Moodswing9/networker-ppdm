---
description: Ask any NetWorker or PPDM question — answered by Claude Opus 4.7 using relevant sections from the domain knowledge base
argument-hint: '"Your question about NetWorker, PPDM, or Data Domain"'
allowed-tools: ["Bash", "Read", "Glob"]
---

The user wants to ask: $ARGUMENTS

**Execute every step yourself. Do not ask the user to run commands.**

## Step 1 — Parse arguments

From `$ARGUMENTS` extract the question (full quoted string or unquoted text).

If `$ARGUMENTS` is empty, stop:
> "Provide a question — example: `/networker-ask 'How do I protect a Kubernetes namespace in PPDM?'`"

## Step 2 — Check for backupctl

Use the Bash tool to check if `backupctl` is installed:

```bash
python3 -c "import importlib.util; print('available' if importlib.util.find_spec('orchestrator') else 'unavailable')" 2>/dev/null || echo "unavailable"
```

**If available:** skip to Step 4 (use `backupctl ask` directly).
**If unavailable:** continue to Step 3 (standalone mode).

## Step 3 — Standalone mode: locate SKILL.md and answer via Claude

Use Glob to find `skills/networker-ppdm/SKILL.md` starting from common locations:
- `./skills/networker-ppdm/SKILL.md`
- `~/networker-ppdm/skills/networker-ppdm/SKILL.md`
- Any path containing `networker-ppdm/skills/networker-ppdm/SKILL.md`

If not found, tell the user:
> "Install the package first: `pip install -e .` from the networker-ppdm repo, or clone it from `github.com/Moodswing9/networker-ppdm`."

Read the SKILL.md. Then use the Bash tool to run the following, substituting `QUESTION` and `SKILL_CONTENT`:

```bash
python3 - << 'PYEOF'
import anthropic

QUESTION     = """<substitute question here>"""
SKILL_CONTENT = """<substitute full SKILL.md content here>"""

client = anthropic.Anthropic()
with client.messages.stream(
    model='claude-opus-4-7',
    max_tokens=1024,
    thinking={'type': 'adaptive'},
    system=[{
        'type': 'text',
        'text': (
            'You are an expert Dell EMC NetWorker and PowerProtect Data Manager (PPDM) administrator. '
            'Use the provided domain knowledge base to give accurate, concise answers with exact CLI '
            'commands and API calls where relevant. If the answer is not in the knowledge base, say so.'
        ),
        'cache_control': {'type': 'ephemeral'},
    }],
    messages=[{
        'role': 'user',
        'content': f'Domain knowledge base:\n\n{SKILL_CONTENT[:80000]}\n\n---\n\nQuestion: {QUESTION}',
    }],
) as stream:
    for text in stream.text_stream:
        print(text, end='', flush=True)
print()
PYEOF
```

## Step 4 — backupctl mode

Use the Bash tool to run:

```bash
backupctl ask "<QUESTION>" --verbose
```

If `NVIDIA_API_KEY` is not set, re-run without `--verbose` (embeddings require it; the LLM uses `ANTHROPIC_API_KEY`):

```bash
backupctl ask "<QUESTION>"
```

## Step 5 — Handle errors

| Error | Response |
|---|---|
| `AuthenticationError` | "Set your API key: `export ANTHROPIC_API_KEY=sk-ant-…`" |
| `ModuleNotFoundError: anthropic` | "Install the SDK: `pip install anthropic`" |
| `ModuleNotFoundError: openai` | "Embedder requires openai: `pip install openai>=1.0`" (only in backupctl mode) |
| SKILL.md not found | Tell user to clone the repo or run `pip install -e .` |
