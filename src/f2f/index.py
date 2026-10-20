"""Barangay priority index (contract C3), INFORM-style.

Components scaled to [1, 10], geometric mean across hazard, exposure, vulnerability and coping gap,
so a barangay that doesn't flood can't rank high on crowding alone. Rank bands come from
Monte Carlo weight jitter (index.weight_jitter in config).
"""
import pandas as pd


def build_index(layers: pd.DataFrame, cfg: dict, exposure_mode: str) -> pd.DataFrame:
    raise NotImplementedError
