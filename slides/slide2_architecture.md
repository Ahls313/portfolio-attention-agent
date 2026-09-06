# Slide 2 — Architecture & Flow

Diagram bullets:
- Data sources: RecordedBridge (sandbox) / MCP (live)
- Pipeline: orchestrator -> attention_score -> early_signal -> debate -> attempt_trade
- Persistence: append-only decision journal + demo_output logs
- Safety: RiskManager prevents oversized trades in demo

Speaker notes:
- Explain RecordedBridge allows deterministic demo without keys.
- Mention MCPBridge protocol for live agent connectors (Claude MCP).
- Note risk controls and auditable logs.
