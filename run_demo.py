"""
One-command demo runner
------------------------
Runs the full recorded pipeline, captures the output to a file, and
generates the backtest report -- all in one command, so recording a demo
is "run this one script" instead of juggling three separate commands.

Adapted from an earlier draft that depended on risk.py (a thin, unused
budget cap) and mcp_sandbox.py (a one-line wrapper around RecordedBridge).
Both were dropped: this calls RecordedBridge and backtest_replay directly,
so there's nothing between this script and the actual pipeline code that
hasn't been tested.
"""

import os
import io
from contextlib import redirect_stdout
from datetime import datetime, timezone

from orchestrator import RecordedBridge, run_pipeline
import backtest_replay

OUTPUT_DIR = "demo_output"
TRADE_BUDGET_USDT = 1.90  # matches the real historical trade this bridge replays

os.makedirs(OUTPUT_DIR, exist_ok=True)


def main():
    bridge = RecordedBridge()
    demo_log_path = os.path.join(OUTPUT_DIR, "demo_run.txt")

    buf = io.StringIO()
    with redirect_stdout(buf):
        print(f"Demo run at {datetime.now(timezone.utc).isoformat()}")
        print("Running pipeline in SANDBOX mode (RecordedBridge, real recorded data)...\n")
        run_pipeline(bridge, budget_usdt=TRADE_BUDGET_USDT)

    output = buf.getvalue()

    # Write captured output to file
    with open(demo_log_path, "w") as f:
        f.write(output)

    # Also print to console so it's visible live during recording
    print(output)

    # Generate the backtest/replay report from the same recorded data
    report_path = os.path.join(OUTPUT_DIR, "backtest_report.html")
    backtest_replay.generate_report(bridge, report_path)

    print(f"Backtest report written to {report_path}")
    print(f"Demo log written to {demo_log_path}")


if __name__ == "__main__":
    main()