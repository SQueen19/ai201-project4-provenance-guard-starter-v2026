#!/usr/bin/env python3
"""
Run the five extension criteria (6-10 in criteria.md), three separate trials.

    python run_extension_eval.py            # stop any running `python app.py` first

Each trial starts its OWN fresh copy of the service, runs every check, and stops
it again. A fresh start per trial is what criterion 9 needs (the cold start has
to be real), and it resets the in-memory rate limiter between trials. The
server is started with AI201_FAULT_INJECTION=1 so criterion 8 can crash it on
purpose; with that variable unset the switch does nothing.

Order inside a trial, and why:

    C9  cost      1 cold + 10 warm /submit — first, while the model is unloaded
    C6  /status   14 submissions, appealed 0/1/2 times, checked against /submit
    C7  bad ids   4 bad /status requests, then 20 repeats of each refused kind
                  so the latency target has a distribution, not one number
    C8  run log   a 20-request mixed batch: good, bad input, 429, missing route,
                  appeal, status, ping, and one injected crash
    C10 privacy   scans logs/runs.jsonl for the texts sent in this trial

Logs are read straight from disk (audit.py / runlog.py), not over HTTP, so the
evaluator's own reads never add records to the counts it's checking.

Writes, per trial:   results/ext_eval_<stamp>_trial<N>.md   (the real output)
and once:            results/ext_run_log_<stamp>.md         (the run log table)
"""

import argparse
import datetime as dt
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
import uuid

import audit
import config
import runlog
from measure_cost import TEXT as COST_TEXT
from run_status_check import check_submission, SCENARIO_NAMES
from scenarios import SCENARIOS

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass

URL = f"http://{config.HOST}:{config.PORT}"
TIMEOUT = 120
STATUS_TEXTS = [t for s in SCENARIOS if s["name"] in SCENARIO_NAMES for t in s.get("texts", [])]
LATENCY_REPEATS = 20

import requests  # noqa: E402  (after the stream fix so import errors print cleanly)


# ── helpers ──────────────────────────────────────────────────────────────────

def start_server():
    try:
        requests.get(f"{URL}/health", timeout=2)
        sys.exit(f"Something is already answering at {URL}. Stop your `python app.py` first — "
                 "each trial needs its own fresh server.")
    except requests.ConnectionError:
        pass
    env = {**os.environ, "AI201_FAULT_INJECTION": "1", "AI201_DEBUG": "0", "PYTHONIOENCODING": "utf-8"}
    log = tempfile.NamedTemporaryFile(prefix="ext_eval_server_", suffix=".log", delete=False)
    proc = subprocess.Popen([sys.executable, "app.py"], cwd=config.ROOT, env=env,
                            stdout=log, stderr=subprocess.STDOUT)
    for _ in range(120):
        try:
            requests.get(f"{URL}/health", timeout=2)
            return proc, log.name
        except requests.ConnectionError:
            if proc.poll() is not None:
                sys.exit(f"The server exited on start. Its output is in {log.name}")
            time.sleep(0.5)
    proc.terminate()
    sys.exit(f"The server never answered. Its output is in {log.name}")


def stop_server(proc):
    proc.terminate()
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()


def runs_by_id():
    return {r.get("run_id"): r for r in runlog.read_runs()}


def rejected_count():
    return sum(1 for e in audit.read_entries() if e.get("status") == "rejected")


def timed(method, path, **kw):
    t0 = time.perf_counter()
    r = requests.request(method, f"{URL}{path}", timeout=TIMEOUT, **kw)
    return r, round((time.perf_counter() - t0) * 1000, 1)


def pct(values, p):
    s = sorted(values)
    k = max(0, min(len(s) - 1, round(p / 100 * (len(s) - 1))))
    return s[k]


def outcome_for(status):
    return "error" if status >= 500 else "refused" if status >= 400 else "ok"


# ── criterion 9: cost ────────────────────────────────────────────────────────

