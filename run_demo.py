"""
One-command demo runner for the sandboxed pipeline.
Runs the recorded pipeline, captures output to demo_output/, and generates
a simple backtest report.
"""
import os
import io
from contextlib import redirect_stdout
from datetime import datetime

from orchestrator import run_pipeline
from mcp_sandbox import get_sandbox_bridge
import backtest_replay
from risk import DEFAULT_RISK_MANAGER

OUTPUT_DIR = "demo_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def main():
    bridge = get_sandbox_bridge()
    demo_log_path = os.path.join(OUTPUT_DIR, "demo_run.txt")

    buf = io.StringIO()
    with redirect_stdout(buf):
        print(f"Demo run at {datetime.utcnow().isoformat()}Z")
        print("Running pipeline in SANDBOX mode (RecordedBridge)...\n")
        # Use a safe budget per risk manager default
        safe_budget = min(1.90, DEFAULT_RISK_MANAGER.per_trade_cap_usdt)
        run_pipeline(bridge, budget_usdt=safe_budget)

    output = buf.getvalue()

    # Write captured output to file
    with open(demo_log_path, "w") as f:
        f.write(output)

    # Also print to console for CI runs
    print(output)

    # Run backtest / replay report
    report_path = os.path.join(OUTPUT_DIR, "backtest_report.html")
    backtest_replay.generate_report(bridge, report_path)
    print(f"Backtest report written to {report_path}")
    print(f"Demo log written to {demo_log_path}")


if __name__ == "__main__":
    main()
