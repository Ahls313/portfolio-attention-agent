# Portfolio Attention Score

Built for the Binance Agent OS Mini Hackathon (Track A).

## The problem

Most portfolio alert tools use a flat threshold: "notify me if a coin moves more
than X%." That's noisy in practice. A coin like DOGE can swing 4% on a boring day,
while a 4% move in a low-volatility asset like BTC is genuinely significant. A flat
threshold treats both the same, so it either spams you or misses the moves that
actually matter.

## The approach

This agent scores each holding relative to **its own historical volatility**, not
a fixed number, then combines three signals into a single 0-100 Attention Score:

1. **Volatility-adjusted deviation (z-score)** — how unusual is today's move
   compared to this specific asset's normal daily range?
2. **Market isolation** — is this move happening across the whole market, or is
   it specific to this one holding?
3. **News confidence** — is there an actual headline that plausibly explains the
   move, or is the correlation unclear? (Deliberately conservative: no match
   means no forced explanation.)

The output isn't just "here's what happened," it's a ranked, statistically
grounded answer to "does this actually deserve my attention today."

## How it connects to Binance Agent OS

- **Price/holdings data**: pulled via Binance MCP (`agent.binance.com/mcp/agentic`)
  through a connected AI client (Claude, in this build)
- **Historical volatility baseline**: computed from Binance's public klines
  endpoint (no auth required for market data)
- **News matching**: headlines pulled via the connected agent and matched against
  holdings by symbol relevance

`attention_score.py` contains the core scoring logic, independent of any single
AI client, it's a plain, auditable statistical model, not an LLM guessing at
significance.

## Running it

The script runs standalone with sample data to demonstrate the logic:

```bash
python3 attention_score.py
```

For a live run against a real portfolio, holdings and price history are fed in
via the Binance MCP connection (see demo video), then scored through this same
logic.

## Example output

```
BTC: Score 83.2/100 — WORTH CHECKING IN
  BTC moved -4.1%, which is highly unusual for this asset (z=8.54).
  Possibly explained by: Major exchange reports BTC outflow spike amid
  regulatory concerns

DOGE: Score 48.0/100 — MILD, KEEP AN EYE
  DOGE moved +3.2%, within its normal range for this asset. This move is
  isolated to this asset, not the broader market.

ETH: Score 36.6/100 — MILD, KEEP AN EYE
  ETH moved -0.8%, somewhat above its normal daily range (z=1.8). This
  tracks the broader market move, likely not asset-specific.
```

Notice BTC ranks highest despite the smallest raw percentage move among the
three, because it's the most statistically unusual move *for that asset*.
That's the point: raw percentage change is a bad signal on its own.
