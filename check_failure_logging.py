#!/usr/bin/env python3
"""
Check that failed requests leave a record in the run log.

    python check_failure_logging.py

No server needed: this drives the app in-process with Flask's test client, so
it can break things on purpose. It sends requests that fail in different ways
and checks each left a record in logs/runs.jsonl with the right outcome:

    bad JSON              -> 400 refused
    text too short        -> 400 refused
    unknown /status id    -> 404 refused
    route that isn't there -> 404 refused
    a crash inside /submit -> 500 error, with the exception type and where it
                              happened (stylometry.style_signal is swapped for
                              one that raises, for this one request only)

The crash request never touches gpt2's output — the signal it breaks runs
after the model — but the model still loads, so the first run takes a few
seconds.
"""

import sys

import app as service
import runlog
import stylometry

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass

LONG_TEXT = " ".join(["The committee met on Tuesday and talked about the budget for next year."] * 6)


def _broken_style_signal(text):
    raise ValueError("injected failure: style signal unavailable")


def main():
    client = service.app.test_client()
    cases = []

    def send(name, expect_status, expect_outcome, call):
        response = call()
        run_id = response.headers.get("X-Run-Id")
        record = next((r for r in reversed(runlog.read_runs(limit=50)) if r.get("run_id") == run_id), None)
        problems = []
        if response.status_code != expect_status:
            problems.append(f"HTTP {response.status_code}, expected {expect_status}")
        if record is None:
            problems.append("no run-log record")
        elif record.get("outcome") != expect_outcome:
            problems.append(f"outcome {record.get('outcome')!r}, expected {expect_outcome!r}")
        cases.append((name, response.status_code, record, problems))
        print(f"  {name:<24} HTTP {response.status_code}  "
              f"{'PASS' if not problems else 'FAIL: ' + '; '.join(problems)}")

    send("bad JSON", 400, "refused",
         lambda: client.post("/submit", data="not json", content_type="application/json"))
    send("text too short", 400, "refused",
         lambda: client.post("/submit", json={"text": "too short", "creator_id": "failcheck"}))
    send("unknown /status id", 404, "refused",
         lambda: client.get("/status/00000000-0000-0000-0000-000000000000"))
    send("route that isn't there", 404, "refused",
         lambda: client.get("/nope"))

    original = stylometry.style_signal
    stylometry.style_signal = _broken_style_signal
    try:
        send("crash inside /submit", 500, "error",
             lambda: client.post("/submit", json={"text": LONG_TEXT, "creator_id": "failcheck_crash"}))
    finally:
        stylometry.style_signal = original

    crash = cases[-1][2] or {}
    if crash.get("error"):
        print(f"\n  crash record error field: {crash['error']}")

    failed = sum(bool(c[3]) for c in cases)
    print(f"\n{len(cases) - failed}/{len(cases)} failures left the right record.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
