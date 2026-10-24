"""streamlit run app/streamlit_app.py

Reads one artifact folder. The only things it writes are decided plans and the approval log.
"""
import json
import os
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

from f2f import config, geo
from f2f.planner import log_action, make_plan, plan_state

# Okabe-Ito, readable with the common colour-vision deficiencies; tier is also spelled out in the tooltip
TIER_RGB = {"act_now": [213, 94, 0, 210], "prepare": [230, 159, 0, 190], "monitor": [86, 180, 233, 170]}

ROOT = Path(__file__).resolve().parents[1]
cfg = config.load(ROOT / "configs" / "carina_2024.yaml")
art_root = Path(os.environ.get("F2F_ARTIFACTS", ROOT / cfg["paths"]["artifacts"]))

st.set_page_config(page_title="Flood-to-Fever | Navotas", layout="wide")
st.title("Flood-to-Fever: Navotas City")

runs = sorted(p for p in art_root.glob("*") if (p / "barangay_index_resident.parquet").exists()) if art_root.exists() else []
if not runs:
    st.info("No artifacts yet. Build them with `python -m f2f.run --config configs/carina_2024.yaml`, "
            "or `python -m f2f.fixtures` for fake ones.")
    st.stop()

run = st.sidebar.selectbox("Run", runs[::-1], format_func=lambda p: p.name)
if (run / "manifest.json").exists():
    mf = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    st.sidebar.caption(f"Cases through {mf['cases_through']} · rain through {mf['rain_through']} "
                       f"({', '.join(mf['rain_sources'])}) · built {mf['created'][:10]} from {mf['git_sha']}"
                       + ("" if mf["flood_log"] else " · no flood log: flood flags off"))
mode = st.sidebar.radio("Exposure", ["resident", "daytime"])
idx = pd.read_parquet(run / f"barangay_index_{mode}.parquet")
if mode == "daytime":
    e = cfg["exposure"]
    st.sidebar.caption(f"Scenario estimate: residents × {e['daytime_factor']} + {e['nfpc_scenario']:,} fish port "
                       "workers on the NBBS barangays. Not a headcount.")

# forecast
if (run / "forecast.parquet").exists():
    fc = pd.read_parquet(run / "forecast.parquet")
    issue = st.select_slider("Issue date", sorted(fc["issue_date"].unique()),
                             format_func=lambda d: pd.Timestamp(d).strftime("%d %b %Y"))
    now = fc[fc["issue_date"] == issue].sort_values("h")
    for col, r in zip(st.columns(len(now)), now.itertuples()):
        col.metric(f"P(elevated), week +{r.h}", f"{r.p_elevated:.0%}", r.alert, delta_color="off")
    seen = fc[(fc["h"] == 2) & (fc["issue_date"] <= issue)]
    st.line_chart(seen.set_index("target_week")["p_elevated"])
    st.caption(f"Rain through {now['rain_through'].max():%d %b %Y}. "
               f"Cases through {now['cases_through'].max():%d %b %Y}.")
else:
    issue = pd.Timestamp(cfg["replay"]["event_window"][0])
    st.info("No forecast in this run yet. Showing the barangay index only.")

# barangays
st.subheader("Barangays")
if (run / "barangays.geojson").exists():
    shapes = json.loads((run / "barangays.geojson").read_text(encoding="utf-8"))
    rows = idx.set_index("psgc10")
    expo = "exposure_day" if mode == "daytime" else "exposure_res"
    for f in shapes["features"]:
        r = rows.loc[f["properties"]["psgc10"]]
        f["properties"].update(
            tier=r["tier"].replace("_", " "), rank=int(r["rank"]), band=f"{r['rank_p05']}-{r['rank_p95']}",
            fill=TIER_RGB[r["tier"]], hazard=round(r["hazard"], 1), exposure=round(r[expo], 1),
            vulnerability=round(r["vulnerability"], 1), coping_gap=round(r["coping_gap"], 1))
    cents = [geo.area_centroid(f["geometry"])[1:] for f in shapes["features"]]
    lons, lats = zip(*cents)
    view = pdk.ViewState(longitude=(min(lons) + max(lons)) / 2, latitude=(min(lats) + max(lats)) / 2, zoom=11.9)
    st.pydeck_chart(pdk.Deck(
        layers=[pdk.Layer("GeoJsonLayer", shapes, pickable=True, stroked=True, filled=True,
                          get_fill_color="properties.fill", get_line_color=[60, 60, 60, 255], line_width_min_pixels=1)],
        # basemap tiles are decoration; offline they don't load and the polygons still draw
        initial_view_state=view, map_style=None,
        tooltip={"html": "<b>{name}</b><br/>{tier}, rank {rank} (band {band})<br/>hazard {hazard} · "
                         "exposure {exposure}<br/>vulnerability {vulnerability} · coping gap {coping_gap}"}))
    st.caption("Vermillion: act now · Orange: prepare · Sky blue: monitor. Hover a barangay for its components.")
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
        try:
            if plan_state(audit, plan["plan_id"]) is None:
                log_action(audit, plan["plan_id"], "created", "dashboard")
            log_action(audit, plan["plan_id"], action, actor, note)
        except ValueError as err:  # already decided: plan ids are stable, so a second decision is refused
            st.error(str(err))
            st.stop()
        st.success(f"Plan {plan['plan_id']} {action} by {actor.strip()}. Nothing is dispatched from here.")
