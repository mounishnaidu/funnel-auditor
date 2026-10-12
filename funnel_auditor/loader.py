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


def load_invoice_funnel(csv_path: str, encoding: str = "latin1") -> pd.DataFrame:
    """One row per invoice; won = invoice was kept (not a cancellation).

    Exact duplicate lines are dropped first (the gatekeeper proves they are
    byte-identical); the drop count is printed so nothing happens silently.
    """
    raw = pd.read_csv(csv_path, dtype=str, encoding=encoding).fillna("")
    n_dupes = int(raw.duplicated().sum())
    df = raw.drop_duplicates().reset_index(drop=True)
    print(f"Dropped {n_dupes:,} exact duplicate lines before the audit.")
    g = df.groupby("InvoiceNo")
    out = pd.DataFrame({
        "invoice_id": g["InvoiceNo"].first().values,
        "country": g["Country"].agg(
            lambda s: s.mode().iloc[0] if len(s) else "").values,
        "invoice_date": g["InvoiceDate"].first().values,
        "lines": g.size().values,
    })
    out["won"] = (~out["invoice_id"].str.startswith("C")).astype(int)
    return out[["invoice_id", "country", "invoice_date", "lines", "won"]]


def load(config: dict) -> pd.DataFrame:
    kind = config.get("loader", "olist")
    if kind == "olist":
        return load_olist_funnel(config["mqls_csv"], config["deals_csv"])
    if kind == "invoice_funnel":
        return load_invoice_funnel(config["csv_path"],
                                   config.get("encoding", "latin1"))
    raise ValueError(f"unknown loader: {kind}")
