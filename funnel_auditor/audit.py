"""The audit engine. Read-only: it never writes, sends, or mutates anything.

A Finding is a claim plus its evidence plus the exact computation that produced
it. If a finding can't show its work, it doesn't ship.
"""
from dataclasses import dataclass, field


@dataclass
class Finding:
    title: str
    severity: str          # "info" | "warning" | "critical"
    summary: str
    evidence: dict = field(default_factory=dict)
    how_computed: str = ""


def funnel_stages(df, stages: list, noun_pl: str = "MQLs") -> list[Finding]:
    names = [s["name"] for s in stages]
    first, last = names[0], names[-1]
    total = len(df)
    won = int(df["won"].sum())
    conv = won / total if total else 0.0
    lost = total - won
    return [Finding(
        title=f"Overall funnel: {first} -> {last}",
        severity="info",
        summary=(f"{total:,} {noun_pl} entered, {won:,} reached {last} "
                 f"({conv:.1%} conversion). {lost:,} lost ({1 - conv:.1%})."),
        evidence={"entrants": total, "converted": won,
                  "conversion_rate": round(conv, 4), "lost": lost},
        how_computed=(f"one row per {first}; won = reached {last}; "
                      f"conversion = converted / entrants"),
    )]


def biggest_leak(df, stages: list) -> list[Finding]:
    # Written for N stages; the measurable funnel may be fewer.
    order = [s["name"] for s in stages]
    counts = {order[0]: len(df), order[-1]: int(df["won"].sum())}
    leaks = []
    for prev, cur in zip(order, order[1:]):
        drop = counts[prev] - counts[cur]
        rate = drop / counts[prev] if counts[prev] else 0.0
        leaks.append((prev, cur, drop, rate))
    if not leaks:
        return []
    prev, cur, drop, rate = max(leaks, key=lambda x: x[2])
    return [Finding(
        title=f"Biggest leak: {prev} -> {cur}",
        severity="warning",
        summary=(f"{drop:,} entrants lost between {prev} and {cur} "
                 f"({rate:.1%} of the {prev} stage). This is where the "
                 f"funnel bleeds most in absolute terms."),
        evidence={"from_stage": prev, "to_stage": cur,
                  "lost": drop, "leak_rate": round(rate, 4)},
        how_computed=(f"stage counts {counts}; leak = count(prev) - "
                      f"count(cur) per adjacent stage pair"),
    )]


def _is_unusable(val, unknown_markers) -> bool:
    if pd_isna(val):
        return True
    return str(val).strip().lower() in [m.lower() for m in unknown_markers]


def slice_performance(df, dims, min_volume, under_ratio, over_ratio,
                      unknown_markers, noun="MQL") -> list[Finding]:
    overall = df["won"].mean()
    out = []
    for dim in dims:
        if dim not in df.columns:
            continue
        g = df.groupby(dim, dropna=False)["won"].agg(["count", "sum", "mean"])
        for val, row in g.iterrows():
            if _is_unusable(val, unknown_markers):
                continue  # data-quality story, not an investment signal
            n, w, r = int(row["count"]), int(row["sum"]), float(row["mean"])
            label = str(val)
            if n >= min_volume and r < under_ratio * overall:
                out.append(Finding(
                    title=f"Underperformer: {dim} = {label}",
                    severity="warning",
                    summary=(f"{label} converts at {r:.1%} on {n:,} {noun} — "
                             f"well below the {overall:.1%} average. Worth "
                             f"investigating before spending more here."),
                    evidence={"dimension": dim, "value": label, "mqls": n,
                              "won": w, "conversion_rate": round(r, 4),
                              "overall_rate": round(float(overall), 4)},
                    how_computed=(f"grouped by {dim}; conversion = won/total "
                                  f"per group; flagged when n >= {min_volume} "
                                  f"and rate < {under_ratio} x overall"),
                ))
            elif n >= min_volume and r > over_ratio * overall:
                out.append(Finding(
                    title=f"Outperformer: {dim} = {label}",
                    severity="info",
                    summary=(f"{label} converts at {r:.1%} on {n:,} {noun} — "
                             f"well above the {overall:.1%} average. "
                             f"Candidate for more investment."),
                    evidence={"dimension": dim, "value": label, "mqls": n,
                              "won": w, "conversion_rate": round(r, 4),
                              "overall_rate": round(float(overall), 4)},
                    how_computed=(f"grouped by {dim}; flagged when n >= "
                                  f"{min_volume} and rate > {over_ratio} x "
                                  f"overall"),
                ))
    return out


