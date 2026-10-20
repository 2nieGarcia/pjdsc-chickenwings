import random

import pytest

from f2f.planner import log_action, make_plan, plan_state

CAPS = {"act_now": 4, "prepare": 6, "monitor": 2}


def req(rows, stock=1000, uptake=0.5, buffer=0.15):
    return {"issue_date": "2024-07-22", "uptake": uptake, "buffer": buffer, "stock_on_hand": stock,
            "exposure_mode": "resident", "rows": rows, "synthetic_stock": True}


def test_never_over_allocates():
    rng = random.Random(7)
    for _ in range(500):
        rows = [{"psgc10": f"b{i}", "tier": rng.choice(list(CAPS)), "exposed": rng.randint(0, 5000),
                 "score": rng.uniform(1, 10)} for i in range(18)]
        plan = make_plan(req(rows, stock=rng.randint(0, 50_000), uptake=rng.choice([0.3, 0.5, 0.7])), CAPS)
        assert plan["total_alloc"] <= plan["stock_on_hand"]
        for a in plan["allocations"]:
            assert 0 <= a["alloc_caps"] <= a["need_caps"]
            assert a["unmet_caps"] == a["need_caps"] - a["alloc_caps"]


def test_act_now_filled_before_prepare():
    rows = [{"psgc10": "prep", "tier": "prepare", "exposed": 100, "score": 9.9},
            {"psgc10": "now", "tier": "act_now", "exposed": 100, "score": 2.0}]
    plan = make_plan(req(rows, stock=100, uptake=1, buffer=0), CAPS)
    got = {a["psgc10"]: a for a in plan["allocations"]}
    assert got["now"]["alloc_caps"] == 100
    assert got["prep"]["alloc_caps"] == 0
    assert got["prep"]["unmet_caps"] == 600


def test_need_rounds_up():
    plan = make_plan(req([{"psgc10": "a", "tier": "monitor", "exposed": 1}], uptake=0.3, buffer=0.1), CAPS)
    assert plan["allocations"][0]["need_caps"] == 1  # 1 * 0.3 * 2 * 1.1 = 0.66


@pytest.mark.parametrize("bad", [
    {"uptake": 1.5}, {"buffer": -0.1}, {"stock_on_hand": -1}, {"exposure_mode": "nightly"},
    {"rows": [{"psgc10": "a", "tier": "panic", "exposed": 1}]},
    {"rows": [{"psgc10": "a", "tier": "monitor", "exposed": -3}]},
    {"rows": [{"psgc10": "a", "tier": "monitor", "exposed": 1}, {"psgc10": "a", "tier": "prepare", "exposed": 1}]},
])
def test_rejects_bad_requests(bad):
    with pytest.raises(ValueError):
        make_plan({**req([{"psgc10": "a", "tier": "monitor", "exposed": 1}]), **bad}, CAPS)


def test_audit_transitions(tmp_path):
    log = tmp_path / "audit.jsonl"
    assert plan_state(log, "p1") is None
    with pytest.raises(ValueError):
        log_action(log, "p1", "approved", "cho")  # must be created first
    log_action(log, "p1", "created", "pipeline")
    log_action(log, "p1", "approved", "cho", "go")
    assert plan_state(log, "p1") == "approved"
    with pytest.raises(ValueError):
        log_action(log, "p1", "rejected", "cho")
    with pytest.raises(ValueError):
        log_action(log, "p2", "created", "  ")
