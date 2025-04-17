"""User Interface Module for Stock Picker Application

This module creates a Flask-based user interface for the Stock Picker app,
displaying stock scanner results and trading recommendations.
"""

from flask import Flask, render_template, request, jsonify, session
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.utils
import json
from datetime import datetime, timedelta
import time
import logging
import os
import sys
import threading
import webbrowser
import asyncio
import atexit
from websockets.server import serve as websockets_serve
from websockets.exceptions import ConnectionClosed
from log_handler import WebSocketHandler

# Import our modules
from data_retrieval import MarketDataFetcher, NewsDataFetcher
from stock_scanner import StockScanner
from trading_strategy import TradingStrategy

# Set up logging with WebSocket handler
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('stock_picker_ui')

# Create and add WebSocket handler
ws_log_handler = WebSocketHandler()
ws_log_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(ws_log_handler)

# Add WebSocket handler to other loggers
for logger_name in ['data_retrieval', 'stock_scanner', 'trading_strategy']:
    logging.getLogger(logger_name).addHandler(ws_log_handler)

# Initialize components
market_data = MarketDataFetcher()
news_data = NewsDataFetcher()
scanner = StockScanner()
strategy = TradingStrategy()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'stock_picker_secret_key'  # For session management

# Add template context processors
@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

# Helper functions
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

