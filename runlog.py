"""
The run log — one structured record per request, to logs/runs.jsonl.

The audit log (audit.py) records *decisions*: what was judged and how. This
records *runs*: every request the service handled, how long it took, how much
CPU it used, what came in, what went out, and whether it failed. Refusals,
rate-limit 429s and crashes all leave a record — a failure that shows up only
as an absence is one you'll never find.

    import runlog
    runlog.install(app)                   # once, in app.py
    runlog.note(detector_ms=412.3)        # inside a route: extra fields for this run

Read it back with `runlog.read_runs()` or `GET /runs?limit=10`.

Each record:

    timestamp, run_id, method, path, http_status, outcome,
    duration_ms, cpu_ms, input, output, error, ...anything noted by the route

`outcome` is `ok` (2xx), `refused` (4xx — the service said no on purpose) or
`error` (5xx — something broke). The raw text a writer submits is not stored:
`input` keeps its length, word count, a short preview and a hash, which is
enough to find the matching run again without copying people's writing into a
second file.
"""

import hashlib
import json
import threading
import time
import traceback
import uuid
from datetime import datetime, timezone

from flask import g, jsonify, request
from werkzeug.exceptions import HTTPException

import config

_lock = threading.Lock()

PREVIEW_CHARS = 60
MAX_OUTPUT_BYTES = 2_000  # bigger responses (like GET /log) are summarised, not copied


def note(**fields) -> None:
    """Attach extra fields to the record for the current request."""
    try:
        g.run_extra.update(fields)
    except AttributeError:  # outside a request, or install() wasn't called
        pass


def install(app) -> None:
    """Register the hooks that time every request and write its record."""

    @app.before_request
    def _start():
        g.run_id = uuid.uuid4().hex[:12]
        g.run_start = time.perf_counter()
        g.run_cpu_start = time.process_time()
        g.run_extra = {}
        g.run_error = None

    @app.errorhandler(Exception)
    def _crash(exc):
        # HTTP errors (a route that doesn't exist, a wrong method...) are normal
        # answers, not crashes — but Werkzeug renders them as HTML pages. Answer
        # in JSON like every other reply. Redirects (code < 400) pass through
        # untouched. Errors with their own handler (429) never reach here.
        if isinstance(exc, HTTPException):
            if exc.code is None or exc.code < 400:
                return exc
            return jsonify({
                "error": exc.name.lower().replace(" ", "_"),
                "message": exc.description,
            }), exc.code
        g.run_error = {
            "type": type(exc).__name__,
            "message": str(exc)[:500],
            "where": _where(exc),
        }
        return jsonify({"error": "internal_error",
                        "message": "Something went wrong on our side. It has been logged."}), 500

    @app.after_request
    def _finish(response):
        try:
            _write(response)
        except Exception:  # logging must never break the answer itself
            pass
        response.headers["X-Run-Id"] = getattr(g, "run_id", "")
        return response


def _where(exc) -> str:
    """The innermost file:line of the traceback — where it actually broke."""
    frames = traceback.extract_tb(exc.__traceback__)
    if not frames:
        return ""
    last = frames[-1]
    return f"{last.filename.rsplit(chr(92), 1)[-1].rsplit('/', 1)[-1]}:{last.lineno}"


def _summarise_text(text: str) -> dict:
    return {
        "chars": len(text),
        "words": len(text.split()),
        "preview": text[:PREVIEW_CHARS],
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16],
    }


def _summarise_input():
    payload = request.get_json(silent=True)
    if payload is None:
        raw = request.get_data(cache=True)
        return {"json": False, "bytes": len(raw)} if raw else None
    if not isinstance(payload, dict):
        return {"json": True, "type": type(payload).__name__}
    out = {}
    for key, value in payload.items():
        if isinstance(value, str) and len(value) > PREVIEW_CHARS:
            out[key] = _summarise_text(value)
        else:
            out[key] = value
    return out


def _summarise_output(response):
    if response.direct_passthrough or not response.is_json:
        return None
    body = response.get_data()
    if len(body) > MAX_OUTPUT_BYTES:
        data = response.get_json(silent=True)
        keys = sorted(data) if isinstance(data, dict) else None
        return {"bytes": len(body), "keys": keys}
    data = response.get_json(silent=True)
    # The label is a long sentence the audit log already keeps in full.
    if isinstance(data, dict) and isinstance(data.get("label"), str) and len(data["label"]) > PREVIEW_CHARS:
        data = {**data, "label": data["label"][:PREVIEW_CHARS] + "…"}
    if isinstance(data, dict) and isinstance(data.get("decision"), dict):
        decision = data["decision"]
        if isinstance(decision.get("label"), str) and len(decision["label"]) > PREVIEW_CHARS:
            data = {**data, "decision": {**decision, "label": decision["label"][:PREVIEW_CHARS] + "…"}}
    return data


def _outcome(status: int) -> str:
    if status >= 500:
        return "error"
    if status >= 400:
        return "refused"
    return "ok"


def _write(response) -> None:
    start = getattr(g, "run_start", None)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "run_id": getattr(g, "run_id", None),
        "method": request.method,
        "path": request.path,
        "http_status": response.status_code,
        "outcome": _outcome(response.status_code),
        "duration_ms": round((time.perf_counter() - start) * 1000, 1) if start else None,
        "cpu_ms": round((time.process_time() - g.run_cpu_start) * 1000, 1) if start else None,
        "input": _summarise_input(),
        "output": _summarise_output(response),
        "error": getattr(g, "run_error", None),
        **getattr(g, "run_extra", {}),
    }
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False)
    with _lock:
        with config.RUN_LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def read_runs(limit: int | None = None) -> list[dict]:
    """The run log, oldest first. `limit` keeps the most recent N."""
    if not config.RUN_LOG.exists():
        return []
    runs = []
    for line in config.RUN_LOG.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(entry, dict):
            runs.append(entry)
    return runs[-limit:] if limit and limit > 0 else runs
