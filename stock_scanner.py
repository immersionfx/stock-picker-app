"""
Stock Scanner Module for Stock Picker Application

This module is responsible for scanning stocks based on specific criteria:
- Price deviation (>4%)
- Volume and liquidity
- ATR (Average True Range)
- Technical indicators
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from data_retrieval import MarketDataFetcher, NewsDataFetcher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('stock_scanner')

class ATRCalculator:
    """
    Class for calculating Average True Range (ATR)
    """
    
    @staticmethod
    def calculate_atr(data, period=14):
        """
        Calculate Average True Range (ATR)
        
        Args:
            data (pandas.DataFrame): DataFrame with OHLC data
            period (int): Period for ATR calculation
            
        Returns:
            pandas.Series: ATR values
        """
        try:
            # Make sure we have the required columns
            required_columns = ['High', 'Low', 'Close']
            if not all(col in data.columns for col in required_columns):
                logger.error("Missing required columns for ATR calculation")
                return pd.Series()
            
            # Calculate True Range
            high_low = data['High'] - data['Low']
            high_close = (data['High'] - data['Close'].shift()).abs()
            low_close = (data['Low'] - data['Close'].shift()).abs()
            
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            
            # Calculate ATR using Simple Moving Average
            atr = tr.rolling(window=period).mean()
            
            return atr
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {str(e)}")
            return pd.Series()

class StockScanner:
    """
    Class for scanning stocks based on specific criteria
    """
    
    def __init__(self):
        """Initialize the StockScanner"""
        self.market_data = MarketDataFetcher()
        self.news_data = NewsDataFetcher()
        self.atr_calculator = ATRCalculator()
    
    def scan_for_price_deviation(self, symbols, min_deviation=4.0, include_premarket=True):
        """
        Scan for stocks with significant price deviation
        
        Args:
            symbols (list): List of stock symbols to scan
            min_deviation (float): Minimum price deviation percentage
            include_premarket (bool): Whether to include pre-market data
            
        Returns:
            list: List of dictionaries with symbol and deviation information
        """
        results = []
        
        for symbol in symbols:
            try:
                # Get today's data including pre-market if specified
                data = self.market_data.get_stock_data(
                    symbol, 
                    period="1d", 
                    interval="1m", 
                    include_premarket=include_premarket
                )
                
                if data.empty:
                    continue
                
                # Get previous close
                prev_close = data['Close'].iloc[0]
                
                # Get current price (latest available)
                current_price = data['Close'].iloc[-1]
                
                # Calculate deviation
                deviation_pct = ((current_price - prev_close) / prev_close) * 100
                
                # Check if deviation meets the criteria
                if abs(deviation_pct) >= min_deviation:
                    results.append({
                        'symbol': symbol,
                        'current_price': current_price,
                        'prev_close': prev_close,
                        'deviation_pct': deviation_pct,
                        'direction': 'up' if deviation_pct > 0 else 'down',
                        'last_update': data.index[-1].strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            except Exception as e:
                logger.error(f"Error scanning {symbol} for price deviation: {str(e)}")
        
        # Sort results by absolute deviation (descending)
        results.sort(key=lambda x: abs(x['deviation_pct']), reverse=True)
        
        return results
    
    def scan_for_high_relative_volume(self, symbols, min_rel_volume=1.5):
        """
        Scan for stocks with high relative volume
        
        Args:
            symbols (list): List of stock symbols to scan
            min_rel_volume (float): Minimum relative volume
            
        Returns:
            list: List of dictionaries with symbol and volume information
        """
        results = []
        
        for symbol in symbols:
            try:
                # Calculate relative volume
                rel_volume = self.market_data.get_relative_volume(symbol)
                
                # Get today's data
                data = self.market_data.get_stock_data(symbol, period="1d", interval="1d")
                
                if data.empty or rel_volume == 0:
                    continue
                
                # Check if relative volume meets the criteria
                if rel_volume >= min_rel_volume:
                    results.append({
                        'symbol': symbol,
                        'relative_volume': rel_volume,
                        'current_volume': data['Volume'].iloc[-1] if not data.empty else 0,
                        'avg_volume': data['Volume'].iloc[-1] / rel_volume if not data.empty and rel_volume > 0 else 0
                    })
            
            except Exception as e:
                logger.error(f"Error scanning {symbol} for high relative volume: {str(e)}")
        
        # Sort results by relative volume (descending)
        results.sort(key=lambda x: x['relative_volume'], reverse=True)
        
        return results
    
    def scan_for_high_atr(self, symbols, lookback_period=20):
        """
        Scan for stocks with high ATR relative to their industry/sector
        
        Args:
            symbols (list): List of stock symbols to scan
            lookback_period (int): Period for ATR calculation
            
        Returns:
            list: List of dictionaries with symbol and ATR information
        """
        results = []
        
        # Get historical data for all symbols
        all_data = {}
        for symbol in symbols:
            try:
                data = self.market_data.get_stock_data(
                    symbol, 
                    period=f"{lookback_period+10}d",  # Add buffer days
                    interval="1d"
                )
                
                if not data.empty and len(data) >= lookback_period:
                    all_data[symbol] = data
            
            except Exception as e:
                logger.error(f"Error getting data for {symbol}: {str(e)}")
        
        # Calculate ATR for each symbol
        atr_values = {}
        for symbol, data in all_data.items():
            try:
                atr = self.atr_calculator.calculate_atr(data, period=14)
                
                if not atr.empty:
                    # Get the latest ATR value
                    latest_atr = atr.iloc[-1]
                    
                    # Calculate ATR as percentage of price
                    latest_price = data['Close'].iloc[-1]
                    atr_percentage = (latest_atr / latest_price) * 100
                    
                    atr_values[symbol] = {
                        'atr': latest_atr,
                        'atr_percentage': atr_percentage,
                        'price': latest_price
                    }
            
            except Exception as e:
                logger.error(f"Error calculating ATR for {symbol}: {str(e)}")
        
        # Calculate average ATR percentage
        if atr_values:
            avg_atr_percentage = sum(item['atr_percentage'] for item in atr_values.values()) / len(atr_values)
            
            # Find stocks with above-average ATR
            for symbol, values in atr_values.items():
                if values['atr_percentage'] > avg_atr_percentage:
                    results.append({
                        'symbol': symbol,
                        'atr': values['atr'],
                        'atr_percentage': values['atr_percentage'],
                        'price': values['price'],
                        'atr_ratio': values['atr_percentage'] / avg_atr_percentage
                    })
        
        # Sort results by ATR ratio (descending)
        results.sort(key=lambda x: x['atr_ratio'], reverse=True)
        
        return results
    
    def check_for_catalysts(self, symbols):
        """
        Check for catalysts in news for the given symbols
        
        Args:
            symbols (list): List of stock symbols to check
            
        Returns:
            list: List of dictionaries with symbol and catalyst information
        """
        results = []
        
        for symbol in symbols:
            try:
                catalyst_info = self.news_data.check_for_catalyst(symbol)
                
                if catalyst_info.get('has_catalyst', False):
                    results.append({
                        'symbol': symbol,
                        'catalyst_type': catalyst_info.get('catalyst_type', []),
                        'news_title': catalyst_info.get('news_item', {}).get('title', ''),
                        'news_link': catalyst_info.get('news_item', {}).get('link', ''),
                        'news_date': catalyst_info.get('news_item', {}).get('publish_date', '')
                    })
            
            except Exception as e:
                logger.error(f"Error checking catalysts for {symbol}: {str(e)}")
        
        return results
    
    def calculate_relative_strength(self, symbols, period_weeks=13):
        """
        Calculate relative strength ranking for the given symbols
        
        Args:
            symbols (list): List of stock symbols
            period_weeks (int): Period in weeks for relative strength calculation
            
        Returns:
            list: List of dictionaries with symbol and relative strength information
        """
        results = []
        
        try:
            # Calculate days needed for the period
            days_needed = period_weeks * 7
            
            # Get historical data for all symbols
            all_data = {}
            for symbol in symbols:
                try:
                    data = self.market_data.get_stock_data(
                        symbol, 
                        period=f"{days_needed+10}d",  # Add buffer days
                        interval="1d"
                    )
                    
                    if not data.empty and len(data) >= days_needed:
                        all_data[symbol] = data
                
                except Exception as e:
                    logger.error(f"Error getting data for {symbol}: {str(e)}")
            
            # Calculate performance for each symbol
            performances = {}
            for symbol, data in all_data.items():
                try:
                    # Get price at start of period and current price
                    start_price = data['Close'].iloc[-days_needed]
                    current_price = data['Close'].iloc[-1]
                    
                    # Calculate performance
                    performance = ((current_price - start_price) / start_price) * 100
                    performances[symbol] = performance
                
                except Exception as e:
                    logger.error(f"Error calculating performance for {symbol}: {str(e)}")
            
            # Rank symbols by performance
            ranked_symbols = sorted(performances.items(), key=lambda x: x[1], reverse=True)
            
            # Create results
            for i, (symbol, performance) in enumerate(ranked_symbols):
                results.append({
                    'symbol': symbol,
                    'relative_strength': performance,
                    'rank': i + 1,
                    'percentile': 100 - (i / len(ranked_symbols) * 100)
                })
        
        except Exception as e:
            logger.error(f"Error calculating relative strength: {str(e)}")
        
        return results
    
    def run_comprehensive_scan(self, min_price=5, max_price=100, min_volume=500000):
        """
        Run a comprehensive scan to find trading opportunities
        
        Args:
            min_price (float): Minimum stock price
            max_price (float): Maximum stock price
            min_volume (int): Minimum average daily volume
            
        Returns:
            dict: Dictionary with scan results
        """
        try:
            logger.info("Starting comprehensive stock scan")
            
            # Get stock universe
            logger.info("Getting stock universe")
            universe = self.market_data.get_stock_universe(min_price, max_price, min_volume)
            logger.info(f"Found {len(universe)} stocks in universe")
            
            # Scan for price deviation
            logger.info("Scanning for price deviation")
            deviation_results = self.scan_for_price_deviation(universe, min_deviation=4.0)
            logger.info(f"Found {len(deviation_results)} stocks with significant price deviation")
            
            # Get symbols with significant deviation
            deviation_symbols = [item['symbol'] for item in deviation_results]
            
            # If we have too few stocks with deviation, expand the universe for other scans
            scan_symbols = deviation_symbols if len(deviation_symbols) >= 10 else universe[:100]
            
            # Scan for high relative volume
            logger.info("Scanning for high relative volume")
            volume_results = self.scan_for_high_relative_volume(scan_symbols)
            logger.info(f"Found {len(volume_results)} stocks with high relative volume")
            
            # Scan for high ATR
            logger.info("Scanning for high ATR")
            atr_results = self.scan_for_high_atr(scan_symbols)
            logger.info(f"Found {len(atr_results)} stocks with high ATR")
            
            # Check for catalysts
            logger.info("Checking for catalysts")
            catalyst_results = self.check_for_catalysts(deviation_symbols)
            logger.info(f"Found {len(catalyst_results)} stocks with potential catalysts")
            
            # Calculate relative strength
            logger.info("Calculating relative strength")
            strength_results = self.calculate_relative_strength(scan_symbols)
            logger.info(f"Calculated relative strength for {len(strength_results)} stocks")
            
            # Combine results to find the best opportunities
            opportunities = self._find_opportunities(
                deviation_results, 
                volume_results, 
                atr_results, 
                catalyst_results, 
                strength_results
            )
            
            logger.info(f"Identified {len(opportunities)} trading opportunities")
            
            return {
                'universe_size': len(universe),
                'deviation_results': deviation_results,
                'volume_results': volume_results,
                'atr_results': atr_results,
                'catalyst_results': catalyst_results,
                'strength_results': strength_results,
                'opportunities': opportunities
            }
            
        except Exception as e:
            logger.error(f"Error running comprehensive scan: {str(e)}")
            return {
                'error': str(e),
                'universe_size': 0,
                'deviation_results': [],
                'volume_results': [],
                'atr_results': [],
                'catalyst_results': [],
                'strength_results': [],
                'opportunities': []
            }
    
    def _find_opportunities(self, deviation_results, volume_results, atr_results, 
                           catalyst_results, strength_results):
        """
        Combine scan results to find the best trading opportunities
        
        Args:
            deviation_results (list): Results from price deviation scan
            volume_results (list): Results from volume scan
            atr_results (list): Results from ATR scan
            catalyst_results (list): Results from catalyst check
            strength_results (list): Results from relative strength calculation
            
        Returns:
            list: List of trading opportunities
        """
        try:
            # Create dictionaries for easy lookup
            deviation_dict = {item['symbol']: item for item in deviation_results}
            volume_dict = {item['symbol']: item for item in volume_results}
            atr_dict = {item['symbol']: item for item in atr_results}
            catalyst_dict = {item['symbol']: item for item in catalyst_results}
            strength_dict = {item['symbol']: item for item in strength_results}
            
            # Collect all unique symbols
            all_symbols = set(list(deviation_dict.keys()) + 
                             list(volume_dict.keys()) + 
                             list(atr_dict.keys()) + 
                             list(catalyst_dict.keys()))
            
            opportunities = []
            
            for symbol in all_symbols:
                # Skip if not in deviation results (must have significant price movement)
                if symbol not in deviation_dict:
                    continue
                
                # Calculate a score based on various factors
                score = 0
                
                # Price deviation factor (0-50 points)
                deviation = abs(deviation_dict[symbol]['deviation_pct'])
                score += min(deviation * 5, 50)  # Cap at 50 points
                
                # Direction preference (prefer upward movement)
                if deviation_dict[symbol]['direction'] == 'up':
                    score += 10
                
                # Volume factor (0-20 points)
                if symbol in volume_dict:
                    rel_volume = volume_dict[symbol]['relative_volume']
                    score += min(rel_volume * 5, 20)  # Cap at 20 points
                
                # ATR factor (0-15 points)
                if symbol in atr_dict:
                    atr_ratio = atr_dict[symbol]['atr_ratio']
                    score += min(atr_ratio * 5, 15)  # Cap at 15 points
                
                # Catalyst factor (0-25 points)
                if symbol in catalyst_dict:
                    score += 25
                
                # Relative strength factor (0-20 points)
                if symbol in strength_dict:
                    percentile = strength_dict[symbol]['percentile']
                    score += percentile / 5  # 0-20 points based on percentile
                
                # Create opportunity object
                opportunity = {
                    'symbol': symbol,
                    'score': score,
                    'price': deviation_dict[symbol]['current_price'],
                    'deviation_pct': deviation_dict[symbol]['deviation_pct'],
                    'direction': deviation_dict[symbol]['direction'],
                    'has_catalyst': symbol in catalyst_dict,
                    'relative_volume': volume_dict[symbol]['relative_volume'] if symbol in volume_dict else 0,
                    'atr_percentage': atr_dict[symbol]['atr_percentage'] if symbol in atr_dict else 0,
                    'relative_strength_percentile': strength_dict[symbol]['percentile'] if symbol in strength_dict else 0
                }
                
                # Add catalyst details if available
                if symbol in catalyst_dict:
                    opportunity['catalyst'] = {
                        'type': catalyst_dict[symbol]['catalyst_type'],
                        'news_title': catalyst_dict[symbol]['news_title'],
                        'news_link': catalyst_dict[symbol]['news_link']
                    }
                
                opportunities.append(opportunity)
            
            # Sort opportunities by score (descending)
            opportunities.sort(key=lambda x: x['score'], reverse=True)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error finding opportunities: {str(e)}")
            return []


# Example usage
if __name__ == "__main__":
    # Initialize scanner
    scanner = StockScanner()
    
    # Run a test scan with a small universe
    test_symbols = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA']
    
    # Scan for price deviation
    deviation_results = scanner.scan_for_price_deviation(test_symbols)
    print("\nStocks with significant price deviation:")
    for result in deviation_results:
        print(f"{result['symbol']}: {result['deviation_pct']:.2f}% ({result['direction']})")
    
    # Scan for high relative volume
    volume_results = scanner.scan_for_high_relative_volume(test_symbols)
    print("\nStocks with high relative volume:")
    for result in volume_results:
        print(f"{result['symbol']}: {result['relative_volume']:.2f}x")
    
    # Check for catalysts
    catalyst_results = scanner.check_for_catalysts(test_symbols)
    print("\nStocks with potential catalysts:")
    for result in catalyst_results:
        print(f"{result['symbol']}: {result['news_title']}")
