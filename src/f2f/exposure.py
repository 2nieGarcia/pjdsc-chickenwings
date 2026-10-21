"""Who is in each barangay during the day, not just who sleeps there. A scenario, never a count.

present_pop = POPCEN 2024 x daytime_factor + Navotas Fish Port inflow.
daytime_factor 0.93 is JICA MUCEP's Navotas day/night ratio (194.4k / 209.4k).
Inflow is 30k/40k/50k workers (DA 2026), placed on exposure.nfpc_barangays.
"""
import pandas as pd

from f2f import barangays


def present_population(cfg: dict, inflow: int | None = None) -> pd.DataFrame:
    """psgc10, name, pop_resident, nfpc_inflow, pop_daytime. inflow defaults to exposure.nfpc_scenario."""
    e = cfg["exposure"]
    inflow = e["nfpc_scenario"] if inflow is None else inflow
    if inflow < 0:
        raise ValueError("nfpc inflow must be >= 0")
    if not 0 < e["daytime_factor"] <= 1.5:
        raise ValueError("daytime_factor looks wrong; MUCEP gives 0.93")

    df = barangays.load()[["psgc10", "name", "pop_2024"]].rename(columns={"pop_2024": "pop_resident"})
    port = df["psgc10"].isin(e["nfpc_barangays"])
    if port.sum() != len(e["nfpc_barangays"]):
        raise ValueError("exposure.nfpc_barangays has codes that aren't Navotas barangays")
    # shortcut: equal split across the port barangays; weight by CLUP industrial land area once someone extracts it
    df["nfpc_inflow"] = port * (inflow / port.sum())
    df["pop_daytime"] = df["pop_resident"] * e["daytime_factor"] + df["nfpc_inflow"]
    return df
