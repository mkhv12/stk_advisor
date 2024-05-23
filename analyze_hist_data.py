import pandas as pd
from datetime import datetime, timedelta
from main_analysis import fetch_stock_data, calculate_vwap

# Load portfolio data from Excel
portfolio_data = pd.read_excel('portfolio.xlsx')

def calculate_fibonacci_levels(data):
    high = data['High'].max()
    low = data['Low'].min()

    # Calculate Fibonacci levels
    fibonacci_levels = {
        0.382: low + 0.382 * (high - low),
        0.618: low + 0.618 * (high - low)
    }

    return fibonacci_levels

def analyze_historical_data(symbol, start_date, end_date, interval):
    # Fetch historical data
    historical_data = fetch_stock_data(symbol, start_date, end_date, interval)

    if historical_data.empty:
        print(f"No historical data found for {symbol}")
        return None

    # Calculate VWAP for historical data
    historical_data['VWAP'] = calculate_vwap(historical_data)

    # Calculate Fibonacci retracement levels
    fibonacci_levels = calculate_fibonacci_levels(historical_data)

    return historical_data, fibonacci_levels

def predict_next_30_days(symbol, start_date, end_date, interval):
    # Fetch historical data for the past 365 days
    historical_data = fetch_stock_data(symbol, start_date, end_date, interval)

    if historical_data.empty:
        print(f"No historical data found for the past year for {symbol}")
        return None

    # Calculate VWAP for historical data
    historical_data['VWAP'] = calculate_vwap(historical_data)

    # Smooth the data using a moving average to reduce noise
    historical_data['VWAP_MA'] = historical_data['VWAP'].rolling(window=30, min_periods=1).mean()

    # Calculate average VWAP over the last 30 days
    average_vwap = historical_data['VWAP_MA'].mean()

    return average_vwap

def main():
    # Step 1: Define the date range and interval
    today = datetime.now() + timedelta(days=1)
    end_date = today.strftime("%Y-%m-%d")
    start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    interval = '1d'

    print(f"\nDate range: {start_date} to {end_date} and {interval} chart")

    # Loop through each row in the portfolio data
    for index, row in portfolio_data.iterrows():
        symbol = row['Symbol']
        
        print(f"\nAnalyzing historical data for {symbol}...")

        # Analyze historical data
        historical_data, fibonacci_levels = analyze_historical_data(symbol, start_date, end_date, interval)

        if historical_data is not None:
            # Calculate current VWAP
            historical_data['VWAP'] = calculate_vwap(historical_data)
            current_vwap = historical_data['VWAP'].iloc[-1]

            # Predict next 30 days VWAP based on historical data
            predicted_vwap = predict_next_30_days(symbol, start_date, end_date, interval)
            if predicted_vwap:
                print(f"Current VWAP: {current_vwap:.2f}")
                print(f"Predicted average VWAP for the next 30 days: {predicted_vwap:.2f}")

                # Print current price
                current_price = historical_data['Close'].iloc[-1]
                print(f"Current Price: ${current_price:.2f}")

                # Loop through each Fibonacci level
                for level, price in fibonacci_levels.items():
                    print(f"Fibonacci Level {level}: ${price:.2f} - {'Price is potentially bullish' if current_vwap < price else 'Price is potentially bearish'}")
            else:
                print(f"Could not predict VWAP for the next 30 days for {symbol}")
        else:
            print(f"Could not analyze historical data for {symbol}")

if __name__ == "__main__":
    main()
