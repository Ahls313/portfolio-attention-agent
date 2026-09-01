"""
Terminal Dashboard for Portfolio Attention Score
--------------------------------------------------
Renders the output of attention_score.run_portfolio_scan() as a colored,
bar-charted terminal dashboard. Dependency-free (plain ANSI escape codes),
so it runs anywhere Python runs with zero installs -- useful for a live
hackathon demo where you don't want to depend on pip working on the day.

Usage:
    from attention_score import run_portfolio_scan, score_trend
    from dashboard import render_dashboard

    results = run_portfolio_scan(holdings, market_avg, news_items)
    render_dashboard(results, market_avg_move_pct=market_avg, trends={"BTC": trend_dict})
"""

# ---- ANSI styling (no external deps) ----
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

RED = "\033[38;5;203m"
YELLOW = "\033[38;5;221m"
GREEN = "\033[38;5;114m"
GRAY = "\033[38;5;244m"
CYAN = "\033[38;5;74m"
WHITE = "\033[38;5;255m"

BAR_CHAR = "█"
BAR_WIDTH = 30


def _verdict_color(verdict: str) -> str:
    if verdict == "worth checking in":
        return RED
    if verdict == "mild, keep an eye":
        return YELLOW
    return GREEN


def _score_bar(score: float, color: str) -> str:
    filled = round((score / 100) * BAR_WIDTH)
    filled = max(0, min(BAR_WIDTH, filled))
    bar = BAR_CHAR * filled + DIM + "·" * (BAR_WIDTH - filled) + RESET
    return f"{color}{bar}{RESET}"


def _pct_color(pct: float) -> str:
    if pct > 0:
        return GREEN
    if pct < 0:
        return RED
    return GRAY


def _trend_arrow(trend: dict) -> str:
    if not trend:
        return ""
    direction = trend.get("direction", "")
    delta = trend.get("delta", 0.0)
    if "climbing" in direction or "rising" in direction:
        return f"{RED}▲ {direction}{RESET}"
    if "cooling" in direction:
        return f"{GREEN}▼ {direction}{RESET}"
    if direction == "stable":
        return f"{GRAY}→ stable ({delta:+.1f}){RESET}"
    return f"{GRAY}{direction}{RESET}"


def render_dashboard(results: list, market_avg_move_pct: float = None, trends: dict = None):
    """
    results: output of run_portfolio_scan() -- list of score dicts, sorted
    market_avg_move_pct: today's broader market average move, for header context
    trends: optional {symbol: score_trend(...) dict} for coins with history
    """
    trends = trends or {}
    width = 72

    print()
    print(f"{BOLD}{WHITE}{'PORTFOLIO ATTENTION SCAN'.center(width)}{RESET}")
    if market_avg_move_pct is not None:
        mkt_color = _pct_color(market_avg_move_pct)
        subtitle = f"Market avg today: {mkt_color}{market_avg_move_pct:+.1f}%{RESET}"
        pad = (width - len(subtitle) + len(mkt_color) + len(RESET)) // 2
        print(" " * max(pad, 0) + subtitle)
    print(f"{DIM}{'─' * width}{RESET}")
    print()

    for r in results:
        color = _verdict_color(r["verdict"])
        pct_color = _pct_color(r.get("today_pct_change", 0))
        symbol = r["symbol"]

        header = f"{BOLD}{WHITE}{symbol:<6}{RESET}  {color}{r['score']:>5.1f}/100{RESET}  {color}{r['verdict'].upper()}{RESET}"
        print(header)
        print(f"  {_score_bar(r['score'], color)}")

        detail_bits = [
            f"z={r['z_score']:.2f}",
            f"isolation={r['isolation']:.2f}",
        ]
        if r.get("volume_confirmation", 0) > 0:
            detail_bits.append(f"volume={r['volume_confirmation']:.2f}")
        if r.get("news_confidence", 0) > 0:
            detail_bits.append(f"news={r['news_confidence']:.2f}")
        print(f"  {GRAY}{'  '.join(detail_bits)}{RESET}")

        if symbol in trends:
            print(f"  {_trend_arrow(trends[symbol])}")

        print(f"  {DIM}{r['explanation']}{RESET}")
        print()

    print(f"{DIM}{'─' * width}{RESET}")
    top = results[0] if results else None
    if top and top["verdict"] == "worth checking in":
        print(f"{RED}{BOLD}  → {top['symbol']} deserves a look today.{RESET}")
    else:
        print(f"{GREEN}{BOLD}  → Nothing urgent in the portfolio today.{RESET}")
    print()


if __name__ == "__main__":
    # Demo run using the same sample data as attention_score.py
    from attention_score import (
        Holding, NewsItem, run_portfolio_scan, score_trend
    )

    sample_holdings = [
        Holding(
            symbol="BTC", amount=0.05, today_pct_change=-4.1,
            historical_daily_moves=[0.5, -0.3, 0.8, -0.6, 0.2, -0.4, 0.9, -0.7, 0.3,
                                     -0.2, 0.6, -0.5, 0.4, -0.3, 0.7, -0.6, 0.2, -0.4,
                                     0.5, -0.3, 0.6, -0.5, 0.4, -0.2, 0.3, -0.4, 0.5,
                                     -0.3, 0.6, -0.4],
            today_volume=42_000, avg_daily_volume=14_500,
        ),
        Holding(
            symbol="DOGE", amount=500, today_pct_change=3.2,
            historical_daily_moves=[2.1, -3.4, 4.2, -2.8, 3.1, -4.0, 2.9, -3.2, 3.8,
                                     -2.5, 3.3, -3.9, 2.7, -3.1, 4.1, -2.9, 3.4, -3.6,
                                     2.8, -3.3, 3.9, -2.7, 3.2, -3.5, 2.6, -3.8, 3.5,
                                     -2.9, 3.1, -3.4],
            today_volume=8_200_000, avg_daily_volume=7_900_000,
        ),
        Holding(
            symbol="ETH", amount=0.8, today_pct_change=-0.8,
            historical_daily_moves=[0.4, -0.5, 0.6, -0.3, 0.5, -0.4, 0.7, -0.6, 0.3,
                                     -0.5, 0.6, -0.4, 0.5, -0.3, 0.6, -0.5, 0.4, -0.3,
                                     0.5, -0.4, 0.6, -0.5, 0.4, -0.3, 0.5, -0.4, 0.6,
                                     -0.5, 0.4, -0.3],
            today_volume=310_000, avg_daily_volume=305_000,
        ),
    ]
    sample_news = [
        NewsItem(headline="Major exchange reports BTC outflow spike amid regulatory concerns",
                  related_symbols=["BTC"]),
        NewsItem(headline="DOGE sees renewed retail interest after social media mention",
                  related_symbols=["DOGE"]),
    ]
    market_avg = -0.9

    results = run_portfolio_scan(sample_holdings, market_avg, sample_news)
    for r, h in zip(results, sorted(sample_holdings, key=lambda h: next(
            x["score"] for x in results if x["symbol"] == h.symbol), reverse=True)):
        r["today_pct_change"] = h.today_pct_change

    btc_trend = score_trend([38.5, 55.0, next(r["score"] for r in results if r["symbol"] == "BTC")])

    render_dashboard(results, market_avg_move_pct=market_avg, trends={"BTC": btc_trend})
