"""Project CCHAIN tables. Get them from Kaggle (doi 10.34740/kaggle/ds/4918229) into data/raw/cchain/."""
from pathlib import Path

import pandas as pd


def load_pidsr(raw: Path) -> pd.DataFrame:
    """Weekly leptospirosis (A27) for all 12 CCHAIN cities, from disease_pidsr_totals.

    Never mix with FHSIS rows: PIDSR counts are already inside the FHSIS annual totals.
    """
    raise NotImplementedError


def load_climate(raw: Path) -> pd.DataFrame:
    """Daily rainfall per city, 2008-2022, for training. Must line up with CHIRPS over 2015-2022."""
    raise NotImplementedError


def brgy_lepto_rows(raw: Path) -> pd.DataFrame:
    """Day-1 check: Navotas A27 rows in disease_lgu_disaggregated_totals.

    Empty result means barangay case validation waits on the CESU request.
    """
    raise NotImplementedError