def c9_cost(trial, stamp):
    sent = []
    for i in range(11):  # 0 = cold start
        r, client_ms = timed("POST", "/submit",
                             json={"text": COST_TEXT, "creator_id": f"ext{trial}_{stamp}_cost{i}"})
        sent.append((r.status_code, r.headers.get("X-Run-Id"), client_ms))
    recs = runs_by_id()
    rows = []
    for status, run_id, client_ms in sent:
        rec = recs.get(run_id, {})
        rows.append({"http": status, "run_id": run_id, "client_ms": client_ms,
                     "duration_ms": rec.get("duration_ms"), "cpu_ms": rec.get("cpu_ms"),
                     "detector_ms": rec.get("detector_ms"), "style_ms": rec.get("style_ms"),
                     "model_was_loaded": rec.get("model_was_loaded")})
    warm = rows[1:]
    mean_wall = statistics.mean(r["duration_ms"] for r in warm)
    mean_gpt2 = statistics.mean(r["detector_ms"] for r in warm)
    share = mean_gpt2 / mean_wall
    cold_count = sum(r["model_was_loaded"] is False for r in rows)
    problems = []
    if not mean_wall < 450:
        problems.append(f"mean wall {mean_wall:.1f} ms not < 450")
    if not 295.8 <= mean_wall <= 400.2:
        problems.append(f"mean wall {mean_wall:.1f} ms outside 296–400")
    if share < 0.95:
        problems.append(f"gpt2 share {share:.1%} < 95%")
    if cold_count != 1:
        problems.append(f"{cold_count} of 11 runs had model_was_loaded=false, expected 1")
    if any(r["http"] != 200 for r in rows):
        problems.append("a cost run did not return 200")
    return {
        "pass": not problems, "problems": problems,
        "mean_wall_ms": round(mean_wall, 1), "sd_wall_ms": round(statistics.stdev(r["duration_ms"] for r in warm), 1),
        "p50_wall_ms": pct([r["duration_ms"] for r in warm], 50),
        "max_wall_ms": max(r["duration_ms"] for r in warm),
        "mean_cpu_ms": round(statistics.mean(r["cpu_ms"] for r in warm), 1),
        "mean_gpt2_ms": round(mean_gpt2, 1), "gpt2_share": round(share, 4),
        "cold_ms": rows[0]["duration_ms"], "cold_starts": cold_count,
        "cell": f"{mean_wall:.0f} ms ±{statistics.stdev(r['duration_ms'] for r in warm):.0f}, gpt2 {share:.1%}, "
                f"cold starts {cold_count}/11",
        "rows": rows,
    }


# ── criterion 6: /status truthfulness ────────────────────────────────────────

def c6_status(trial, stamp):
    rows = []
    for i, text in enumerate(STATUS_TEXTS):
        rows.append(check_submission(requests, URL, TIMEOUT, text, f"ext{trial}_{stamp}_status{i}", i % 3))
    ok = sum(not r["problems"] for r in rows)
    status_ok = sum(r["status"] == r["expected"] for r in rows)
    count_ok = sum(r["appeal_count"] == r["appeals_sent"] for r in rows)
    return {
        "pass": ok == len(rows), "rows": [{k: v for k, v in r.items() if k != "response"} for r in rows],
        "status_ok": status_ok, "count_ok": count_ok, "all_ok": ok, "n": len(rows),
        "cell": f"{ok}/{len(rows)} (status {status_ok}/{len(rows)}, count {count_ok}/{len(rows)})",
        "example": rows[2]["response"] if len(rows) > 2 else None,
        "ids": [r["content_id"] for r in rows],
    }


# ── criterion 7: bad /status requests ────────────────────────────────────────

