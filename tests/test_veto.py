import sys, os
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from veto import cooldown_veto, exposure_veto, liquidity_veto, evidence_veto, evaluate_vetoes


class TestCooldownVeto:
    def test_recent_action_blocks(self):
        recent = datetime.now(timezone.utc).isoformat()
        blocked, reason = cooldown_veto("BTC", recent, cooldown_minutes=60)
        assert blocked
        assert "BTC" in reason

    def test_no_prior_action_passes(self):
        blocked, reason = cooldown_veto("BTC", None, cooldown_minutes=60)
        assert not blocked
        assert reason is None


class TestExposureVeto:
    def test_over_limit_blocks(self):
        blocked, reason = exposure_veto(
            "BTC",
            {"total_value_usdt": 1000.0, "positions": {"BTC": 350.0}},
            {"BTC": 0.30, "default": 0.20},
        )
        assert blocked

    def test_under_limit_passes(self):
        blocked, reason = exposure_veto(
            "BTC",
            {"total_value_usdt": 1000.0, "positions": {"BTC": 100.0}},
            {"BTC": 0.30, "default": 0.20},
        )
        assert not blocked

    def test_zero_total_value_does_not_crash(self):
        blocked, reason = exposure_veto("BTC", {"total_value_usdt": 0.0}, {"default": 0.20})
        assert not blocked


class TestLiquidityVeto:
    def test_thin_book_blocks(self):
        blocked, reason = liquidity_veto(
            "DOGE", {"bid_depth_usdt": 200.0, "ask_depth_usdt": 5000.0}, min_depth_usdt=1000.0
        )
        assert blocked

    def test_deep_book_passes(self):
        blocked, reason = liquidity_veto(
            "BTC", {"bid_depth_usdt": 5000.0, "ask_depth_usdt": 5000.0}, min_depth_usdt=1000.0
        )
        assert not blocked


class TestEvidenceVeto:
    def test_missing_source_blocks(self):
        blocked, reason = evidence_veto({"evidence_refs": ["klines"]}, ["klines", "news"])
        assert blocked
        assert "news" in reason

    def test_all_sources_present_passes(self):
        blocked, reason = evidence_veto({"evidence_refs": ["klines", "news"]}, ["klines", "news"])
        assert not blocked


class TestEvaluateVetoes:
    def test_single_veto_failure_blocks_overall(self):
        signal_context = {"symbol": "BTC", "evidence_refs": ["klines", "news"]}
        veto_config = {
            "cooldown": {"last_action_ts": None, "cooldown_minutes": 60},
            "exposure": {
                "portfolio_state": {"total_value_usdt": 1000.0, "positions": {"BTC": 350.0}},
                "exposure_limits": {"BTC": 0.30, "default": 0.20},
            },
        }
        allowed, reasons = evaluate_vetoes(signal_context, veto_config)
        assert not allowed
        assert len(reasons) == 1

    def test_all_clean_allows(self):
        signal_context = {"symbol": "BTC"}
        veto_config = {
            "cooldown": {"last_action_ts": None, "cooldown_minutes": 60},
            "exposure": {
                "portfolio_state": {"total_value_usdt": 1000.0, "positions": {"BTC": 100.0}},
                "exposure_limits": {"BTC": 0.30, "default": 0.20},
            },
        }
        allowed, reasons = evaluate_vetoes(signal_context, veto_config)
        assert allowed
        assert reasons == []

    def test_omitted_veto_keys_are_skipped_not_failed(self):
        """An empty veto_config should allow everything through -- no vetoes configured."""
        allowed, reasons = evaluate_vetoes({"symbol": "BTC"}, {})
        assert allowed
        assert reasons == []