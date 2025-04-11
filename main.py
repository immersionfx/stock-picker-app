"""
Main entry point for the Stock Picker application.
This file initializes the application and provides a simple way to run it.
"""

import os
import sys
import logging
import subprocess
import webbrowser
from threading import Timer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('stock_picker_main')

def open_browser():
    """Open web browser to the Streamlit app"""
    webbrowser.open('http://localhost:8501')

def main():
    """Main function to run the Stock Picker application"""
    logger.info("Starting Stock Picker application")
    
    # Check if required modules are installed
    try:
        import streamlit
        import pandas
        import numpy
        import plotly
        import yfinance
    except ImportError as e:
        logger.error(f"Missing required module: {str(e)}")
        logger.info("Installing required modules...")
        subprocess.run(["pip", "install", "streamlit", "pandas", "numpy", "plotly", "yfinance"])
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the Streamlit app
    app_path = os.path.join(script_dir, "app.py")
    
    # Check if app.py exists
    if not os.path.exists(app_path):
        logger.error(f"App file not found: {app_path}")
        return
    
    logger.info(f"Running Streamlit app: {app_path}")
    
    # Open browser after a delay
    Timer(2, open_browser).start()
    
    # Run the Streamlit app
    subprocess.run(["streamlit", "run", app_path])

if __name__ == "__main__":
    main()
