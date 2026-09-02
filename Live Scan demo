import sys
sys.path.insert(0, '/home/claude')
from attention_score import Holding, NewsItem, run_portfolio_scan, score_trend
from dashboard import render_dashboard

# Live data pulled via Binance MCP (spot.ticker24hr + spot.klines, Sept 2 2026)
watchlist = [
    Holding(symbol="BTC", amount=1, today_pct_change=-1.821,
        historical_daily_moves=[0.92,0.87,-0.53,0.93,0.06,-0.09,-1.43,-0.58,-0.19,0.02,-0.70,0.07,-0.30,2.59,0.30,7.12,5.32,7.28,-1.61,0.86,1.62,-0.57,0.62,1.55,-2.99,0.49,-0.70,1.16,-1.45,0.05],
        today_volume=1086215351.90, avg_daily_volume=850000000),
    Holding(symbol="ETH", amount=1, today_pct_change=-2.582,
        historical_daily_moves=[0.50,2.09,-0.25,0.53,0.13,-0.32,-1.96,0.50,-0.15,0.34,-0.21,0.02,-0.35,1.94,0.22,17.47,3.28,8.15,-3.72,1.68,0.77,-1.60,2.63,0.17,-2.70,0.61,-1.66,2.10,-1.99,-0.32],
        today_volume=710405456.58, avg_daily_volume=450000000),
    Holding(symbol="SOL", amount=1, today_pct_change=-4.017,
        historical_daily_moves=[0.26,-1.81,1.32,3.19,0.34,-0.37,0.42,-0.88,0.86,-1.15,-0.07,-0.98,1.89,1.36,10.82,2.67,6.91,0.11,1.72,3.71,-2.39,5.66,6.93,-4.57,1.40,-3.65,1.29,-2.97,-0.15],
        today_volume=264192523.98, avg_daily_volume=150000000),
    Holding(symbol="XRP", amount=1, today_pct_change=-3.030,
        historical_daily_moves=[-1.08,-2.56,-1.33,-2.34,1.83,-0.94,-1.71,0.94,-1.70,0.39,-0.97,-0.92,0.94,-0.11,10.38,14.65,14.69,0.52,4.00,-2.55,-3.20,-0.80,2.15,-4.79,0.91,-2.79,1.64,-2.03,-0.56],
        today_volume=161783425.44, avg_daily_volume=60000000),
    Holding(symbol="ADA", amount=1, today_pct_change=-2.478,
        historical_daily_moves=[-0.98,5.29,-0.20,-0.65,-2.49,-2.55,-1.75,-2.04,-2.40,-0.05,-1.26,-2.36,-0.34,-0.17,7.16,6.36,15.13,-1.35,0.44,-2.42,-5.60,1.58,0.66,-5.00,-0.64,-4.51,2.65,-0.56,0.05],
        today_volume=20175223.42, avg_daily_volume=13000000),
]

market_avg = -2.79  # avg move across watchlist today (macro-driven, matches ~1.4% broader-cap decline weighted toward alts)

news = [
    NewsItem(headline="Fed Chair Warsh's hawkish Jackson Hole comments push September rate hike odds to 60 percent",
             related_symbols=["BTC","ETH","SOL","XRP","ADA"]),
    NewsItem(headline="Binance BTC reserves climb to 2026 high of 687,000 BTC, signaling exchange supply overhang",
             related_symbols=["BTC"]),
    NewsItem(headline="Global crypto market cap falls 1.4 percent as broad pullback follows August rally",
             related_symbols=["BTC","ETH","SOL","XRP","ADA"]),
]

results = run_portfolio_scan(watchlist, market_avg, news)
for r, h in zip(results, watchlist):
    match = next(x for x in watchlist if x.symbol == r["symbol"])
    r["today_pct_change"] = match.today_pct_change

render_dashboard(results, market_avg_move_pct=market_avg)
