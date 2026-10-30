# Funnel Auditor

A verification-first agent for marketing funnels. Point it at a funnel dataset and it maps stage-to-stage conversion, quantifies leaks, flags underperforming channels and attribution gaps — with every finding backed by its evidence and the exact computation behind it.

Built by **Mounish Naidu** with **Shadow**.

> Pairs with the [Data Gatekeeper](https://github.com/mounishnaidu/data-gatekeeper): the gatekeeper cleans and validates the data first, the auditor analyzes what comes out. The gatekeeper's `auditor_config.json` points here at cleaned data.

## Features

- **Stage conversion** — entry, conversion, and leak at every stage of the funnel
- **Leak quantification** — the biggest absolute leak, named, not just the worst rate
- **Channel and segment benchmarks** — best and worst performers at volume, with underperformer flags
- **Attribution-gap flag** — how much of the funnel has no usable origin, so every slice built on it is honestly understated
- **Velocity** — median time from entry to conversion, overall and per segment
- **Every finding shows its work** — evidence plus a plain-English description of the exact computation (`--show-work` prints both)
- **Actions cost an approval** — writing the report requires an explicit yes. Deny by default; undo is always one file deletion

## Prerequisites

- Python 3.10 or higher
- pandas 2.0 or higher

## Installation

```bash
git clone https://github.com/mounishnaidu/funnel-auditor
cd funnel-auditor
pip install -r requirements.txt
```

## Quick start

```bash
python3 cli.py --config olist_config.json            # run the audit (asks before writing)
python3 cli.py --config olist_config.json --show-work # also print evidence + methods
python3 cli.py --config olist_config.json --yes       # auto-approve (scripting)
```

## Adapting to a new funnel

No code changes. A new funnel is a new config file — that is the point, and it is proven below. Pick one of the three loaders:

| Loader | Funnel shape | Config needs |
|---|---|---|
| `funnel_join` | Two tables: entrants joined to conversions on any key | left/right table paths and key names |
| `status_funnel` | One table with a status column (enrolled/completed, sent/clicked) | table path, id column, status column, winning values; `exclude_values` drops censored rows (e.g. "In Progress") instead of counting them as lost |
| `invoice_funnel` | One table where conversion is "not cancelled" (invoice kept, order fulfilled) | table path, encoding |

Then set in the config:

- `stages` — ordered stage names
- `slice_dims` — dimensions to benchmark (channel, segment, campaign, …)
- `unknown_markers` — values that mean "untracked" for your data
- `min_volume_for_flag`, `underperform_ratio`, `outperform_ratio` — flag sensitivity
- `attribution_dim`, `best_dim`, `velocity` — optional, all config-driven

## Proven on three datasets, three funnel shapes

Config only, zero code changes each time:

- **Olist marketing funnel** (two-table join): 8,000 MQLs → 842 won = **10.5%**; paid_search best at **12.3%** on 1,586 MQLs; attribution gap **14.5%**; median **14 days** to close.
- **Online Retail invoices** (invoice-kept): 25,900 invoices → 22,064 kept = **85.2%**; Netherlands best country at **94.1%**; Germany lowest at 75.8% (a watch item, not flagged).
- **Online course enrollments** (status funnel): 22,018 resolved enrollments → 12,329 completed = **56.0%**; Advanced courses underperform at **36.3%**; Pinnacle Courses best platform at **65.2%**; median **19 days** to completion.

These reproduce known truth on data the agent had never seen — that is the test it has to pass before it ships.

## Project structure

```
funnel_auditor/
  loader.py   # data in -> one row per entrant, boolean `won` (three loaders, all config-driven)
  audit.py    # findings engine (read-only by design)
  gates.py    # human approval gates — nothing writes without a yes
  report.py   # timestamped Markdown reports (append-only, never overwritten)
cli.py              # entry point
olist_config.json   # two-table join funnel (Olist demo data)
retail_config.json  # invoice-kept funnel (Online Retail demo data)
course_config.json  # status funnel (course enrollment demo data)
reports/            # generated audit reports land here
```

## Technologies used — and why

- **Python** — readable, runs anywhere, no server to deploy. An agent that needs infrastructure before it runs is an agent that doesn't get used.
- **pandas** — the funnel math is groupby, merge, and date arithmetic, which is exactly what pandas is for. Slices are groupbys; joins are merges; velocity is date subtraction. No custom engine needed.
- **JSON configs** — a new funnel is a new config, not new code. This is what makes the three-dataset proof possible: the loader, stages, slices, and thresholds all live in the config.
- **Markdown reports** — timestamped, append-only, human-readable, and diffable. A report you can't read without a dashboard is a report nobody verifies.
- **CLI, no web server** — the auditor is a tool, not a service. It runs on any machine, on any dataset, with no deployment step.

## The idea

Most marketing agents act first and explain later. This one is built the other way around:

- **Findings are read-only.** The audit engine never writes, sends, or mutates anything.
- **Unknown is a tracking problem, not a channel.** Unusable origin values are excluded from investment advice and owned by the attribution-gap finding — never presented as an "opportunity."
- **Structural missingness is not a finding.** Columns blank by construction (deal-side fields for lost deals) are excluded from slice flags, not reported as underperformance.
