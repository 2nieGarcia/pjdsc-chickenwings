"""Builds the city_week panel (contract C1).

Leakage rule: a weekly feature lagged k weeks behind the target week may feed horizon h only if k >= h + 1;
lag h is the week that starts on the issue Monday (target = issue_date + h).
Case lags also need the reporting delay added to h.
"""
import pandas as pd

RAIN_LAGS = range(1, 7)


def build_city_week(pidsr: pd.DataFrame, rain: pd.DataFrame, pop: pd.DataFrame, cfg: dict,
                    flood_log: pd.DataFrame | None = None) -> pd.DataFrame:
    """pidsr: city_psgc, week_start, cases. rain: city_psgc, date, rain_mm (daily), optional source
    (default cchain; a week with any chirps day is a chirps week). pop: city_psgc, year, pop.
    flood_log: f2f.ingest.events format, Navotas only; None when the log file is missing (flood_event stays False).

    Weeks run Monday-Sunday. Every city gets every Monday from the first PIDSR week through the
    end of the replay window plus the longest horizon; cases are <NA> after 2022, rain is <NA>
    wherever the source has no complete week.
    """
    end = pd.Timestamp(cfg.get("replay", {}).get("issue_end", pidsr["week_start"].max())) + pd.Timedelta(weeks=max(cfg["horizons"]))
    weeks = pd.date_range(pidsr["week_start"].min(), end, freq="W-MON")
    grid = pd.MultiIndex.from_product([sorted(pidsr["city_psgc"].unique()), weeks], names=["city_psgc", "week_start"])
    df = pidsr.set_index(["city_psgc", "week_start"])[["cases"]].reindex(grid).reset_index()
    df["cases"] = df["cases"].astype("Int64")
    df["elevated"] = (df["cases"] >= cfg["target"]["elevated_min_cases"]).astype("boolean")

    r = rain.assign(week_start=rain["date"] - pd.to_timedelta(rain["date"].dt.dayofweek, unit="D"),
                    heavy=rain["rain_mm"] >= cfg["alerts"]["heavy_day_mm"],
                    chirps=rain["source"].eq("chirps") if "source" in rain else False)
    wk = r.groupby(["city_psgc", "week_start"]).agg(rain_wk_mm=("rain_mm", "sum"), heavy_days=("heavy", "sum"),
                                                    n=("rain_mm", "size"), chirps=("chirps", "any"))
    wk[["rain_wk_mm", "heavy_days"]] = wk[["rain_wk_mm", "heavy_days"]].astype(float).where(wk["n"] == 7)
    chirps_weeks = wk.index[wk["chirps"]]
    wk = wk.drop(columns=["n", "chirps"]).reset_index()
    # lags need weeks before the panel starts and after the rain stops (the weeks a forecast targets),
    # so shift on a gap-free weekly grid that covers both
    rain_grid = pd.MultiIndex.from_product([sorted(wk["city_psgc"].unique()),
                                            pd.date_range(wk["week_start"].min(), max(wk["week_start"].max(), end), freq="W-MON")],
                                           names=["city_psgc", "week_start"])
    wk = wk.set_index(["city_psgc", "week_start"]).reindex(rain_grid)
    for k in RAIN_LAGS:
        wk[f"rain_lag{k}_mm"] = wk.groupby(level="city_psgc")["rain_wk_mm"].shift(k)
    wk["rain_cum6_lag1_mm"] = wk[[f"rain_lag{k}_mm" for k in RAIN_LAGS]].sum(axis=1, min_count=len(RAIN_LAGS))
    df = df.merge(wk.reset_index(), on=["city_psgc", "week_start"], how="left")
    df["heavy_days"] = df["heavy_days"].astype("Int64")

    p = pop.set_index(["city_psgc", "year"])["pop"]
    last = pop.groupby("city_psgc")["year"].max()
    year = df["week_start"].dt.year.clip(upper=df["city_psgc"].map(last))
    df["pop"] = [p.get((c, y)) for c, y in zip(df["city_psgc"], year)]
    if df["pop"].isna().any():
        raise ValueError(f"no population for {sorted(df.loc[df['pop'].isna(), 'city_psgc'].unique())}")
    df["pop"] = df["pop"].astype(int)

    navotas = df["city_psgc"] == cfg["city"]["psgc10"]
    df["flood_event"] = False
    if flood_log is not None and len(flood_log):
        fl = flood_log[flood_log["kind"] == "flood"]
        flood_weeks = set(fl["date"] - pd.to_timedelta(fl["date"].dt.dayofweek, unit="D"))
        df["flood_event"] = navotas & df["week_start"].isin(flood_weeks)
    gate = cfg.get("gate_impaired")
    df["gate_impaired"] = False
    if gate:
        # any day of the week inside the window counts
        df["gate_impaired"] = (navotas & (df["week_start"] <= pd.Timestamp(gate["end"]))
                               & (df["week_start"] + pd.Timedelta(days=6) >= pd.Timestamp(gate["start"])))

    df["source"] = "cchain"
    df.loc[pd.MultiIndex.from_frame(df[["city_psgc", "week_start"]]).isin(chirps_weeks), "source"] = "chirps"
    cols = ["city_psgc", "week_start", "cases", "elevated", "pop", "rain_wk_mm",
            *[f"rain_lag{k}_mm" for k in RAIN_LAGS], "rain_cum6_lag1_mm", "heavy_days",
            "flood_event", "gate_impaired", "source"]
    return df[cols].sort_values(["city_psgc", "week_start"]).reset_index(drop=True)