def c7_bad_ids(real_id):
    typo = real_id[:-1] + ("0" if real_id[-1] != "0" else "1")
    refused_cases = [
        ("unknown uuid", lambda: str(uuid.uuid4()), 404, "unknown_content_id"),
        ("one char changed", lambda: typo, 404, "unknown_content_id"),
        ("200-char id", lambda: "x" * 200, 400, "invalid_content_id"),
    ]
    first = []
    timings = {name: {"client": [], "server": []} for name, *_ in refused_cases}
    problems = []
    n500 = 0
    for name, make_id, code, err in refused_cases:
        for rep in range(LATENCY_REPEATS):
            before = rejected_count()
            r, client_ms = timed("GET", f"/status/{make_id()}")
            rec = runs_by_id().get(r.headers.get("X-Run-Id"), {})
            audit_delta = rejected_count() - before
            body = r.json() if r.headers.get("Content-Type", "").startswith("application/json") else {}
            n500 += r.status_code >= 500
            ok = (r.status_code == code and body.get("error") == err and audit_delta == 1
                  and rec.get("outcome") == "refused")
            if not ok:
                problems.append(f"{name} rep {rep + 1}: HTTP {r.status_code} {body.get('error')}, "
                                f"audit +{audit_delta}, run outcome {rec.get('outcome')}")
            timings[name]["client"].append(client_ms)
            timings[name]["server"].append(rec.get("duration_ms"))
            if rep == 0:
                first.append({"case": name, "http": r.status_code, "error": body.get("error"),
                              "audit_rejected_added": audit_delta, "run_outcome": rec.get("outcome"),
                              "client_ms": client_ms, "pass": ok})

    # Spaces around a real id: must be accepted, same answer as the clean id.
    clean, _ = timed("GET", f"/status/{real_id}")
    before = rejected_count()
    spaced, client_ms = timed("GET", f"/status/%20{real_id}%20")
    rec = runs_by_id().get(spaced.headers.get("X-Run-Id"), {})
    audit_delta = rejected_count() - before
    same = spaced.status_code == 200 and spaced.json() == clean.json()
    ok = same and audit_delta == 0 and rec.get("outcome") == "ok"
    if not ok:
        problems.append(f"spaces: HTTP {spaced.status_code}, same answer {same}, audit +{audit_delta}")
    first.append({"case": "spaces around real id", "http": spaced.status_code, "error": None,
                  "audit_rejected_added": audit_delta, "run_outcome": rec.get("outcome"),
                  "client_ms": client_ms, "pass": ok})

    all_client = [t for v in timings.values() for t in v["client"]]
    all_server = [t for v in timings.values() for t in v["server"] if t is not None]
    over = sum(t >= 100 for t in all_client)
    if over:
        problems.append(f"{over} of {len(all_client)} refused requests took ≥ 100 ms")
    if n500:
        problems.append(f"{n500} responses were 5xx")
    return {
        "pass": not problems, "problems": problems, "cases": first,
        "audit_entries": len(audit.read_entries()),
        "latency": {
            "n": len(all_client),
            "client_p50": pct(all_client, 50), "client_p95": pct(all_client, 95), "client_max": max(all_client),
            "server_p50": pct(all_server, 50), "server_p95": pct(all_server, 95), "server_max": max(all_server),
            "per_case": {k: {"client_p50": pct(v["client"], 50), "client_max": max(v["client"])}
                         for k, v in timings.items()},
        },
        "cell": f"{sum(c['pass'] for c in first)}/4 cases, {n500} × 5xx, "
                f"p95 {pct(all_client, 95):.0f} ms / max {max(all_client):.0f} ms (n={len(all_client)})",
    }


# ── criterion 8: one record per request ──────────────────────────────────────

