#!/usr/bin/env python3
"""
scripts/ondemand_backup.py

Trigger an on-demand PPDM backup for a named asset and poll until completion.

Usage:
    python scripts/ondemand_backup.py --asset "my-namespace" --policy "k8s-daily"
    python scripts/ondemand_backup.py --asset "my-namespace" --policy "k8s-daily" --wait

Environment:
    PPDM_HOST, PPDM_USER, PPDM_PASS  (required)
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ppdm import PPDMClient

_POLL_INTERVAL = 10   # seconds between status checks
_TIMEOUT       = 3600 # max wait time in seconds


def main() -> int:
    parser = argparse.ArgumentParser(description="Trigger on-demand PPDM backup")
    parser.add_argument("--asset",  required=True, help="Asset name to back up")
    parser.add_argument("--policy", required=True, help="Protection policy name")
    parser.add_argument("--wait",   action="store_true",
                        help="Poll until the backup completes")
    args = parser.parse_args()

    with PPDMClient.from_env() as ppdm:
        # Resolve asset
        assets = ppdm.list_assets(name=args.asset)
        if not assets:
            print(f"Error: asset '{args.asset}' not found.", file=sys.stderr)
            return 1
        asset = assets[0]
        asset_id = asset["id"]

        # Resolve policy
        policy = ppdm.get_policy_by_name(args.policy)
        if not policy:
            print(f"Error: policy '{args.policy}' not found.", file=sys.stderr)
            return 1
        policy_id = policy["id"]

        # Trigger
        result = ppdm.trigger_backup(policy_id, asset_ids=[asset_id])
        activity_id = result.get("activityId") or result.get("id")
        print(f"Backup triggered — activity ID: {activity_id}")

        if not args.wait:
            return 0

        # Poll
        print(f"Polling every {_POLL_INTERVAL}s (timeout: {_TIMEOUT}s)...")
        deadline = time.time() + _TIMEOUT
        while time.time() < deadline:
            time.sleep(_POLL_INTERVAL)
            activity = ppdm.get_activity(activity_id)
            state    = activity.get("state", "UNKNOWN")
            progress = (activity.get("stats") or {}).get("percentComplete", 0)
            print(f"  [{state}] {progress}% complete")

            if state in ("SUCCEEDED", "FAILED", "CANCELED"):
                if state == "SUCCEEDED":
                    print("Backup completed successfully.")
                    return 0
                else:
                    error = (activity.get("result") or {}).get("error", {})
                    print(f"Backup {state}: {error.get('message', 'no detail')}")
                    return 1

        print("Timed out waiting for backup to complete.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