def best_known_channel(df, dim, min_volume, unknown_markers,
                       noun="MQL") -> list[Finding]:
    """The highest-converting *attributable* value at volume.

    'Unknown' converting well is a tracking problem, not a channel to scale —
    so it is excluded here and owned by the attribution-gap finding instead.
    """
    if dim not in df.columns:
        return []
    g = df.groupby(dim, dropna=False)["won"].agg(["count", "sum", "mean"])
    cands = [(v, r["count"], r["mean"]) for v, r in g.iterrows()
             if not _is_unusable(v, unknown_markers) and r["count"] >= min_volume]
    if not cands:
        return []
    val, n, r = max(cands, key=lambda x: x[2])
    return [Finding(
        title=f"Best {dim} at volume: {val}",
        severity="info",
        summary=(f"Among attributable {dim} values with {min_volume}+ {noun}, "
                 f"{val} converts best at {r:.1%} on {int(n):,} {noun}."),
        evidence={dim: str(val), "mqls": int(n),
                  "conversion_rate": round(float(r), 4)},
        how_computed=(f"grouped by {dim}, excluded unusable values "
                      f"{unknown_markers}, ranked conversion rate at "
                      f"n >= {min_volume}"),
    )]


def attribution_gap(df, dim, unknown_markers,
                    noun="MQL") -> list[Finding]:
    col = df[dim].fillna("").astype(str).str.strip().str.lower()
    unknown = col.isin([m.lower() for m in unknown_markers]).sum()
    share = unknown / len(df) if len(df) else 0.0
    sev = "critical" if share >= 0.15 else ("warning" if share >= 0.05 else "info")
    return [Finding(
        title="Attribution gap",
        severity=sev,
        summary=(f"{unknown:,} of {len(df):,} {noun} ({share:.1%}) have no "
                 f"usable {dim} — every slice built on this dimension is "
                 f"understated by that much."),
        evidence={"dimension": dim, "unknown_count": int(unknown),
                  "unknown_share": round(float(share), 4)},
        how_computed=(f"counted rows where lower(strip({dim})) in "
                      f"{unknown_markers} (or missing)"),
    )]


def velocity(df, start_col: str, end_col: str, group_dim: str,
             entrant_noun: str = "entrant",
             won_noun: str = "conversion") -> list[Finding]:
    df = df.copy()
    df["_days"] = (pd_to_datetime(df[end_col], format="mixed", errors="coerce")
                   - pd_to_datetime(df[start_col], format="mixed",
                                     errors="coerce")).dt.days
    conv = df[(df["won"] == 1) & df["_days"].notna()]
    if conv.empty:
        return []
    med = float(conv["_days"].median())
    by_group = conv.groupby(group_dim)["_days"].median().round(0).to_dict()
    return [Finding(
        title="Time to convert",
        severity="info",
        summary=(f"Median {entrant_noun} -> {won_noun} is {med:.0f} days. "
                 f"Per-{group_dim} medians are in the evidence — speed "
                 f"differences are a second dimension of quality."),
        evidence={"median_days": round(med, 1),
                  f"median_days_by_{group_dim}":
                  {str(k): v for k, v in by_group.items()}},
        how_computed=(f"days = {end_col} - {start_col}; median over converted, "
                       f"then grouped by {group_dim}"),
    )]


def pd_to_datetime(*a, **k):
    import pandas as pd
    return pd.to_datetime(*a, **k)


def pd_isna(v):
    try:
        import pandas as pd
        return pd.isna(v)
    except Exception:
        return v is None


def run_audit(df, config: dict) -> list[Finding]:
    noun = config["stages"][0]["name"]
    # naive plural is fine for the nouns we use (MQL, Invoice)
    noun_pl = noun if noun.endswith("s") else noun + "s"
    findings: list[Finding] = []
    findings += funnel_stages(df, config["stages"], noun_pl)
    findings += biggest_leak(df, config["stages"])
    findings += slice_performance(
        df,
        config["slice_dims"],
        config["min_volume_for_flag"],
        config["underperform_ratio"],
        config["outperform_ratio"],
        config["unknown_markers"],
        noun_pl,
    )
    if config.get("best_dim"):
        findings += best_known_channel(df, config["best_dim"],
                                       config["min_volume_for_flag"],
                                       config["unknown_markers"],
                                       noun_pl)
    if config.get("attribution_dim"):
        findings += attribution_gap(df, config["attribution_dim"],
                                    config["unknown_markers"],
                                    noun_pl)
    if config.get("velocity"):
        v = config["velocity"]
        findings += velocity(df, v["start_col"], v["end_col"],
                             v["group_dim"],
                             config["stages"][0]["name"].lower(),
                             config["stages"][-1]["name"].lower())
    order = {"critical": 0, "warning": 1, "info": 2}
    return sorted(findings, key=lambda f: order[f.severity])
