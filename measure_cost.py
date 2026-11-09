#!/usr/bin/env python3
"""
Measure what one /submit costs.

    python app.py              # in one terminal (a fresh start, so the cold run is real)
    python measure_cost.py     # in another

There's no API bill here — the model runs locally — so the real cost of a run
is compute: seconds of wall-clock time and seconds of CPU. This sends the same
text to /submit ten times and reads each run's own record back from the run
log (`GET /runs`), so every number comes from the server's timers, not from a
guess:

    duration_ms   wall-clock time inside the service, request in to response out
    cpu_ms        CPU time the service process used for that request, summed
                  over all its threads (torch uses several, so this can exceed
                  duration_ms)
    detector_ms   time spent in signal one (gpt2)
    style_ms      time spent in signal two (stylometry)

It also times each request from the client side (round trip, including HTTP).

If the model isn't loaded yet, the first request pays to load it. That run is
reported separately as the cold start and kept out of the average — it happens
once per server start, not once per submission.

Writes results/cost_<timestamp>.md.
"""

import argparse
import datetime as dt
import os
import platform
import statistics
import sys
import time

import config

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass

DEFAULT_URL = f"http://{config.HOST}:{config.PORT}"

# One ordinary submission (~150 words), sent every time so the runs differ only
# in timing, not in input.
TEXT = (
    "I started walking to work last spring because the bus kept running late, "
    "and I did not expect it to change much. At first it was just a way to save "
    "time and a little money. Then I began to notice things. There is a bakery "
    "on the corner that opens at six, and by seven the line is out the door. An "
    "old man feeds the pigeons on the same bench every morning and talks to them "
    "like they owe him rent. Near the bridge the light comes off the river in a "
    "way I still can't describe properly, even after a year of trying. Some days "
    "it rains and I arrive soaked and annoyed, and I wonder why I bother. But on "
    "the days I take the bus now, I feel like I've missed something. I leave the "
    "house earlier than I need to. I think that is the real change: I used to "
    "count the minutes, and now I mostly just walk."
)
METRICS = ("client_ms", "duration_ms", "cpu_ms", "detector_ms", "style_ms")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()

    import requests

    try:
        health = requests.get(f"{args.url}/health", timeout=5).json()
    except requests.ConnectionError:
        sys.exit(f"Nothing answering at {args.url}. Start it with `python app.py` first.")

    stamp = dt.datetime.now().strftime("%H%M%S")

    def one_run(i):
        body = {"text": TEXT, "creator_id": f"cost_{stamp}_{i}"}  # own id each, so the rate limit never fires
        t0 = time.perf_counter()
        response = requests.post(f"{args.url}/submit", json=body, timeout=args.timeout)
        client_ms = round((time.perf_counter() - t0) * 1000, 1)
        if response.status_code != 200:
            sys.exit(f"Run {i} got HTTP {response.status_code}: {response.text[:200]}")
        return response.headers.get("X-Run-Id"), client_ms

    cold = None
    if not health.get("detector_loaded"):
        print("Model not loaded yet — the first request is the cold start.")
        cold = one_run(0)

    sent = []
    for i in range(1, args.runs + 1):
        run_id, client_ms = one_run(i)
        sent.append((run_id, client_ms))
        print(f"  run {i:>2}: {client_ms:>8.1f} ms round trip")

    records = {r["run_id"]: r for r in
               requests.get(f"{args.url}/runs", params={"limit": 200}, timeout=10).json()["runs"]}

    def row(run_id, client_ms):
        rec = records.get(run_id, {})
        return {"run_id": run_id, "client_ms": client_ms,
                **{m: rec.get(m) for m in METRICS[1:]},
                "model_was_loaded": rec.get("model_was_loaded")}

    rows = [row(*s) for s in sent]
    cold_row = row(*cold) if cold else None
    missing = [r["run_id"] for r in rows if r["duration_ms"] is None]
    if missing:
        sys.exit(f"No run-log record for {missing} — is runlog installed in app.py?")

    summary = {m: (statistics.mean(r[m] for r in rows),
                   statistics.stdev(r[m] for r in rows) if len(rows) > 1 else 0.0,
                   min(r[m] for r in rows), max(r[m] for r in rows)) for m in METRICS}

    print(f"\nAverage over {len(rows)} warm runs: "
          f"{summary['duration_ms'][0]:.0f} ms wall in the service, "
          f"{summary['cpu_ms'][0]:.0f} ms CPU, "
          f"{summary['detector_ms'][0]:.0f} ms of it in gpt2.")
    if cold_row:
        print(f"Cold start (first run, model loading): {cold_row['duration_ms']:.0f} ms.")
    write_report(rows, cold_row, summary, args)


def write_report(rows, cold_row, summary, args):
    config.RESULTS_DIR.mkdir(exist_ok=True)
    now = dt.datetime.now()
    path = config.RESULTS_DIR / f"cost_{now.strftime('%Y-%m-%d_%H%M')}.md"

    lines = [
        "# Cost of one /submit",
        "",
        "- Produced by: `measure_cost.py::main`, reading `logs/runs.jsonl` via `GET /runs`",
        f"- {now.strftime('%Y-%m-%d %H:%M')} · {len(rows)} runs · same {len(TEXT.split())}-word text each time",
        f"- Machine: {platform.system()} {platform.release()}, {platform.processor() or platform.machine()}, "
        f"{os.cpu_count()} logical CPUs · model `{config.DETECTOR_MODEL}` on CPU",
        "",
        "| Measure | Mean | Std dev | Min | Max |",
        "|---|---|---|---|---|",
    ]
    names = {"client_ms": "Round trip (client)", "duration_ms": "Wall time in service",
             "cpu_ms": "CPU time (all threads)", "detector_ms": "Signal one (gpt2)",
             "style_ms": "Signal two (stylometry)"}
    for m in METRICS:
        mean, sd, lo, hi = summary[m]
        lines.append(f"| {names[m]} | {mean:.1f} ms | {sd:.1f} | {lo:.1f} | {hi:.1f} |")

    if cold_row:
        lines += ["", f"**Cold start** (first request after `python app.py`, loads gpt2): "
                      f"{cold_row['duration_ms']:.1f} ms wall, {cold_row['cpu_ms']:.1f} ms CPU, "
                      f"{cold_row['detector_ms']:.1f} ms in gpt2. Not in the average."]

    lines += ["", "| Run | run_id | Round trip | Service wall | CPU | gpt2 | Style |",
              "|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        lines.append(f"| {i} | `{r['run_id']}` | {r['client_ms']} | {r['duration_ms']} | "
                     f"{r['cpu_ms']} | {r['detector_ms']} | {r['style_ms']} |")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {path.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()