def create_price_chart(symbol, period="5d", interval="15m", include_premarket=True):
    """
    Create a price chart for a stock
    
    Args:
        symbol (str): Stock symbol
        period (str): Period of data to retrieve
        interval (str): Data interval
        include_premarket (bool): Whether to include pre-market data
        
    Returns:
        JSON: Chart data for plotly
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
        
        return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))
        
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
        JSON: Chart data for plotly
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
        
        return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))
        
    except Exception as e:
        logger.error(f"Error creating ATR chart for {symbol}: {str(e)}")
        return None

def run_stock_scan():
    """Run the stock scanner and return results"""
    try:
        # Get filter parameters from session
        min_price = session.get('min_price', 5)
        max_price = session.get('max_price', 100)
        min_volume = session.get('min_volume', 500000)
        min_deviation = session.get('min_deviation', 4.0)
        
        # Run comprehensive scan
        scan_results = scanner.run_comprehensive_scan(
            min_price=min_price,
            max_price=max_price,
            min_volume=min_volume
        )
        
        # Generate trade plans
        opportunities = scan_results.get('opportunities', [])
        trade_plans = strategy.generate_trade_plans(opportunities)
        
        # Store results in session
        session['scan_results'] = scan_results
        session['trade_plans'] = trade_plans
        session['last_scan_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return scan_results, trade_plans
    except Exception as e:
        logger.error(f"Error running stock scan: {str(e)}")
        return {}, []

def create_trade_plan_chart(symbol, trade_plan):
    """Create a chart with trade plan levels"""
    try:
        # Get stock data
        data = market_data.get_stock_data(symbol, period="1d", interval="15m")
        
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
        
        return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))
    
    except Exception as e:
        logger.error(f"Error creating trade plan chart: {str(e)}")
        return None

# Routes
# Add this after other imports
import json
from pathlib import Path

# Add this after other route definitions
@app.route('/save_filters', methods=['POST'])
def save_filters():
    try:
        # Get filter values from form
        filters = {
            'min_price': request.form.get('min_price', 5, type=float),
            'max_price': request.form.get('max_price', 100, type=float),
            'min_volume': request.form.get('min_volume', 500000, type=int),
            'min_deviation': request.form.get('min_deviation', 4.0, type=float)
        }
        
        # Save to a JSON file
        filters_file = Path('static/saved_filters.json')
        with open(filters_file, 'w') as f:
            json.dump(filters, f)
        
        return jsonify({
            'success': True,
            'message': 'Filters saved successfully'
        })
    except Exception as e:
        logger.error(f"Error saving filters: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to save filters'
        })

# Modify the index route to load saved filters
@app.route('/')
def index():
    # Try to load saved filters
    try:
        filters_file = Path('static/saved_filters.json')
        if filters_file.exists():
            with open(filters_file, 'r') as f:
                saved_filters = json.load(f)
        else:
            saved_filters = {}
    except Exception as e:
        logger.error(f"Error loading saved filters: {str(e)}")
        saved_filters = {}

    # Get filter parameters from query string, saved filters, or use defaults
    min_price = request.args.get('min_price', saved_filters.get('min_price', 5), type=float)
    max_price = request.args.get('max_price', saved_filters.get('max_price', 100), type=float)
    min_volume = request.args.get('min_volume', saved_filters.get('min_volume', 500000), type=int)
    min_deviation = request.args.get('min_deviation', saved_filters.get('min_deviation', 4.0), type=float)
    
    # Store in session
    session['min_price'] = min_price
    session['max_price'] = max_price
    session['min_volume'] = min_volume
    session['min_deviation'] = min_deviation
    
    # Check if we need to run a scan
    run_scan = request.args.get('run_scan', False, type=bool)
    
    scan_results = {}
    trade_plans = []
    last_scan_time = 'Never'
    
    if run_scan or 'scan_results' not in session:
        scan_results, trade_plans = run_stock_scan()
        last_scan_time = session.get('last_scan_time', 'Just now')
    else:
        scan_results = session.get('scan_results', {})
        trade_plans = session.get('trade_plans', [])
        last_scan_time = session.get('last_scan_time', 'Unknown')
    
    return render_template('index.html', 
                          scan_results=scan_results,
                          trade_plans=trade_plans,
                          last_scan_time=last_scan_time,
                          min_price=min_price,
                          max_price=max_price,
                          min_volume=min_volume,
                          min_deviation=min_deviation)

@app.route('/run_scan', methods=['POST'])
def run_scan_route():
    # Get filter parameters from form
    min_price = request.form.get('min_price', 5, type=float)
    max_price = request.form.get('max_price', 100, type=float)
    min_volume = request.form.get('min_volume', 500000, type=int)
    min_deviation = request.form.get('min_deviation', 4.0, type=float)
    
    # Store in session
    session['min_price'] = min_price
    session['max_price'] = max_price
    session['min_volume'] = min_volume
    session['min_deviation'] = min_deviation
    
    # Run scan
    scan_results, trade_plans = run_stock_scan()
    
    return jsonify({
        'success': True,
        'redirect': '/'
    })

@app.route('/api/opportunities')
def api_opportunities():
    scan_results = session.get('scan_results', {})
    opportunities = scan_results.get('opportunities', [])
    return jsonify(opportunities)

@app.route('/api/deviation_results')
def api_deviation_results():
    scan_results = session.get('scan_results', {})
    deviation_results = scan_results.get('deviation_results', [])
    return jsonify(deviation_results)

@app.route('/api/volume_results')
def api_volume_results():
    scan_results = session.get('scan_results', {})
    volume_results = scan_results.get('volume_results', [])
    return jsonify(volume_results)

@app.route('/api/atr_results')
def api_atr_results():
    scan_results = session.get('scan_results', {})
    atr_results = scan_results.get('atr_results', [])
    return jsonify(atr_results)

@app.route('/api/catalyst_results')
def api_catalyst_results():
    scan_results = session.get('scan_results', {})
    catalyst_results = scan_results.get('catalyst_results', [])
    return jsonify(catalyst_results)

@app.route('/api/stock_details/<symbol>')
def api_stock_details(symbol):
    try:
        # Get trade plans from session
        trade_plans = session.get('trade_plans', [])
        trade_plan = next((plan for plan in trade_plans if plan['symbol'] == symbol), None)
        
        # Create charts
        price_chart = create_price_chart(symbol)
        atr_chart = create_atr_chart(symbol)
        trade_plan_chart = None
        
        if trade_plan:
            trade_plan_chart = create_trade_plan_chart(symbol, trade_plan)
        
        # Get stock data for metrics
        stock_data = market_data.get_stock_data(symbol, period="1d", interval="1d")
        stock_metrics = {}
        
        if not stock_data.empty:
            current_price = stock_data['Close'].iloc[-1]
            prev_close = stock_data['Open'].iloc[0]
            change = current_price - prev_close
            change_pct = (change / prev_close) * 100
            
            stock_metrics = {
                'current_price': current_price,
                'change_pct': change_pct,
                'volume': stock_data['Volume'].iloc[-1],
                'rel_volume': market_data.get_relative_volume(symbol),
                'day_high': stock_data['High'].iloc[-1],
                'day_low': stock_data['Low'].iloc[-1]
            }
        
        # Get technical indicators
        tech_indicators = {}
        data = market_data.get_stock_data(symbol, period="20d", interval="1d")
        
        if not data.empty:
            # Calculate ATR
            atr = scanner.atr_calculator.calculate_atr(data)
            
            if not atr.empty:
                latest_atr = atr.iloc[-1]
                latest_price = data['Close'].iloc[-1]
                atr_percentage = (latest_atr / latest_price) * 100
                
                tech_indicators['atr'] = latest_atr
                tech_indicators['atr_pct'] = atr_percentage
        
        # Get relative strength
        strength_results = scanner.calculate_relative_strength([symbol])
        
        if strength_results:
            tech_indicators['rel_strength'] = strength_results[0]['relative_strength']
            tech_indicators['percentile'] = strength_results[0]['percentile']
        
        # Get news
        news_items = news_data.get_stock_news(symbol, max_news=10)
        catalyst_info = news_data.check_for_catalyst(symbol)

        details = {
            'symbol': symbol,
            'stock_metrics': stock_metrics,
            'tech_indicators': tech_indicators,
            'price_chart': price_chart,
            'atr_chart': atr_chart,
            'trade_plan_chart': trade_plan_chart,
            'trade_plan': trade_plan,
            'news_items': news_items,
            'catalyst_info': catalyst_info
        }
        
        # Render only the content template
        return render_template('stock_details_content.html', details=details)
    except Exception as e:
        return f'<div class="error-message">Error loading details for {symbol}: {str(e)}</div>', 500

def open_browser():
    """Open the default web browser to the Flask app URL."""
    webbrowser.open_new('http://127.0.0.1:5000')

async def handle_websocket(websocket, path):
    """Handle WebSocket connections"""
    try:
        logger.info("New WebSocket client connected")
        # Add client to handler
        ws_log_handler.add_client(websocket)
        
        # Send a test message
        test_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': 'DEBUG',
            'message': 'WebSocket connection established',
            'logger': 'websocket'
        }
        await websocket.send(json.dumps(test_entry))
        
        # Keep connection alive
        while True:
            try:
                # Wait for messages (keeps connection alive)
                message = await websocket.recv()
                # Echo back any received messages
                await websocket.send(message)
            except ConnectionClosed:
                break
            
    except Exception as e:
        logger.error(f"Error in websocket handler: {str(e)}")
    finally:
        # Remove client when disconnected
        ws_log_handler.remove_client(websocket)
        logger.info("WebSocket client disconnected")

def run_websocket_server():
    """Run the WebSocket server"""
    async def serve():
        async with websockets_serve(
            handle_websocket,
            "localhost",
            8765,
            ping_interval=None,  # Disable ping to prevent timeouts
        ) as server:
            await asyncio.Future()  # run forever

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(serve())
    except Exception as e:
        logger.error(f"Error starting WebSocket server: {str(e)}")
    finally:
        loop.close()

# Add cleanup function
def cleanup():
    """Clean up resources before exit"""
    ws_log_handler.close()

# Register cleanup function
atexit.register(cleanup)

if __name__ == '__main__':
    # Create templates and static directories if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Start a thread to open the browser
    threading.Timer(1, open_browser).start()
    
    # Start WebSocket server in a separate thread
    websocket_thread = threading.Thread(target=run_websocket_server, daemon=True)
    websocket_thread.start()
    
    app.run(debug=False, port=5000)