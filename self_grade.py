"""
Self-Grading
------------
The decision journal proves the agent held and explains why, at the moment
of the decision. It doesn't say whether holding turned out to be right.

This module closes that loop: given a past decision (symbol, the score/
conditions at the time) and a real subsequent price move for that same
symbol — pulled live from Binance's public ticker endpoint, no API key or
MCP auth required — it grades the decision after the fact.

The grading logic is intentionally simple and stated up front so it can't
be quietly adjusted to look better after the fact:
  - If the agent held AND the subsequent real move stayed under
    MOVE_THRESHOLD_PCT -> "HOLD CONFIRMED": there was nothing to catch.
  - If the agent held AND the subsequent real move exceeded
    MOVE_THRESHOLD_PCT -> "HOLD MISSED A MOVE": a real move happened that
    the hold, in hindsight, didn't act on. This is reported the same way
    a confirmed hold is — the point of this module is that both outcomes
    get shown, not just the flattering one.
  - If the agent acted, grading requires knowing the price at the moment
    of action plus the subsequent move; "ACT" grading follows the same
    threshold logic but in the profit/loss direction instead.

Run this directly (`python3 self_grade.py`) and it pulls live current
prices itself via urllib against Binance's public REST API
(api.binance.com/api/v3/ticker/24hr) — no dependencies, no auth, works
anywhere with internet access.
"""

import json
import urllib.request
from dataclasses import dataclass
from typing import List, Optional

MOVE_THRESHOLD_PCT = 3.0  # a subsequent move at or above this magnitude counts as "a real move happened"

BINANCE_PUBLIC_TICKER_URL = "https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}USDT"


def fetch_live_pct_change(symbol: str) -> Optional[float]:
    """
    Pulls the real, current 24hr priceChangePercent for `symbol` from
    Binance's public REST API. No API key needed -- this endpoint is
    public market data. Returns None if the request fails (e.g. no
    internet), so callers can fall back gracefully instead of crashing.
    """
    url = BINANCE_PUBLIC_TICKER_URL.format(symbol=symbol)
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        return float(data["priceChangePercent"])
    except Exception as e:
        print(f"  (couldn't fetch live price for {symbol}: {e})")
        return None


@dataclass
class PastDecision:
    symbol: str
    decision: str          # "act" or "no_act"
    score_at_decision: float
    move_at_decision_pct: float   # the % move that triggered/didn't trigger the score
    decision_date: str            # human label, e.g. "2026-09-05"


@dataclass
class GradedDecision:
    symbol: str
    decision: str
    score_at_decision: float
    move_at_decision_pct: float
    subsequent_move_pct: float
    verdict: str
    explanation: str


