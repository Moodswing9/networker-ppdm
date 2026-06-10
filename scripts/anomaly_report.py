"""
Batch API anomaly detection for backup job history.

Submits each activity as a separate Batch API request to Claude Haiku
for classification: NORMAL / ANOMALOUS / DEGRADING.

Usage:
  python scripts/anomaly_report.py [--days 30] [--wait] [--batch-id <ID>]

  --wait        Block until the batch completes (polls every 30 s, 24 h max)
  --batch-id    Resume polling / collecting a previously submitted batch
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import anthropic
from ppdm.client import PPDMClient

_MODEL         = "claude-haiku-4-5-20251001"
_POLL_INTERVAL = 30
_MAX_WAIT      = 86_400


def _fetch_activities(days: int) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    try:
        with PPDMClient(
            os.environ["PPDM_HOST"],
            os.environ["PPDM_USER"],
            os.environ["PPDM_PASS"],
        ) as ppdm:
            all_acts = ppdm.list_activities(page_size=500)
    except Exception as exc:
        print(f"[anomaly-report] PPDM unavailable: {exc}", file=sys.stderr)
        return []

    out = []
    for act in all_acts:
        ts = act.get("startTime") or act.get("createTime", "")
        try:
            if datetime.fromisoformat(ts.replace("Z", "+00:00")) >= cutoff:
                out.append(act)
        except (ValueError, AttributeError):
            continue
    return out


def _build_requests(activities: list[dict]) -> list[dict]:
    requests = []
    for act in activities:
        summary = {
            "id":               act.get("id"),
            "asset":            act.get("assetName"),
            "type":             act.get("assetType"),
            "state":            act.get("state"),
            "startTime":        act.get("startTime"),
            "duration_s":       act.get("duration"),
            "bytesTransferred": act.get("bytesTransferred"),
            "errorCode":        act.get("errorCode"),
            "errorMessage":     (act.get("error") or {}).get("message", ""),
        }
        requests.append({
            "custom_id": str(act.get("id", f"act-{len(requests)}")),
            "params": {
                "model":      _MODEL,
                "max_tokens": 256,
                "system": (
                    "You are a backup anomaly classifier. Classify each backup activity as:\n"
                    "- NORMAL: completed successfully within expected parameters\n"
                    "- ANOMALOUS: failed, or succeeded with unexpected errors/warnings\n"
                    "- DEGRADING: succeeded but shows declining performance\n\n"
                    "Respond with JSON only: "
                    '{"classification":"NORMAL|ANOMALOUS|DEGRADING",'
                    '"reason":"<one sentence>","risk_score":0-10}'
                ),
                "messages": [{"role": "user", "content": json.dumps(summary)}],
            },
        })
    return requests


def _submit(client: anthropic.Anthropic, requests: list[dict]) -> str:
    batch = client.messages.batches.create(requests=requests)
    print(f"[anomaly-report] Batch submitted: {batch.id}  ({len(requests)} requests)")
    return batch.id


def _poll(client: anthropic.Anthropic, batch_id: str, wait: bool) -> str | None:
    start = time.time()
    while True:
        batch  = client.messages.batches.retrieve(batch_id)
        status = batch.processing_status
        c      = batch.request_counts
        print(
            f"[anomaly-report] {batch_id}  status={status}  "
            f"succeeded={c.succeeded}  errored={c.errored}  processing={c.processing}",
            file=sys.stderr,
        )
        if status == "ended":
            return batch_id
        if not wait:
            print(f"[anomaly-report] Still processing. Re-run: --batch-id {batch_id} --wait")
            return None
        if time.time() - start > _MAX_WAIT:
            print("[anomaly-report] Timeout.", file=sys.stderr)
            return None
        time.sleep(_POLL_INTERVAL)


def _collect(client: anthropic.Anthropic, batch_id: str) -> list[dict]:
    results = []
    for r in client.messages.batches.results(batch_id):
        if r.result.type == "succeeded":
            raw = next(
                (b.text for b in r.result.message.content if b.type == "text"), ""
            )
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = {"classification": "UNKNOWN", "reason": raw, "risk_score": 0}
        else:
            parsed = {"classification": "ERROR", "reason": str(r.result), "risk_score": 0}
        results.append({"id": r.custom_id, **parsed})
    return results


def _print_report(results: list[dict]) -> None:
    buckets: dict[str, list] = {}
    for r in results:
        buckets.setdefault(r["classification"], []).append(r)

    total = len(results)
    print("\n" + "═" * 72)
    print("  BACKUP ANOMALY REPORT")
    print("═" * 72)
    for cls in ["ANOMALOUS", "DEGRADING", "NORMAL", "ERROR", "UNKNOWN"]:
        items = buckets.get(cls, [])
        if not items:
            continue
        pct = len(items) / total * 100
        print(f"\n{cls}: {len(items)} ({pct:.1f}%)")
        for item in sorted(items, key=lambda x: -x.get("risk_score", 0))[:5]:
            print(f"  • [{item.get('risk_score', 0):2d}/10] {item['id']}  — {item['reason']}")
    health = len(buckets.get("NORMAL", [])) / total * 100 if total else 0
    print(f"\nOverall health score: {health:.1f}%")
    print("═" * 72)


def run(days: int = 30, wait: bool = False, batch_id: str | None = None) -> None:
    client = anthropic.Anthropic()
    if not batch_id:
        activities = _fetch_activities(days)
        if not activities:
            print("[anomaly-report] No activities found. Check PPDM credentials.")
            return
        batch_id = _submit(client, _build_requests(activities))

    completed = _poll(client, batch_id, wait=wait)
    if completed:
        _print_report(_collect(client, completed))


def main() -> None:
    p = argparse.ArgumentParser(description="Batch anomaly detection for backup jobs")
    p.add_argument("--days",     type=int, default=30)
    p.add_argument("--wait",     action="store_true")
    p.add_argument("--batch-id", dest="batch_id", default=None)
    args = p.parse_args()
    run(days=args.days, wait=args.wait, batch_id=args.batch_id)


if __name__ == "__main__":
    main()
