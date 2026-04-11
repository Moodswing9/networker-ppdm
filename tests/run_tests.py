#!/usr/bin/env python3
"""
networker-ppdm skill test runner
─────────────────────────────────
Injects SKILL.md as a system prompt, sends each test prompt to Claude,
and validates the response against assertions defined in test_cases.yaml.

Usage:
    python tests/run_tests.py                          # run all tests
    python tests/run_tests.py --category "Kubernetes" # run one category
    python tests/run_tests.py --id k8s_policy         # run one test by ID
    python tests/run_tests.py --fail-fast             # stop on first failure
    python tests/run_tests.py --verbose               # print full responses
    python tests/run_tests.py --output results.json   # save JSON report

Requirements:
    pip install anthropic pyyaml

Environment:
    ANTHROPIC_API_KEY — required
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import anthropic
import yaml

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
SKILL_FILE = ROOT / "SKILL.md"
TESTS_FILE = Path(__file__).parent / "test_cases.yaml"

# ── Config ─────────────────────────────────────────────────────────────────
MODEL = "claude-haiku-4-5-20251001"   # fast + cheap for test validation
MAX_TOKENS = 1024
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5   # seconds between retries on rate limit

# ── ANSI colours ───────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"
TICK   = f"{GREEN}✓{RESET}"
CROSS  = f"{RED}✗{RESET}"
SKIP   = f"{YELLOW}○{RESET}"


def load_skill() -> str:
    if not SKILL_FILE.exists():
        sys.exit(f"ERROR: SKILL.md not found at {SKILL_FILE}")
    return SKILL_FILE.read_text(encoding="utf-8")


def load_tests() -> list[dict]:
    if not TESTS_FILE.exists():
        sys.exit(f"ERROR: test_cases.yaml not found at {TESTS_FILE}")
    with open(TESTS_FILE, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("tests", [])


def build_system_prompt(skill_content: str) -> str:
    return f"""You are an expert assistant with deep knowledge of Dell EMC NetWorker and PowerProtect Data Manager (PPDM). The following is your knowledge base — use it to answer questions accurately and completely.

{skill_content}

