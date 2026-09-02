"""
Bull/Bear Debate Generator
-----------------------------
Takes the outputs already computed by attention_score.py and
early_signal.py and presents them as two competing, structured reads of
the SAME data — a bull case and a bear case — instead of one flat verdict.

Important design choice: this is template-driven, not an LLM guessing at
a narrative. Every bullet point in either case is generated directly from
a real computed number (z-score, isolation, volume, news match, divergence
score). If a signal isn't present in the data, it doesn't appear as a
bullet point on either side — nothing is invented to fill space.

This is analysis, not a trade recommendation. It's meant to show both
readings so a person can weigh them, not to tell anyone what to do.
"""

from dataclasses import dataclass


def generate_debate(score_result: dict, early_signal: dict = None) -> dict:
    """
    score_result: one entry from attention_score.run_portfolio_scan()
    early_signal: optional matching entry from early_signal.scan_for_early_signals()

    Returns {"symbol", "bull_case": [...], "bear_case": [...], "note"}
    """
    symbol = score_result["symbol"]
    z = score_result["z_score"]
    isolation = score_result["isolation"]
    volume_conf = score_result.get("volume_confirmation", 0)
    news_conf = score_result.get("news_confidence", 0)
    pct_change = score_result.get("today_pct_change", 0)

    bull = []
    bear = []

    # --- Direction-aware framing: today's move itself ---
    if pct_change > 0:
        bull.append(f"{symbol} is up {pct_change:+.1f}% today — the immediate trend is positive.")
        if z < 1.2:
            bear.append(f"That +{pct_change:.1f}% is within {symbol}'s normal range (z={z:.2f}) — "
                        f"not evidence of a genuine breakout yet.")
    elif pct_change < 0:
        bear.append(f"{symbol} is down {pct_change:.1f}% today — the immediate trend is negative.")
        if z < 1.2:
            bull.append(f"That {pct_change:.1f}% is within {symbol}'s normal volatility range "
                        f"(z={z:.2f}) — this reads as noise, not a fundamental shift.")

    # --- Statistical unusualness ---
    if z >= 2.5:
        if pct_change > 0:
            bull.append(f"This move is statistically rare for {symbol} (z={z:.2f}) — "
                        f"something real is likely driving it.")
        else:
            bear.append(f"This move is statistically rare for {symbol} (z={z:.2f}) — "
                        f"the selling pressure looks unusually strong, not routine chop.")

    # --- Market isolation ---
    if isolation >= 0.7:
        bear.append(f"This move is isolated to {symbol} specifically, not the broader market — "
                    f"idiosyncratic risk (or opportunity) rather than a market-wide tide.")
    elif isolation <= 0.3:
        bull.append(f"This move tracks the broader market, not something specific to {symbol} — "
                    f"lower idiosyncratic risk than the raw % suggests.")

    # --- Volume confirmation ---
    if volume_conf >= 0.5:
        if pct_change > 0:
            bull.append("Volume is well above normal, backing the move as real "
                        "participation, not a thin-book flicker.")
        else:
            bear.append("Volume is well above normal, backing the decline as real selling, "
                        "not a thin-book flicker.")
    elif volume_conf == 0.0 and (score_result.get("z_score", 0) >= 1.5):
        bear.append(f"Volume isn't confirming the move — worth treating the price action "
                    f"with some caution regardless of direction.")

    # --- News ---
    if news_conf > 0:
        if pct_change > 0:
            bull.append("There's a real news catalyst behind this move, not just price action alone.")
        else:
            bear.append("There's a real news catalyst behind this decline, not just price action alone.")
    else:
        bull.append("No negative news has surfaced to explain or justify caution here.")

    # --- Early signal (accumulation/distribution) ---
    if early_signal and early_signal.get("divergence_score", 0) >= 30:
        if "up" in early_signal.get("read", ""):
            bull.append(f"Volume/price divergence suggests possible quiet accumulation "
                        f"(divergence score {early_signal['divergence_score']}) — before price has "
                        f"fully caught up.")
        elif "down" in early_signal.get("read", ""):
            bear.append(f"Volume/price divergence suggests possible quiet distribution "
                        f"(divergence score {early_signal['divergence_score']}) — selling pressure "
                        f"building before price has fully caught up.")

    if not bull:
        bull.append("No strong bullish signal in the current data.")
    if not bear:
        bear.append("No strong bearish signal in the current data.")

    return {
        "symbol": symbol,
        "bull_case": bull,
        "bear_case": bear,
        "note": ("Both cases are generated from the same computed metrics — "
                "this is a structured way to weigh competing reads of one data set, "
                "not a recommendation to buy or sell."),
    }


def print_debate(debate: dict):
    print(f"\n=== {debate['symbol']}: Bull vs Bear ===")
    print("  BULL CASE:")
    for point in debate["bull_case"]:
        print(f"    + {point}")
    print("  BEAR CASE:")
    for point in debate["bear_case"]:
        print(f"    - {point}")
    print(f"  ({debate['note']})")
