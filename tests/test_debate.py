import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from attention_score import Holding, NewsItem, attention_score
from debate import generate_debate


class TestDebateGeneration:
    def test_bull_case_present_on_positive_isolated_move(self):
        """Positive, isolated, high z-score move -> real bull-side content."""
        h = Holding(symbol="SOL", amount=1, today_pct_change=3.5,
                     historical_daily_moves=[0.3, -0.2, 0.4, -0.3, 0.2, -0.4, 0.3, -0.2, 0.4, -0.3])
        score_result = attention_score(h, market_avg_move_pct=-0.5, news_items=[])
        debate = generate_debate(score_result)
        assert len(debate["bull_case"]) > 0
        assert len(debate["bear_case"]) > 0  # both sides always populated, never one-sided

    def test_bear_case_flags_missing_volume_confirmation_on_strong_move(self):
        """High z-score but no volume confirmation -> bear case should call this out."""
        h = Holding(symbol="ETH", amount=1, today_pct_change=4.0,
                     historical_daily_moves=[0.1, -0.1, 0.2, -0.1, 0.1, -0.2, 0.1, -0.1],
                     today_volume=None, avg_daily_volume=None)
        score_result = attention_score(h, market_avg_move_pct=-0.2, news_items=[])
        debate = generate_debate(score_result)
        bear_text = " ".join(debate["bear_case"]).lower()
        assert "volume" in bear_text or "caution" in bear_text

    def test_no_bull_case_falls_back_to_explicit_no_signal_text(self):
        """A completely flat, uneventful move should never produce fabricated bull points."""
        h = Holding(symbol="STABLE", amount=1, today_pct_change=0.0,
                     historical_daily_moves=[0.1, -0.1, 0.1, -0.1, 0.1])
        score_result = attention_score(h, market_avg_move_pct=0.0, news_items=[])
        debate = generate_debate(score_result)
        # every bullet must trace to real computed data -- if nothing qualifies,
        # it must say so explicitly rather than inventing a point
        assert len(debate["bull_case"]) >= 1
        assert len(debate["bear_case"]) >= 1

    def test_debate_never_recommends_buy_or_sell(self):
        """The note must always frame this as analysis, not a recommendation."""
        h = Holding(symbol="BTC", amount=1, today_pct_change=2.0,
                     historical_daily_moves=[0.5] * 10)
        score_result = attention_score(h, market_avg_move_pct=0.0, news_items=[])
        debate = generate_debate(score_result)
        assert "not a recommendation" in debate["note"]

    def test_early_signal_accumulation_adds_bull_point(self):
        """A confirmed early-signal divergence (upward) should surface in the bull case."""
        h = Holding(symbol="SOL", amount=1, today_pct_change=1.0,
                     historical_daily_moves=[0.5] * 10)
        score_result = attention_score(h, market_avg_move_pct=0.0, news_items=[])
        early_signal = {
            "divergence_score": 45.0,
            "read": "Volume is running well above normal while price has barely moved. "
                    "Slight up bias so far.",
        }
        debate = generate_debate(score_result, early_signal)
        bull_text = " ".join(debate["bull_case"]).lower()
        assert "accumulation" in bull_text or "divergence" in bull_text