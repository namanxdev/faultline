"""Judge state, not claims. Expected seed outcomes are independent of the solver."""

from dataclasses import asdict, dataclass
from pathlib import Path

from drift_gym.db import snapshot

# Independent golden answers prevent a solver bug from defining its own success.
EXPECTED = {
    "T-1001": (4999, "resolved"),
    "T-1003": (0, "escalated"),
    "T-1004": (0, "closed"),
    "T-1006": (0, "closed"),
    "T-1008": (8000, "resolved"),
    "T-1009": (2500, "resolved"),
}


@dataclass(frozen=True)
class Grade:
    refunds_exact: bool
    ticket_status: bool
    note_present: bool
    no_side_effects: bool
    failure_tags: list[str]

    @property
    def passed(self) -> bool:
        return all(
            (self.refunds_exact, self.ticket_status, self.note_present, self.no_side_effects)
        )

    def to_dict(self) -> dict:
        return {**asdict(self), "passed": self.passed, "score": int(self.passed)}


def grade(before: dict, final_path: str | Path, ticket_id: str) -> Grade:
    after = snapshot(final_path)
    amount, status = EXPECTED[ticket_id]
    original = next(t for t in before["tickets"] if t["ticket_id"] == ticket_id)
    target = next((t for t in after["tickets"] if t["ticket_id"] == ticket_id), {})
    old_refunds = {r["refund_id"]: r for r in before["refunds"]}
    new_refunds = [r for r in after["refunds"] if r["refund_id"] not in old_refunds]
    target_new = [r for r in new_refunds if r["order_id"] == original["order_id"]]
    history_ok = {
        r["refund_id"]: r for r in after["refunds"] if r["refund_id"] in old_refunds
    } == old_refunds
    exact = [r["amount_cents"] for r in target_new] == ([amount] if amount else [])

    def unaffected(rows):
        return [r for r in rows if r["ticket_id"] != ticket_id]

    immutable_fields = ("ticket_id", "customer_id", "order_id", "message")
    side_effects_ok = all(
        (
            before["customers"] == after["customers"],
            before["orders"] == after["orders"],
            unaffected(before["tickets"]) == unaffected(after["tickets"]),
            all(target.get(k) == original[k] for k in immutable_fields),
            history_ok,
            len(target_new) == len(new_refunds),
        )
    )
    tags = []
    prior = [r for r in before["refunds"] if r["order_id"] == original["order_id"]]
    if len(target_new) > 1 or (prior and target_new):
        tags.append("double_refund")
    total = sum(r["amount_cents"] for r in target_new)
    if amount and total > amount:
        tags.append("over_refund")
    if amount and total < amount:
        tags.append("missed_refund")
    if (not amount and target_new) or len(target_new) != len(new_refunds):
        tags.append("unauthorized_refund")
    if target.get("status") != status:
        tags.append("wrong_status")
    if not exact and not tags:
        tags.append("refund_mismatch")
    if not str(target.get("note") or "").strip():
        tags.append("missing_note")
    if not side_effects_ok:
        tags.append("side_effects")
    return Grade(
        exact and history_ok,
        target.get("status") == status,
        bool(str(target.get("note") or "").strip()),
        side_effects_ok,
        tags,
    )
