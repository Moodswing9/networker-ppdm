---
description: Report all failed PPDM backup activities (CI-friendly)
argument-hint: "[--asset-type <TYPE>] [--json] [--since <TIMESTAMP>]"
allowed-tools: ["Bash"]
---

Run the failed-jobs check:

```bash
python scripts/check_failed_jobs.py $ARGUMENTS
```

The script exits 1 if failures are found, making it CI-friendly.

After running:

- If exit code is 0 and no failures: confirm "no failed activities" and stop
- If failures found: group by asset type (Kubernetes · VMware · Database · NAS · etc.), then by failure reason
- For the top 3 most common failure reasons, suggest the next diagnostic step (which log to check, which REST endpoint to query)
- If `--json` was passed, format the output as a clean table for the operator

Common failure patterns to flag immediately:
- `vProxy unreachable` → check vProxy registration and network
- `Lockbox access denied` → check credential rotation
- `Storage unit full` → check Data Domain `filesystem_stats`
- `Backup window expired` → policy schedule misalignment
