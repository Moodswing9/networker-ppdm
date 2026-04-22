#!/usr/bin/env python3
"""
scripts/sla_report.py

Print a compliance summary for all PPDM-protected assets.
Highlights assets that are out of compliance (no recent backup copy).

Usage:
    python scripts/sla_report.py
    python scripts/sla_report.py --asset-type KUBERNETES
    python scripts/sla_report.py --non-compliant-only

Environment:
    PPDM_HOST, PPDM_USER, PPDM_PASS  (required)
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ppdm import PPDMClient


def main() -> int:
    parser = argparse.ArgumentParser(description="PPDM SLA compliance report")
    parser.add_argument("--asset-type", help="Filter by asset type")
    parser.add_argument("--non-compliant-only", action="store_true",
                        help="Show only non-compliant assets")
    args = parser.parse_args()

    with PPDMClient.from_env() as ppdm:
        assets = ppdm.list_assets(asset_type=args.asset_type)

    if not assets:
        print("No assets found.")
        return 0

    compliant     = [a for a in assets if a.get("complianceStatus") == "IN_COMPLIANCE"]
    non_compliant = [a for a in assets if a.get("complianceStatus") != "IN_COMPLIANCE"]
    unprotected   = [a for a in assets if not a.get("protectionPolicyName")]

    print(f"\nSLA Compliance Report")
    print(f"{'─' * 60}")
    print(f"  Total assets    : {len(assets)}")
    print(f"  In compliance   : {len(compliant)}")
    print(f"  Non-compliant   : {len(non_compliant)}")
    print(f"  Unprotected     : {len(unprotected)}")
    print()

    display = non_compliant if args.non_compliant_only else assets
    col_w = 38

    print(f"  {'Asset':<{col_w}} {'Type':<22} {'Policy':<25} Status")
    print(f"  {'─' * col_w} {'─' * 22} {'─' * 25} {'─' * 15}")

    for a in sorted(display, key=lambda x: x.get("complianceStatus", "") or ""):
        name   = (a.get("name") or "")[:col_w]
        atype  = (a.get("type") or "")[:22]
        policy = (a.get("protectionPolicyName") or "—")[:25]
        status = a.get("complianceStatus") or "UNPROTECTED"
        marker = "  " if status == "IN_COMPLIANCE" else "! "
        print(f"  {marker}{name:<{col_w - 2}} {atype:<22} {policy:<25} {status}")

    print()
    return 1 if non_compliant else 0


if __name__ == "__main__":
    sys.exit(main())
