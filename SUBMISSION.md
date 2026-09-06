# Submission README — Binance BUILD YOUR AI AGENT

This file summarizes what to include when submitting this repo for the hackathon.

What this repo demonstrates:
- Autonomous agent workflows: orchestrator.py, watch_agent.py, decision journal
- Data & Analysis: attention_score, early_signal, debate modules and backtest_report
- Trading Workflows: recorded trade evidence (RecordedBridge) and end-to-end pipeline

Included in this branch (build-your-ai-mvp):
- One-command sandbox demo (run_demo.py) — no keys required
- Minimal RiskManager (risk.py) enforcing per-trade cap
- Backtest/replay report generator (backtest_replay.py)
- Demo artifacts in demo_output/ after running

How to run (local):
1. git checkout build-your-ai-mvp
2. python -m pip install -r requirements.txt
3. python3 run_demo.py
4. Open demo_output/backtest_report.html in a browser

What’s simulated vs real:
- Market data and trade fills are replayed from a real Sept 2 2026 capture. The demo does not execute new live trades.
- The code supports live MCP connectors via MCPBridge; live runs require an MCP-enabled agent and appropriate credentials.

Submission assets to attach:
- Demo video (2–3 min)
- 3-slide architecture deck (slides/)
- demo_output logs & backtest_report.html
- PR linking build-your-ai-mvp branch

Contact: GitHub: @Ahls313
