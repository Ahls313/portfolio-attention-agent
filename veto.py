"""
Veto Gates
----------
Even when all 3 confirming signals agree (attention score, early-signal
divergence, debate direction), there are still concrete, non-statistical
reasons to hold: you already acted on this symbol recently, you're already
overexposed to it, or the order book is too thin to fill safely.

This module implements those as small, independent, testable veto
functions. Each one returns (blocked: bool, reason: str | None). The
aggregator `evaluate_vetoes` runs all configured vetoes and returns
whether the action is allowed plus the list of reasons it wasn't, if any.

None of these vetoes require a live orderbook feed or portfolio service to
exist for the demo — they're written to work off plain dicts so they're
easy to test and easy to wire into orchestrator.py without new
dependencies.
"""

from datetime import datetime, timezone
from typing import Optional


def cooldown_veto(symbol: str, last_action_ts: Optional[str], cooldown_minutes: float) -> tuple:
    """
    Blocks action if the agent already acted on this symbol within the
    cooldown window. Prevents rapid-fire repeat trades off the same
    underlying move, which would just be re-reacting to the same event.

    last_action_ts: ISO8601 timestamp of the last action on this symbol,
                     or None if it has never acted on this symbol before.
    """
    if last_action_ts is None:
        return (False, None)

    last = datetime.fromisoformat(last_action_ts)
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    minutes_elapsed = (now - last).total_seconds() / 60.0

    if minutes_elapsed < cooldown_minutes:
        remaining = cooldown_minutes - minutes_elapsed
        return (True, f"cooldown active for {symbol}: {remaining:.0f} more minutes "
                       f"before another action is allowed")
    return (False, None)


def exposure_veto(symbol: str, portfolio_state: dict, exposure_limits: dict) -> tuple:
    """
    Blocks action if acting would push this symbol's share of the
    portfolio above its configured limit.

    portfolio_state: {"total_value_usdt": float, "positions": {"BTC": 120.0, ...}}
    exposure_limits: {"BTC": 0.30, "ETH": 0.30, "default": 0.20}  (max fraction of
                      total portfolio value allowed in one symbol)
    """
    total = portfolio_state.get("total_value_usdt", 0.0)
    if total <= 0:
        return (False, None)

    current_position = portfolio_state.get("positions", {}).get(symbol, 0.0)
    current_fraction = current_position / total
    limit = exposure_limits.get(symbol, exposure_limits.get("default", 0.20))

    if current_fraction >= limit:
        return (True, f"{symbol} already at {current_fraction:.0%} of portfolio, "
                       f"at or above the {limit:.0%} limit")
    return (False, None)


def liquidity_veto(symbol: str, orderbook_snapshot: dict, min_depth_usdt: float) -> tuple:
    """
    Blocks action if there isn't enough visible depth to fill the intended
    size without excessive slippage.

    orderbook_snapshot: {"bid_depth_usdt": float, "ask_depth_usdt": float}
    """
    bid_depth = orderbook_snapshot.get("bid_depth_usdt", 0.0)
    ask_depth = orderbook_snapshot.get("ask_depth_usdt", 0.0)
    shallow_side = min(bid_depth, ask_depth)

    if shallow_side < min_depth_usdt:
        return (True, f"{symbol} orderbook too thin: ${shallow_side:,.0f} depth "
                       f"available, ${min_depth_usdt:,.0f} required")
    return (False, None)


def notional_veto(symbol: str, order_notional_usdt: float, max_notional_usdt: float) -> tuple:
    """
    Blocks action when the intended order notional exceeds the hard
    pre-trade dollar cap.

    order_notional_usdt: intended order value in USDT.
    max_notional_usdt: maximum allowed value for a single order.
    """
    try:
        notional = float(order_notional_usdt)
        cap = float(max_notional_usdt)
    except (TypeError, ValueError):
        return (True, f"{symbol} invalid order notional/cap: "
                       f"notional={order_notional_usdt!r}, cap={max_notional_usdt!r}")

    if notional < 0:
        return (True, f"{symbol} invalid order notional: ${notional:,.2f} "
                       "cannot be negative")
    if cap < 0:
        return (True, f"{symbol} invalid notional cap: ${cap:,.2f} "
                       "cannot be negative")

    if notional > cap:
        return (True, f"{symbol} order notional ${notional:,.2f} exceeds "
                       f"hard ${cap:,.2f} pre-trade limit")
    return (False, None)


def evidence_veto(signal_context: dict, required_sources: list) -> tuple:
    """
    Blocks action if the signal isn't backed by all the evidence sources
    the pipeline expects (e.g. it should never act on an attention score
    alone without a news-correlation check having actually run).

    signal_context: expected to have an "evidence_refs" list of source
                     names that were actually used to build this decision.
    """
    have = set(signal_context.get("evidence_refs", []))
    missing = [s for s in required_sources if s not in have]
    if missing:
        return (True, f"missing required evidence: {', '.join(missing)}")
    return (False, None)


