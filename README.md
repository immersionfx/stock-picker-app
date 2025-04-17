# Stock Picker Application - User Guide

## Overview

The Stock Picker application is a powerful tool designed to help day traders identify potential trading opportunities based on specific criteria including price movement, volume, ATR (Average True Range), and pre-market activity. The application follows your trading strategy preferences, focusing on stocks that deviate more than 4%, especially those with high relative volume and clear catalysts.

## Features

- **Pre-market Scanning**: Starts scanning from 7am to identify early opportunities
- **Price Deviation Detection**: Focuses on stocks moving more than 4% from previous close
- **Volume Analysis**: Identifies stocks with high relative volume to ensure liquidity
- **ATR Calculation**: Measures volatility to find stocks with higher ATR vs. their sector
- **News & Catalyst Detection**: Automatically checks for news catalysts while avoiding mergers/buyouts
- **Risk Management**: Implements your risk management rules (risk $50 to make $100, daily max loss at -$100)
- **Position Sizing**: Automatically calculates appropriate position sizes based on risk parameters
- **Technical Analysis**: Includes 13-week relative strength ranking
- **Interactive Dashboard**: Displays all information in an easy-to-use interface

## Installation

### Prerequisites

- Python 3.8 or higher
- Internet connection for real-time data

### Installation Steps

1. Ensure you have Python installed on your system
2. Download and extract the Stock Picker application package
3. Open a terminal/command prompt and navigate to the extracted directory
4. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

To start the Stock Picker application:

```bash
python app.py
```

This will launch the Streamlit web interface in your default browser. If the browser doesn't open automatically, you can access the application at http://localhost:8501.

## Using the Application

### Dashboard

The main dashboard displays:

1. **Summary Metrics**: Overview of stocks scanned, matches found, and potential trades
2. **Top Trading Opportunities**: Table of the best trading opportunities based on your criteria
3. **Price Deviation Results**: Stocks with significant price movement

### Stock Details

Click on any stock in the dashboard to view detailed information:

1. **Price Chart**: Interactive candlestick chart with volume
2. **Technical Analysis**: ATR and relative strength metrics
3. **News**: Recent news and potential catalysts
4. **Trade Plan**: Suggested entry, stop loss, and take profit levels with risk analysis

### Settings

Adjust the application settings in the sidebar:

1. **Account Settings**:
   - Account Size: Your trading account size
   - Max Daily Loss: Maximum allowed daily loss
   - Risk Per Trade: Amount to risk per trade

2. **Scanner Settings**:
   - Min/Max Price: Price range for stocks to scan
   - Min Volume: Minimum volume threshold
   - Min Price Deviation: Minimum percentage movement to consider

## Trading Strategy

The application implements your specific trading strategy:

1. **Timing**: Focuses on the morning session (7am until momentum cools off)
2. **Stock Selection**: Prioritizes stocks deviating more than 4%
3. **Volume**: Identifies stocks with highest relative volume
4. **Catalysts**: Checks for news catalysts while avoiding mergers/buyouts
5. **Risk Management**: Implements your 1:2 risk-reward ratio and daily loss limits
6. **Technical Factors**: Considers previous trading ranges and relative strength

## Components

The application consists of several key components:

1. **Data Retrieval Module**: Fetches market data and news
2. **Stock Scanner Module**: Applies filters to identify opportunities
3. **Technical Analysis Module**: Calculates indicators like ATR and relative strength
4. **Trading Strategy Module**: Implements risk management and generates trade plans
5. **User Interface**: Streamlit-based dashboard for interaction

## Troubleshooting

If you encounter any issues:

1. **No data appears**: Check your internet connection
2. **Application crashes**: Ensure all dependencies are installed correctly
3. **No trading opportunities found**: Try adjusting the scanner settings in the sidebar

## Future Enhancements

Potential future improvements:

1. Integration with trading platforms for automated execution
2. Machine learning for pattern recognition
3. Mobile application for alerts on the go
4. Backtesting module to validate strategies
5. Additional data sources for enhanced analysis

## Support

For questions or support, please contact the developer.

---

Happy Trading!
