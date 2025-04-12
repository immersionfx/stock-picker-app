"""
User Interface Module for Stock Picker Application

This module creates a Streamlit-based user interface for the Stock Picker app,
displaying stock scanner results and trading recommendations.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import logging
import os
import sys

# Import our modules
from data_retrieval import MarketDataFetcher, NewsDataFetcher
from stock_scanner import StockScanner
from trading_strategy import TradingStrategy

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('stock_picker_ui')

# Initialize components
market_data = MarketDataFetcher()
news_data = NewsDataFetcher()
scanner = StockScanner()
strategy = TradingStrategy()

# Page configuration
st.set_page_config(
    page_title="Daily Stock Picker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
        margin-bottom: 0.5rem;
    }
    .card {
        border-radius: 5px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .card-green {
        background-color: rgba(76, 175, 80, 0.1);
        border-left: 5px solid #4CAF50;
    }
    .card-red {
        background-color: rgba(244, 67, 54, 0.1);
        border-left: 5px solid #F44336;
    }
    .card-blue {
        background-color: rgba(33, 150, 243, 0.1);
        border-left: 5px solid #2196F3;
    }
    .card-yellow {
        background-color: rgba(255, 193, 7, 0.1);
        border-left: 5px solid #FFC107;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #616161;
    }
    .up-value {
        color: #4CAF50;
    }
    .down-value {
        color: #F44336;
    }
    .highlight {
        background-color: yellow;
        padding: 0 2px;
    }
</style>
""", unsafe_allow_html=True)

