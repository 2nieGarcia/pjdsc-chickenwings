"""Doxycycline stock-gap planner and the approval log.

The planner proposes. Nothing here moves stock; an official approves or
rejects each plan and that decision is the only thing written down.
"""
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from f2f.contracts import EXPOSURE_MODES, TIERS

TIER_ORDER = {"act_now": 0, "prepare": 1, "monitor": 2}
ACTIONS = {"created", "approved", "rejected"}
_NEXT = {None: {"created"}, "created": {"approved", "rejected"}}


def make_plan(req: dict, caps_per_person: dict) -> dict:
    """Greedy allocation: act_now first, then prepare, then monitor; higher score first within a tier."""
    _validate(req, caps_per_person)
    rows = sorted(req["rows"], key=lambda r: (TIER_ORDER[r["tier"]], -r.get("score", 0)))

    left = int(req["stock_on_hand"])
    allocations = []
    for r in rows:
        need = math.ceil(r["exposed"] * req["uptake"] * caps_per_person[r["tier"]] * (1 + req["buffer"]))
        alloc = min(need, left)
        left -= alloc
        allocations.append({"psgc10": r["psgc10"], "need_caps": need, "alloc_caps": alloc, "unmet_caps": need - alloc})

    return {
        # same inputs, same id: a re-render or re-export can never mint a second plan to approve
        "plan_id": hashlib.sha1(json.dumps(req, sort_keys=True, default=str).encode()).hexdigest()[:8],
        "issue_date": str(req["issue_date"]),
        "exposure_mode": req["exposure_mode"],
        "uptake": req["uptake"],
        "buffer": req["buffer"],
        "allocations": allocations,
        "total_need": sum(a["need_caps"] for a in allocations),
        "total_alloc": sum(a["alloc_caps"] for a in allocations),
        "stock_on_hand": int(req["stock_on_hand"]),
        "status": "draft",
        "synthetic_stock": bool(req.get("synthetic_stock", True)),
    }


def _validate(req, caps_per_person):
    if not 0 <= req["uptake"] <= 1:
        raise ValueError("uptake must be in [0, 1]")
    if req["buffer"] < 0:
        raise ValueError("buffer must be >= 0")
    if req["stock_on_hand"] < 0:
        raise ValueError("stock_on_hand must be >= 0")
    if req["exposure_mode"] not in EXPOSURE_MODES:
        raise ValueError(f"exposure_mode must be one of {sorted(EXPOSURE_MODES)}")
    seen = set()
    for r in req["rows"]:
        if r["tier"] not in TIERS or r["tier"] not in caps_per_person:
            raise ValueError(f"unknown tier {r['tier']!r} for {r['psgc10']}")
        if r["exposed"] < 0:
            raise ValueError(f"negative exposed count for {r['psgc10']}")
        if r["psgc10"] in seen:
            raise ValueError(f"duplicate barangay {r['psgc10']}")
        seen.add(r["psgc10"])


def plan_state(audit_path: Path, plan_id: str) -> str | None:
    """Last recorded action for plan_id, or None if never logged."""
    state = None
    if Path(audit_path).exists():
        for line in Path(audit_path).read_text(encoding="utf-8").splitlines():
            entry = json.loads(line)
            if entry["plan_id"] == plan_id:
                state = entry["action"]
    return state


def log_action(audit_path: Path, plan_id: str, action: str, actor: str, note: str = "") -> dict:
    """Append to the audit log. created -> approved | rejected, and that's final."""
    if action not in ACTIONS:
        raise ValueError(f"action must be one of {sorted(ACTIONS)}")
    if not actor.strip():
        raise ValueError("actor is required")
    state = plan_state(audit_path, plan_id)
    if action not in _NEXT.get(state, set()):
        raise ValueError(f"plan {plan_id} is {state or 'unlogged'}; cannot mark {action}")

    entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "plan_id": plan_id,
             "action": action, "actor": actor.strip(), "note": note}
    Path(audit_path).parent.mkdir(parents=True, exist_ok=True)
    with open(audit_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry
