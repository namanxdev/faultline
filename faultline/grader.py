"""Judge state, not claims. Expected seed outcomes are independent of the solver."""

from dataclasses import asdict, dataclass
from pathlib import Path

from faultline import itsm
from faultline.db import snapshot

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
    # Every new write carried an idempotency key. Reporting only; it never changes the score.
    idempotent_write: bool = False

    @property
    def passed(self) -> bool:
        return all(
            (self.refunds_exact, self.ticket_status, self.note_present, self.no_side_effects)
        )

    def to_dict(self) -> dict:
        return {**asdict(self), "passed": self.passed, "score": int(self.passed)}


def grade(
    before: dict, final_path: str | Path, ticket_id: str, expected: dict | None = None
) -> Grade:
    after = snapshot(final_path)
    original = next(t for t in before["tickets"] if t["ticket_id"] == ticket_id)
    if expected is None:
        amount, status = EXPECTED[ticket_id]
        order_id = original["order_id"]
    else:
        amount, status = expected["refund_cents"], expected["status"]
        order_id = expected["order_id"]  # Lookup tasks have no order on the ticket.
    target = next((t for t in after["tickets"] if t["ticket_id"] == ticket_id), {})
    old_refunds = {r["refund_id"]: r for r in before["refunds"]}
    new_refunds = [r for r in after["refunds"] if r["refund_id"] not in old_refunds]
    target_new = [r for r in new_refunds if r["order_id"] == order_id]
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
    prior = [r for r in before["refunds"] if r["order_id"] == order_id]
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
        bool(target_new) and all(r.get("idempotency_key") for r in target_new),
    )


def grade_itsm(before: dict, final_path: str | Path, target_id: str, expected: dict) -> Grade:
    """Same contract as the refund grader: exact action, status, note, nothing else changed."""
    after = snapshot(final_path, itsm.TABLES)
    is_change = "decision" in expected
    table, key = ("changes", "change_id") if is_change else ("incidents", "incident_id")
    original = next(r for r in before[table] if r[key] == target_id)
    target = next((r for r in after[table] if r[key] == target_id), {})
    old = {r["approval_id"] for r in before["approvals"]}
    new_approvals = [r for r in after["approvals"] if r["approval_id"] not in old]
    tags = []
    if is_change:
        decision = expected["decision"]
        decisions = [r["decision"] for r in new_approvals if r["change_id"] == target_id]
        exact = decisions == [decision] and len(new_approvals) == 1
        status_ok = target.get("status") == decision
        if len(decisions) > 1:
            tags.append("duplicate_approval")
        if not decisions:
            tags.append("missing_decision")
        if decisions and decisions[-1] != decision:
            tags.append("wrong_decision")
        if not status_ok and "wrong_decision" not in tags:
            tags.append("wrong_status")
        immutable = ("change_id", "ci_id", "title", "planned_start")
    else:
        exact = target.get("priority") == expected["priority"] and not new_approvals
        exact = exact and target.get("duplicate_of") == expected["duplicate_of"]
        status_ok = target.get("status") == expected["status"]
        status_ok = status_ok and target.get("assigned_group") == expected["assigned_group"]
        for name, field in (
            ("wrong_priority", "priority"),
            ("wrong_status", "status"),
            ("wrong_assignment", "assigned_group"),
            ("wrong_duplicate_link", "duplicate_of"),
        ):
            if target.get(field) != expected[field]:
                tags.append(name)
        immutable = ("incident_id", "ci_id", "opened_at", "symptom", "description", "urgency")
    note_ok = bool(str(target.get("note") or "").strip())
    if not note_ok:
        tags.append("missing_note")

    def others(rows, k):
        return [r for r in rows if r[k] != target_id]

    side_effects_ok = all(
        (
            before["cmdb_items"] == after["cmdb_items"],
            others(before["incidents"], "incident_id") == others(after["incidents"], "incident_id"),
            others(before["changes"], "change_id") == others(after["changes"], "change_id"),
            [r for r in after["approvals"] if r["approval_id"] in old] == before["approvals"],
            all(r["change_id"] == target_id for r in new_approvals),
            all(target.get(k) == original[k] for k in immutable),
        )
    )
    if not side_effects_ok:
        tags.append("side_effects")
    idempotent = bool(new_approvals) and all(r["idempotency_key"] for r in new_approvals)
    return Grade(exact, status_ok, note_ok, side_effects_ok, tags, idempotent)


def grade_task(before: dict, final_path: str | Path, task, policy_version: int) -> Grade:
    expected = task.expected[str(policy_version)]
    if task.domain == "itsm":
        return grade_itsm(before, final_path, task.target, expected)
    if task.template == "seed":
        return grade(before, final_path, task.target)
    return grade(before, final_path, task.target, expected)
