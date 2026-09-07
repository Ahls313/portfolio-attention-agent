import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from attention_score import (
    Holding, NewsItem, volatility_adjusted_deviation, market_isolation_score,
    volume_confirmation_score, news_confidence_score, attention_score,
    run_portfolio_scan, score_trend,
)


class TestVolatilityAdjustedDeviation:
    def test_normal_move_low_z_score(self):
        """Moving 0.5% when the asset normally swings ~1% = boring (low z)."""
        h = Holding(symbol="BTC", amount=1, today_pct_change=0.5,
                     historical_daily_moves=[0.8, -1.2, 0.6, -0.9, 1.1, -0.7, 0.5, -0.8])
        z = volatility_adjusted_deviation(h)
        assert z < 1.5, f"expected low z, got {z}"

    def test_unusual_move_high_z_score(self):
        """Moving 4% when the asset normally moves ~0.2% = clearly unusual (high z)."""
        h = Holding(symbol="ETH", amount=1, today_pct_change=4.0,
                     historical_daily_moves=[0.2, -0.1, 0.3, -0.2, 0.1, -0.3, 0.2, -0.1])
        z = volatility_adjusted_deviation(h)
        assert z > 2.0, f"expected high z, got {z}"

    def test_insufficient_history_returns_zero(self):
        """Fewer than 5 days of history -> no verdict, returns 0.0."""
        h = Holding(symbol="ALT", amount=1, today_pct_change=2.0,
                     historical_daily_moves=[1.0, -0.5])
        assert volatility_adjusted_deviation(h) == 0.0

    def test_zero_std_dev_returns_zero_not_error(self):
        """Perfectly flat history (std dev 0) must not divide-by-zero crash."""
        h = Holding(symbol="STABLE", amount=1, today_pct_change=0.0,
                     historical_daily_moves=[0.0] * 10)
        assert volatility_adjusted_deviation(h) == 0.0


class TestMarketIsolationScore:
    def test_isolated_move_score_is_high(self):
        """Asset +3% while market -1% (4pt divergence) = mostly isolated."""
        h = Holding(symbol="SOL", amount=1, today_pct_change=3.0,
                     historical_daily_moves=[0.5] * 10)
        isolation = market_isolation_score(h, market_avg_move_pct=-1.0)
        assert isolation > 0.7, f"expected high isolation, got {isolation}"

    def test_correlated_move_score_is_zero(self):
        """Asset moves exactly with the market -> fully correlated, 0 isolation."""
        h = Holding(symbol="BTC", amount=1, today_pct_change=-1.0,
                     historical_daily_moves=[0.5] * 10)
        isolation = market_isolation_score(h, market_avg_move_pct=-1.0)
        assert isolation == 0.0

    def test_isolation_caps_at_one(self):
        """A 10pt divergence should cap at 1.0, not exceed it."""
        h = Holding(symbol="XRP", amount=1, today_pct_change=9.0,
                     historical_daily_moves=[0.5] * 10)
        isolation = market_isolation_score(h, market_avg_move_pct=-1.0)
        assert isolation == 1.0


class TestVolumeConfirmationScore:
    def test_high_volume_spike_confirms(self):
        """3x normal volume should push confirmation toward the top of the range."""
        h = Holding(symbol="DOGE", amount=1, today_pct_change=2.0,
                     historical_daily_moves=[1.0] * 10,
                     today_volume=30_000, avg_daily_volume=10_000)
        assert volume_confirmation_score(h) == 1.0

    def test_normal_volume_no_confirmation(self):
        """Volume at 1x normal gives zero confirmation, not partial credit."""
        h = Holding(symbol="ETH", amount=1, today_pct_change=1.0,
                     historical_daily_moves=[0.5] * 10,
                     today_volume=10_000, avg_daily_volume=10_000)
        assert volume_confirmation_score(h) == 0.0

    def test_missing_volume_data_returns_zero_not_penalized(self):
        """No volume data available -> neutral 0.0, this is an optional signal."""
        h = Holding(symbol="ALT", amount=1, today_pct_change=2.0,
                     historical_daily_moves=[1.0] * 10,
                     today_volume=None, avg_daily_volume=None)
        assert volume_confirmation_score(h) == 0.0


