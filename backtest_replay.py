"""
Simple backtest/replay utilities for the demo MVP.
Generates basic metrics (cumulative return, avg daily return, max drawdown)
and produces a minimal HTML report.
"""
import os
import math
from statistics import mean, stdev
from jinja2 import Template


def _series_metrics(returns):
    # returns: list of daily pct returns (e.g., [1.2, -0.5, ...])
    if not returns:
        return {}
    daily_frac = [r / 100.0 for r in returns]
    cum_returns = []
    acc = 1.0
    for r in daily_frac:
        acc *= (1 + r)
        cum_returns.append(acc - 1)
    cumulative_return = cum_returns[-1]
    avg_daily = mean(daily_frac)
    vol = stdev(daily_frac) if len(daily_frac) > 1 else 0.0

    # max drawdown
    peak = -math.inf
    max_dd = 0.0
    running = 1.0
    peak = running
    trough = running
    max_dd = 0.0
    running = 1.0
    for r in daily_frac:
        running *= (1 + r)
        if running > peak:
            peak = running
        dd = (peak - running) / peak
        if dd > max_dd:
            max_dd = dd

    return {
        "cumulative_return": cumulative_return,
        "avg_daily_return": avg_daily,
        "volatility": vol,
        "max_drawdown": max_dd,
    }


HTML_TMPL = """
<html>
  <head><title>Backtest Report</title></head>
  <body>
    <h1>Backtest / Replay Report (Sandbox)</h1>
    <p>Generated from recorded sandbox data.</p>
    {% for sym, metrics in symbols.items() %}
      <h2>{{ sym }}</h2>
      <ul>
        <li>Cumulative return: {{ metrics.cumulative_return|round(4) }}</li>
        <li>Avg daily return: {{ metrics.avg_daily_return|round(6) }}</li>
        <li>Volatility (stdev): {{ metrics.volatility|round(6) }}</li>
        <li>Max drawdown: {{ metrics.max_drawdown|round(6) }}</li>
      </ul>
    {% endfor %}
  </body>
</html>
"""


def generate_report(bridge, out_path: str):
    # bridge is expected to be an instance similar to RecordedBridge
    symbols = {}
    # attempt to iterate over known recorded closes if available
    closes_attr = getattr(bridge, "_CLOSES", {})
    for pair, closes in closes_attr.items():
        # compute daily pct moves
        returns = []
        for i in range(1, len(closes)):
            prev = closes[i - 1]
            cur = closes[i]
            if prev == 0:
                continue
            returns.append((cur - prev) / prev * 100.0)
        metrics = _series_metrics(returns)
        symbols[pair.replace('USDT','')] = metrics

    rendered = Template(HTML_TMPL).render(symbols=symbols)
    with open(out_path, "w") as f:
        f.write(rendered)
