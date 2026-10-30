#!/usr/bin/env python3
"""Verify the multi-stage upgrade properly: demo vs manifest, multi-table
join unit case, and Olist/retail/course regressions against known values.

Fails loudly on any mismatch. Run from the repo root.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from funnel_auditor import audit, loader

ROOT = Path(__file__).resolve().parent
failures = []


def check(label, got, want):
    ok = got == want
    print(f"  {'PASS' if ok else 'FAIL'} {label}: got {got}, want {want}")
    if not ok:
        failures.append(label)


def findings_by_title(findings):
    return {f.title: f for f in findings}


# --- 1. Multi-stage demo vs manifest -------------------------------------
print("== demo (status_funnel, 4 stages) ==")
cfg = json.loads((ROOT / "multistage_config.json").read_text())
df = loader.load(cfg)
man = json.loads((ROOT / "demo_multistage" / "manifest.json").read_text())
fs = findings_by_title(audit.run_audit(df, cfg))

check("loader stage_idx distribution",
      df["stage_idx"].value_counts().sort_index().to_dict(),
      {0: 4000, 1: 3000, 2: 1800, 3: 1200})
ov = fs["Overall funnel: Lead -> Paid"].evidence
check("overall converted", ov["converted"], 1200)
check("overall rate", ov["conversion_rate"], 0.12)
for t in man["transitions"]:
    ev = fs[f"Stage conversion: {t['from']} -> {t['to']}"].evidence
    check(f"transition {t['from']}->{t['to']} rate",
          ev["conversion_rate"], t["rate"])
    check(f"transition {t['from']}->{t['to']} lost", ev["lost"], t["lost"])
lk = fs["Biggest leak: Lead -> Signed up"].evidence
check("biggest leak", (lk["from_stage"], lk["to_stage"], lk["lost"]),
      ("Lead", "Signed up", 4000))
vel = fs["Time to convert"].evidence
check("velocity median", vel["median_days"], float(man["velocity_median_days"]))

# --- 2. Multi-table join unit case ----------------------------------------
print("== multi-table join (3 tiny tables) ==")
tmp = Path("/tmp/multistage-join-test")
tmp.mkdir(exist_ok=True)
(tmp / "e.csv").write_text("id,seg\n" + "\n".join(
    f"E{i:02d},a" for i in range(1, 11)) + "\n")
(tmp / "s2.csv").write_text("id\n" + "\n".join(
    f"E{i:02d}" for i in range(1, 7)) + "\n")
(tmp / "s3.csv").write_text("id\n" + "\n".join(
    f"E{i:02d}" for i in range(1, 4)) + "\n")
jcfg = {
    "name": "join unit test",
    "loader": "funnel_join",
    "stages": [{"name": "A"}, {"name": "B"}, {"name": "C"}],
    "join": {"stages": [
        {"path": str(tmp / "e.csv"), "key": "id"},
        {"path": str(tmp / "s2.csv"), "key": "id"},
        {"path": str(tmp / "s3.csv"), "key": "id"},
    ]},
    "slice_dims": ["seg"], "min_volume_for_flag": 100,
    "underperform_ratio": 0.7, "outperform_ratio": 1.3,
    "unknown_markers": ["unknown", "", "n/a", "na", "none"],
}
jdf = loader.load(jcfg)
jfs = findings_by_title(audit.run_audit(jdf, jcfg))
check("join overall rate",
      jfs["Overall funnel: A -> C"].evidence["conversion_rate"], 0.3)
check("join A->B rate",
      jfs["Stage conversion: A -> B"].evidence["conversion_rate"], 0.6)
check("join B->C rate",
      jfs["Stage conversion: B -> C"].evidence["conversion_rate"], 0.5)
check("join biggest leak",
      jfs["Biggest leak: A -> B"].evidence["lost"], 4)

# --- 3. Regressions --------------------------------------------------------
print("== regressions (known values) ==")
for name, cfg_file, entrants, converted in [
        ("olist", "olist_config.json", 8000, 842),
        ("retail", "retail_config.json", 25900, 22064),
        ("course", "course_config.json", 22018, 12329)]:
    c = json.loads((ROOT / cfg_file).read_text())
    d = loader.load(c)
    f = findings_by_title(audit.run_audit(d, c))
    ovf = [v for k, v in f.items() if k.startswith("Overall funnel")][0]
    ev = ovf.evidence
    check(f"{name} entrants", ev["entrants"], entrants)
    check(f"{name} converted", ev["converted"], converted)

print()
if failures:
    print(f"{len(failures)} FAILURES: {failures}")
    sys.exit(1)
print("ALL CHECKS PASSED")
