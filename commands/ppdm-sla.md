---
description: Generate SLA compliance report across PPDM protected assets
argument-hint: "[--non-compliant-only] [--policy <NAME>]"
allowed-tools: ["Bash"]
---

Run the SLA report:

```bash
python scripts/sla_report.py $ARGUMENTS
```

After running:

- Surface the overall compliance percentage prominently
- List non-compliant assets with: asset name, policy, last successful backup, hours over SLA
- Group non-compliant assets by root cause if patterns emerge (e.g., all in one cluster, all using same policy)
- For the top non-compliant policy, suggest whether the issue is schedule misalignment, asset registration, or actual backup failure

If the user passed `--non-compliant-only`, skip the compliant section entirely and lead with the action items.