def evaluate_vetoes(signal_context: dict, veto_config: dict) -> tuple:
    """
    Runs every veto configured in veto_config against signal_context and
    returns (allowed: bool, veto_reasons: list[str]).

    veto_config selectively enables vetoes by including their keys:
    {
        "cooldown": {"last_action_ts": ..., "cooldown_minutes": 60},
        "exposure": {"portfolio_state": {...}, "exposure_limits": {...}},
        "liquidity": {"orderbook_snapshot": {...}, "min_depth_usdt": 5000},
        "notional": {"order_notional_usdt": 25, "max_notional_usdt": 100},
        "evidence": {"required_sources": ["news", "klines"]},
    }
    Any key omitted simply skips that veto rather than failing.
    """
    symbol = signal_context.get("symbol", "UNKNOWN")
    reasons = []

    if "cooldown" in veto_config:
        cfg = veto_config["cooldown"]
        blocked, reason = cooldown_veto(symbol, cfg.get("last_action_ts"),
                                         cfg.get("cooldown_minutes", 60))
        if blocked:
            reasons.append(reason)

    if "exposure" in veto_config:
        cfg = veto_config["exposure"]
        blocked, reason = exposure_veto(symbol, cfg.get("portfolio_state", {}),
                                         cfg.get("exposure_limits", {}))
        if blocked:
            reasons.append(reason)

    if "liquidity" in veto_config:
        cfg = veto_config["liquidity"]
        blocked, reason = liquidity_veto(symbol, cfg.get("orderbook_snapshot", {}),
                                          cfg.get("min_depth_usdt", 0))
        if blocked:
            reasons.append(reason)

    if "notional" in veto_config:
        cfg = veto_config["notional"]
        blocked, reason = notional_veto(
            symbol,
            cfg.get("order_notional_usdt"),
            cfg.get("max_notional_usdt", 0),
        )
        if blocked:
            reasons.append(reason)

    if "evidence" in veto_config:
        cfg = veto_config["evidence"]
        blocked, reason = evidence_veto(signal_context, cfg.get("required_sources", []))
        if blocked:
            reasons.append(reason)

    allowed = len(reasons) == 0
    return (allowed, reasons)


if __name__ == "__main__":
    # Smoke tests / usage examples

    # cooldown: should block, action was 5 min ago with a 60 min cooldown
    recent = datetime.now(timezone.utc).isoformat()
    blocked, reason = cooldown_veto("BTC", recent, cooldown_minutes=60)
    assert blocked, "expected cooldown veto to trigger"
    print("cooldown_veto:", reason)

    # cooldown: should pass, no prior action
    blocked, reason = cooldown_veto("BTC", None, cooldown_minutes=60)
    assert not blocked
    print("cooldown_veto (no history): passed")

    # exposure: should block, already at 35% with a 30% limit
    blocked, reason = exposure_veto(
        "BTC",
        {"total_value_usdt": 1000.0, "positions": {"BTC": 350.0}},
        {"BTC": 0.30, "default": 0.20},
    )
    assert blocked
    print("exposure_veto:", reason)

    # liquidity: should block, thin book
    blocked, reason = liquidity_veto(
        "DOGE", {"bid_depth_usdt": 200.0, "ask_depth_usdt": 5000.0}, min_depth_usdt=1000.0
    )
    assert blocked
    print("liquidity_veto:", reason)

    # notional: should block an order above the hard pre-trade cap
    blocked, reason = notional_veto("BTC", 125.0, max_notional_usdt=100.0)
    assert blocked
    print("notional_veto:", reason)

    # notional: should allow an order at the cap
    blocked, reason = notional_veto("BTC", 100.0, max_notional_usdt=100.0)
    assert not blocked
    print("notional_veto (at cap): passed")

    # aggregator: exposure should block even though cooldown and liquidity pass
    signal_context = {"symbol": "BTC", "evidence_refs": ["klines", "news", "ticker24hr"]}
    veto_config = {
        "cooldown": {"last_action_ts": None, "cooldown_minutes": 60},
        "exposure": {
            "portfolio_state": {"total_value_usdt": 1000.0, "positions": {"BTC": 350.0}},
            "exposure_limits": {"BTC": 0.30, "default": 0.20},
        },
        "liquidity": {
            "orderbook_snapshot": {"bid_depth_usdt": 5000.0, "ask_depth_usdt": 5000.0},
            "min_depth_usdt": 1000.0,
        },
        "evidence": {"required_sources": ["klines", "news"]},
    }
    allowed, reasons = evaluate_vetoes(signal_context, veto_config)
    assert not allowed and len(reasons) == 1
    print("evaluate_vetoes (mixed):", allowed, reasons)

    # aggregator: notional cap should block an otherwise clean action
    veto_config_notional = {
        "notional": {"order_notional_usdt": 101.0, "max_notional_usdt": 100.0},
    }
    allowed, reasons = evaluate_vetoes({"symbol": "BTC"}, veto_config_notional)
    assert not allowed and len(reasons) == 1
    print("evaluate_vetoes (notional cap):", allowed, reasons)

    # aggregator: everything clean, should allow
    veto_config_clean = {
        "cooldown": {"last_action_ts": None, "cooldown_minutes": 60},
        "exposure": {
            "portfolio_state": {"total_value_usdt": 1000.0, "positions": {"BTC": 100.0}},
            "exposure_limits": {"BTC": 0.30, "default": 0.20},
        },
    }
    allowed, reasons = evaluate_vetoes(signal_context, veto_config_clean)
    assert allowed and reasons == []
    print("evaluate_vetoes (clean):", allowed, reasons)

    print("\nveto.py: all smoke tests passed.")
