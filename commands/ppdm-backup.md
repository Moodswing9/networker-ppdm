---
description: Trigger an on-demand PPDM backup, optionally polling until completion
argument-hint: "--asset <NAME> --policy <NAME> [--wait]"
allowed-tools: ["Bash"]
---

Trigger an on-demand backup:

```bash
python scripts/ondemand_backup.py $ARGUMENTS
```

Behavior:

- If `--wait` is **not** passed: confirm the activity was queued, return the activity ID, and stop
- If `--wait` **is** passed: poll until the activity completes, then summarize duration, throughput, and final state

If the trigger fails:

- `policy not found` → list available policies via `backupctl inventory --format json | jq '.ppdm.policies[].name'`
- `asset not assigned` → suggest running `assign_assets` first
- `protection rule conflict` → check for overlapping rules on this asset
- `credentials expired` → recommend lockbox refresh

Always confirm the asset name and policy with the operator before triggering if either looks ambiguous (e.g., wildcard match returned >1 result).
