"""
Test script for the Stock Picker application.
This file tests the various components of the application with sample data.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to path to import modules
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

# Import our modules
from data_retrieval import MarketDataFetcher, NewsDataFetcher
from stock_scanner import StockScanner, ATRCalculator
from trading_strategy import TradingStrategy

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('stock_picker_test')

def test_data_retrieval():
    """Test the data retrieval functionality"""
    logger.info("Testing data retrieval functionality...")
    
    # Initialize data fetchers
    market_data = MarketDataFetcher()
    news_data = NewsDataFetcher()
    
    # Test symbols
    test_symbols = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META']
    
    # Test stock data retrieval
    success_count = 0
    for symbol in test_symbols:
        try:
            data = market_data.get_stock_data(symbol, period="5d", interval="1d")
            if not data.empty:
                logger.info(f"Successfully retrieved data for {symbol}: {len(data)} rows")
                success_count += 1
            else:
                logger.warning(f"Retrieved empty data for {symbol}")
        except Exception as e:
            logger.error(f"Error retrieving data for {symbol}: {str(e)}")
    
    logger.info(f"Stock data retrieval test: {success_count}/{len(test_symbols)} successful")
    
    # Test relative volume calculation
    success_count = 0
    for symbol in test_symbols:
        try:
            rel_volume = market_data.get_relative_volume(symbol)
            if rel_volume > 0:
                logger.info(f"Successfully calculated relative volume for {symbol}: {rel_volume:.2f}x")
                success_count += 1
            else:
                logger.warning(f"Could not calculate relative volume for {symbol}")
        except Exception as e:
            logger.error(f"Error calculating relative volume for {symbol}: {str(e)}")
    
    logger.info(f"Relative volume calculation test: {success_count}/{len(test_symbols)} successful")
    
    # Test news retrieval
    success_count = 0
    for symbol in test_symbols:
        try:
            news = news_data.get_stock_news(symbol, max_news=3)
            if news:
                logger.info(f"Successfully retrieved news for {symbol}: {len(news)} items")
                success_count += 1
            else:
                logger.warning(f"No news found for {symbol}")
        except Exception as e:
            logger.error(f"Error retrieving news for {symbol}: {str(e)}")
    
    logger.info(f"News retrieval test: {success_count}/{len(test_symbols)} successful")
    
    return success_count >= len(test_symbols) * 0.6  # At least 60% success rate

def test_stock_scanner():
    """Test the stock scanner functionality"""
    logger.info("Testing stock scanner functionality...")
    
    # Initialize scanner
    scanner = StockScanner()
    
    # Test symbols
    test_symbols = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA', 'JPM', 'V', 'JNJ']
    
    # Test price deviation scan
    try:
        deviation_results = scanner.scan_for_price_deviation(test_symbols)
        logger.info(f"Price deviation scan: found {len(deviation_results)} stocks with significant deviation")
        
        if deviation_results:
            logger.info(f"Sample result: {deviation_results[0]}")
    except Exception as e:
        logger.error(f"Error in price deviation scan: {str(e)}")
        return False
    
    # Test high relative volume scan
    try:
        volume_results = scanner.scan_for_high_relative_volume(test_symbols)
        logger.info(f"High relative volume scan: found {len(volume_results)} stocks with high volume")
        
        if volume_results:
            logger.info(f"Sample result: {volume_results[0]}")
    except Exception as e:
        logger.error(f"Error in high relative volume scan: {str(e)}")
        return False
    
    # Test ATR calculation
    try:
        atr_results = scanner.scan_for_high_atr(test_symbols)
        logger.info(f"High ATR scan: found {len(atr_results)} stocks with high ATR")
        
        if atr_results:
            logger.info(f"Sample result: {atr_results[0]}")
    except Exception as e:
        logger.error(f"Error in high ATR scan: {str(e)}")
        return False
    
    # Test catalyst check
    try:
        catalyst_results = scanner.check_for_catalysts(test_symbols)
        logger.info(f"Catalyst check: found {len(catalyst_results)} stocks with potential catalysts")
        
        if catalyst_results:
            logger.info(f"Sample result: {catalyst_results[0]}")
    except Exception as e:
        logger.error(f"Error in catalyst check: {str(e)}")
        return False
    
    # Test relative strength calculation
    try:
        strength_results = scanner.calculate_relative_strength(test_symbols)
        logger.info(f"Relative strength calculation: calculated for {len(strength_results)} stocks")
        
        if strength_results:
            logger.info(f"Sample result: {strength_results[0]}")
    except Exception as e:
        logger.error(f"Error in relative strength calculation: {str(e)}")
        return False
    
    # Test comprehensive scan
    try:
        scan_results = scanner.run_comprehensive_scan(min_price=5, max_price=1000, min_volume=100000)
        logger.info(f"Comprehensive scan: scanned {scan_results.get('universe_size', 0)} stocks")
        logger.info(f"Found {len(scan_results.get('opportunities', []))} trading opportunities")
        
        if scan_results.get('opportunities', []):
            logger.info(f"Top opportunity: {scan_results['opportunities'][0]}")
    except Exception as e:
        logger.error(f"Error in comprehensive scan: {str(e)}")
        return False
    
    return True

def test_trading_strategy():
    """Test the trading strategy functionality"""
    logger.info("Testing trading strategy functionality...")
    
    # Initialize strategy
    strategy = TradingStrategy(account_size=10000, max_daily_loss=100, risk_reward_ratio=2.0)
    
    # Create sample opportunities
    sample_opportunities = [
        {
            'symbol': 'AAPL',
            'price': 150.0,
            'deviation_pct': 5.2,
            'direction': 'up',
            'has_catalyst': True,
            'score': 85.5,
            'catalyst': {
                'type': ['earnings'],
                'news_title': 'Apple Reports Record Earnings',
                'news_link': 'https://example.com/news/apple'
            }
        },
        {
            'symbol': 'MSFT',
            'price': 280.0,
            'deviation_pct': 4.8,
            'direction': 'up',
            'has_catalyst': False,
            'score': 75.2
        },
        {
            'symbol': 'TSLA',
            'price': 200.0,
            'deviation_pct': -6.5,
            'direction': 'down',
            'has_catalyst': True,
            'score': 82.1,
            'catalyst': {
                'type': ['recall'],
                'news_title': 'Tesla Announces Vehicle Recall',
                'news_link': 'https://example.com/news/tesla'
            }
        }
    ]
    
    # Test trade plan generation
    try:
        trade_plans = strategy.generate_trade_plans(sample_opportunities)
        logger.info(f"Generated {len(trade_plans)} trade plans")
        
        for plan in trade_plans:
            logger.info(f"Trade plan for {plan['symbol']} ({plan['direction']}):")
            logger.info(f"  Entry: ${plan['entry_price']:.2f}")
            logger.info(f"  Stop Loss: ${plan['stop_loss']:.2f}")
            logger.info(f"  Take Profit: ${plan['take_profit']:.2f}")
            logger.info(f"  Position Size: {plan['position_size']} shares")
            logger.info(f"  Potential Loss: ${plan['potential_loss']:.2f}")
            logger.info(f"  Potential Profit: ${plan['potential_profit']:.2f}")
    except Exception as e:
        logger.error(f"Error generating trade plans: {str(e)}")
        return False
    
    # Test risk management rules
    try:
        # Test consecutive losses rule
        strategy.consecutive_losses = 3
        can_trade = strategy.can_take_trade()
        logger.info(f"Can take trade after 3 consecutive losses: {can_trade} (expected: False)")
        
        strategy.consecutive_losses = 2
        can_trade = strategy.can_take_trade()
        logger.info(f"Can take trade after 2 consecutive losses: {can_trade} (expected: True)")
        
        # Test daily loss limit rule
        strategy.daily_pnl = -110
        can_trade = strategy.can_take_trade()
        logger.info(f"Can take trade after -$110 daily P&L: {can_trade} (expected: False)")
        
        strategy.daily_pnl = -90
        can_trade = strategy.can_take_trade()
        logger.info(f"Can take trade after -$90 daily P&L: {can_trade} (expected: True)")
        
        # Reset for further tests
        strategy.consecutive_losses = 0
        strategy.daily_pnl = 0
    except Exception as e:
        logger.error(f"Error testing risk management rules: {str(e)}")
        return False
    
    # Test trade result recording
    try:
        # Sample trade plan
        trade_plan = trade_plans[0]
        
        # Record a winning trade
        strategy.record_trade_result(trade_plan, 'win', 100.0)
        logger.info(f"Recorded winning trade: Daily P&L=${strategy.daily_pnl:.2f}, Consecutive losses={strategy.consecutive_losses}")
        
        # Record a losing trade
        strategy.record_trade_result(trade_plan, 'loss', -50.0)
        logger.info(f"Recorded losing trade: Daily P&L=${strategy.daily_pnl:.2f}, Consecutive losses={strategy.consecutive_losses}")
        
        # Get trading summary
        summary = strategy.get_trading_summary()
        logger.info(f"Trading summary: {summary}")
    except Exception as e:
        logger.error(f"Error testing trade result recording: {str(e)}")
        return False
    
    return True

def run_all_tests():
    """Run all tests and report results"""
    logger.info("Starting Stock Picker application tests")
    
    # Run tests
    data_retrieval_success = test_data_retrieval()
    scanner_success = test_stock_scanner()
    strategy_success = test_trading_strategy()
    
    # Report results
    logger.info("\n--- Test Results ---")
    logger.info(f"Data Retrieval: {'PASS' if data_retrieval_success else 'FAIL'}")
    logger.info(f"Stock Scanner: {'PASS' if scanner_success else 'FAIL'}")
    logger.info(f"Trading Strategy: {'PASS' if strategy_success else 'FAIL'}")
    
    # Overall result
    overall_success = data_retrieval_success and scanner_success and strategy_success
    logger.info(f"\nOverall Test Result: {'PASS' if overall_success else 'FAIL'}")
    
    return overall_success

if __name__ == "__main__":
    run_all_tests()
