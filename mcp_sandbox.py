"""
MCP Sandbox helper
Provides a simple way to obtain a RecordedBridge for demo/sandbox runs.
"""
from orchestrator import RecordedBridge


def get_sandbox_bridge():
    """Return a bridge instance that replays recorded MCP responses."""
    return RecordedBridge()
