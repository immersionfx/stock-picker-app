# Stock Picker Application Architecture

## Overview
The Stock Picker application is designed to help day traders identify potential trading opportunities based on specific criteria including price movement, volume, ATR (Average True Range), and pre-market activity. The application follows a modular design pattern to ensure maintainability, scalability, and ease of use.

## System Components

### 1. Data Retrieval Module
This module is responsible for fetching stock data from various sources.

**Components:**
- **Market Data Fetcher**: Retrieves real-time and historical market data
  - Pre-market data (from 7am)
  - Regular market hours data (9:30am-4pm)
  - Historical data for technical analysis
- **News Data Fetcher**: Retrieves news and catalysts for stocks
- **Data Caching**: Stores frequently accessed data to improve performance

**Technologies:**
- Yahoo Finance API (via datasource module)
- yfinance Python library (for additional functionality)
- Requests library for API calls

### 2. Stock Scanning Module
This module applies filters to identify stocks meeting the specified criteria.

**Components:**
- **Filter Engine**: Applies various filters to the stock universe
  - Price deviation filter (>4% movement)
  - Volume filter (high relative volume)
  - Liquidity filter (to avoid slippage)
  - Price range filter
- **Stock Universe Manager**: Maintains the list of stocks to scan
- **Scan Scheduler**: Runs scans at specified intervals

**Technologies:**
- Pandas for data manipulation
- NumPy for numerical operations

### 3. Technical Analysis Module
This module calculates technical indicators used in the trading strategy.

**Components:**
- **Indicator Calculator**: Computes various technical indicators
  - ATR (Average True Range) calculator
  - EMA (Exponential Moving Average) calculator
  - Relative Strength calculator (13-week ranking)
- **Pattern Detector**: Identifies chart patterns
- **Ranking System**: Ranks stocks based on technical criteria

**Technologies:**
- TA-Lib or stockstats for technical indicators
- Pandas for data manipulation
- NumPy for numerical operations

### 4. News Analysis Module
This module analyzes news to identify potential catalysts.

**Components:**
- **News Fetcher**: Retrieves news for stocks
- **Catalyst Identifier**: Identifies potential catalysts
- **Sentiment Analyzer**: Analyzes news sentiment

**Technologies:**
- Yahoo Finance API for news data
- NLTK or TextBlob for basic sentiment analysis

### 5. User Interface Module
This module provides the interface for users to interact with the application.

**Components:**
- **Dashboard**: Displays scan results and key metrics
- **Stock Detail View**: Shows detailed information for selected stocks
- **Configuration Panel**: Allows users to customize scan parameters
- **Alert System**: Notifies users of new opportunities

**Technologies:**
- Streamlit for web-based UI
- Plotly for interactive charts
- Pandas for data display

## Data Flow

1. **Data Collection Phase**
   - Fetch pre-market data starting at 7am
   - Retrieve historical data for technical analysis
   - Collect news and potential catalysts

2. **Scanning Phase**
   - Apply initial filters (price deviation, volume)
   - Calculate technical indicators
   - Rank stocks based on criteria

3. **Analysis Phase**
   - Perform deeper analysis on filtered stocks
   - Check for news catalysts
   - Apply relative strength ranking

4. **Presentation Phase**
   - Display results in user interface
   - Highlight top opportunities
   - Provide detailed analysis for selected stocks

## Implementation Strategy

### Phase 1: Core Functionality
- Implement data retrieval module
- Implement basic scanning functionality
- Create simple command-line interface

### Phase 2: Enhanced Analysis
- Implement technical analysis module
- Add news analysis capabilities
- Enhance scanning with additional filters

### Phase 3: User Interface
- Develop web-based dashboard
- Add interactive charts
- Implement configuration options

### Phase 4: Optimization
- Optimize performance
- Add caching mechanisms
- Implement parallel processing for faster scanning

## Risk Management Integration

The application will incorporate the user's risk management rules:
- Risk $50 to make $100 (1:2 risk-reward ratio)
- Daily max loss at -$100
- Stop after three consecutive losses

This will be implemented through:
- Position sizing calculator
- Risk tracking system
- Trading session manager

## Technical Requirements

