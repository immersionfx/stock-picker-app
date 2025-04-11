"""
Trading Strategy Module for Stock Picker Application

This module implements trading strategy logic based on the stock scanner results:
- Risk management rules (risk $50 to make $100, daily max loss -$100)
- Position sizing
- Entry and exit points
- Stop loss calculation
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from data_retrieval import MarketDataFetcher
from stock_scanner import StockScanner, ATRCalculator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('trading_strategy')

class TradingStrategy:
    """
    Class for implementing trading strategy logic
    """
    
    def __init__(self, account_size=10000, max_daily_loss=100, risk_reward_ratio=2.0):
        """
        Initialize the TradingStrategy
        
        Args:
            account_size (float): Trading account size in dollars
            max_daily_loss (float): Maximum daily loss in dollars
            risk_reward_ratio (float): Risk-reward ratio (e.g., 2.0 means risking $50 to make $100)
        """
        self.account_size = account_size
        self.max_daily_loss = max_daily_loss
        self.risk_reward_ratio = risk_reward_ratio
        self.max_risk_per_trade = 50  # Risk $50 per trade as per requirements
        
        self.market_data = MarketDataFetcher()
        self.scanner = StockScanner()
        self.atr_calculator = ATRCalculator()
        
        # Trading session tracking
        self.daily_pnl = 0
        self.consecutive_losses = 0
        self.trades = []
    
    def calculate_position_size(self, entry_price, stop_loss_price):
        """
        Calculate position size based on risk parameters
        
        Args:
            entry_price (float): Entry price
            stop_loss_price (float): Stop loss price
            
        Returns:
            float: Number of shares to trade
        """
        try:
            # Calculate risk per share
            risk_per_share = abs(entry_price - stop_loss_price)
            
            if risk_per_share <= 0:
                logger.warning("Invalid risk per share (zero or negative)")
                return 0
            
            # Calculate number of shares based on max risk per trade
            shares = self.max_risk_per_trade / risk_per_share
            
            # Round down to nearest whole share
            shares = int(shares)
            
            # Calculate total position value
            position_value = shares * entry_price
            
            # Check if position value exceeds account size
            if position_value > self.account_size * 0.25:  # Limit to 25% of account
                shares = int((self.account_size * 0.25) / entry_price)
                logger.info(f"Position size reduced to {shares} shares due to account size limit")
            
            return shares
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return 0
    
    def calculate_stop_loss(self, symbol, entry_price, direction, atr_multiplier=1.5):
        """
        Calculate stop loss price based on ATR
        
        Args:
            symbol (str): Stock symbol
            entry_price (float): Entry price
            direction (str): Trade direction ('long' or 'short')
            atr_multiplier (float): Multiplier for ATR to set stop loss
            
        Returns:
            float: Stop loss price
        """
        try:
            # Get historical data
            data = self.market_data.get_stock_data(symbol, period="20d", interval="1d")
            
            if data.empty:
                logger.warning(f"No data available for {symbol}")
                
                # Fallback: use a percentage-based stop loss
                if direction == 'long':
                    return entry_price * 0.97  # 3% below entry for long
                else:
                    return entry_price * 1.03  # 3% above entry for short
            
            # Calculate ATR
            atr = self.atr_calculator.calculate_atr(data)
            
            if atr.empty:
                logger.warning(f"Could not calculate ATR for {symbol}")
                
                # Fallback: use a percentage-based stop loss
                if direction == 'long':
                    return entry_price * 0.97  # 3% below entry for long
                else:
                    return entry_price * 1.03  # 3% above entry for short
            
            # Get latest ATR value
            latest_atr = atr.iloc[-1]
            
            # Calculate stop loss based on ATR
            if direction == 'long':
                stop_loss = entry_price - (latest_atr * atr_multiplier)
            else:
                stop_loss = entry_price + (latest_atr * atr_multiplier)
            
            return stop_loss
            
        except Exception as e:
            logger.error(f"Error calculating stop loss: {str(e)}")
            
            # Fallback: use a percentage-based stop loss
            if direction == 'long':
                return entry_price * 0.97  # 3% below entry for long
            else:
                return entry_price * 1.03  # 3% above entry for short
    
    def calculate_take_profit(self, entry_price, stop_loss_price, direction):
        """
        Calculate take profit price based on risk-reward ratio
        
        Args:
            entry_price (float): Entry price
            stop_loss_price (float): Stop loss price
            direction (str): Trade direction ('long' or 'short')
            
        Returns:
            float: Take profit price
        """
        try:
            # Calculate risk per share
            risk_per_share = abs(entry_price - stop_loss_price)
            
            # Calculate reward per share based on risk-reward ratio
            reward_per_share = risk_per_share * self.risk_reward_ratio
            
            # Calculate take profit price
            if direction == 'long':
                take_profit = entry_price + reward_per_share
            else:
                take_profit = entry_price - reward_per_share
            
            return take_profit
            
        except Exception as e:
            logger.error(f"Error calculating take profit: {str(e)}")
            
            # Fallback: use a percentage-based take profit
            if direction == 'long':
                return entry_price * 1.06  # 6% above entry for long
            else:
                return entry_price * 0.94  # 6% below entry for short
    
    def can_take_trade(self):
        """
        Check if a new trade can be taken based on risk management rules
        
        Returns:
            bool: True if a new trade can be taken, False otherwise
        """
        # Check if daily loss limit has been reached
        if self.daily_pnl <= -self.max_daily_loss:
            logger.info("Daily loss limit reached, no more trades today")
            return False
        
        # Check if three consecutive losses have occurred
        if self.consecutive_losses >= 3:
            logger.info("Three consecutive losses reached, no more trades today")
            return False
        
        return True
    
    def generate_trade_plan(self, opportunity):
        """
        Generate a trade plan for a given opportunity
        
        Args:
            opportunity (dict): Trading opportunity from scanner
            
        Returns:
            dict: Trade plan with entry, stop loss, take profit, and position size
        """
        try:
            # Check if we can take a trade
            if not self.can_take_trade():
                return None
            
            symbol = opportunity['symbol']
            current_price = opportunity['price']
            direction = 'long' if opportunity['direction'] == 'up' else 'short'
            
            # For simplicity, we'll use the current price as entry
            entry_price = current_price
            
            # Calculate stop loss
            stop_loss = self.calculate_stop_loss(symbol, entry_price, direction)
            
            # Calculate take profit
            take_profit = self.calculate_take_profit(entry_price, stop_loss, direction)
            
            # Calculate position size
            position_size = self.calculate_position_size(entry_price, stop_loss)
            
            # Calculate potential profit and loss
            potential_loss = position_size * abs(entry_price - stop_loss)
            potential_profit = position_size * abs(entry_price - take_profit)
            
            # Create trade plan
            trade_plan = {
                'symbol': symbol,
                'direction': direction,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'position_size': position_size,
                'potential_loss': potential_loss,
                'potential_profit': potential_profit,
                'risk_reward_ratio': self.risk_reward_ratio,
                'score': opportunity['score'],
                'deviation_pct': opportunity['deviation_pct'],
                'has_catalyst': opportunity.get('has_catalyst', False),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Add catalyst details if available
            if 'catalyst' in opportunity:
                trade_plan['catalyst'] = opportunity['catalyst']
            
            return trade_plan
            
        except Exception as e:
            logger.error(f"Error generating trade plan: {str(e)}")
            return None
    
    def generate_trade_plans(self, opportunities, max_plans=5):
        """
        Generate trade plans for multiple opportunities
        
        Args:
            opportunities (list): List of trading opportunities from scanner
            max_plans (int): Maximum number of trade plans to generate
            
        Returns:
            list: List of trade plans
        """
        trade_plans = []
        
        for opportunity in opportunities[:max_plans]:
            trade_plan = self.generate_trade_plan(opportunity)
            if trade_plan:
                trade_plans.append(trade_plan)
        
        return trade_plans
    
    def record_trade_result(self, trade_plan, result, actual_profit_loss):
        """
        Record the result of a trade
        
        Args:
            trade_plan (dict): Trade plan
            result (str): Trade result ('win', 'loss', or 'breakeven')
            actual_profit_loss (float): Actual profit or loss from the trade
            
        Returns:
            None
        """
        # Update daily P&L
        self.daily_pnl += actual_profit_loss
        
        # Update consecutive losses
        if result == 'loss':
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        # Record trade
        trade_record = {
            'symbol': trade_plan['symbol'],
            'direction': trade_plan['direction'],
            'entry_price': trade_plan['entry_price'],
            'stop_loss': trade_plan['stop_loss'],
            'take_profit': trade_plan['take_profit'],
            'position_size': trade_plan['position_size'],
            'result': result,
            'profit_loss': actual_profit_loss,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.trades.append(trade_record)
        
        logger.info(f"Trade recorded: {trade_record['symbol']} {trade_record['direction']} - {result} (${actual_profit_loss:.2f})")
        logger.info(f"Daily P&L: ${self.daily_pnl:.2f}, Consecutive losses: {self.consecutive_losses}")
    
    def reset_daily_stats(self):
        """
        Reset daily trading statistics
        
        Returns:
            None
        """
        self.daily_pnl = 0
        self.consecutive_losses = 0
        logger.info("Daily trading statistics reset")
    
    def get_trading_summary(self):
        """
        Get a summary of trading activity
        
        Returns:
            dict: Trading summary
        """
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_profit_loss': 0,
                'average_profit_loss': 0,
                'largest_win': 0,
                'largest_loss': 0
            }
        
        # Calculate statistics
        total_trades = len(self.trades)
        winning_trades = sum(1 for trade in self.trades if trade['result'] == 'win')
        losing_trades = sum(1 for trade in self.trades if trade['result'] == 'loss')
        
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        total_profit_loss = sum(trade['profit_loss'] for trade in self.trades)
        average_profit_loss = total_profit_loss / total_trades if total_trades > 0 else 0
        
        largest_win = max((trade['profit_loss'] for trade in self.trades if trade['result'] == 'win'), default=0)
        largest_loss = min((trade['profit_loss'] for trade in self.trades if trade['result'] == 'loss'), default=0)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_profit_loss': total_profit_loss,
            'average_profit_loss': average_profit_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'daily_pnl': self.daily_pnl,
            'consecutive_losses': self.consecutive_losses
        }


# Example usage
if __name__ == "__main__":
    # Initialize trading strategy
    strategy = TradingStrategy(account_size=10000, max_daily_loss=100, risk_reward_ratio=2.0)
    
    # Initialize scanner
    scanner = StockScanner()
    
    # Run a test scan with a small universe
    test_symbols = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA']
    
    # Scan for price deviation
    deviation_results = scanner.scan_for_price_deviation(test_symbols)
    
    # Create sample opportunities
    sample_opportunities = []
    for result in deviation_results:
        opportunity = {
            'symbol': result['symbol'],
            'price': result['current_price'],
            'deviation_pct': result['deviation_pct'],
            'direction': result['direction'],
            'has_catalyst': False,
            'score': abs(result['deviation_pct']) * 5  # Simple score for testing
        }
        sample_opportunities.append(opportunity)
    
    # Generate trade plans
    trade_plans = strategy.generate_trade_plans(sample_opportunities)
    
    # Print trade plans
    print("\nGenerated Trade Plans:")
    for plan in trade_plans:
        print(f"\nSymbol: {plan['symbol']} ({plan['direction']})")
        print(f"Entry: ${plan['entry_price']:.2f}")
        print(f"Stop Loss: ${plan['stop_loss']:.2f}")
        print(f"Take Profit: ${plan['take_profit']:.2f}")
        print(f"Position Size: {plan['position_size']} shares")
        print(f"Potential Loss: ${plan['potential_loss']:.2f}")
        print(f"Potential Profit: ${plan['potential_profit']:.2f}")
        print(f"Risk-Reward Ratio: {plan['risk_reward_ratio']:.1f}")
