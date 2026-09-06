# Recording storyboard — frame-accurate

Total length: ~2:30 (150 seconds). Use a single continuous screen capture and record narration separately or live.

0s — 10s: Title frame
- Visual: Slide/title or terminal header
- Narration: "Portfolio Attention Scanner — sandbox demo for Binance BUILD YOUR AI AGENT"

10s — 30s: Show branch & key files
- Command: git checkout build-your-ai-mvp
- Open in editor or 'ls' to show files: orchestrator.py, attention_score.py, watch_agent.py, run_demo.py
- Narration: "Key modules: orchestrator, attention_score, early_signal, debate, watch_agent. I added run_demo.py and sandbox bridge for reproducible demo."

30s — 90s: Run demo
- Command: python3 run_demo.py
- Let pipeline output unfold; pause briefly after dashboard and before trade attempt to narrate what viewers see.
- Narration: Explain attention scores, early signals, debates, and that trade fills are recorded.

90s — 110s: Show demo_output/demo_run.txt
- Command: sed -n '1,120p' demo_output/demo_run.txt (or open in editor)
- Narration: "This is the decision journal and full pipeline output; it is append-only and auditable."

110s — 130s: Open backtest_report.html
- Command: (open in browser) or python -m http.server 8000 then open, but simpler: open file in browser
- Narration: "Backtest report shows simple per-symbol metrics computed from recorded history."

130s — 150s: Final notes & CTA
- Show risk.py and DEMO.md quickly
- Narration: "Risk controls are in risk.py. For submission assets, see demo_output, slides/, and PR description. I can open the PR and add CI; please merge to main to include in submission."
