"""
Minimal risk management for demo MVP.
Provides a simple allow_trade check used by the orchestrator demo to block
excessly large demo trades.
"""

from dataclasses import dataclass


@dataclass
class RiskManager:
    per_trade_cap_usdt: float = 5.0
    max_portfolio_exposure_usdt: float = 100.0
    daily_loss_limit_usdt: float = 20.0

    def allow_trade(self, budget_usdt: float) -> bool:
        """Simple rule: allow if proposed budget <= per_trade_cap_usdt."""
        return budget_usdt <= self.per_trade_cap_usdt


# Simple default instance used by the demo orchestrator
DEFAULT_RISK_MANAGER = RiskManager()
