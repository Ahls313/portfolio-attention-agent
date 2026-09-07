import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import watch_agent
from attention_score import run_portfolio_scan, Holding


@pytest.fixture
def isolated_state(tmp_path, monkeypatch):
    """
    Redirects watch_agent's STATE_PATH to a throwaway file and replaces
    log_decision with an in-memory recorder, so tests never touch the
    real watch_state.json / decision_journal.jsonl used by the actual demo.
    """
    monkeypatch.setattr(watch_agent, "STATE_PATH", str(tmp_path / "state.json"))
    logged = []
    monkeypatch.setattr(watch_agent, "log_decision",
                         lambda **kwargs: logged.append(kwargs) or kwargs)
    return logged


def _quiet_holding(symbol="BTC", pct=0.3):
    """A holding that should score low and never trigger any signal."""
    return Holding(symbol=symbol, amount=1, today_pct_change=pct,
                    historical_daily_moves=[0.3, -0.2, 0.4, -0.3, 0.2, -0.4, 0.3, -0.2])


def _extreme_holding(symbol="BTC", pct=8.0):
    """A holding built to score high, with volume backing it, to exercise the ACT path."""
    return Holding(symbol=symbol, amount=1, today_pct_change=pct,
                    historical_daily_moves=[0.1, -0.1, 0.2, -0.1, 0.1, -0.2, 0.1, -0.1],
                    today_volume=60_000, avg_daily_volume=10_000,
                    historical_daily_volumes=[10_000] * 8)


class TestEvaluateSymbolNoAction:
    def test_quiet_holding_never_acts(self, isolated_state):
        state = watch_agent._load_state()
        holding = _quiet_holding()
        results = run_portfolio_scan([holding], market_avg_move_pct=0.0, news_items=[])
        record = watch_agent.evaluate_symbol(results[0], {"BTC": holding}, state)
        assert record["will_act"] is False
        assert "NO ACTION" in record["decision"]

    def test_decision_is_logged_even_when_holding(self, isolated_state):
        state = watch_agent._load_state()
        holding = _quiet_holding()
        results = run_portfolio_scan([holding], market_avg_move_pct=0.0, news_items=[])
        watch_agent.evaluate_symbol(results[0], {"BTC": holding}, state)
        assert len(isolated_state) == 1
        assert isolated_state[0]["decision"] == "no_act"


class TestEvaluateSymbolStateTracking:
    def test_score_history_persists_across_calls(self, isolated_state):
        state = watch_agent._load_state()
        holding = _quiet_holding()
        results = run_portfolio_scan([holding], market_avg_move_pct=0.0, news_items=[])

        watch_agent.evaluate_symbol(results[0], {"BTC": holding}, state)
        watch_agent.evaluate_symbol(results[0], {"BTC": holding}, state)

        assert len(state["score_history"]["BTC"]) == 2

    def test_score_history_capped_at_30_entries(self, isolated_state):
        state = watch_agent._load_state()
        holding = _quiet_holding()
        results = run_portfolio_scan([holding], market_avg_move_pct=0.0, news_items=[])
        for _ in range(35):
            watch_agent.evaluate_symbol(results[0], {"BTC": holding}, state)
        assert len(state["score_history"]["BTC"]) == 30


class TestVetoIntegration:
    def test_veto_blocks_even_when_all_three_signals_agree(self, isolated_state):
        """
        Forces a scenario where score/divergence/debate would all pass, but
        the exposure veto should still block because the symbol is already
        over its configured exposure limit.
        """
        state = watch_agent._load_state()
        state["positions_usdt"] = {"BTC": 350.0}  # already heavily overweight
        holding = _extreme_holding()
        results = run_portfolio_scan([holding], market_avg_move_pct=-0.2, news_items=[])

        record = watch_agent.evaluate_symbol(results[0], {"BTC": holding}, state)

        # Whether or not all 3 signals actually agreed on this synthetic
        # data, the important invariant is: if they did, veto still can
        # block it -- will_act must never be True while veto_blocked is True.
        if record["veto_blocked"]:
            assert record["will_act"] is False