def create_price_chart(symbol, period="5d", interval="15m", include_premarket=True):
    """
    Create a price chart for a stock
    
    Args:
        symbol (str): Stock symbol
        period (str): Period of data to retrieve
        interval (str): Data interval
        include_premarket (bool): Whether to include pre-market data
        
    Returns:
        plotly.graph_objects.Figure: Price chart
    """
    try:
        # Get stock data
        data = market_data.get_stock_data(symbol, period=period, interval=interval, include_premarket=include_premarket)
        
        if data.empty:
            return None
        
        # Create figure
        fig = go.Figure()
        
        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='Price'
            )
        )
        
        # Add volume bars
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data['Volume'],
                name='Volume',
                marker_color='rgba(0, 0, 255, 0.3)',
                opacity=0.3,
                yaxis='y2'
            )
        )
        
        # Update layout
        fig.update_layout(
            title=f'{symbol} Price Chart',
            xaxis_title='Date',
            yaxis_title='Price',
            yaxis2=dict(
                title='Volume',
                overlaying='y',
                side='right',
                showgrid=False
            ),
            height=500,
            margin=dict(l=50, r=50, t=50, b=50),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Add range slider
        fig.update_layout(
            xaxis=dict(
                rangeslider=dict(visible=True),
                type='date'
            )
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating price chart for {symbol}: {str(e)}")
        return None

def create_atr_chart(symbol, period="20d", interval="1d"):
    """
    Create an ATR chart for a stock
    
    Args:
        symbol (str): Stock symbol
        period (str): Period of data to retrieve
        interval (str): Data interval
        
    Returns:
        plotly.graph_objects.Figure: ATR chart
    """
    try:
        # Get stock data
        data = market_data.get_stock_data(symbol, period=period, interval=interval)
        
        if data.empty:
            return None
        
        # Calculate ATR
        atr = scanner.atr_calculator.calculate_atr(data)
        
        if atr.empty:
            return None
        
        # Create figure
        fig = go.Figure()
        
        # Add ATR line
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=atr,
                name='ATR',
                line=dict(color='purple', width=2)
            )
        )
        
        # Update layout
        fig.update_layout(
            title=f'{symbol} Average True Range (ATR)',
            xaxis_title='Date',
            yaxis_title='ATR',
            height=300,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating ATR chart for {symbol}: {str(e)}")
        return None

def format_large_number(num):
    """Format large numbers with K, M, B suffixes"""
    if num >= 1e9:
        return f"{num/1e9:.2f}B"
    elif num >= 1e6:
        return f"{num/1e6:.2f}M"
    elif num >= 1e3:
        return f"{num/1e3:.2f}K"
    else:
        return f"{num:.2f}"

def run_stock_scan():
    """Run the stock scanner and return results"""
    with st.spinner('Scanning for trading opportunities...'):
        # Get filter parameters from session state
        min_price = st.session_state.get('min_price', 5)
        max_price = st.session_state.get('max_price', 100)
        min_volume = st.session_state.get('min_volume', 500000)
        min_deviation = st.session_state.get('min_deviation', 4.0)
        
        # Run comprehensive scan
        scan_results = scanner.run_comprehensive_scan(
            min_price=min_price,
            max_price=max_price,
            min_volume=min_volume
        )
        
        # Generate trade plans
        opportunities = scan_results.get('opportunities', [])
        trade_plans = strategy.generate_trade_plans(opportunities)
        
        # Store results in session state
        st.session_state['scan_results'] = scan_results
        st.session_state['trade_plans'] = trade_plans
        st.session_state['last_scan_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return scan_results, trade_plans

def display_stock_details(symbol):
    """Display detailed information for a selected stock"""
    st.markdown(f"<h2 class='sub-header'>{symbol} Details</h2>", unsafe_allow_html=True)
    
    # Create tabs for different sections
    tabs = st.tabs(["Price Chart", "Technical Analysis", "News", "Trade Plan"])
    
    with tabs[0]:  # Price Chart
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Price chart
            fig = create_price_chart(symbol)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Could not create price chart")
        
        with col2:
            # Stock info
            try:
                # Get stock data
                data = market_data.get_stock_data(symbol, period="1d", interval="1d")
                
                if not data.empty:
                    current_price = data['Close'].iloc[-1]
                    prev_close = data['Open'].iloc[0]
                    change = current_price - prev_close
                    change_pct = (change / prev_close) * 100
                    
                    # Display metrics
                    st.metric(
                        label="Current Price",
                        value=f"${current_price:.2f}",
                        delta=f"{change_pct:.2f}%"
                    )
                    
                    st.metric(
                        label="Volume",
                        value=format_large_number(data['Volume'].iloc[-1])
                    )
                    
                    # Get relative volume
                    rel_volume = market_data.get_relative_volume(symbol)
                    st.metric(
                        label="Relative Volume",
                        value=f"{rel_volume:.2f}x"
                    )
                    
                    # Display high and low
                    st.metric(
                        label="Day High",
                        value=f"${data['High'].iloc[-1]:.2f}"
                    )
                    
                    st.metric(
                        label="Day Low",
                        value=f"${data['Low'].iloc[-1]:.2f}"
                    )
            
            except Exception as e:
                st.error(f"Error getting stock info: {str(e)}")
    
    with tabs[1]:  # Technical Analysis
        col1, col2 = st.columns(2)
        
        with col1:
            # ATR chart
            fig = create_atr_chart(symbol)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Could not create ATR chart")
        
        with col2:
            # Technical indicators
            try:
                # Get stock data
                data = market_data.get_stock_data(symbol, period="20d", interval="1d")
                
                if not data.empty:
                    # Calculate ATR
                    atr = scanner.atr_calculator.calculate_atr(data)
                    
                    if not atr.empty:
                        latest_atr = atr.iloc[-1]
                        latest_price = data['Close'].iloc[-1]
                        atr_percentage = (latest_atr / latest_price) * 100
                        
                        st.metric(
                            label="ATR",
                            value=f"${latest_atr:.2f}",
                            delta=f"{atr_percentage:.2f}% of price"
                        )
                
                # Get relative strength
                strength_results = scanner.calculate_relative_strength([symbol])
                
                if strength_results:
                    st.metric(
                        label="13-Week Relative Strength",
                        value=f"{strength_results[0]['relative_strength']:.2f}%",
                        delta=f"Percentile: {strength_results[0]['percentile']:.2f}"
                    )
            
            except Exception as e:
                st.error(f"Error getting technical indicators: {str(e)}")
    
    with tabs[2]:  # News
        try:
            # Get news
            news = news_data.get_stock_news(symbol, max_news=10)
            
            if news:
                for item in news:
                    with st.container():
                        st.markdown(f"""
                        <div class="card card-blue">
                            <h4>{item['title']}</h4>
                            <p>Publisher: {item['publisher']} | Date: {item['publish_date']}</p>
                            <a href="{item['link']}" target="_blank">Read more</a>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No recent news found")
            
            # Check for catalyst
            catalyst_info = news_data.check_for_catalyst(symbol)
            
            if catalyst_info.get('has_catalyst', False):
                st.markdown(f"""
                <div class="card card-yellow">
                    <h4>Potential Catalyst Detected</h4>
                    <p>Type: {', '.join(catalyst_info['catalyst_type'])}</p>
                    <p>News: {catalyst_info['news_item']['title']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"Error getting news: {str(e)}")
    
    with tabs[3]:  # Trade Plan
        try:
            # Find trade plan for this symbol
            trade_plans = st.session_state.get('trade_plans', [])
            
            trade_plan = next((plan for plan in trade_plans if plan['symbol'] == symbol), None)
            
            if trade_plan:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    <div class="card card-{'green' if trade_plan['direction'] == 'long' else 'red'}">
                        <h3>{trade_plan['direction'].upper()} {symbol}</h3>
                        <p><b>Entry:</b> ${trade_plan['entry_price']:.2f}</p>
                        <p><b>Stop Loss:</b> ${trade_plan['stop_loss']:.2f}</p>
                        <p><b>Take Profit:</b> ${trade_plan['take_profit']:.2f}</p>
                        <p><b>Position Size:</b> {trade_plan['position_size']} shares</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="card card-blue">
                        <h3>Risk Analysis</h3>
                        <p><b>Potential Loss:</b> ${trade_plan['potential_loss']:.2f}</p>
                        <p><b>Potential Profit:</b> ${trade_plan['potential_profit']:.2f}</p>
                        <p><b>Risk-Reward Ratio:</b> 1:{trade_plan['risk_reward_ratio']:.1f}</p>
                        <p><b>Score:</b> {trade_plan['score']:.1f}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Add price chart with entry, stop loss, and take profit levels
                data = market_data.get_stock_data(symbol, period="1d", interval="15m")
                
                if not data.empty:
                    fig = go.Figure()
                    
                    # Add candlestick chart
                    fig.add_trace(
                        go.Candlestick(
                            x=data.index,
                            open=data['Open'],
                            high=data['High'],
                            low=data['Low'],
                            close=data['Close'],
                            name='Price'
                        )
                    )
                    
                    # Add horizontal lines for entry, stop loss, and take profit
                    fig.add_hline(
                        y=trade_plan['entry_price'],
                        line_dash="solid",
                        line_color="blue",
                        annotation_text="Entry",
                        annotation_position="right"
                    )
                    
                    fig.add_hline(
                        y=trade_plan['stop_loss'],
                        line_dash="dash",
                        line_color="red",
                        annotation_text="Stop Loss",
                        annotation_position="right"
                    )
                    
                    fig.add_hline(
                        y=trade_plan['take_profit'],
                        line_dash="dash",
                        line_color="green",
                        annotation_text="Take Profit",
                        annotation_position="right"
                    )

                    # Update layout
                    fig.update_layout(
                        title=f'{symbol} Trade Plan',
                        xaxis_title='Time',
                        yaxis_title='Price',
                        height=400,
                        margin=dict(l=50, r=50, t=50, b=50)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No trade plan available for this stock")
        
        except Exception as e:
            st.error(f"Error displaying trade plan: {str(e)}")

def display_scan_results():
    """Display stock scanner results"""
    st.markdown("<h2 class='sub-header'>Scan Results</h2>", unsafe_allow_html=True)
    
    # Check if we have scan results
    if 'scan_results' not in st.session_state:
        st.info("No scan results available. Run a scan to see results.")
        return
    
    scan_results = st.session_state['scan_results']
    trade_plans = st.session_state.get('trade_plans', [])
    last_scan_time = st.session_state.get('last_scan_time', 'Unknown')
    
    # Display scan summary
    st.markdown(f"<p>Last scan: {last_scan_time}</p>", unsafe_allow_html=True)
    st.markdown(f"<p>Universe size: {scan_results.get('universe_size', 0)} stocks</p>", unsafe_allow_html=True)
    
    # Create tabs for different result types
    tabs = st.tabs(["Trading Opportunities", "Price Deviation", "High Volume", "High ATR", "Catalysts", "All Stocks"])
    
    with tabs[0]:  # Trading Opportunities
        opportunities = scan_results.get('opportunities', [])
        
        if opportunities:
            # Create a dataframe for display
            df = pd.DataFrame(opportunities)
            
            # Add trade plan info
            df['trade_plan'] = df['symbol'].apply(
                lambda x: next((True for plan in trade_plans if plan['symbol'] == x), False)
            )
            
            # Display as a table
            st.dataframe(
                df[['symbol', 'price', 'direction', 'score', 'trade_plan']],
                column_config={
                    'symbol': 'Symbol',
                    'price': st.column_config.NumberColumn('Price', format="$%.2f"),
                    'direction': 'Direction',
                    'score': st.column_config.NumberColumn('Score', format="%.1f"),
                    'trade_plan': st.column_config.CheckboxColumn('Trade Plan')
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Allow user to select a stock for detailed view
            selected_symbol = st.selectbox(
                "Select a stock for detailed view",
                options=[item['symbol'] for item in opportunities]
            )
            
            if selected_symbol:
                display_stock_details(selected_symbol)
        else:
            st.info("No trading opportunities found")
    
    with tabs[1]:  # Price Deviation
        deviation_results = scan_results.get('deviation_results', [])
        
        if deviation_results:
            # Create a dataframe for display
            df = pd.DataFrame(deviation_results)
            
            # Display as a table
            st.dataframe(
                df[['symbol', 'current_price', 'deviation_pct', 'direction']],
                column_config={
                    'symbol': 'Symbol',
                    'current_price': st.column_config.NumberColumn('Price', format="$%.2f"),
                    'deviation_pct': st.column_config.NumberColumn('Deviation', format="%.2f%%"),
                    'direction': 'Direction'
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Allow user to select a stock for detailed view
            selected_symbol = st.selectbox(
                "Select a stock for detailed view",
                options=[item['symbol'] for item in deviation_results],
                key="deviation_select"
            )
            
            if selected_symbol:
                display_stock_details(selected_symbol)
        else:
            st.info("No stocks with significant price deviation found")
    
    with tabs[2]:  # High Volume
        volume_results = scan_results.get('volume_results', [])
        
        if volume_results:
            # Create a dataframe for display
            df = pd.DataFrame(volume_results)
            
            # Display as a table
            st.dataframe(
                df[['symbol', 'current_price', 'relative_volume', 'volume']],
                column_config={
                    'symbol': 'Symbol',
                    'current_price': st.column_config.NumberColumn('Price', format="$%.2f"),
                    'relative_volume': st.column_config.NumberColumn('Relative Volume', format="%.2fx"),
                    'volume': st.column_config.NumberColumn('Volume', format="%d")
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Allow user to select a stock for detailed view
            selected_symbol = st.selectbox(
                "Select a stock for detailed view",
                options=[item['symbol'] for item in volume_results],
                key="volume_select"
            )
            
            if selected_symbol:
                display_stock_details(selected_symbol)
        else:
            st.info("No stocks with high relative volume found")
    
    with tabs[3]:  # High ATR
        atr_results = scan_results.get('atr_results', [])
        
        if atr_results:
            # Create a dataframe for display
            df = pd.DataFrame(atr_results)
            
            # Check available columns and use appropriate ones
            columns_to_display = []
            if 'symbol' in df.columns:
                columns_to_display.append('symbol')
            
            # Use 'price' instead of 'current_price' if it exists
            if 'price' in df.columns:
                columns_to_display.append('price')
            elif 'current_price' in df.columns:
                columns_to_display.append('current_price')
            
            # Add other columns if they exist
            for col in ['atr', 'atr_percentage', 'atr_ratio']:
                if col in df.columns:
                    columns_to_display.append(col)
            
            # Display as a table with available columns
            st.dataframe(
                df[columns_to_display],
                column_config={
                    'symbol': 'Symbol',
                    'price': st.column_config.NumberColumn('Price', format="$%.2f"),
                    'current_price': st.column_config.NumberColumn('Price', format="$%.2f"),
                    'atr': st.column_config.NumberColumn('ATR', format="$%.2f"),
                    'atr_percentage': st.column_config.NumberColumn('ATR %', format="%.2f%%"),
                    'atr_ratio': st.column_config.NumberColumn('ATR Ratio', format="%.2fx")
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Allow user to select a stock for detailed view
            selected_symbol = st.selectbox(
                "Select a stock for detailed view",
                options=[item['symbol'] for item in atr_results],
                key="atr_select"
            )
            
            if selected_symbol:
                display_stock_details(selected_symbol)
        else:
            st.info("No stocks with high ATR found")
    
    with tabs[4]:  # Catalysts
        catalyst_results = scan_results.get('catalyst_results', [])
        
        if catalyst_results:
            # Create a dataframe for display
            df = pd.DataFrame(catalyst_results)
            
            # Display as a table
            st.dataframe(
                df[['symbol', 'has_catalyst', 'catalyst_type']],
                column_config={
                    'symbol': 'Symbol',
                    'has_catalyst': st.column_config.CheckboxColumn('Has Catalyst'),
                    'catalyst_type': 'Catalyst Type'
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Allow user to select a stock for detailed view
            selected_symbol = st.selectbox(
                "Select a stock for detailed view",
                options=[item['symbol'] for item in catalyst_results],
                key="catalyst_select"
            )
            
            if selected_symbol:
                display_stock_details(selected_symbol)
        else:
            st.info("No stocks with potential catalysts found")
    
    with tabs[5]:  # All Stocks
        # Get all stocks by significance
        if 'all_stocks' not in st.session_state:
            with st.spinner('Loading all stocks...'):
                min_price = st.session_state.get('min_price', 5)
                max_price = st.session_state.get('max_price', 100)
                min_volume = st.session_state.get('min_volume', 500000)
                
                all_stocks = scanner.get_all_stocks_by_significance(
                    min_price=min_price,
                    max_price=max_price,
                    min_volume=min_volume
                )
                
                st.session_state['all_stocks'] = all_stocks
        else:
            all_stocks = st.session_state['all_stocks']
        
        if all_stocks:
            # Create a dataframe for display
            df = pd.DataFrame(all_stocks)
            
            # Display as a table
            st.dataframe(
                df[['symbol', 'price', 'deviation_pct', 'direction', 'relative_volume', 'atr_percentage', 'significance']],
                column_config={
                    'symbol': 'Symbol',
                    'price': st.column_config.NumberColumn('Price', format="$%.2f"),
                    'deviation_pct': st.column_config.NumberColumn('Deviation', format="%.2f%%"),
                    'direction': 'Direction',
                    'relative_volume': st.column_config.NumberColumn('Rel Volume', format="%.2fx"),
                    'atr_percentage': st.column_config.NumberColumn('ATR %', format="%.2f%%"),
                    'significance': st.column_config.NumberColumn('Significance', format="%.2f")
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Allow user to select a stock for detailed view
            selected_symbol = st.selectbox(
                "Select a stock for detailed view",
                options=[item['symbol'] for item in all_stocks],
                key="all_stocks_select"
            )
            
            if selected_symbol:
                display_stock_details(selected_symbol)
        else:
            st.info("No stocks found")

def main():
    """Main function to run the app"""
    # Set up the header
    st.markdown("<h1 class='main-header'>Daily Stock Picker</h1>", unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.markdown("<h2 class='main-header'>Stock Scanner</h2>", unsafe_allow_html=True)
    
    # Get tooltips from scanner
    tooltips = scanner.get_metric_tooltips()
    
    # Price filter with tooltip
    st.sidebar.subheader("Price Filter")
    min_price = st.sidebar.number_input(
        "Minimum Price ($)", 
        min_value=1.0, 
        max_value=1000.0, 
        value=5.0,
        step=1.0,
        help=tooltips.get('price', {}).get('description', "Minimum stock price to include in scan.") if 'price' in tooltips else "Minimum stock price to include in scan."
    )
    
    max_price = st.sidebar.number_input(
        "Maximum Price ($)", 
        min_value=1.0, 
        max_value=10000.0, 
        value=100.0,
        step=10.0,
        help=tooltips.get('price', {}).get('description', "Maximum stock price to include in scan.") if 'price' in tooltips else "Maximum stock price to include in scan."
    )
    
    # Volume filter with tooltip
    st.sidebar.subheader("Volume Filter")
    min_volume = st.sidebar.number_input(
        "Minimum Volume", 
        min_value=10000, 
        max_value=10000000, 
        value=500000,
        step=100000,
        format="%d",
        help=tooltips.get('volume', {}).get('description', "Minimum trading volume to include in scan.") if 'volume' in tooltips else "Minimum trading volume to include in scan."
    )
    
    # Price deviation filter with tooltip
    st.sidebar.subheader("Price Deviation")
    min_deviation = st.sidebar.number_input(
        "Minimum Deviation (%)", 
        min_value=1.0, 
        max_value=20.0, 
        value=4.0,
        step=0.5,
        help=tooltips.get('price_deviation', {}).get('description', "Minimum price deviation percentage to flag a stock.") if 'price_deviation' in tooltips else "Minimum price deviation percentage to flag a stock."
    )
    
    # Relative volume filter with tooltip
    st.sidebar.subheader("Relative Volume")
    min_rel_volume = st.sidebar.number_input(
        "Minimum Relative Volume", 
        min_value=1.0, 
        max_value=10.0, 
        value=1.5,
        step=0.1,
        help=tooltips.get('relative_volume', {}).get('description', "Minimum relative volume to flag a stock.") if 'relative_volume' in tooltips else "Minimum relative volume to flag a stock."
    )
    
    # ATR filter with tooltip
    st.sidebar.subheader("ATR Filter")
    min_atr_ratio = st.sidebar.number_input(
        "Minimum ATR Ratio", 
        min_value=0.5, 
        max_value=5.0, 
        value=1.2,
        step=0.1,
        help=tooltips.get('atr_ratio', {}).get('description', "Minimum ATR ratio to flag a stock.") if 'atr_ratio' in tooltips else "Minimum ATR ratio to flag a stock."
    )
    
    # Store filter values in session state
    if st.sidebar.button("Apply Filters"):
        st.session_state['min_price'] = min_price
        st.session_state['max_price'] = max_price
        st.session_state['min_volume'] = min_volume
        st.session_state['min_deviation'] = min_deviation
        st.session_state['min_rel_volume'] = min_rel_volume
        st.session_state['min_atr_ratio'] = min_atr_ratio
        
        # Clear cached results
        if 'all_stocks' in st.session_state:
            del st.session_state['all_stocks']
        
        # Run scan with new filters
        run_stock_scan()
    
    # Run scan button
    if st.sidebar.button("Run Stock Scan"):
        run_stock_scan()
    
    # Display last scan time
    if 'last_scan_time' in st.session_state:
        st.sidebar.markdown(f"Last scan: {st.session_state['last_scan_time']}")
    
    # Display scan results
    display_scan_results()

if __name__ == "__main__":
    main()