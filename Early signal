"""
Early Signal Detector
-----------------------
The Attention Score (attention_score.py) is reactive by design: it scores
moves that already happened. This module looks for the pattern that often
shows up BEFORE a big move — volume behaving unusually while price hasn't
caught up yet.

The idea: large positions rarely enter or exit a market instantly without
moving the order book. Unusual volume with a still-normal price often means
size is being absorbed quietly — accumulation (buying pressure building) or
distribution (selling pressure building) — before the market has fully
repriced. Not every volume spike leads anywhere, which is why this is framed
as "worth watching," not a prediction.

This is still a data-grounded model, not a forecast: it does not claim to
know direction or timing, only that current conditions resemble the
volume-leads-price pattern more than the current price move alone would
suggest.
"""

import math
from dataclasses import dataclass
from typing import Optional

from attention_score import Holding, _decay_weights


def _weighted_zscore(today_value: float, history: list, half_life_days: float = 7.0) -> float:
    """Generic recency-weighted z-score, shared logic for price and volume."""
    n = len(history)
    if n < 5:
        return 0.0
    weights = _decay_weights(n, half_life_days)
    total_weight = sum(weights)
    wmean = sum(w * v for w, v in zip(weights, history)) / total_weight
    wvar = sum(w * (v - wmean) ** 2 for w, v in zip(weights, history)) / total_weight
    std = math.sqrt(wvar)
    if std == 0:
        return 0.0
    return abs(today_value - wmean) / std


def volume_price_divergence(holding: Holding) -> dict:
    """
    Compares today's volume z-score against today's price-move z-score.

    High volume z-score + low price z-score = classic "quiet accumulation"
    pattern: something's moving size, but price hasn't reflected it yet.
    High volume z-score + high price z-score = the move has already
    happened and is confirmed (this is attention_score.py's job, not this
    module's).

    Returns a divergence score 0-100: how strongly this looks like a
    pre-move setup rather than either "nothing happening" or "already
    happened."
    """
    if not holding.historical_daily_volumes or not holding.today_volume:
        return {
            "divergence_score": 0.0,
            "volume_z": 0.0,
            "price_z": 0.0,
            "read": "insufficient volume history to assess",
        }

    volume_z = _weighted_zscore(holding.today_volume, holding.historical_daily_volumes)
    price_z = _weighted_zscore(holding.today_pct_change, holding.historical_daily_moves)

    # Normalize each to 0-1 (cap at z=3 as "maximally unusual", matching
    # the same convention used in attention_score.py for consistency)
    volume_component = min(volume_z / 3.0, 1.0)
    price_component = min(price_z / 3.0, 1.0)

    # Divergence peaks when volume is unusual AND price is still normal.
    # If price has already moved a lot, this isn't an "early" signal anymore.
    divergence = volume_component * (1.0 - price_component) * 100
    divergence = round(divergence, 1)

    if volume_z >= 2.0 and price_z < 1.0:
        direction = "up" if holding.today_pct_change >= 0 else "down"
        read = (f"Volume is running well above normal (z={volume_z:.2f}) while "
                f"price has barely moved (z={price_z:.2f}). Slight {direction} "
                f"bias so far. Resembles a quiet accumulation/distribution phase "
                f"more than a confirmed move — worth watching, not yet a signal.")
    elif volume_z >= 2.0 and price_z >= 1.0:
        read = ("Volume and price are both elevated — this looks like a move "
                "that's already underway and visible, not an early setup.")
    else:
        read = "No meaningful volume/price divergence detected."

    return {
        "divergence_score": divergence,
        "volume_z": round(volume_z, 2),
        "price_z": round(price_z, 2),
        "read": read,
    }


def scan_for_early_signals(holdings: list, threshold: float = 30.0) -> list:
    """
    Runs volume_price_divergence across a watchlist and returns only the
    holdings that cross `threshold` — i.e. worth surfacing, not every coin.
    Sorted by divergence score, highest first.
    """
    flagged = []
    for h in holdings:
        result = volume_price_divergence(h)
        if result["divergence_score"] >= threshold:
            flagged.append({"symbol": h.symbol, **result})
    flagged.sort(key=lambda r: r["divergence_score"], reverse=True)
    return flagged
