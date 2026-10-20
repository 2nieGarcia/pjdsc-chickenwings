"""streamlit run app/streamlit_app.py

Reads one artifact folder. The only things it writes are decided plans and the approval log.
"""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from f2f import config
from f2f.planner import log_action, make_plan

ROOT = Path(__file__).resolve().parents[1]
cfg = config.load(ROOT / "configs" / "carina_2024.yaml")
art_root = ROOT / cfg["paths"]["artifacts"]

st.set_page_config(page_title="Flood-to-Fever | Navotas", layout="wide")
st.title("Flood-to-Fever: Navotas City")

runs = sorted(p for p in art_root.glob("*") if (p / "forecast.parquet").exists()) if art_root.exists() else []
if not runs:
    st.info("No artifacts yet. Build them with `python -m f2f.run --config configs/carina_2024.yaml`.")
    st.stop()

run = st.sidebar.selectbox("Run", runs[::-1], format_func=lambda p: p.name)
mode = st.sidebar.radio("Exposure", ["resident", "daytime"])
fc = pd.read_parquet(run / "forecast.parquet")
idx = pd.read_parquet(run / f"barangay_index_{mode}.parquet")

# forecast
issue = st.select_slider("Issue date", sorted(fc["issue_date"].unique()),
                         format_func=lambda d: pd.Timestamp(d).strftime("%d %b %Y"))
now = fc[fc["issue_date"] == issue].sort_values("h")
for col, r in zip(st.columns(len(now)), now.itertuples()):
    col.metric(f"P(elevated), week +{r.h}", f"{r.p_elevated:.0%}", r.alert, delta_color="off")
seen = fc[(fc["h"] == 2) & (fc["issue_date"] <= issue)]
st.line_chart(seen.set_index("target_week")["p_elevated"])
st.caption(f"Rain through {now['rain_through'].max():%d %b %Y}. "
           f"Cases through {now['cases_through'].max():%d %b %Y}.")

# barangays
st.subheader("Barangays")
st.dataframe(idx.sort_values("rank")[["name", "tier", "score", "hazard", "exposure_res", "exposure_day",
                                      "vulnerability", "coping_gap", "rank_p05", "rank_p95"]], hide_index=True)

# stock gap
st.subheader("Doxycycline stock gap")
if cfg["stock"]["synthetic"]:
    st.warning("Stock on hand is synthetic. No real inventory is shown.")
uptake = st.select_slider("Uptake", cfg["planner"]["uptake_scenarios"], value=cfg["planner"]["uptake"])
stock = st.number_input("Usable stock (100 mg capsules)", min_value=0, value=cfg["stock"]["on_hand_caps"], step=500)

plan = make_plan({
    "issue_date": pd.Timestamp(issue).date(), "uptake": uptake, "buffer": cfg["planner"]["buffer"],
    "stock_on_hand": stock, "exposure_mode": mode, "synthetic_stock": cfg["stock"]["synthetic"],
    "rows": idx[["psgc10", "tier", "exposed_n", "score"]].rename(columns={"exposed_n": "exposed"}).to_dict("records"),
}, cfg["planner"]["caps_per_person"])

a, b, c = st.columns(3)
a.metric("Need", f"{plan['total_need']:,}")
b.metric("Allocated", f"{plan['total_alloc']:,}")
c.metric("Unmet", f"{plan['total_need'] - plan['total_alloc']:,}")
st.dataframe(pd.DataFrame(plan["allocations"]).merge(idx[["psgc10", "name", "tier"]], on="psgc10"), hide_index=True)

actor = st.text_input("Approving official")
note = st.text_input("Note")
audit = run / "audit.jsonl"
for col, action in zip(st.columns(2), ["approved", "rejected"]):
    if col.button(action.capitalize(), disabled=not actor.strip()):
        (run / "plans").mkdir(exist_ok=True)
        (run / "plans" / f"{plan['plan_id']}.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
        log_action(audit, plan["plan_id"], "created", "dashboard")
        log_action(audit, plan["plan_id"], action, actor, note)
        st.success(f"Plan {plan['plan_id']} {action} by {actor.strip()}. Nothing is dispatched from here.")
