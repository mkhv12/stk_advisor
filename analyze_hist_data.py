import pandas as pd
from datetime import datetime, timedelta
from main_analysis import fetch_stock_data, calculate_rsi, calculate_macd, calculate_vwap

# Load portfolio data from Excel
portfolio_data = pd.read_excel('portfolio.xlsx')

def analyze_historical_data(symbol, start_date, end_date, interval):
    # Adjust start and end dates to match the same date last year
    last_year_start = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=365)).strftime("%Y-%m-%d")
    last_year_end = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=365)).strftime("%Y-%m-%d")

    # Fetch historical data for last year
    historical_data = fetch_stock_data(symbol, last_year_start, last_year_end, interval)

    if historical_data.empty:
        print(f"No historical data found for {symbol}")
        return None

    # Calculate RSI, MACD, and VWAP for historical data
    historical_data['RSI'] = calculate_rsi(historical_data)
    macd_histogram, macd_line, signal_line = calculate_macd(historical_data)
    historical_data['VWAP'] = calculate_vwap(historical_data)

    # Perform analysis on historical data
    # You can add your custom analysis logic here
    # For example, compare current price with historical VWAP, RSI, or MACD

    return historical_data

def main():
    # Step 1: Define the date range
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=365)).strftime("%Y-%m-%d")
    interval = '1d'

    print(f"\nDate range: {start_date} to {end_date} and {interval} chart")

    # Loop through each row in the portfolio data
    for index, row in portfolio_data.iterrows():
        symbol = row['Symbol']
        
        print(f"\nAnalyzing historical data for {symbol}...")

        # Analyze historical data
        historical_data = analyze_historical_data(symbol, start_date, end_date, interval)

        # Perform analysis on historical data and output results
        if historical_data is not None:
            print(historical_data.head())  # Example: Output first few rows of historical data
            # Add your custom analysis logic here based on historical data
        else:
            print(f"Could not analyze historical data for {symbol}")

if __name__ == "__main__":
    main()
