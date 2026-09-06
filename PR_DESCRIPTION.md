# PR: Merge build-your-ai-mvp → main

Title: MVP: sandbox demo, risk manager, backtest report, Dockerfile, LICENSE (MIT)

Body:
This PR packages a focused MVP for the Binance BUILD YOUR AI AGENT hackathon. It provides a reproducible sandbox demo and key artifacts for judges:

- One-command demo: run_demo.py (writes demo_output/demo_run.txt and backtest_report.html)
- MCP sandbox accessor (mcp_sandbox.py) uses RecordedBridge — no keys required
- Minimal RiskManager (risk.py) to enforce safe demo budgets
- backtest_replay.py to compute simple per-symbol metrics and emit an HTML report
- Dockerfile and requirements.txt for reproducibility
- LICENSE (MIT), CONTRIBUTING, DEMO.md, README addendum
- GitHub Actions workflow (.github/workflows/demo-smoke.yml) to run the demo on push to this branch and upload demo_output as an artifact

Requested reviewers: @Ahls313

Checklist before merge:
- [ ] Confirm LICENSE and contributor guidelines
- [ ] Confirm demo video recorded and uploaded to submission form
- [ ] (Optional) Add CI secrets if enabling live MCP testing (not recommended for hackathon)

Notes:
- Payments and Onchain flows are currently simulated / out of scope for this MVP due to time constraints; we can add MCP-based transfer and a DeFi demo in follow-up commits.
