---
description: Cross-platform health check for PPDM, NetWorker, and Data Domain
allowed-tools: ["Bash"]
---

Run the unified health check across all three backup products:

```bash
backupctl doctor
```

If `backupctl` is not installed, fall back to:

```bash
python -m orchestrator.doctor
```

After running, summarize the output for the operator:

- Group findings by product (PPDM · NetWorker · Data Domain)
- Highlight any **errors** in red, **warnings** in yellow, **info** in muted text
- For each error, suggest the most likely root cause based on symptom
- If everything is green, confirm in one line and stop

If credentials are missing (no `.env` file or env vars), prompt the user to copy `.env.example` to `.env` and fill in connection details before retrying.
