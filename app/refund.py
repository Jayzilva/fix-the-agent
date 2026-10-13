"""Refund eligibility: one SQL query and a date subtraction. No model needed."""
import sqlite3
from dataclasses import asdict, dataclass
from datetime import date

from app.config import DB_PATH

# Plan id -> refund window in days. Free has no charges; Enterprise is handled by the account manager.
REFUND_WINDOWS = {"starter_monthly": 14, "pro_monthly": 14, "pro_annual": 30}


@dataclass(frozen=True)
class RefundDecision:
    customer_id: str
    found: bool
    plan_id: str | None
    plan_name: str | None
    eligible: bool
    last_charge: str | None
    days_since_charge: int | None
    window_days: int

    def as_dict(self):
        return asdict(self)


def check_refund(customer_id, as_of):
    """Eligible if the latest successful charge on or before `as_of` is within the plan's window."""
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        row = con.execute(
            "SELECT p.id, p.name, "
            "  (SELECT MAX(charged_at) FROM charges ch "
            "   WHERE ch.customer_id = c.id AND ch.status = 'succeeded' AND ch.charged_at <= ?) "
            "FROM customers c JOIN plans p ON p.id = c.plan_id WHERE c.id = ?",
            (str(as_of), customer_id),
        ).fetchone()
    finally:
        con.close()
    if row is None:
        return RefundDecision(customer_id, False, None, None, False, None, None, 0)
    plan_id, plan_name, last_charge = row
    window = REFUND_WINDOWS.get(plan_id, 0)
    days = (date.fromisoformat(str(as_of)) - date.fromisoformat(last_charge)).days if last_charge else None
    eligible = bool(window and days is not None and 0 <= days <= window)
    return RefundDecision(customer_id, True, plan_id, plan_name, eligible, last_charge, days, window)
