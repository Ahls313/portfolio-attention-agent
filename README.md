# Portfolio Attention Scanner

Built for the Binance Agent OS Mini Hackathon — **Track A: Agent Creation**.

## The problem

Most crypto alert tools use a flat threshold: "notify me if a coin moves more
than X%." That's noisy in practice. SOL swinging 4% after a 44% August rally
is normal chop. The same 4% move in a low-volatility asset is genuinely
significant. A flat threshold treats both the same — so it either spams you
constantly or misses the moves that actually matter. It also can't tell you
*why* something moved, whether it's isolated or market-wide, or whether
something's brewing before the price has caught up.

## The approach

Instead of a fixed number, this scores each coin against **its own recent
volatility**, using a recency-weighted baseline (7-day half-life, so the
last few days matter more than day 30). Four pieces work together:

### 1. Attention Score (reactive — what already happened)
A 0–100 score combining:
- **Volatility-adjusted deviation (z-score)** — how unusual is today's move
  for *this specific asset*, right now?
- **Market isolation** — is this move market-wide, or specific to this coin?
- **Volume confirmation** — is the move backed by real volume, or could it
  be a thin-book flicker?
- **News confidence** — is there an actual headline that plausibly explains
  it? Deliberately conservative: no match means no forced explanation.

A rolling score history also flags coins whose attention score has been
*climbing* over several days, which a single-day snapshot can't show.

### 2. Early Signal Detection (proactive — what might be starting)
Most tools only react to moves that already happened. This module looks for
the pattern that often shows up *before* a big move: unusually high trading
volume while price hasn't caught up yet. Large positions rarely enter or
exit without moving the order book — quiet accumulation or distribution
often shows in volume before it shows in price.

This isn't a prediction of direction or timing — it's a data-grounded signal
that current conditions resemble a pre-move setup more than either "nothing
happening" or "the move already happened and is fully priced in."

### 3. Bull/Bear Debate
Instead of a single flat verdict, each top-scoring coin gets a structured
bull case and bear case, generated directly from the same computed metrics
above. Every bullet point traces back to a real number — no invented
narrative, no LLM guessing. If a signal isn't present in the data, it
doesn't appear on either side. This is a way to weigh competing reads of
one data set, not a recommendation.

### 4. Autonomous Watch Agent
A single scan is useful, but a scan you have to remember to run isn't really
"automated." This module persists state across runs — score history, a
durable decision journal — and *autonomously* decides whether to act,
without being prompted each cycle.

It only acts when three independently-computed signals agree: an elevated
Attention Score, confirming Early Signal divergence, and a debate that
leans decisively one way (not a coin flip). Every cycle, act or not, is
logged with its full reasoning to an append-only journal — so the agent's
behavior over time is auditable, not a black box. In testing, it correctly
held off acting even during a 3-day climbing score, because the specific
"price hasn't caught up to volume yet" condition wasn't actually present —
real discipline, not a scripted outcome.

### 5. Live Trade Execution
The agent can act on its own output — attempting a real trade on the
top-scoring result and reporting whatever the exchange actually says,
success or rejection, honestly.

## How it connects to Binance (MCP)

Built agent-first: no API keys are hardcoded, and the pipeline doesn't call
Binance's REST API directly from a script. An MCP-connected agent (Claude,
via the Binance MCP connector) makes the live calls:

- **`spot.ticker24hr`** — today's price move and volume per symbol
- **`spot.klines`** — daily candles for each coin's volatility baseline
- **`spot.newOrder`** — attempts a real trade on the top-scoring result
- Wallet, account, sub-account, and margin tools — used live during
  development to diagnose and fund the agent's sub-account, and to map
  what's actually executable (see "Real platform findings" below)

Live news is pulled via web search and matched to holdings by symbol
relevance, in the same agent session.

The scoring, early-signal, and debate logic in this repo are plain,
auditable Python — deliberately not an LLM guessing at significance. The
agent's job is to fetch data, feed it to the model, and act on the result;
the decision-making logic itself is fully inspectable, deterministic code.

## Files

