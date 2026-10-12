"""Load funnel data into one analysis-ready frame.

The contract: whatever the source, the loader returns a DataFrame with one row
per funnel entrant and a boolean `won` column marking who reached the final
stage. Everything downstream only trusts these two things.
"""
from pathlib import Path

import pandas as pd


def load_funnel_join(join_cfg: dict) -> pd.DataFrame:
    """Generic two-table funnel: entrants LEFT JOIN conversions.

    Config: join.left / join.right each give {path, key, encoding}.
    won = 1 when the entrant's key matches a row on the right, else 0.
    All columns from both sides ride along; slices and dates are picked
    up from the audit config downstream.

    Loud failure, not silent wrongness: duplicate keys on either side
    break the one-row-per-entrant contract, so the loader refuses and
    points at the gatekeeper instead of guessing.
    """
    def read(spec):
        return pd.read_csv(spec["path"], dtype=str,
                           encoding=spec.get("encoding", "utf-8")).fillna("")

    left, right = read(join_cfg["left"]), read(join_cfg["right"])
    lk, rk = join_cfg["left"]["key"], join_cfg["right"]["key"]

    for name, df, k in (("left", left, lk), ("right", right, rk)):
        n_dup = int(df[k].duplicated().sum())
        if n_dup:
            raise ValueError(
                f"{name} table has {n_dup:,} duplicate '{k}' values — "
                f"one-row-per-entrant is broken. Run the gatekeeper first.")

    f = left.merge(right, left_on=lk, right_on=rk, how="left", indicator=True,
                   suffixes=("", "_right"))
    f["won"] = (f["_merge"] == "both").astype(int)
    drop = ["_merge"] + ([rk] if rk != lk else [])
    return f.drop(columns=drop)


def load_status_funnel(cfg: dict) -> pd.DataFrame:
    """Single table, one row per id_col; won = status_col in won_values.

    Config: table {path, id_col, encoding}, status_col, won_values.
    The common shape for event logs that already carry their outcome
    (enrolled/completed, sent/clicked, applied/hired).
    """
    t = cfg["table"]
    df = pd.read_csv(t["path"], dtype=str,
                     encoding=t.get("encoding", "utf-8")).fillna("")
    id_col = t["id_col"]
    n_dup = int(df[id_col].duplicated().sum())
    if n_dup:
        raise ValueError(
            f"{n_dup:,} duplicate '{id_col}' values — one-row-per-entrant "
            f"is broken. Run the gatekeeper first.")
    excluded = cfg.get("exclude_values", [])
    if excluded:
        n_ex = int(df[cfg["status_col"]].isin(excluded).sum())
        df = df[~df[cfg["status_col"]].isin(excluded)].reset_index(drop=True)
        print(f"Excluded {n_ex:,} rows with unresolved status {excluded} "
              f"(censored, not lost).")
    df["won"] = df[cfg["status_col"]].isin(cfg["won_values"]).astype(int)
    return df


def load(config: dict) -> pd.DataFrame:
    kind = config.get("loader", "funnel_join")
    if kind == "funnel_join":
        return load_funnel_join(config["join"])
    if kind == "invoice_funnel":
        return load_invoice_funnel(config["csv_path"],
                                   config.get("encoding", "latin1"))
    if kind == "status_funnel":
        return load_status_funnel(config)
    raise ValueError(f"unknown loader: {kind}")