When answering questions:
- Be specific and include exact API endpoints, CLI commands, and code examples from the knowledge base
- Include relevant port numbers, authentication methods, and request bodies
- Do not say "I don't know" — use the knowledge base to provide a complete answer
"""


def ask_claude(client: anthropic.Anthropic, system: str, prompt: str) -> str:
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except anthropic.RateLimitError:
            if attempt < RETRY_ATTEMPTS:
                print(f"    {YELLOW}Rate limited — waiting {RETRY_DELAY}s (attempt {attempt}/{RETRY_ATTEMPTS}){RESET}")
                time.sleep(RETRY_DELAY)
            else:
                raise
        except anthropic.APIError as e:
            if attempt < RETRY_ATTEMPTS:
                print(f"    {YELLOW}API error: {e} — retrying...{RESET}")
                time.sleep(2)
            else:
                raise


def run_test(client: anthropic.Anthropic, system: str, test: dict, verbose: bool) -> dict:
    test_id       = test["id"]
    category      = test.get("category", "Uncategorized")
    section       = test.get("section", "")
    prompt        = test["prompt"]
    assertions    = test.get("assertions", [])
    neg_assertions = test.get("negative_assertions", [
        "I don't know",
        "I cannot answer",
        "not in my knowledge",
        "I'm not sure",
    ])

    try:
        response = ask_claude(client, system, prompt)
    except Exception as e:
        return {
            "id": test_id, "category": category, "section": section,
            "passed": False, "error": str(e),
            "failed_assertions": [], "failed_neg_assertions": [],
            "response": "",
        }

    response_lower = response.lower()

    failed      = [a for a in assertions    if a.lower() not in response_lower]
    failed_neg  = [a for a in neg_assertions if a.lower() in response_lower]

    passed = (len(failed) == 0 and len(failed_neg) == 0)

    result = {
        "id": test_id,
        "category": category,
        "section": section,
        "prompt": prompt,
        "passed": passed,
        "failed_assertions": failed,
        "failed_neg_assertions": failed_neg,
        "response": response,
        "error": None,
    }

    # Print result line
    status = TICK if passed else CROSS
    print(f"  {status} [{test_id}] {prompt[:70]}{'...' if len(prompt) > 70 else ''}")

    if not passed:
        if failed:
            print(f"      {RED}Missing assertions:{RESET} {failed}")
        if failed_neg:
            print(f"      {RED}Unwanted phrases found:{RESET} {failed_neg}")

    if verbose:
        print(f"      {CYAN}Response:{RESET}")
        for line in response.strip().split("\n"):
            print(f"        {line}")
        print()

    return result


def print_summary(results: list[dict], elapsed: float):
    total   = len(results)
    passed  = sum(1 for r in results if r["passed"])
    failed  = total - passed
    pct     = (passed / total * 100) if total else 0

    print()
    print(f"{BOLD}{'─' * 60}{RESET}")
    print(f"{BOLD}RESULTS{RESET}")
    print(f"{'─' * 60}")
    print(f"  Total  : {total}")
    print(f"  {GREEN}Passed : {passed}{RESET}")
    print(f"  {RED if failed else GREEN}Failed : {failed}{RESET}")
    print(f"  Score  : {pct:.1f}%")
    print(f"  Time   : {elapsed:.1f}s")
    print(f"{'─' * 60}")

    if failed:
        print(f"\n{BOLD}{RED}FAILED TESTS:{RESET}")
        for r in results:
            if not r["passed"]:
                print(f"  {CROSS} {r['id']} ({r['category']})")
                if r.get("error"):
                    print(f"      Error: {r['error']}")
                if r["failed_assertions"]:
                    print(f"      Missing: {r['failed_assertions']}")

    # Per-category breakdown
    categories: dict[str, dict] = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"pass": 0, "fail": 0}
        if r["passed"]:
            categories[cat]["pass"] += 1
        else:
            categories[cat]["fail"] += 1

    print(f"\n{BOLD}CATEGORY BREAKDOWN:{RESET}")
    for cat, counts in sorted(categories.items()):
        total_cat = counts["pass"] + counts["fail"]
        icon = TICK if counts["fail"] == 0 else CROSS
        print(f"  {icon} {cat:<35} {counts['pass']}/{total_cat}")

    print()
    if pct == 100.0:
        print(f"{BOLD}{GREEN}All tests passed!{RESET}")
    elif pct >= 80:
        print(f"{BOLD}{YELLOW}Most tests passed ({pct:.1f}%). Review failures above.{RESET}")
    else:
        print(f"{BOLD}{RED}Significant failures ({failed} tests). Skill may need updates.{RESET}")


def save_report(results: list[dict], output_path: str, elapsed: float):
    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "model": MODEL,
        "total": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "failed": sum(1 for r in results if not r["passed"]),
        "elapsed_seconds": round(elapsed, 1),
        "results": results,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="networker-ppdm skill test runner"
    )
    parser.add_argument("--category", help="Run only tests matching this category (case-insensitive)")
    parser.add_argument("--id",       help="Run only the test with this ID")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first failure")
    parser.add_argument("--verbose",  action="store_true", help="Print full Claude responses")
    parser.add_argument("--output",   help="Save JSON report to this file path")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ERROR: ANTHROPIC_API_KEY environment variable not set.")

    client = anthropic.Anthropic(api_key=api_key)

    print(f"\n{BOLD}networker-ppdm skill test runner{RESET}")
    print(f"Model  : {MODEL}")
    print(f"Skill  : {SKILL_FILE}")
    print(f"Tests  : {TESTS_FILE}")

    skill_content = load_skill()
    all_tests     = load_tests()
    system        = build_system_prompt(skill_content)

    # ── Filter ──────────────────────────────────────────────────────────────
    tests = all_tests
    if args.id:
        tests = [t for t in tests if t["id"] == args.id]
        if not tests:
            sys.exit(f"ERROR: No test found with id '{args.id}'")
    elif args.category:
        tests = [t for t in tests if args.category.lower() in t.get("category", "").lower()]
        if not tests:
            sys.exit(f"ERROR: No tests found in category '{args.category}'")

    print(f"Running: {len(tests)} test(s)\n")

    # ── Group by category for display ───────────────────────────────────────
    current_category = None
    results = []
    start_time = time.time()

    for test in tests:
        cat = test.get("category", "Uncategorized")
        if cat != current_category:
            current_category = cat
            print(f"\n{BOLD}{CYAN}{cat}{RESET}")

        result = run_test(client, system, test, args.verbose)
        results.append(result)

        if args.fail_fast and not result["passed"]:
            print(f"\n{RED}Stopping on first failure (--fail-fast){RESET}")
            break

    elapsed = time.time() - start_time
    print_summary(results, elapsed)

    if args.output:
        save_report(results, args.output, elapsed)

    # Exit 1 if any failures
    sys.exit(0 if all(r["passed"] for r in results) else 1)


if __name__ == "__main__":
    main()
