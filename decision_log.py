"""
Decision Log
------------
A small, dependency-free, append-only JSON Lines logger for agent decisions.

This replaces the ad-hoc journal-writing that used to live inline in
watch_agent.py with a reusable module any part of the pipeline can call:
attention scoring, early signal, debate, vetoes, or the orchestrator itself.

Every entry is one JSON object per line, written with a single atomic
`write` + `flush` + `fsync` so a crash mid-run can't corrupt the file or
leave a half-written line. Nothing here is deleted or rewritten — this is
meant to be a durable trail of "why did the agent do (or not do) X",
including the no-action cases, which are the majority of a well-behaved
agent's decisions.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Callable, List, Optional

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "decision_journal.jsonl")


def log_decision(
    module: str,
    symbol: str,
    decision: str,
    reasons: Optional[List[str]] = None,
    path: str = DEFAULT_PATH,
    **extra,
) -> dict:
    """
    Appends one decision record and returns the record that was written.

    module:   which part of the pipeline made this call, e.g. "watch_agent",
              "early_signal", "veto"
    symbol:   the asset this decision concerns, e.g. "BTC"
    decision: short machine-checkable label, e.g. "act", "no_act", "info"
    reasons:  list of short human-readable reason strings
    path:     journal file to append to (defaults to decision_journal.jsonl
              next to this module)
    **extra:  any additional fields to attach (score, trend, debate_leaning,
              veto_reasons, etc.) — stored as-is alongside the standard fields

    Every entry gets a run_id so multiple records from the same pipeline run
    can be grouped/joined later even though they're written independently.
    """
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "module": module,
        "symbol": symbol,
        "decision": decision,
        "reasons": reasons or [],
        "run_id": extra.pop("run_id", None) or str(uuid.uuid4()),
        **extra,
    }

    line = json.dumps(entry) + "\n"
    # Open in append mode; write + flush + fsync so the line is durable
    # even if the process is killed right after this call returns.
    with open(path, "a") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())

    return entry


def read_last(n: int = 100, path: str = DEFAULT_PATH) -> List[dict]:
    """Returns the last `n` entries, oldest-first within that window."""
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        lines = [line for line in f if line.strip()]
    tail = lines[-n:]
    return [json.loads(line) for line in tail]


def query(filter_fn: Callable[[dict], bool], path: str = DEFAULT_PATH) -> List[dict]:
    """
    Returns every entry for which filter_fn(entry) is True, oldest-first.

    Example:
        # every time the agent actually acted
        query(lambda e: e["decision"] == "act")

        # every no-action decision for BTC in the last run
        query(lambda e: e["symbol"] == "BTC" and e["decision"] == "no_act")
    """
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        entries = [json.loads(line) for line in f if line.strip()]
    return [e for e in entries if filter_fn(e)]


if __name__ == "__main__":
    # Minimal smoke test / usage example. Uses a throwaway file so it
    # doesn't touch the real decision_journal.jsonl.
    test_path = os.path.join(os.path.dirname(__file__), "_decision_log_test.jsonl")
    if os.path.exists(test_path):
        os.remove(test_path)

    log_decision("watch_agent", "BTC", "no_act",
                 reasons=["attention score below threshold"],
                 path=test_path, score=41.0)
    log_decision("watch_agent", "BTC", "no_act",
                 reasons=["no confirming early-signal divergence"],
                 path=test_path, score=68.5)
    log_decision("watch_agent", "ETH", "act",
                 reasons=["all 3 signals agree"],
                 path=test_path, score=91.0)

    last_two = read_last(2, path=test_path)
    assert len(last_two) == 2
    assert last_two[-1]["symbol"] == "ETH"

    acted = query(lambda e: e["decision"] == "act", path=test_path)
    assert len(acted) == 1 and acted[0]["symbol"] == "ETH"

    btc_holds = query(lambda e: e["symbol"] == "BTC" and e["decision"] == "no_act",
                       path=test_path)
    assert len(btc_holds) == 2

    os.remove(test_path)
    print("decision_log.py: all smoke tests passed.")