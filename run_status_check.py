#!/usr/bin/env python3
"""
Check that GET /status/<content_id> tells the truth.

    python app.py                    # in one terminal
    python run_status_check.py       # in another

For each text in the "plain writers" and "label coverage" scenarios it:

  1. submits it,
  2. appeals it 0, 1 or 2 times (rotating),
  3. asks /status and checks the answer against what actually happened:
     - status is `decided` with no appeal, `under_review` after any appeal
     - appeal_count equals the number of appeals sent
     - guess, label, confidence and both scores match the /submit response

Then it checks the refusals: an unknown id gets a 404, an overlong id a 400,
and both leave a `rejected` entry in the audit log.

Writes results/status_check_<timestamp>.md.
"""

import argparse
import datetime as dt
import json
import sys
import uuid

import config
from scenarios import SCENARIOS

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass

DEFAULT_URL = f"http://{config.HOST}:{config.PORT}"
SCENARIO_NAMES = ("plain writers", "label coverage")
DECISION_FIELDS = (("guess", "guess"), ("label", "label"), ("confidence", "confidence"),
                   ("model_score", "model_score"), ("style_score", "style_score"))


def check_submission(requests, url, timeout, text, creator_id, n_appeals):
    """Submit, appeal n times, read /status, and list every mismatch."""
    submitted = requests.post(f"{url}/submit", json={"text": text, "creator_id": creator_id},
                              timeout=timeout).json()
    content_id = submitted["content_id"]

    for i in range(n_appeals):
        requests.post(f"{url}/appeal", json={"content_id": content_id,
                                             "reasoning": f"status check appeal {i + 1}"},
                      timeout=timeout).raise_for_status()

    response = requests.get(f"{url}/status/{content_id}", timeout=timeout)
    body = response.json()

    expected_status = "under_review" if n_appeals else "decided"
    problems = []
    if response.status_code != 200:
        problems.append(f"HTTP {response.status_code}")
    if body.get("status") != expected_status:
        problems.append(f"status {body.get('status')!r}, expected {expected_status!r}")
    if body.get("appeal_count") != n_appeals:
        problems.append(f"appeal_count {body.get('appeal_count')}, expected {n_appeals}")
    decision = body.get("decision") or {}
    for status_key, submit_key in DECISION_FIELDS:
        if decision.get(status_key) != submitted.get(submit_key):
            problems.append(f"{status_key} {decision.get(status_key)!r} != submit {submitted.get(submit_key)!r}")

    return {"content_id": content_id, "appeals_sent": n_appeals, "expected": expected_status,
            "status": body.get("status"), "appeal_count": body.get("appeal_count"),
            "guess": decision.get("guess"), "problems": problems, "response": body}


def check_refusal(requests, url, timeout, content_id, expected_code, expected_error):
    before = requests.get(f"{url}/log", timeout=timeout).json()["count"]
    response = requests.get(f"{url}/status/{content_id}", timeout=timeout)
    after = requests.get(f"{url}/log", timeout=timeout).json()

    problems = []
    if response.status_code != expected_code:
        problems.append(f"HTTP {response.status_code}, expected {expected_code}")
    if response.json().get("error") != expected_error:
        problems.append(f"error {response.json().get('error')!r}, expected {expected_error!r}")
    last = after["entries"][-1] if after["entries"] else {}
    if after["count"] != before + 1 or last.get("reason") != expected_error:
        problems.append("no matching `rejected` entry in the audit log")

    return {"sent": content_id if len(content_id) < 50 else f"{content_id[:20]}… ({len(content_id)} chars)",
            "http": response.status_code, "error": response.json().get("error"),
            "problems": problems}


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--timeout", type=float, default=90.0)
    args = parser.parse_args()

    import requests

    try:
        requests.get(f"{args.url}/health", timeout=5)
    except requests.ConnectionError:
        sys.exit(f"Nothing answering at {args.url}. Start it with `python app.py` first.")

    texts = [t for s in SCENARIOS if s["name"] in SCENARIO_NAMES for t in s.get("texts", [])]
    rows = []
    for i, text in enumerate(texts):
        n_appeals = i % 3  # 0, 1, 2, 0, 1, 2, ...
        row = check_submission(requests, args.url, args.timeout, text, f"status_check_{i + 1}", n_appeals)
        rows.append(row)
        print(f"  {i + 1:>2}. appeals={n_appeals} status={row['status']:<13} "
              f"{'PASS' if not row['problems'] else 'FAIL: ' + '; '.join(row['problems'])}")

    refusals = [
        check_refusal(requests, args.url, args.timeout, str(uuid.uuid4()), 404, "unknown_content_id"),
        check_refusal(requests, args.url, args.timeout, "x" * 200, 400, "invalid_content_id"),
    ]
    for r in refusals:
        print(f"  refusal {r['sent']}: HTTP {r['http']} "
              f"{'PASS' if not r['problems'] else 'FAIL: ' + '; '.join(r['problems'])}")

    passed = sum(not r["problems"] for r in rows)
    refusals_passed = sum(not r["problems"] for r in refusals)
    print(f"\n{passed}/{len(rows)} submissions report the right status; "
          f"{refusals_passed}/{len(refusals)} refusals correct.")
    write_report(rows, refusals, passed, refusals_passed)


def write_report(rows, refusals, passed, refusals_passed):
    config.RESULTS_DIR.mkdir(exist_ok=True)
    now = dt.datetime.now()
    path = config.RESULTS_DIR / f"status_check_{now.strftime('%Y-%m-%d_%H%M')}.md"

    appealed = [r for r in rows if r["appeals_sent"]]
    lines = [
        "# /status check",
        "",
        "- Produced by: `run_status_check.py::main`",
        "- Endpoint: `app.py::status`",
        f"- {now.strftime('%Y-%m-%d %H:%M')}",
        "",
        f"- **{passed}/{len(rows)}** submissions: `/status` matched what happened",
        f"- **{sum(not r['problems'] for r in appealed)}/{len(appealed)}** appealed submissions report `under_review`",
        f"- **{refusals_passed}/{len(refusals)}** bad ids refused and logged",
        "",
        "| # | Appeals sent | Expected | Got | appeal_count | Guess | Result |",
        "|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows, 1):
        result = "PASS" if not r["problems"] else "FAIL: " + "; ".join(r["problems"])
        lines.append(f"| {i} | {r['appeals_sent']} | {r['expected']} | {r['status']} | "
                     f"{r['appeal_count']} | {r['guess']} | {result} |")

    lines += ["", "| Bad id sent | HTTP | error | Result |", "|---|---|---|---|"]
    for r in refusals:
        result = "PASS" if not r["problems"] else "FAIL: " + "; ".join(r["problems"])
        lines.append(f"| `{r['sent']}` | {r['http']} | {r['error']} | {result} |")

    example = next((r for r in rows if r["appeals_sent"] == 2), rows[0] if rows else None)
    if example:
        lines += ["", "## Example response", "", "```json",
                  json.dumps(example["response"], indent=2), "```", ""]

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {path.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()