- Python 3.8+
- Required libraries:
  - yfinance
  - pandas
  - numpy
  - ta-lib or stockstats
  - streamlit
  - plotly
  - requests
- Internet connection for real-time data
- Sufficient memory for data processing (minimum 4GB RAM recommended)

## Future Enhancements

- Machine learning for pattern recognition
- Integration with trading platforms for automated execution
- Mobile application for alerts on the go
- Backtesting module to validate strategies
- Additional data sources for enhanced analysis

## Metrics Guide

### Sidebar Metrics

1. **Price Filter**
   - **Min/Max Price**: Sets the price range for scanned stocks
   - **Interpretation**: 
     - Lower-priced stocks ($5-$20): Higher volatility, larger % moves
     - Mid-range stocks ($20-$50): Balance of volatility and stability
     - Higher-priced stocks ($50+): Generally more stable, institutional interest

2. **Volume Filter**
   - **Minimum Volume**: Daily trading volume threshold
   - **Interpretation**:
     - Below 500,000: May lack liquidity, higher spread risk
     - 500,000-2M: Good retail trading liquidity
     - Above 2M: High institutional interest, excellent liquidity

3. **Price Deviation**
   - **Minimum Deviation (%)**: Percentage change from previous close
   - **Interpretation**:
     - 2-4%: Minor movement, might indicate starting trend
     - 4-8%: Significant movement, primary trading focus
     - Above 8%: Major movement, higher volatility risk

4. **Relative Volume**
   - **Minimum Relative Volume**: Current volume compared to average
   - **Interpretation**:
     - 1.0-1.5x: Normal trading activity
     - 1.5-2.5x: Strong interest, good for trading
     - Above 2.5x: Exceptional interest, potential catalyst

5. **ATR Filter**
   - **Minimum ATR Ratio**: Stock's ATR compared to market average
   - **Interpretation**:
     - Below 1.0: Less volatile than average
     - 1.0-1.5: Normal volatility range
     - Above 1.5: Higher volatility, larger profit potential but higher risk

### Main Page Metrics

1. **Price Action**
   - **Current Price**: Real-time trading price
   - **Day High/Low**: Trading range for the day
   - **Pre-market High/Low**: Early trading range
   - **Interpretation**: Wide ranges indicate high volatility and trading opportunities

2. **Technical Indicators**
   - **ATR (Average True Range)**
     - Measures stock's average daily range
     - Higher values indicate more volatility and potential for larger moves
     - Used for stop loss and position sizing calculations

   - **13-Week Relative Strength**
     - Compares stock's performance to market
     - Above 70: Strong uptrend, outperforming
     - Below 30: Weak performance, potential reversal

3. **Volume Analysis**
   - **Current Volume**: Today's trading volume
   - **Average Volume**: 20-day average volume
   - **Relative Volume**: Ratio of current to average
   - **Interpretation**: Higher volumes validate price movements

4. **Risk Metrics**
   - **Stop Loss Distance**: Calculated safe stop loss level
   - **Risk Per Share**: Dollar risk based on stop loss
   - **Position Size**: Recommended number of shares
   - **Risk-Reward Ratio**: Potential profit vs risk (targeting 1:2)

5. **Catalyst Information**
   - **Has Catalyst**: Yes/No indicator
   - **Catalyst Type**: News, Earnings, FDA, etc.
   - **Interpretation**: Catalysts explain price movement and suggest potential continuation

6. **Trading Score**
   - **Composite score (0-100)**
   - Based on:
     - Price deviation (40%)
     - Relative volume (30%)
     - Technical factors (20%)
     - Catalyst presence (10%)
   - **Interpretation**:
     - Below 50: Weak opportunity
     - 50-70: Moderate opportunity
     - Above 70: Strong opportunity

### Trading Plan Metrics

1. **Entry Parameters**
   - **Entry Price**: Suggested entry point
   - **Stop Loss**: Maximum risk level
   - **Take Profit**: Profit target
   - **Position Size**: Number of shares based on risk

2. **Risk Analysis**
   - **Potential Loss**: Maximum dollar risk
   - **Potential Profit**: Target dollar profit
   - **Risk-Reward Ratio**: Profit potential vs risk
   - **Score**: Overall trade quality score
