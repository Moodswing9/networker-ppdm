#!/usr/bin/env python3
"""
scripts/check_failed_jobs.py

Report all failed PPDM backup activities, grouped by asset type.

Usage:
    python scripts/check_failed_jobs.py
    python scripts/check_failed_jobs.py --asset-type KUBERNETES
    python scripts/check_failed_jobs.py --json

Environment:
    PPDM_HOST, PPDM_USER, PPDM_PASS  (required)
    PPDM_PORT, PPDM_VERIFY_SSL        (optional)
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ppdm import PPDMClient


def main() -> int:
    parser = argparse.ArgumentParser(description="Report failed PPDM activities")
    parser.add_argument("--asset-type", help="Filter by asset type, e.g. KUBERNETES")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    with PPDMClient.from_env() as ppdm:
        failed = ppdm.failed_activities(asset_type=args.asset_type)

    if not failed:
        print("No failed activities found.")
        return 0

    if args.json:
        print(json.dumps(failed, indent=2))
        return 1

    # Group by asset type
    by_type: dict[str, list] = {}
    for job in failed:
        atype = job.get("assetType", "UNKNOWN")
        by_type.setdefault(atype, []).append(job)

    print(f"\nFailed backup activities: {len(failed)}\n")
    for atype, jobs in sorted(by_type.items()):
        print(f"  {atype} ({len(jobs)})")
        for j in jobs:
            error = (j.get("result") or {}).get("error", {})
            code  = error.get("code", "—")
            msg   = error.get("message", "—")[:80]
            print(f"    [{j.get('startTime', '')[:19]}] {j.get('name', '')} "
                  f"| error {code}: {msg}")
        print()

    return 1  # non-zero = failures exist (useful in CI/cron)


if __name__ == "__main__":
    sys.exit(main())
