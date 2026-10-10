"""Human approval gates. The one rule of this module:

Nothing leaves this process — no file written, no data exported, nothing sent
anywhere — without the human explicitly saying so. Findings are free to read;
actions cost an approval.
"""
from dataclasses import dataclass


@dataclass
class ProposedAction:
    name: str
    description: str
    reversible: str   # what happens if the human wants it undone


def request_approval(action: ProposedAction, auto_approve: bool = False) -> bool:
    """Ask the human. Returns True only on an explicit yes."""
    print(f"\n[ACTION] {action.name}")
    print(f"  What: {action.description}")
    print(f"  Undo: {action.reversible}")
    if auto_approve:
        print("  (--yes passed: auto-approved)")
        return True
    answer = input("  Approve? [y/N] ").strip().lower()
    approved = answer in ("y", "yes")
    print(f"  -> {'APPROVED' if approved else 'DENIED — nothing was done'}")
    return approved
