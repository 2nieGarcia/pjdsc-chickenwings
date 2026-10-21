import json
import threading
import urllib.error
import urllib.request

import pytest

from f2f import config, export, fixtures, serve
from f2f.planner import plan_state


@pytest.fixture
def server(tmp_path, monkeypatch):
    run = fixtures.write(tmp_path / "run", config.load(config.BASE.parent / "carina_2024.yaml"))
    data = tmp_path / "data"
    monkeypatch.setattr(export, "OUT", data)
    export.main(["--run", str(run)])
    srv = serve.make_server(0, tmp_path, data, run)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    plan_id = next(iter(serve.load_plans(data)))
    yield f"http://127.0.0.1:{srv.server_address[1]}", run, plan_id
    srv.shutdown()


def post(url, body):
    req = urllib.request.Request(f"{url}/api/decision", json.dumps(body).encode(), {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_one_decision_per_plan(server):
    url, run, plan_id = server
    assert post(url, {"plan_id": plan_id, "action": "approved", "actor": "CHO duty officer"})[0] == 200
    status, body = post(url, {"plan_id": plan_id, "action": "approved", "actor": "CHO duty officer"})
    assert status == 409 and "already approved" in body["error"]
    lines = (run / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(x)["action"] for x in lines] == ["created", "approved"]
    assert (run / "plans" / f"{plan_id}.json").exists()
    with urllib.request.urlopen(f"{url}/api/decisions") as r:
        assert json.loads(r.read())[plan_id]["actor"] == "CHO duty officer"


@pytest.mark.parametrize("body,status", [
    ({"action": "approved", "actor": "x"}, 404),
    ({"action": "dispatched", "actor": "x"}, 400),
    ({"action": "approved", "actor": "  "}, 400),
    ({"action": "approved", "actor": "x" * 81}, 400),
])
def test_rejects_bad_requests(server, body, status):
    url, run, plan_id = server
    body = {"plan_id": plan_id if status != 404 else "nope", **body}
    assert post(url, body)[0] == status
    assert plan_state(run / "audit.jsonl", plan_id) is None


def test_plan_ids_are_stable_across_exports(tmp_path, monkeypatch):
    run = fixtures.write(tmp_path / "run", config.load(config.BASE.parent / "carina_2024.yaml"))
    ids = []
    for i in range(2):
        monkeypatch.setattr(export, "OUT", tmp_path / f"d{i}")
        export.main(["--run", str(run)])
        ids.append(sorted(serve.load_plans(tmp_path / f"d{i}")))
    assert ids[0] == ids[1]
