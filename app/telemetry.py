"""Per-ticket, per-step telemetry: tokens, cost, calls, turns, tool calls and latency.

Every model call and every pipeline step is written as one JSON line to
`<telemetry.dir>/<run_id>.jsonl` - one file per process, so parallel workers never interleave.
`scripts/telemetry_report.py` turns those files into per-ticket / per-step tables and an HTML dashboard.

Context (ticket id, step) travels in contextvars, so concurrent tickets are attributed
correctly. Optionally mirrors spans to OpenTelemetry (GenAI semantic conventions).
"""
import contextlib
import contextvars
import json
import logging
import threading
import time
import uuid
from collections import defaultdict

import yaml

from app.config import ROOT, SETTINGS

log = logging.getLogger("ticketpilot")

CFG = SETTINGS["telemetry"]
PRICES = yaml.safe_load((ROOT / CFG["prices"]).read_text(encoding="utf-8"))["models"]
RUN_ID = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]

_ticket = contextvars.ContextVar("ticket_id", default=None)
_step = contextvars.ContextVar("step", default=None)
_lock = threading.Lock()
_totals = defaultdict(float)  # "run" and per-ticket USD
_file = None

try:  # optional
    if CFG.get("otel"):
        from opentelemetry import trace

        _tracer = trace.get_tracer("ticketpilot")
    else:
        _tracer = None
except ImportError:
    _tracer = None


class BudgetExceeded(RuntimeError):
    pass


def _write(record):
    global _file
    if not CFG["enabled"]:
        return
    with _lock:
        if _file is None:
            directory = ROOT / CFG["dir"]
            directory.mkdir(parents=True, exist_ok=True)
            _file = open(directory / f"{RUN_ID}.jsonl", "a", encoding="utf-8")
        _file.write(json.dumps(record, default=str) + "\n")
        _file.flush()


def price(model, usage):
    """USD for one call from a usage dict (input/cache_write/cache_read/output tokens)."""
    p = PRICES.get(model)
    if p is None:
        log.warning("no price for model %s; cost recorded as 0", model)
        return 0.0
    return (
        usage.get("input_tokens", 0) * p["input"]
        + usage.get("cache_creation_input_tokens", 0) * p["cache_write"]
        + usage.get("cache_read_input_tokens", 0) * p["cache_read"]
        + usage.get("output_tokens", 0) * p["output"]
    ) / 1_000_000


def check_budget():
    """Raise before a call if the run or the current ticket is over budget."""
    b = SETTINGS["budget"]
    ticket = _ticket.get()
    if b["max_usd_per_run"] and _totals["__run__"] >= b["max_usd_per_run"]:
        raise BudgetExceeded(f"run budget ${b['max_usd_per_run']} reached (${_totals['__run__']:.4f})")
    if ticket and b["max_usd_per_ticket"] and _totals[ticket] >= b["max_usd_per_ticket"]:
        raise BudgetExceeded(f"ticket {ticket} budget ${b['max_usd_per_ticket']} reached")


def _add_cost(usd):
    with _lock:
        _totals["__run__"] += usd
        if _ticket.get():
            _totals[_ticket.get()] += usd


def ticket_cost(ticket_id):
    return _totals[ticket_id]


def run_cost():
    return _totals["__run__"]


@contextlib.contextmanager
def ticket(ticket_id):
    token = _ticket.set(ticket_id)
    started = time.perf_counter()
    status = "ok"
    try:
        yield
    except BaseException as e:
        status = f"error: {type(e).__name__}"
        raise
    finally:
        _write({"type": "ticket", "run_id": RUN_ID, "ticket_id": ticket_id, "status": status,
                "latency_s": round(time.perf_counter() - started, 3), "cost_usd": round(_totals[ticket_id], 6),
                "ts": time.time()})
        _ticket.reset(token)


@contextlib.contextmanager
def step(name, **attrs):
    """A pipeline step span (model or no model). Nested model calls inherit the step name."""
    token = _step.set(name)
    started = time.perf_counter()
    span = _tracer.start_as_current_span(f"ticketpilot.{name}") if _tracer else contextlib.nullcontext()
    status = "ok"
    with span as otel_span:
        if otel_span is not None:
            otel_span.set_attribute("ticketpilot.ticket_id", _ticket.get() or "")
        try:
            yield attrs
        except BaseException as e:
            status = f"error: {type(e).__name__}: {e}"[:300]
            raise
        finally:
            _write({"type": "step", "run_id": RUN_ID, "ticket_id": _ticket.get(), "step": name, "status": status,
                    "latency_s": round(time.perf_counter() - started, 3), **attrs, "ts": time.time()})
            _step.reset(token)


def _usage_dict(usage):
    if usage is None:
        return {}
    if hasattr(usage, "model_dump"):
        usage = usage.model_dump()
    return {k: (usage.get(k) or 0) for k in
            ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")}


def record_llm_call(surface, model, usage, latency_s, *, request_id=None, stop_reason=None, extra=None):
    """One Messages API call (surface='messages')."""
    u = _usage_dict(usage)
    usd = price(model, u)
    _add_cost(usd)
    _write({"type": "llm_call", "run_id": RUN_ID, "ticket_id": _ticket.get(), "step": _step.get(),
            "surface": surface, "model": model, **u, "cost_usd": round(usd, 6), "latency_s": round(latency_s, 3),
            "request_id": request_id, "stop_reason": stop_reason, **(extra or {}), "ts": time.time()})
    if _tracer:
        span = trace.get_current_span()
        span.set_attribute("gen_ai.request.model", model)
        span.set_attribute("gen_ai.usage.input_tokens", u.get("input_tokens", 0))
        span.set_attribute("gen_ai.usage.output_tokens", u.get("output_tokens", 0))
        span.set_attribute("ticketpilot.cost_usd", usd)


def record_agent_run(surface, model, *, cost_usd, usage, turns, tool_calls, latency_s, extra=None):
    """One Agent SDK query() or Managed Agents session.

    Agent SDK: priced from usage with our price table (the bundled CLI may not know a new model's
    price); its own total_cost_usd is kept as reported_cost_usd. Managed Agents: the session's
    list_cost, which also includes runtime.
    """
    u = _usage_dict(usage)
    reported = cost_usd or 0.0
    if surface == "agent_sdk" and model in PRICES:
        cost_usd = price(model, u)
    _add_cost(cost_usd or 0.0)
    _write({"type": "agent_run", "run_id": RUN_ID, "ticket_id": _ticket.get(), "step": _step.get(),
            "surface": surface, "model": model, **u, "cost_usd": round(cost_usd or 0.0, 6),
            "reported_cost_usd": round(reported, 6), "turns": turns,
            "tool_calls": tool_calls, "latency_s": round(latency_s, 3), **(extra or {}), "ts": time.time()})


def record_tool_call(name, ok, latency_s):
    _write({"type": "tool_call", "run_id": RUN_ID, "ticket_id": _ticket.get(), "step": _step.get(),
            "tool": name, "ok": ok, "latency_s": round(latency_s, 4), "ts": time.time()})
