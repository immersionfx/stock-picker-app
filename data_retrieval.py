"""
Data Retrieval Module for Stock Picker Application

This module is responsible for fetching stock data from various sources including:
- Yahoo Finance API for market data
- News data for catalysts
"""

import sys
import os
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('data_retrieval')

class MarketDataFetcher:
    """
    Class for retrieving market data from Yahoo Finance
    """
    
    def __init__(self):
        """Initialize the MarketDataFetcher"""
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = 300  # Cache duration in seconds (5 minutes)
        
    def get_stock_data(self, symbol, period="1d", interval="1m", include_premarket=True):
        """
        Get stock data for a specific symbol
        
        Args:
            symbol (str): Stock symbol
            period (str): Period of data to retrieve (e.g., "1d", "5d", "1mo")
            interval (str): Data interval (e.g., "1m", "5m", "1h", "1d")
            include_premarket (bool): Whether to include pre-market data
            
        Returns:
            pandas.DataFrame: DataFrame containing stock data
        """
        cache_key = f"{symbol}_{period}_{interval}_{include_premarket}"
        
        # Check if data is in cache and not expired
        current_time = time.time()
        if (cache_key in self.cache and 
            cache_key in self.cache_expiry and 
            current_time < self.cache_expiry[cache_key]):
            logger.info(f"Using cached data for {symbol}")
            return self.cache[cache_key]
        
        try:
            logger.info(f"Fetching data for {symbol} with period={period}, interval={interval}")
            stock = yf.Ticker(symbol)
            data = stock.history(period=period, interval=interval, prepost=include_premarket)
            
            # Cache the data
            self.cache[cache_key] = data
            self.cache_expiry[cache_key] = current_time + self.cache_duration
            
            return data
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def get_multiple_stock_data(self, symbols, period="1d", interval="1m", include_premarket=True):
        """
        Get stock data for multiple symbols
        
        Args:
            symbols (list): List of stock symbols
            period (str): Period of data to retrieve
            interval (str): Data interval
            include_premarket (bool): Whether to include pre-market data
            
        Returns:
            dict: Dictionary mapping symbols to their respective DataFrames
        """
        result = {}
        for symbol in symbols:
            result[symbol] = self.get_stock_data(symbol, period, interval, include_premarket)
        return result
    
    def get_premarket_data(self, symbols):
        """
        Get pre-market data for a list of symbols
        
        Args:
            symbols (list): List of stock symbols
            
        Returns:
            dict: Dictionary mapping symbols to their pre-market data
        """
        # Get current date
        today = datetime.now().strftime('%Y-%m-%d')
        
        result = {}
        for symbol in symbols:
            try:
                # Use 1m interval to get the most recent pre-market data
                data = self.get_stock_data(symbol, period="1d", interval="1m", include_premarket=True)
                
                # Filter for pre-market data (before 9:30 AM)
                market_open_time = pd.Timestamp(f"{today} 09:30:00", tz='America/New_York')
                premarket_data = data[data.index < market_open_time]
                
                if not premarket_data.empty:
                    result[symbol] = premarket_data
                    
            except Exception as e:
                logger.error(f"Error fetching pre-market data for {symbol}: {str(e)}")
                
        return result
    
    def get_stock_universe(self, min_price=5, max_price=100, min_volume=500000):
        """
        Get a universe of stocks that meet basic criteria
        
        Args:
            min_price (float): Minimum stock price
            max_price (float): Maximum stock price
            min_volume (int): Minimum average daily volume
            
        Returns:
            list: List of stock symbols that meet the criteria
        """
        try:
            # This is a simplified approach. In a production environment,
            # you would use a more comprehensive method to get the stock universe.
            
            # For demonstration, we'll use a list of major indices and extract their components
            indices = ['^GSPC', '^NDX', '^DJI']  # S&P 500, Nasdaq 100, Dow Jones
            
            all_symbols = []
            for index in indices:
                try:
                    # Get index components
                    index_ticker = yf.Ticker(index)
                    
                    # This is a workaround as yfinance doesn't directly provide index components
                    # In a production environment, you would use a more reliable data source
                    if hasattr(index_ticker, 'components'):
                        components = index_ticker.components
                        all_symbols.extend(components)
                except Exception as e:
                    logger.error(f"Error getting components for index {index}: {str(e)}")
            
            # For demonstration, if we couldn't get components, use a sample list
            if not all_symbols:
                logger.info("Using sample stock list as fallback")
                all_symbols = [
                    'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA', 'JPM', 
                    'JNJ', 'V', 'PG', 'UNH', 'HD', 'BAC', 'MA', 'DIS', 'ADBE', 'CRM', 
                    'NFLX', 'INTC', 'VZ', 'CSCO', 'PFE', 'ABT', 'KO', 'PEP', 'NKE', 
                    'MRK', 'WMT', 'T', 'AMD', 'PYPL', 'CMCSA', 'XOM', 'CVX', 'COST'
                ]
            
            # Filter the symbols based on price and volume criteria
            filtered_symbols = []
            for symbol in all_symbols:
                try:
                    data = self.get_stock_data(symbol, period="5d", interval="1d")
                    if not data.empty:
                        avg_price = data['Close'].mean()
                        avg_volume = data['Volume'].mean()
                        
                        if (min_price <= avg_price <= max_price and avg_volume >= min_volume):
                            filtered_symbols.append(symbol)
                except Exception as e:
                    logger.error(f"Error filtering symbol {symbol}: {str(e)}")
            
            return filtered_symbols
            
        except Exception as e:
            logger.error(f"Error getting stock universe: {str(e)}")
            return []

    def get_relative_volume(self, symbol, lookback=20):
        """
        Calculate relative volume for a stock
        
        Args:
            symbol (str): Stock symbol
            lookback (int): Number of days to look back for average volume
            
        Returns:
            float: Relative volume (today's volume / average volume)
        """
        try:
            # Get historical data
            hist_data = self.get_stock_data(symbol, period=f"{lookback+1}d", interval="1d")
            
            if hist_data.empty or len(hist_data) < lookback:
                return 0
            
            # Calculate average volume excluding the most recent day
            avg_volume = hist_data['Volume'][:-1].mean()
            
            # Get today's volume
            today_volume = hist_data['Volume'].iloc[-1]
            
            # Calculate relative volume
            if avg_volume > 0:
                rel_volume = today_volume / avg_volume
                return rel_volume
            else:
                return 0
                
        except Exception as e:
            logger.error(f"Error calculating relative volume for {symbol}: {str(e)}")
            return 0