def c8_runlog(trial, stamp, status_ids):
    a = f"ext{trial}_{stamp}_batchA"
    b = f"ext{trial}_{stamp}_batchB"
    plan = (
        [("good submit", "POST", "/submit", {"json": {"text": COST_TEXT, "creator_id": a}}, 200)] * 10
        + [("rate limited", "POST", "/submit", {"json": {"text": COST_TEXT, "creator_id": a}}, 429),
           ("empty text", "POST", "/submit", {"json": {"text": "", "creator_id": b}}, 400),
           ("no creator_id", "POST", "/submit", {"json": {"text": COST_TEXT}}, 400),
           ("too short", "POST", "/submit", {"json": {"text": "Only a few words here.", "creator_id": b}}, 400),
           ("status real", "GET", f"/status/{status_ids[0]}", {}, 200),
           ("status unknown", "GET", f"/status/{uuid.uuid4()}", {}, 404),
           ("appeal", "POST", "/appeal", {"json": {"content_id": status_ids[1], "reasoning": "batch appeal"}}, 200),
           ("missing route", "GET", "/nope", {}, 404),
           ("ping", "POST", "/ping", {"json": {"message": "hello"}}, 200),
           ("injected crash", "POST", "/submit",
            {"json": {"text": COST_TEXT, "creator_id": f"ext{trial}_{stamp}_crash"},
             "headers": {"X-Inject-Fault": "style"}}, 500)]
    )
    before = len(runlog.read_runs())
    sent = []
    for name, method, path, kw, expect in plan:
        r, client_ms = timed(method, path, **kw)
        sent.append((name, expect, r))
    after_runs = runlog.read_runs()
    added = len(after_runs) - before
    recs = {x.get("run_id"): x for x in after_runs[before:]}

    rows, problems = [], []
    for name, expect, r in sent:
        rid = r.headers.get("X-Run-Id")
        rec = recs.get(rid)
        is_json = r.headers.get("Content-Type", "").startswith("application/json")
        row = {"request": name, "expected_http": expect, "http": r.status_code, "run_id": rid,
               "record_found": rec is not None,
               "outcome": rec.get("outcome") if rec else None,
               "outcome_ok": bool(rec) and rec.get("outcome") == outcome_for(r.status_code),
               "json_response": is_json}
        if name == "injected crash":
            err = (rec or {}).get("error") or {}
            row["error"] = err
            if not (err.get("type") and err.get("where")):
                problems.append("crash record missing error.type / error.where")
        if not row["record_found"]:
            problems.append(f"{name}: no record for run_id {rid}")
        elif not row["outcome_ok"]:
            problems.append(f"{name}: outcome {row['outcome']} for HTTP {r.status_code}")
        if not is_json:
            problems.append(f"{name}: HTTP {r.status_code} response is {r.headers.get('Content-Type')}, not JSON")
        if r.status_code != expect:
            problems.append(f"{name}: HTTP {r.status_code}, expected {expect}")
        rows.append(row)
    if added != len(plan):
        problems.append(f"run log gained {added} records for {len(plan)} requests")
    matched = sum(r["record_found"] and r["outcome_ok"] for r in rows)
    non_json = sum(not r["json_response"] for r in rows)
    return {
        "pass": not problems, "problems": problems, "rows": rows, "records_added": added,
        "cell": f"{added} records / {len(plan)} requests, {matched}/{len(plan)} matched, "
                f"{non_json} non-JSON",
    }


# ── criterion 10: no writing in the run log ──────────────────────────────────

def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def c10_privacy(first_line):
    raw = config.RUN_LOG.read_text(encoding="utf-8")
    lines = raw.splitlines()
    texts = STATUS_TEXTS + [COST_TEXT]
    found = sum(1 for t in texts if t in raw or json.dumps(t, ensure_ascii=False)[1:-1] in raw)
    trial_lines = lines[first_line:]
    sizes = [len(line.encode("utf-8")) for line in trial_lines]
    longest_input = 0
    for line in trial_lines:
        rec = json.loads(line)
        for s in _strings(rec.get("input")):
            longest_input = max(longest_input, len(s))
    problems = []
    if found:
        problems.append(f"{found} of {len(texts)} submitted texts found in full")
    if longest_input > 60:
        problems.append(f"an input string is {longest_input} chars")
    if max(sizes) >= 3072:
        problems.append(f"largest record {max(sizes)} bytes")
    return {
        "pass": not problems, "problems": problems, "texts_checked": len(texts), "texts_found": found,
        "records_checked": len(trial_lines), "longest_input_string": longest_input,
        "largest_record_bytes": max(sizes), "mean_record_bytes": round(statistics.mean(sizes)),
        "cell": f"{found}/{len(texts)} texts found, longest input {longest_input} chars, "
                f"largest record {max(sizes):,} B",
    }


# ── a trial ──────────────────────────────────────────────────────────────────