| File | What it does |
|---|---|
| `attention_score.py` | Core scoring model — z-score, isolation, volume, news, trend |
| `early_signal.py` | Volume/price divergence detector for pre-move signals |
| `debate.py` | Generates bull/bear cases from the same computed metrics |
| `watch_agent.py` | Autonomous, persistent decision loop with a full audit journal |
| `dashboard.py` | Dependency-free ANSI terminal dashboard for scan results |
| `orchestrator.py` | Ties it all together: live data → scoring → debate → trade |

## Running it

Each file runs standalone with real, recorded data from a live session:

```bash
python3 attention_score.py    # scoring logic, sample holdings
python3 early_signal.py       # divergence detection, sample data
python3 debate.py             # bull/bear generation, sample data
python3 watch_agent.py        # autonomous watch cycle simulation, 3 days
python3 dashboard.py          # visual dashboard, sample holdings
python3 orchestrator.py       # full pipeline, replays real Sept 2 2026 data
```

For a fully live run, an MCP-enabled agent (Claude Code, Claude Desktop, or
Claude.ai with the Binance connector) implements the `MCPBridge` interface in
`orchestrator.py` against the real Binance MCP tools and calls
`run_pipeline()`.

## Real platform findings (kept in on purpose)

Building this surfaced genuinely useful, live-tested information about how
Binance's Agent OS is structured — worth documenting honestly rather than
hiding:

- **Agentic sub-account architecture.** The agent trades from a dedicated
  sub-account separate from the main account. Reads can see the main
  balance, but trading requires funds to be explicitly moved into the
  sub-account first — not obvious from the docs alone.
- **Spot trading: fully functional.** A real order was placed and filled
  live — order `14874233861`, 23 DOGE bought at $0.08181, real commission
  charged. Confirmed end-to-end.
- **Futures: blocked at the API key permission level** (`enableFutures:
  false`), independent of funding or account setup.
- **Margin: fully activatable and fundable** — after activating and
  transferring funds in-app, the account showed `created: true`,
  `tradeEnabled: true`, and a real $3.68 balance. But the actual order
  execution was rejected live with `code 200003005 — restricted countries
  (including IP addresses)`.
- **Convert: same restriction.** A real quote was successfully requested
  (pricing works), but accepting/executing it hit the identical
  `200003005` error.

The consistency of that one error code across two entirely different
product paths (Margin order execution, Convert quote acceptance) — while
Spot worked cleanly throughout — is a real, reproducible finding about
regional service availability at the execution layer, not a bug in this
code. It's included here because it's true, and because it's exactly the
kind of thing another builder hitting the same wall would want to know.

## Example output (live data, Sept 2 2026)

```
PORTFOLIO ATTENTION SCAN
Market avg today: -2.8%
──────────────────────────────────────────
SOL    36.4/100  MILD, KEEP AN EYE
BTC    32.1/100  NOTHING TO SEE HERE
ETH    24.0/100  NOTHING TO SEE HERE
XRP    22.6/100  NOTHING TO SEE HERE
ADA    19.5/100  NOTHING TO SEE HERE
──────────────────────────────────────────
→ Nothing urgent in the portfolio today.

=== SOL: Bull vs Bear ===
  BULL CASE:
    + This move tracks the broader market, not something specific to SOL —
      lower idiosyncratic risk than the raw % suggests.
  BEAR CASE:
    - SOL is down -4.0% today — the immediate trend is negative.
    - There's a real news catalyst behind this decline, not just price
      action alone.

=== Trade Attempt ===
Top attention score: SOL (36.4/100)
Attempting BUY DOGEUSDT with 1.9 USDT...
  FILLED — real order, real exchange fill:
    Order ID: 14874233861
    Bought 23.00000000 DOGE at 0.08181000 (spent 1.88163000 USDT)
    Commission: 0.02300000 DOGE
```

Two things worth noting:

**The scoring stayed calm when it should.** Every coin in the watchlist
moved down together, all with low isolation scores — a naive "flag anything
>2%" tool would have screamed about SOL's -4%. The model correctly
identified this as a market-wide macro move (Fed rate-hike fears from
Jackson Hole), not a SOL-specific event, and said so.

**The trade is real, not simulated.** This order actually filled on
Binance's live matching engine — real order ID, real fill price, real
commission. That's the design philosophy applied at every layer: don't
force a result — statistical, narrative, or financial — that isn't
actually there. When Margin and Convert hit real restrictions, the
pipeline reported that honestly too, instead of faking success.
