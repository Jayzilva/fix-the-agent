import json
import random
import sqlite3
from datetime import date

from claude_agent_sdk import tool

from app.config import DB_PATH

random.seed(42)

REFUND_WINDOWS = {"monthly": 14, "annual": 30}


def _text(value):
    return {"content": [{"type": "text", "text": value}]}


def _rows(sql, params=()):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(sql, params).fetchall()]
    finally:
        con.close()


@tool("get_customer", "Get customer info.", {"type": "object", "properties": {"customer_id": {}}})
async def get_customer(args):
    rows = _rows(
        "SELECT c.*, p.name AS plan_name, p.billing_period, p.price_usd "
        "FROM customers c JOIN plans p ON p.id = c.plan_id"
    )
    return _text(json.dumps(rows))


@tool("get_plan", "Get plan.", {"type": "object", "properties": {"plan_id": {}}})
async def get_plan(args):
    return _text(json.dumps(_rows("SELECT * FROM plans WHERE id = ?", (args.get("plan_id"),)), indent=2))


@tool("get_charges", "Get charges.", {"type": "object", "properties": {"customer_id": {}}})
async def get_charges(args):
    rows = _rows(
        "SELECT * FROM charges WHERE customer_id = ? ORDER BY charged_at DESC", (args.get("customer_id"),)
    )
    return _text(json.dumps(rows, indent=2))


@tool("list_customers", "List customers.", {"type": "object", "properties": {}})
async def list_customers(args):
    return _text(json.dumps(_rows("SELECT id, name, email, company FROM customers"), indent=2))


@tool("check_refund", "Check refund.", {"type": "object", "properties": {"customer_id": {}, "as_of": {}}})
async def check_refund(args):
    if random.random() < 0.3:
        return _text("Error")
    customer = _rows(
        "SELECT c.id, p.billing_period FROM customers c JOIN plans p ON p.id = c.plan_id WHERE c.id = ?",
        (args.get("customer_id"),),
    )
    if not customer:
        return _text("Error")
    period = customer[0]["billing_period"]
    charges = _rows(
        "SELECT charged_at FROM charges WHERE customer_id = ? AND status = 'succeeded' AND charged_at <= ? "
        "ORDER BY charged_at DESC LIMIT 1",
        (args.get("customer_id"), args.get("as_of")),
    )
    window = REFUND_WINDOWS.get(period, 0)
    plan = _rows("SELECT p.id FROM plans p JOIN customers c ON c.plan_id = p.id WHERE c.id = ?",
                 (args.get("customer_id"),))[0]["id"]
    if plan.startswith("enterprise") or not charges or not window:
        return _text(json.dumps({"customer_id": args.get("customer_id"), "eligible": False}))
    days = (date.fromisoformat(str(args.get("as_of"))) - date.fromisoformat(charges[0]["charged_at"])).days
    return _text(json.dumps({"customer_id": args.get("customer_id"), "eligible": days <= window,
                             "days_since_charge": days, "window_days": window}))


CRM_TOOLS = [get_customer, get_plan, get_charges, check_refund, list_customers]
