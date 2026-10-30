#!/usr/bin/env python3
"""Generate a seeded multi-stage funnel demo with a ground-truth manifest.

Funnel: Lead -> Signed up -> Activated -> Paid.
Furthest-stage counts are exact by construction (not probabilistic), so the
manifest is the answer key the auditor must reproduce exactly.
"""
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
N = 10_000
OUT = Path(__file__).resolve().parent / "demo_multistage"
OUT.mkdir(exist_ok=True)

rng = random.Random(SEED)
STAGES = ["Lead", "Signed up", "Activated", "Paid"]
CHANNELS = ["paid_search", "social", "email"]

# Exact furthest-stage buckets: 4000 stop at Lead, 3000 at Signed up,
# 1800 at Activated, 1200 reach Paid.
furthest = (["Lead"] * 4000 + ["Signed up"] * 3000
            + ["Activated"] * 1800 + ["Paid"] * 1200)
rng.shuffle(furthest)

rows = []
paid_days = []
for i, stage in enumerate(furthest, 1):
    signup = date(2026, 1, 1) + timedelta(days=rng.randrange(180))
    if stage == "Paid":
        days = rng.randrange(1, 31)
        paid = signup + timedelta(days=days)
        paid_days.append(days)
    else:
        paid = None
    rows.append({
        "user_id": f"U{i:05d}",
        "channel": rng.choice(CHANNELS),
        "stage": stage,
        "signup_date": signup.isoformat(),
        "paid_date": paid.isoformat() if paid else "",
    })

with open(OUT / "multistage.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["user_id", "channel", "stage",
                                      "signup_date", "paid_date"])
    w.writeheader()
    w.writerows(rows)

stage_counts = []
for i in range(len(STAGES)):
    reached = sum(1 for r in rows if STAGES.index(r["stage"]) >= i)
    stage_counts.append(reached)
transitions = []
for i in range(len(STAGES) - 1):
    entered, converted = stage_counts[i], stage_counts[i + 1]
    transitions.append({
        "from": STAGES[i], "to": STAGES[i + 1],
        "entered": entered, "converted": converted,
        "rate": round(converted / entered, 4),
        "lost": entered - converted,
    })
leak = max(transitions, key=lambda t: t["lost"])
paid_days_sorted = sorted(paid_days)
med = paid_days_sorted[len(paid_days_sorted) // 2]

manifest = {
    "seed": SEED,
    "total": N,
    "stages": STAGES,
    "stage_counts": stage_counts,
    "furthest_counts": {s: furthest.count(s) for s in STAGES},
    "transitions": transitions,
    "overall_rate": round(stage_counts[-1] / stage_counts[0], 4),
    "biggest_leak": {"from": leak["from"], "to": leak["to"],
                     "lost": leak["lost"]},
    "velocity_median_days": med,
}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
print(f"wrote {N} rows; stage counts {stage_counts}; "
      f"overall {manifest['overall_rate']:.1%}; median days {med}")
