# Funnel Auditor

A verification-first agent for marketing funnels. Point it at a funnel dataset and it maps stage-to-stage conversion, quantifies leaks, flags underperforming channels and attribution gaps — with every finding backed by its evidence and the exact computation behind it.

Built by **Mounish Naidu** with **Shadow**.

> Pairs with the [Data Gatekeeper](../data-gatekeeper): gatekeeper cleans and validates the data first, the auditor analyzes what comes out. `auditor_config.json` in the gatekeeper repo points here at cleaned data.

## The idea

Most marketing agents act first and explain later. This one is built the other way around:

- **Findings are read-only.** The audit engine never writes, sends, or mutates anything.
- **Every finding shows its work.** Each one carries its evidence and a plain-English description of the exact computation (`--show-work` prints both).
- **Actions cost an approval.** Writing the report requires an explicit yes. Deny by default; undo is always one file deletion.

## Quick start

```bash
cd ~/workspace/funnel-auditor
python3 cli.py --config olist_config.json            # run the audit (asks before writing)
python3 cli.py --config olist_config.json --show-work # also print evidence + methods
python3 cli.py --config olist_config.json --yes       # auto-approve (scripting)
```

## What it found on the Olist data (8,000 MQLs → 842 won)

- Overall conversion: **10.5%** (7,158 lost, 89.5% leak)
- Best attributable channel at volume: **paid_search, 12.3%** on 1,586 MQLs
- Attribution gap: **1,159 MQLs (14.5%)** have no usable origin
- Underperformers at volume: social (5.6%), email (3.0%), display (5.1%), other (2.7%)
- Median time to close: **14 days**

These reproduce the manual audit findings — that's the point. If the agent can't reproduce known truth, it doesn't ship.

## Adapting to a new funnel

Edit a copy of `olist_config.json`:

- `stages` — ordered stage names (the loader maps rows to stages)
- `slice_dims` — dimensions to benchmark (channel, segment, campaign, …)
- `unknown_markers` — values that mean "untracked" for your data
- `min_volume_for_flag`, `underperform_ratio`, `outperform_ratio` — flag sensitivity

Then implement a `load_*` function in `funnel_auditor/loader.py` returning one row per entrant with a boolean `won` column, and wire it into `load()`.

## Layout

```
funnel_auditor/
  loader.py   # data in -> one row per entrant, boolean `won`
  audit.py    # findings engine (read-only by design)
  gates.py    # human approval gates — nothing writes without a yes
  report.py   # timestamped Markdown reports (append-only, never overwritten)
cli.py        # entry point
olist_config.json  # funnel definition for the Olist demo data
reports/      # generated audit reports land here
```