def grade_decision(past: PastDecision, subsequent_move_pct: float) -> GradedDecision:
    """
    Grades one past decision against a real subsequent price move for the
    same symbol, pulled fresh from the exchange after the fact.
    """
    magnitude = abs(subsequent_move_pct)
    moved_meaningfully = magnitude >= MOVE_THRESHOLD_PCT

    if past.decision == "no_act":
        if moved_meaningfully:
            verdict = "HOLD MISSED A MOVE"
            explanation = (
                f"{past.symbol} was held on {past.decision_date} "
                f"(score={past.score_at_decision}, moved {past.move_at_decision_pct:+.1f}% "
                f"at the time). Since then it moved {subsequent_move_pct:+.1f}%, "
                f"which is a real move the hold did not act on."
            )
        else:
            verdict = "HOLD CONFIRMED"
            explanation = (
                f"{past.symbol} was held on {past.decision_date} "
                f"(score={past.score_at_decision}, moved {past.move_at_decision_pct:+.1f}% "
                f"at the time). Since then it only moved {subsequent_move_pct:+.1f}%, "
                f"confirming there was nothing worth acting on."
            )
    else:  # "act"
        # Direction-aware: an "act" decision implied a directional bet.
        # If the subsequent move continued or reversed hard, say so plainly.
        same_direction = (subsequent_move_pct > 0) == (past.move_at_decision_pct > 0)
        if moved_meaningfully and same_direction:
            verdict = "ACT CONFIRMED"
            explanation = (
                f"{past.symbol} action was taken on {past.decision_date} "
                f"(score={past.score_at_decision}). The move continued in the same "
                f"direction afterward ({subsequent_move_pct:+.1f}%), consistent with the signal."
            )
        elif moved_meaningfully and not same_direction:
            verdict = "ACT REVERSED"
            explanation = (
                f"{past.symbol} action was taken on {past.decision_date} "
                f"(score={past.score_at_decision}), but the move reversed afterward "
                f"({subsequent_move_pct:+.1f}%), against the direction the signal implied."
            )
        else:
            verdict = "ACT — MOVE FADED"
            explanation = (
                f"{past.symbol} action was taken on {past.decision_date} "
                f"(score={past.score_at_decision}), but the subsequent move was small "
                f"({subsequent_move_pct:+.1f}%) — the signal didn't carry through."
            )

    return GradedDecision(
        symbol=past.symbol,
        decision=past.decision,
        score_at_decision=past.score_at_decision,
        move_at_decision_pct=past.move_at_decision_pct,
        subsequent_move_pct=subsequent_move_pct,
        verdict=verdict,
        explanation=explanation,
    )


def grade_batch(pasts: List[PastDecision], subsequent_moves: dict) -> List[GradedDecision]:
    """
    subsequent_moves: {"BTC": 0.435, "ETH": 1.997, ...} — real % moves pulled
    fresh from the exchange for each symbol, after the original decisions.
    """
    graded = []
    for p in pasts:
        if p.symbol not in subsequent_moves:
            continue
        graded.append(grade_decision(p, subsequent_moves[p.symbol]))
    return graded


def print_report(graded: List[GradedDecision]):
    print("\n=== Self-Grading Report ===\n")
    confirmed = sum(1 for g in graded if g.verdict in ("HOLD CONFIRMED", "ACT CONFIRMED"))
    missed = sum(1 for g in graded if g.verdict in ("HOLD MISSED A MOVE", "ACT REVERSED"))
    for g in graded:
        marker = "✅" if g.verdict in ("HOLD CONFIRMED", "ACT CONFIRMED") else (
            "⚠️ " if g.verdict == "HOLD MISSED A MOVE" or g.verdict == "ACT REVERSED" else "➖"
        )
        print(f"{marker} {g.symbol}: {g.verdict}")
        print(f"   {g.explanation}\n")
    print(f"Summary: {confirmed} confirmed, {missed} missed/reversed, "
          f"{len(graded) - confirmed - missed} faded, out of {len(graded)} graded decisions.")


if __name__ == "__main__":
    # Real example: yesterday's live scan (Sept 5, 2026) held on all 5 coins
    # during a market-wide pullback. This pulls TODAY's real prices live,
    # right now, via Binance's public API, to grade those holds against
    # what actually happened.
    yesterday = [
        PastDecision("BTC", "no_act", 24.2, -1.499, "2026-09-05"),
        PastDecision("ETH", "no_act", 21.7, -2.303, "2026-09-05"),
        PastDecision("SOL", "no_act", 19.9, -1.516, "2026-09-05"),
        PastDecision("XRP", "no_act", 21.1, -3.045, "2026-09-05"),
        PastDecision("ADA", "no_act", 30.9, -3.980, "2026-09-05"),
    ]

    print("Pulling live current prices from Binance public API...\n")
    today_real_moves = {}
    for p in yesterday:
        pct = fetch_live_pct_change(p.symbol)
        if pct is not None:
            today_real_moves[p.symbol] = pct
            print(f"  {p.symbol}: {pct:+.3f}% (live, just now)")

    if not today_real_moves:
        print("\nNo live data available (no internet?) -- nothing to grade.")
    else:
        graded = grade_batch(yesterday, today_real_moves)
        print_report(graded)