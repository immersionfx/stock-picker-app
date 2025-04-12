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
            return {}
    
    def _find_opportunities(self, deviation_results, volume_results, atr_results, catalyst_results, strength_results):
        """
        Find trading opportunities by combining results from different scans
        
        Args:
            deviation_results (list): Results from price deviation scan
            volume_results (list): Results from volume scan
            atr_results (list): Results from ATR scan
            catalyst_results (list): Results from catalyst check
            strength_results (list): Results from relative strength calculation
            
        Returns:
            list: List of dictionaries with trading opportunities
        """
        opportunities = []
        
        # Create lookup dictionaries for faster access
        volume_lookup = {item['symbol']: item for item in volume_results}
        atr_lookup = {item['symbol']: item for item in atr_results}
        catalyst_lookup = {item['symbol']: item for item in catalyst_results}
        strength_lookup = {item['symbol']: item for item in strength_results}
        
        # Start with stocks that have significant price deviation
        for dev_item in deviation_results:
            symbol = dev_item['symbol']
            score = 0
            opportunity = {
                'symbol': symbol,
                'price': dev_item['current_price'],
                'deviation': dev_item['deviation_pct'],
                'direction': dev_item['direction'],
                'signals': []
            }
            
            # Add price deviation signal
            opportunity['signals'].append({
                'type': 'price_deviation',
                'value': dev_item['deviation_pct'],
                'description': f"{abs(dev_item['deviation_pct']):.2f}% {dev_item['direction']}"
            })
            score += min(abs(dev_item['deviation_pct']) / 2, 5)  # Cap at 5 points
            
            # Check for high volume
            if symbol in volume_lookup:
                vol_item = volume_lookup[symbol]
                opportunity['relative_volume'] = vol_item['relative_volume']
                opportunity['signals'].append({
                    'type': 'high_volume',
                    'value': vol_item['relative_volume'],
                    'description': f"Volume {vol_item['relative_volume']:.2f}x average"
                })
                score += min(vol_item['relative_volume'] - 1, 3)  # Cap at 3 points
            
            # Check for high ATR
            if symbol in atr_lookup:
                atr_item = atr_lookup[symbol]
                opportunity['atr_ratio'] = atr_item['atr_ratio']
                opportunity['signals'].append({
                    'type': 'high_atr',
                    'value': atr_item['atr_ratio'],
                    'description': f"ATR {atr_item['atr_ratio']:.2f}x average"
                })
                score += min(atr_item['atr_ratio'] - 1, 3)  # Cap at 3 points
            
            # Check for catalysts
            if symbol in catalyst_lookup:
                cat_item = catalyst_lookup[symbol]
                opportunity['catalyst'] = cat_item['catalyst_type']
                opportunity['signals'].append({
                    'type': 'catalyst',
                    'value': 1,
                    'description': f"Catalyst: {', '.join(cat_item['catalyst_type'])}"
                })
                score += 3  # Fixed score for having a catalyst
            
            # Check for relative strength
            if symbol in strength_lookup:
                str_item = strength_lookup[symbol]
                opportunity['relative_strength'] = str_item['relative_strength']
                opportunity['strength_percentile'] = str_item['percentile']
                
                # Add signal if in top 25%
                if str_item['percentile'] >= 75:
                    opportunity['signals'].append({
                        'type': 'high_strength',
                        'value': str_item['percentile'],
                        'description': f"Strong relative performance (top {100-str_item['percentile']:.0f}%)"
                    })
                    score += min((str_item['percentile'] - 75) / 5, 3)  # Cap at 3 points
            
            # Add total score
            opportunity['score'] = score
            
            # Add to opportunities if score is high enough
            if score >= 3:  # Minimum score threshold
                opportunities.append(opportunity)
        
        # Sort opportunities by score (descending)
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        return opportunities
        
    def get_all_stocks_by_significance(self, min_price=5, max_price=100, min_volume=500000):
        """
        Get all stocks in the universe ordered by their overall significance score
        
        Args:
            min_price (float): Minimum stock price
            max_price (float): Maximum stock price
            min_volume (int): Minimum average daily volume
            
        Returns:
            list: List of dictionaries with stock information ordered by significance
        """
        try:
            logger.info("Getting all stocks ordered by significance")
            
            # Get stock universe
            universe = self.market_data.get_stock_universe(min_price, max_price, min_volume)
            logger.info(f"Found {len(universe)} stocks in universe")
            
            # Get data for all stocks
            stock_data = {}
            for symbol in universe:
                try:
                    # Get basic data
                    data = self.market_data.get_stock_data(symbol, period="5d", interval="1d")
                    if data.empty:
                        continue
                    
                    # Calculate basic metrics
                    current_price = data['Close'].iloc[-1]
                    prev_close = data['Close'].iloc[-2] if len(data) > 1 else data['Close'].iloc[0]
                    deviation_pct = ((current_price - prev_close) / prev_close) * 100
                    
                    # Get volume data
                    rel_volume = self.market_data.get_relative_volume(symbol)
                    
                    # Calculate ATR
                    atr = self.atr_calculator.calculate_atr(data, period=5)
                    atr_value = atr.iloc[-1] if not atr.empty and len(atr) > 0 else 0
                    atr_percentage = (atr_value / current_price) * 100 if current_price > 0 else 0
                    
                    # Store data
                    stock_data[symbol] = {
                        'symbol': symbol,
                        'price': current_price,
                        'deviation_pct': deviation_pct,
                        'direction': 'up' if deviation_pct > 0 else 'down',
                        'relative_volume': rel_volume,
                        'atr_percentage': atr_percentage,
                        'volume': data['Volume'].iloc[-1]
                    }
                    
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {str(e)}")
            
            # Calculate significance score for each stock
            results = []
            for symbol, data in stock_data.items():
                # Calculate a composite significance score
                significance = (
                    abs(data['deviation_pct']) * 0.5 +  # Price deviation (50% weight)
                    (data['relative_volume'] - 1) * 30 if data['relative_volume'] > 1 else 0 +  # Volume (30% weight)
                    data['atr_percentage'] * 0.2  # Volatility (20% weight)
                )
                
                # Add significance score to data
                data['significance'] = significance
                results.append(data)
            
            # Sort by significance score (descending)
            results.sort(key=lambda x: x['significance'], reverse=True)
            
            logger.info(f"Processed {len(results)} stocks by significance")
            return results
            
        except Exception as e:
            logger.error(f"Error getting stocks by significance: {str(e)}")
            return []
    
    def get_metric_tooltips(self):
        """
        Get tooltip information for all metrics used in the stock scanner
        
        Returns:
            dict: Dictionary with metric names as keys and tooltip information as values
        """
        return {
            'price_deviation': {
                'title': 'Price Deviation',
                'description': 'The percentage change in price compared to the previous close.',
                'interpretation': 'Higher absolute values (>4%) indicate significant price movement. Positive values show upward movement, negative values show downward movement.'
            },
            'relative_volume': {
                'title': 'Relative Volume',
                'description': 'Today\'s volume compared to the average daily volume.',
                'interpretation': 'Values above 1.5 indicate higher than normal trading activity. Higher values suggest stronger interest in the stock.'
            },
            'atr': {
                'title': 'Average True Range (ATR)',
                'description': 'A measure of stock volatility over a specified period.',
                'interpretation': 'Higher values indicate more volatility. ATR is useful for setting stop losses and determining position sizes.'
            },
            'atr_percentage': {
                'title': 'ATR Percentage',
                'description': 'ATR as a percentage of the stock price.',
                'interpretation': 'Normalizes ATR across different price levels. Higher values indicate more volatile stocks relative to their price.'
            },
            'atr_ratio': {
                'title': 'ATR Ratio',
                'description': 'The ratio of a stock\'s ATR percentage to the average ATR percentage of all stocks.',
                'interpretation': 'Values above 1 indicate above-average volatility. Higher values suggest potential for larger price swings.'
            },
            'relative_strength': {
                'title': 'Relative Strength',
                'description': 'The percentage price change over a specified period (typically 13 weeks).',
                'interpretation': 'Higher values indicate stronger performance. Stocks with positive values are outperforming, while negative values show underperformance.'
            },
            'strength_percentile': {
                'title': 'Strength Percentile',
                'description': 'The percentile rank of a stock\'s relative strength compared to other stocks.',
                'interpretation': 'Values above 75 indicate top-performing stocks. Higher percentiles suggest stronger momentum.'
            },
            'significance': {
                'title': 'Significance Score',
                'description': 'A composite score based on price deviation, volume, and volatility.',
                'interpretation': 'Higher values indicate stocks with more significant market activity. Useful for identifying stocks that deserve attention.'
            },
            'score': {
                'title': 'Opportunity Score',
                'description': 'A weighted score based on multiple factors including price deviation, volume, ATR, catalysts, and relative strength.',
                'interpretation': 'Higher scores indicate more compelling trading opportunities. Scores above 10 suggest strong potential.'
            },
            'catalyst': {
                'title': 'Catalyst',
                'description': 'Significant news or events that could impact the stock price.',
                'interpretation': 'The presence of catalysts often explains price movements and may indicate potential for continued movement.'
            },
            'volume': {
                'title': 'Volume',
                'description': 'The number of shares traded during the current period.',
                'interpretation': 'Higher values indicate more trading activity. Volume confirms price movements - strong moves with high volume are more reliable.'
            },
            'avg_volume': {
                'title': 'Average Volume',
                'description': 'The average number of shares traded daily over a specified period.',
                'interpretation': 'Used as a baseline to measure current trading activity. Higher values indicate more liquid stocks.'
            }
        }
    
    def format_tooltip_for_streamlit(self, metric_name):
        """
        Format tooltip information for display in Streamlit
        
        Args:
            metric_name (str): Name of the metric to get tooltip for
            
        Returns:
            str: Formatted tooltip text for Streamlit
        """
        tooltips = self.get_metric_tooltips()
        
        if metric_name in tooltips:
            info = tooltips[metric_name]
            return f"""
            **{info['title']}**
            
            {info['description']}
            
            *Interpretation:* {info['interpretation']}
            """
        else:
            return f"Information about {metric_name}"