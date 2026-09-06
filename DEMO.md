# Demo & Sandbox Quickstart (MVP branch)

This branch adds a one-command sandbox demo, a minimal risk manager, and a backtest/replay report generator.

One-command demo (local):

1. Install requirements: python -m pip install -r requirements.txt
2. Run: python3 run_demo.py

Or with Docker:

1. docker build -t portfolio-demo .
2. docker run --rm portfolio-demo

What this does:
- Runs the pipeline in SANDBOX mode using a RecordedBridge (no keys required)
- Captures the demo output to demo_output/demo_run.txt
- Writes a simple backtest report to demo_output/backtest_report.html

What is simulated vs real:
- Market data and a recorded trade fill are replayed from a live Sept 2 2026 session (recorded responses). No real keys are required.
- The recorded trade evidence included is a real historical fill captured during earlier development; the demo does not perform a new live trade.

License: MIT
