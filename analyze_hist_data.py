import pandas as pd
from datetime import datetime, timedelta
from main_analysis import fetch_stock_data, calculate_vwap

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

    # Calculate VWAP for historical data
    historical_data['VWAP'] = calculate_vwap(historical_data)

    return historical_data

def predict_next_30_days(symbol, start_date, end_date, interval):
    next_30_days_start = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
    next_30_days_end = next_30_days_start + timedelta(days=29)
    
    # Adjust the dates to fetch data from last year
    last_year_start = next_30_days_start - timedelta(days=365)
    last_year_end = next_30_days_end - timedelta(days=365)

    # Fetch historical data for the next 30 days from last year
    historical_data = fetch_stock_data(symbol, last_year_start.strftime("%Y-%m-%d"), last_year_end.strftime("%Y-%m-%d"), interval)

    if historical_data.empty:
        print(f"No historical data found for the next 30 days last year for {symbol}")
        return None

    # Calculate VWAP for historical data
    historical_data['VWAP'] = calculate_vwap(historical_data)

    # Calculate average VWAP over the last 30 days
    average_vwap = historical_data['VWAP'].mean()

    return average_vwap

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
        last_year_data = analyze_historical_data(symbol, start_date, end_date, interval)

        if last_year_data is not None:
            # Fetch current year data
            current_year_data = fetch_stock_data(symbol, start_date, end_date, interval)
            if not current_year_data.empty:
                current_year_data['VWAP'] = calculate_vwap(current_year_data)
                current_vwap = current_year_data['VWAP'].mean()

                # Predict next 30 days VWAP based on last year's data
                predicted_vwap = predict_next_30_days(symbol, start_date, end_date, interval)
                if predicted_vwap:
                    print(f"Current VWAP: {current_vwap:.2f}")
                    print(f"Predicted average VWAP for the next 30 days: {predicted_vwap:.2f}")

                    # Interpret the result
                    if current_vwap > predicted_vwap:
                        print("The price is likely to go down (possibly bearish)")
                    elif current_vwap < predicted_vwap:
                        print("The price is likely to go up (possibly bullish)")
                    else:
                        print("The price is likely to remain stable")
            else:
                print(f"No data found for {symbol} in the current year")
        else:
            print(f"Could not analyze historical data for {symbol}")

if __name__ == "__main__":
    main()