class NewsDataFetcher:
    """
    Class for retrieving news data for stocks
    """
    
    def __init__(self):
        """Initialize the NewsDataFetcher"""
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = 1800  # Cache duration in seconds (30 minutes)
    
    def get_stock_news(self, symbol, max_news=5):
        """
        Get recent news for a specific stock
        
        Args:
            symbol (str): Stock symbol
            max_news (int): Maximum number of news items to retrieve
            
        Returns:
            list: List of news items with title, publisher, link, and publish date
        """
        cache_key = f"{symbol}_news"
        
        # Check if data is in cache and not expired
        current_time = time.time()
        if (cache_key in self.cache and 
            cache_key in self.cache_expiry and 
            current_time < self.cache_expiry[cache_key]):
            return self.cache[cache_key]
        
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            # Format the news data
            formatted_news = []
            for item in news[:max_news]:
                formatted_news.append({
                    'title': item.get('title', ''),
                    'publisher': item.get('publisher', ''),
                    'link': item.get('link', ''),
                    'publish_date': datetime.fromtimestamp(item.get('providerPublishTime', 0)).strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # Cache the data
            self.cache[cache_key] = formatted_news
            self.cache_expiry[cache_key] = current_time + self.cache_duration
            
            return formatted_news
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {str(e)}")
            return []
    
    def check_for_catalyst(self, symbol):
        """
        Check if there are any potential catalysts in the news
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            dict: Dictionary with catalyst information if found, None otherwise
        """
        try:
            news = self.get_stock_news(symbol)
            
            # Keywords that might indicate a catalyst
            catalyst_keywords = [
                'earnings', 'beat', 'miss', 'guidance', 'upgrade', 'downgrade',
                'fda', 'approval', 'patent', 'launch', 'partnership', 'contract',
                'lawsuit', 'settlement', 'investigation', 'recall', 'dividend',
                'split', 'buyback', 'acquisition', 'merger', 'spinoff', 'ceo',
                'executive', 'resignation', 'appointed', 'clinical', 'trial',
                'data', 'results', 'breakthrough', 'innovation'
            ]
            
            # Keywords to avoid (as per user preferences)
            avoid_keywords = ['merger', 'buyout', 'acquisition']
            
            for item in news:
                title = item['title'].lower()
                
                # Check for catalyst keywords
                found_catalysts = [keyword for keyword in catalyst_keywords if keyword in title]
                
                # Check for keywords to avoid
                found_avoid = [keyword for keyword in avoid_keywords if keyword in title]
                
                if found_catalysts and not found_avoid:
                    return {
                        'has_catalyst': True,
                        'catalyst_type': found_catalysts,
                        'news_item': item
                    }
            
            return {'has_catalyst': False}
            
        except Exception as e:
            logger.error(f"Error checking for catalyst for {symbol}: {str(e)}")
            return {'has_catalyst': False, 'error': str(e)}


# Example usage
if __name__ == "__main__":
    # Initialize data fetchers
    market_data = MarketDataFetcher()
    news_data = NewsDataFetcher()
    
    # Example: Get pre-market data for a few stocks
    symbols = ['AAPL', 'MSFT', 'AMZN']
    premarket_data = market_data.get_premarket_data(symbols)
    
    for symbol, data in premarket_data.items():
        print(f"\nPre-market data for {symbol}:")
        print(data.tail())
    
    # Example: Check for catalysts
    for symbol in symbols:
        catalyst_info = news_data.check_for_catalyst(symbol)
        if catalyst_info['has_catalyst']:
            print(f"\nCatalyst found for {symbol}:")
            print(f"Type: {catalyst_info['catalyst_type']}")
            print(f"News: {catalyst_info['news_item']['title']}")
        else:
            print(f"\nNo catalyst found for {symbol}")