class TestNewsConfidenceScore:
    def test_news_match_increases_confidence(self):
        news = [NewsItem("BTC rally on Fed pause", related_symbols=["BTC"])]
        assert news_confidence_score("BTC", news) == 0.4

    def test_multiple_matches_increase_confidence_further(self):
        news = [
            NewsItem("BTC rally", related_symbols=["BTC"]),
            NewsItem("BTC ETF inflow record", related_symbols=["BTC"]),
        ]
        assert news_confidence_score("BTC", news) == 0.8

    def test_no_matching_headlines_returns_zero(self):
        news = [NewsItem("XRP lawsuit news", related_symbols=["XRP"])]
        assert news_confidence_score("BTC", news) == 0.0


class TestAttentionScoreIntegration:
    def test_high_score_on_unusual_isolated_volume_confirmed_move(self):
        h = Holding(symbol="SOL", amount=1, today_pct_change=4.0,
                     historical_daily_moves=[0.5, -0.3, 0.4, -0.2, 0.3, -0.4, 0.5, -0.3, 0.2, -0.4],
                     today_volume=50_000, avg_daily_volume=10_000)
        news = [NewsItem("SOL breakout imminent", related_symbols=["SOL"])]
        result = attention_score(h, market_avg_move_pct=-0.5, news_items=news)
        assert result["score"] > 60, f"expected high score, got {result['score']}"
        assert result["verdict"] == "worth checking in"

    def test_low_score_on_market_wide_normal_move(self):
        """
        -3% is only "normal" here because BTC's own history also swings
        ~3% a day -- if the baseline volatility were much smaller, -3%
        would correctly register as unusual even though it matches the
        market average (see the isolation-only test above).
        """
        h = Holding(symbol="BTC", amount=1, today_pct_change=-3.0,
                     historical_daily_moves=[3.0, -2.8, 3.2, -2.9, 3.1, -2.7, 2.9, -3.0, 3.1, -2.8],
                     today_volume=100_000, avg_daily_volume=90_000)
        result = attention_score(h, market_avg_move_pct=-3.0, news_items=[])
        assert result["score"] < 35, f"expected low score, got {result['score']}"
        assert result["verdict"] == "nothing to see here"

    def test_run_portfolio_scan_sorts_by_score_descending(self):
        low = Holding(symbol="LOW", amount=1, today_pct_change=0.1,
                       historical_daily_moves=[0.5] * 10)
        high = Holding(symbol="HIGH", amount=1, today_pct_change=8.0,
                        historical_daily_moves=[0.2] * 10)
        results = run_portfolio_scan([low, high], market_avg_move_pct=0.0, news_items=[])
        assert results[0]["symbol"] == "HIGH"
        assert results[0]["score"] >= results[1]["score"]


class TestScoreTrend:
    def test_climbing_trend_detected(self):
        trend = score_trend([40.0, 50.0, 60.0, 70.0])
        assert "climbing" in trend["direction"]
        assert trend["streak"] == 4

    def test_rising_sharply_detected(self):
        """
        A big jump (delta > 10) on the LAST step only -- not a 3-day
        climbing streak, since that takes priority over "rising sharply"
        when both conditions could apply.
        """
        trend = score_trend([10.0, 10.0, 10.0, 55.0])
        assert trend["direction"] == "rising sharply"

    def test_cooling_off_detected(self):
        trend = score_trend([70.0, 60.0, 35.0])
        assert trend["direction"] == "cooling off"

    def test_insufficient_history_reported_honestly(self):
        trend = score_trend([50.0])
        assert trend["direction"] == "insufficient history"