"""python -m f2f.serve [--port 8600]

Serves the built dashboard (web/dist) on 127.0.0.1 and records plan decisions into the run's
audit log. The browser can only ask; this process validates the request, saves the plan and
appends to audit.jsonl through f2f.planner, whose state machine refuses a second decision.

  GET  /api/decisions   -> {plan_id: {action, actor, ts}} for the exported run
  POST /api/decision    {plan_id, action: approved|rejected, actor, note?}
"""
import argparse
import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from f2f import config
from f2f.planner import log_action, plan_state

ROOT = Path(__file__).resolve().parents[2]
MAX_BODY = 4096
_LOCK = threading.Lock()  # the server is threaded; check-then-write on the audit log must not interleave


def load_plans(data_dir: Path) -> dict:
    """plan_id -> plan, from the exported plans.json."""
    plans = json.loads((data_dir / "plans.json").read_text(encoding="utf-8"))
    return {p["plan_id"]: p for by_uptake in plans.values() for p in by_uptake.values()}


def decisions(audit: Path) -> dict:
    out = {}
    if audit.exists():
        for line in audit.read_text(encoding="utf-8").splitlines():
            e = json.loads(line)
            if e["action"] in ("approved", "rejected"):
                out[e["plan_id"]] = {k: e[k] for k in ("action", "actor", "ts")}
    return out


def decide(body: dict, plans: dict, run_dir: Path) -> tuple[int, dict]:
    """Validate one decision and record it. Returns (http status, json body)."""
    plan_id, action = body.get("plan_id"), body.get("action")
    actor = str(body.get("actor") or "").strip()
    note = str(body.get("note") or "").strip()
    if action not in ("approved", "rejected"):
        return 400, {"error": "action must be approved or rejected"}
    if not actor or len(actor) > 80:
        return 400, {"error": "actor is required (80 characters max)"}
    if len(note) > 500:
        return 400, {"error": "note is 500 characters max"}
    if plan_id not in plans:
        return 404, {"error": f"unknown plan {plan_id!r}; re-export and reload"}

    audit = run_dir / "audit.jsonl"
    if plan_state(audit, plan_id) in ("approved", "rejected"):
        return 409, {"error": f"plan {plan_id} is already {plan_state(audit, plan_id)}", "decisions": decisions(audit)}
    (run_dir / "plans").mkdir(parents=True, exist_ok=True)
    (run_dir / "plans" / f"{plan_id}.json").write_text(json.dumps(plans[plan_id], indent=2), encoding="utf-8")
    if plan_state(audit, plan_id) is None:
        log_action(audit, plan_id, "created", "dashboard")
    entry = log_action(audit, plan_id, action, actor, note)
    return 200, entry


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, plans, run_dir, **kw):
        self.plans, self.run_dir = plans, run_dir
        super().__init__(*args, **kw)

    def send_json(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/api/decisions":
            return self.send_json(200, decisions(self.run_dir / "audit.jsonl"))
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/decision":
            return self.send_json(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length") or 0)
        if not 0 < n <= MAX_BODY:
            return self.send_json(400, {"error": "empty or oversized body"})
        try:
            body = json.loads(self.rfile.read(n))
        except json.JSONDecodeError:
            return self.send_json(400, {"error": "body must be JSON"})
        if not isinstance(body, dict):
            return self.send_json(400, {"error": "body must be a JSON object"})
        with _LOCK:
            result = decide(body, self.plans, self.run_dir)
        self.send_json(*result)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")  # a rebuild or re-export must show up on the next reload
        super().end_headers()

    def log_message(self, fmt, *args):  # keep the demo terminal quiet except for decisions
        if self.command == "POST":
            super().log_message(fmt, *args)


def make_server(port: int, static_dir: Path, data_dir: Path, run_dir: Path) -> ThreadingHTTPServer:
    handler = partial(Handler, directory=str(static_dir), plans=load_plans(data_dir), run_dir=run_dir)
    return ThreadingHTTPServer(("127.0.0.1", port), handler)  # localhost only: decisions are not for the network


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8600)
    args = ap.parse_args(argv)
    cfg = config.load(config.BASE.parent / "carina_2024.yaml")
    dist = ROOT / "web" / "dist"
    if not (dist / "index.html").exists():
        raise SystemExit("no web/dist yet: run `npm run build` in web/ first")
    meta = json.loads((dist / "data" / "meta.json").read_text(encoding="utf-8"))
    run_dir = ROOT / cfg["paths"]["artifacts"] / meta["run_id"]
    srv = make_server(args.port, dist, dist / "data", run_dir)
    print(f"dashboard on http://127.0.0.1:{args.port} · decisions -> {run_dir / 'audit.jsonl'}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