def run_trial(trial, stamp):
    print(f"\n── Trial {trial} ──")
    first_line = len(config.RUN_LOG.read_text(encoding="utf-8").splitlines()) if config.RUN_LOG.exists() else 0
    proc, server_log = start_server()
    try:
        print("  C9 cost …", flush=True)
        c9 = c9_cost(trial, stamp)
        print(f"     {c9['cell']}  {'PASS' if c9['pass'] else 'FAIL'}")
        print("  C6 /status …", flush=True)
        c6 = c6_status(trial, stamp)
        print(f"     {c6['cell']}  {'PASS' if c6['pass'] else 'FAIL'}")
        print("  C7 bad ids …", flush=True)
        c7 = c7_bad_ids(c6["ids"][1])
        print(f"     {c7['cell']}  {'PASS' if c7['pass'] else 'FAIL'}")
        print("  C8 run log …", flush=True)
        c8 = c8_runlog(trial, stamp, c6["ids"])
        print(f"     {c8['cell']}  {'PASS' if c8['pass'] else 'FAIL'}")
    finally:
        stop_server(proc)
    print("  C10 privacy …", flush=True)
    c10 = c10_privacy(first_line)
    print(f"     {c10['cell']}  {'PASS' if c10['pass'] else 'FAIL'}")
    return {"trial": trial, "6": c6, "7": c7, "8": c8, "9": c9, "10": c10, "server_log": server_log}


CRITERIA = [
    ("6", "`/status` tells the truth",
     "14/14 status, count and decision fields match /submit"),
    ("7", "Bad `/status` refused, never crashes, logged",
     "4/4 cases right, 0 × 5xx, 1 audit + 1 run record each, every refusal < 100 ms"),
    ("8", "Every request leaves exactly one run record",
     "20 records for 20 requests, 20/20 run_id + outcome match, crash has error.type/where, 0 non-JSON"),
    ("9", "Cost repeats, model loads once",
     "mean warm wall < 450 ms and 296–400 ms, gpt2 ≥ 95%, exactly 1 cold start in 11"),
    ("10", "Run log never stores writing",
     "0 full texts, no input string > 60 chars, every record < 3 KB"),
]


def write_trial(result, stamp):
    path = config.RESULTS_DIR / f"ext_eval_{stamp}_trial{result['trial']}.md"
    lines = [f"# Extension eval — trial {result['trial']}", "",
             "- Produced by: `run_extension_eval.py::run_trial` against a freshly started `app.py`",
             f"- {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}", "",
             "| # | Criterion | Measured | Result |", "|---|---|---|---|"]
    for num, name, _ in CRITERIA:
        c = result[num]
        lines.append(f"| {num} | {name} | {c['cell']} | {'PASS' if c['pass'] else 'FAIL'} |")
    for num, name, _ in CRITERIA:
        c = result[num]
        lines += ["", f"## {num}. {name}", ""]
        if c.get("problems"):
            lines += ["**Problems:**", ""] + [f"- {p}" for p in c["problems"][:25]] + [""]
        detail = {k: v for k, v in c.items() if k not in ("cell", "pass", "problems")}
        lines += ["```json", json.dumps(detail, indent=2, ensure_ascii=False), "```"]
    config.RESULTS_DIR.mkdir(exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_run_log(results, stamp, trial_paths):
    path = config.RESULTS_DIR / f"ext_run_log_{stamp}.md"
    n = len(results)
    lines = ["# Run log — extension criteria (6–10)", "",
             "- Produced by: `run_extension_eval.py::main`",
             f"- {n} trials, each against its own fresh server · {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}",
             "- Raw output per trial: " + ", ".join(f"`{p.name}`" for p in trial_paths), "",
             f"| Criterion | Target | {' | '.join(f'Run {i}' for i in range(1, n + 1))} | Verdict |",
             f"|---|---|{'|'.join(['---'] * n)}|---|"]
    for num, name, target in CRITERIA:
        cells = [f"{r[num]['cell']} — **{'pass' if r[num]['pass'] else 'FAIL'}**" for r in results]
        verdict = "**Met** (all trials)" if all(r[num]["pass"] for r in results) else \
            f"**Missed** ({sum(not r[num]['pass'] for r in results)}/{n} trials failed)"
        lines.append(f"| {num}. {name} | {target} | {' | '.join(cells)} | {verdict} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--trials", type=int, default=3)
    args = parser.parse_args()

    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    results, paths = [], []
    for trial in range(1, args.trials + 1):
        result = run_trial(trial, stamp)
        results.append(result)
        paths.append(write_trial(result, stamp))
        print(f"  wrote {paths[-1].relative_to(config.ROOT)}")
    log_path = write_run_log(results, stamp, paths)
    print(f"\nRun log: {log_path.relative_to(config.ROOT)}")
    print(log_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
