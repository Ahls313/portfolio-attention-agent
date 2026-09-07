import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from attention_score import Holding
from early_signal import volume_price_divergence, scan_for_early_signals


class TestVolumePriceDivergence:
    def test_volume_spike_flat_price_flags_accumulation_pattern(self):
        """
        Volume way above normal, price still flat -> classic pre-move setup.
        Historical baselines need a little natural variance -- a perfectly
        flat (zero-variance) history correctly reads as "not enough signal"
        (std=0 -> z=0), so real variance is needed to detect a spike at all.
        """
        h = Holding(
            symbol="SOL", amount=1, today_pct_change=0.1,
            historical_daily_moves=[0.4, -0.3, 0.5, -0.4, 0.3, -0.5, 0.4, -0.3],
            today_volume=60_000,
            historical_daily_volumes=[9_800, 10_200, 9_900, 10_100, 9_950, 10_050, 9_900, 10_100],
        )
        result = volume_price_divergence(h)
        assert result["divergence_score"] > 30, f"expected a real divergence, got {result}"
        assert "accumulation" in result["read"] or "distribution" in result["read"]

    def test_volume_and_price_both_elevated_scores_low_divergence(self):
        """If price has already moved a lot too, this is a confirmed move, not an early setup."""
        h = Holding(
            symbol="ETH", amount=1, today_pct_change=8.0,
            historical_daily_moves=[0.1, -0.1, 0.2, -0.1, 0.1, -0.2, 0.1, -0.1],
            today_volume=60_000,
            historical_daily_volumes=[10_000] * 8,
        )
        result = volume_price_divergence(h)
        assert result["divergence_score"] < 30, (
            f"expected low divergence once price already moved, got {result}"
        )

    def test_missing_volume_history_reported_honestly(self):
        """No volume history -> explicit 'insufficient' read, not a fabricated 0."""
        h = Holding(symbol="ALT", amount=1, today_pct_change=1.0,
                     historical_daily_moves=[0.5] * 8)
        result = volume_price_divergence(h)
        assert result["divergence_score"] == 0.0
        assert "insufficient" in result["read"]

    def test_no_unusual_activity_reads_as_nothing_detected(self):
        h = Holding(
            symbol="BTC", amount=1, today_pct_change=0.2,
            historical_daily_moves=[0.2, -0.1, 0.3, -0.2, 0.1, -0.3, 0.2, -0.1],
            today_volume=10_500,
            historical_daily_volumes=[10_000] * 8,
        )
        result = volume_price_divergence(h)
        assert result["read"] == "No meaningful volume/price divergence detected."


class TestScanForEarlySignals:
    def test_only_returns_signals_above_threshold(self):
        strong = Holding(
            symbol="STRONG", amount=1, today_pct_change=0.1,
            historical_daily_moves=[0.1, -0.08, 0.12, -0.09, 0.1, -0.11, 0.09, -0.08],
            today_volume=60_000,
            historical_daily_volumes=[9_800, 10_200, 9_900, 10_100, 9_950, 10_050, 9_900, 10_100],
        )
        weak = Holding(
            symbol="WEAK", amount=1, today_pct_change=0.1,
            historical_daily_moves=[0.1, -0.08, 0.12, -0.09, 0.1, -0.11, 0.09, -0.08],
            today_volume=10_100,
            historical_daily_volumes=[9_800, 10_200, 9_900, 10_100, 9_950, 10_050, 9_900, 10_100],
        )
        results = scan_for_early_signals([strong, weak], threshold=30.0)
        symbols = [r["symbol"] for r in results]
        assert "STRONG" in symbols
        assert "WEAK" not in symbols