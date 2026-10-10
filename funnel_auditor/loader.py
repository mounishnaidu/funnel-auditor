"""Load funnel data into one analysis-ready frame.

The contract: whatever the source, the loader returns a DataFrame with one row
per funnel entrant and a boolean `won` column marking who reached the final
stage. Everything downstream only trusts these two things.
"""
from pathlib import Path

import pandas as pd


def load_olist_funnel(mqls_csv: str, deals_csv: str) -> pd.DataFrame:
    mqls = pd.read_csv(mqls_csv, parse_dates=["first_contact_date"])
    deals = pd.read_csv(deals_csv, parse_dates=["won_date"])

    f = mqls.merge(
        deals[["mql_id", "won_date", "business_segment",
               "lead_type", "lead_behaviour_profile"]],
        on="mql_id",
        how="left",
        indicator=True,
    )
    f["won"] = (f["_merge"] == "both").astype(int)
    f["days_to_close"] = (f["won_date"] - f["first_contact_date"]).dt.days
    return f.drop(columns=["_merge"])


def load(config: dict) -> pd.DataFrame:
    return load_olist_funnel(config["mqls_csv"], config["deals_csv"])
