"""Load funnel data into one analysis-ready frame.

The contract: whatever the source, the loader returns a DataFrame with one row
per funnel entrant, a boolean `won` column marking who reached the final
stage, and a `stage_idx` column holding the furthest stage reached
(0 = first stage, n-1 = final stage). Everything downstream only trusts
these three things.
"""
from pathlib import Path

import pandas as pd


def _check_keys(df, key, table_name):
    """Loud failure, not silent wrongness: duplicate keys break the
    one-row-per-entrant contract, so the loader refuses and points at the
    gatekeeper instead of guessing."""
    n_dup = int(df[key].duplicated().sum())
    if n_dup:
        raise ValueError(
            f"{table_name} table has {n_dup:,} duplicate '{key}' values — "
            f"one-row-per-entrant is broken. Run the gatekeeper first.")


def _read(spec):
    return pd.read_csv(spec["path"], dtype=str,
                       encoding=spec.get("encoding", "utf-8")).fillna("")


def load_funnel_join(join_cfg: dict, n_stages: int) -> pd.DataFrame:
    """Join-based funnel: entrants matched against conversion tables.

    Two config shapes:
    - left/right (two tables): the original two-stage funnel. Entrants on
      the left, conversions on the right; won = key matched. Requires
      exactly 2 stages.
    - stages (a list of tables, one per stage): stage 0 is the entrants
      table; stage i's table holds the keys of entrants who reached stage
      i. An entrant's furthest stage is the highest i whose table holds
      their key. Segment columns must live in the entrants table — stage
      tables contribute only their keys.
    """
    if "stages" in join_cfg:
        tables = [_read(s) for s in join_cfg["stages"]]
        keys = [s["key"] for s in join_cfg["stages"]]
        if len(tables) != n_stages:
            raise ValueError(
                f"join.stages lists {len(tables)} tables but the config "
                f"declares {n_stages} stages — they must match.")
        for i, (df, k) in enumerate(zip(tables, keys)):
            _check_keys(df, k, f"stage {i}")
        entrants = tables[0].copy()
        ekey = keys[0]
        stage_idx = pd.Series(0, index=entrants.index)
        for i in range(1, n_stages):
            reached = entrants[ekey].isin(set(tables[i][keys[i]]))
            stage_idx = stage_idx.where(~reached, i)
        entrants["stage_idx"] = stage_idx.astype(int)
        entrants["won"] = (entrants["stage_idx"] == n_stages - 1).astype(int)
        return entrants

    if n_stages != 2:
        raise ValueError(
            "funnel_join with left/right only describes a two-stage funnel. "
            "For more stages, use join.stages (one table per stage).")
    left, right = _read(join_cfg["left"]), _read(join_cfg["right"])
    lk, rk = join_cfg["left"]["key"], join_cfg["right"]["key"]
    _check_keys(left, lk, "left")
    _check_keys(right, rk, "right")
    f = left.merge(right, left_on=lk, right_on=rk, how="left", indicator=True,
                   suffixes=("", "_right"))
    f["won"] = (f["_merge"] == "both").astype(int)
    f["stage_idx"] = f["won"]
    drop = ["_merge"] + ([rk] if rk != lk else [])
    return f.drop(columns=drop)


def load_status_funnel(cfg: dict, n_stages: int) -> pd.DataFrame:
    """Single table, one row per id_col.

    Two modes:
    - stage_col given: the column holds the stage each row reached, named
      with the config's stage names. A value that is not a stage name
      (e.g. "Dropped", blank) maps to stage 0 — entered, went no further.
      won = reached the final stage.
    - legacy (no stage_col): won = status_col in won_values, with
      exclude_values rows dropped first as censored, not lost. Only
      describes entry vs final stage, so it requires exactly 2 stages.
    """
    t = cfg["table"]
    df = pd.read_csv(t["path"], dtype=str,
                     encoding=t.get("encoding", "utf-8")).fillna("")
    id_col = t["id_col"]
    _check_keys(df, id_col, "table")
    excluded = cfg.get("exclude_values", [])
    if excluded:
        n_ex = int(df[cfg["status_col"]].isin(excluded).sum())
        df = df[~df[cfg["status_col"]].isin(excluded)].reset_index(drop=True)
        print(f"Excluded {n_ex:,} rows with unresolved status {excluded} "
              f"(censored, not lost).")
    if "stage_col" in cfg:
        names = [s["name"] for s in cfg["stages"]]
        pos = {name: i for i, name in enumerate(names)}
        df["stage_idx"] = df[cfg["stage_col"]].map(pos).fillna(0).astype(int)
        df["won"] = (df["stage_idx"] == n_stages - 1).astype(int)
        return df
    if n_stages != 2:
        raise ValueError(
            "status_funnel without stage_col only describes entry vs final "
            "stage. For more stages, add stage_col holding the stage names.")
    df["won"] = df[cfg["status_col"]].isin(cfg["won_values"]).astype(int)
    df["stage_idx"] = df["won"] * (n_stages - 1)
    return df


def load_invoice_funnel(csv_path: str, encoding: str = "latin1") -> pd.DataFrame:
    """One row per invoice; won = invoice was kept (not a cancellation).

    Exact duplicate lines are dropped first (the gatekeeper proves they are
    byte-identical); the drop count is printed so nothing happens silently.
    Two stages: Invoice -> Kept.
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
    out["stage_idx"] = out["won"]
    return out[["invoice_id", "country", "invoice_date", "lines", "won",
                "stage_idx"]]


def load(config: dict) -> pd.DataFrame:
    n_stages = len(config["stages"])
    kind = config.get("loader", "funnel_join")
    if kind == "funnel_join":
        return load_funnel_join(config["join"], n_stages)
    if kind == "invoice_funnel":
        if n_stages != 2:
            raise ValueError(
                "invoice_funnel only describes a two-stage funnel "
                "(Invoice -> Kept).")
        return load_invoice_funnel(config["csv_path"],
                                   config.get("encoding", "latin1"))
    if kind == "status_funnel":
        return load_status_funnel(config, n_stages)
    raise ValueError(f"unknown loader: {kind}")
