"""Render findings as a Markdown audit report. Called only after approval."""
from datetime import datetime
from pathlib import Path


def render(findings, funnel_name: str) -> str:
    lines = [
        f"# Funnel Audit — {funnel_name}",
        f"_Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}_",
        "",
    ]
    for f in findings:
        badge = {"critical": "🔴", "warning": "🟡", "info": "🟢"}[f.severity]
        lines += [f"## {badge} {f.title}", "", f.summary, ""]
        if f.evidence:
            lines.append("| metric | value |")
            lines.append("|---|---|")
            for k, v in f.evidence.items():
                lines.append(f"| {k} | {v} |")
            lines.append("")
    lines += ["---", "_Every finding above ships with its evidence. "
                     "Methods: see `--show-work` output._"]
    return "\n".join(lines)


def write_report(markdown: str, reports_dir: str = "reports") -> Path:
    # Timestamped filename: reports are append-only, never overwritten.
    # That is the reversibility story — deleting a report undoes the action.
    d = Path(reports_dir)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"funnel_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    path.write_text(markdown)
    return path
