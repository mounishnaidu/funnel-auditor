"""Funnel Auditor CLI.

    python cli.py --config olist_config.json            # run the audit
    python cli.py --config olist_config.json --show-work # also print methods
    python cli.py --config olist_config.json --yes       # auto-approve writes

Reading findings is always free. Writing the report requires approval.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from funnel_auditor import audit, loader
from funnel_auditor.gates import ProposedAction, request_approval
from funnel_auditor.report import render, write_report


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit a marketing funnel.")
    ap.add_argument("--config", required=True, help="Path to funnel config JSON")
    ap.add_argument("--show-work", action="store_true",
                    help="Print the exact computation behind every finding")
    ap.add_argument("--yes", action="store_true",
                    help="Auto-approve write actions (default: ask first)")
    args = ap.parse_args()

    config = json.loads(Path(args.config).read_text())
    print(f"Auditing: {config['name']}")
    df = loader.load(config)
    print(f"Loaded {len(df):,} funnel entrants.\n")

    findings = audit.run_audit(df, config)

    for f in findings:
        badge = {"critical": "🔴", "warning": "🟡", "info": "🟢"}[f.severity]
        print(f"{badge} {f.title}\n   {f.summary}")
        if args.show_work:
            print(f"   [evidence] {f.evidence}")
            print(f"   [method]   {f.how_computed}")
        print()

    action = ProposedAction(
        name="write_markdown_report",
        description="Save these findings as a timestamped Markdown report "
                    "under ./reports/.",
        reversible="Delete the report file — nothing else is touched.",
    )
    if request_approval(action, auto_approve=args.yes):
        path = write_report(render(findings, config["name"]))
        print(f"\nReport saved: {path}")
    else:
        print("\nNo report written. Findings above were read-only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
