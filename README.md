# Funnel Auditor

A verification-first agent for marketing funnels. A funnel is the steps people go through from first contact to final action — for example, seeing an ad, signing up, then buying. This tool maps how many people make it through each step, where they drop off, and which channels perform best — with every finding backed by its evidence and the exact computation behind it.

Built by **Mounish Naidu** with **Shadow**.

> Pairs with the [Data Gatekeeper](https://github.com/mounishnaidu/data-gatekeeper): the gatekeeper cleans and validates the data first, the auditor analyzes what comes out. The gatekeeper's `auditor_config.json` points here at cleaned data.

## Features

- **Stage conversion** — entry, conversion, and leak at every stage of the funnel
- **Leak quantification** — the biggest absolute leak, named, not just the worst rate
- **Channel and segment benchmarks** — best and worst performers at volume, with underperformer flags
- **Attribution-gap flag** — how many people arrived without us knowing where they came from, so every breakdown built on that data is honestly understated
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
- `slice_dims` — ways to break the numbers down (by channel, by segment, by campaign, …)
- `unknown_markers` — values that mean "untracked" for your data
- `min_volume_for_flag`, `underperform_ratio`, `outperform_ratio` — the minimum volume and thresholds that decide when something gets flagged
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

- **Python** — the programming language the tool is written in. It runs on any computer, with no server to set up. An agent that needs infrastructure before it runs is an agent that doesn't get used.
- **pandas** — a Python tool for working with tables of data. The funnel math is counting rows, grouping them (for example, by channel), linking two tables together, and subtracting dates. That's exactly what pandas is built for, so no custom engine was needed.
- **JSON configs** — plain-text settings files you can edit in any text editor. A new funnel means a new settings file, not new code. That's what makes the three-dataset proof possible: the data source, stages, breakdowns, and thresholds all live in the settings file.
- **Markdown reports** — simple text files, dated, never overwritten. You can read them anywhere, no special software needed. A report you can't read without a dashboard is a report nobody verifies.
- **Command-line tool, no web server** — you run it by typing a command. No website to deploy, no account to create. It runs on any machine, on any dataset.

## The idea

Most marketing agents act first and explain later. This one is built the other way around:

- **Findings are read-only.** The audit engine never writes, sends, or mutates anything.
- **Unknown is a tracking problem, not a channel.** When we don't know where someone came from, that's a gap in tracking — not a marketing channel to invest in. Those cases are counted in the attribution gap, never presented as an "opportunity."
- **Empty doesn't always mean broken.** Some columns are empty on purpose — a lost deal has no closing date because it never closed. The auditor doesn't treat that as underperformance.
