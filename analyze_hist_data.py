import pandas as pd
from datetime import datetime, timedelta
from main_analysis import fetch_stock_data
import tech_analysis_tools
from sklearn.linear_model import LinearRegression
import numpy as np
import argparse

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

def calculate_vwap_ema(historical_data, span=30):
    historical_data['VWAP_EMA'] = historical_data['VWAP'].ewm(span=span, adjust=False).mean()
    return historical_data

def calculate_rsi(data, window=14):
    delta = data['Close'].diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=window, min_periods=1).mean()
    avg_loss = loss.rolling(window=window, min_periods=1).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    data['RSI'] = rsi
    return data

def apply_trendline(data, days):
    y = data['VWAP'].values[-days:]
    x = np.arange(days).reshape(-1, 1)
    model = LinearRegression().fit(x, y)
    slope = model.coef_[0]
    intercept = model.intercept_
    trendline_prediction = [(slope * i + intercept) for i in range(days, days + PREDICTION_DAYS)]
    return slope, intercept, trendline_prediction

def weighted_average_prediction(vwap, vwap_ema, trendline_prediction, vwap_weight=0.2, ema_weight=0.5, trendline_weight=0.3):
    return (vwap_weight * vwap) + (ema_weight * vwap_ema) + (trendline_weight * np.mean(trendline_prediction))

def calculate_volatility(data, days=30):
    recent_data = data['Close'][-days:]
    return recent_data.std()

def analyze_historical_data(symbol, start_date, end_date, interval):
    historical_data = fetch_stock_data(symbol, start_date, end_date, interval)

    if historical_data.empty:
        print(f"No historical data found for {symbol}")
        return None

    # Calculate VWAP for historical data
    historical_data['VWAP'] = tech_analysis_tools.calculate_vwap(historical_data)

    # Apply technical indicators
    historical_data = calculate_vwap_ema(historical_data)
    historical_data = calculate_rsi(historical_data)
    fibonacci_levels = calculate_fibonacci_levels(historical_data)
    
    return historical_data, fibonacci_levels

def predict_next_period(symbol, start_date, end_date, interval):
    historical_data = fetch_stock_data(symbol, start_date, end_date, interval)

    if historical_data.empty:
        print(f"No historical data found for {symbol}")
        return None

    # Calculate VWAP and other indicators
    historical_data['VWAP'] = tech_analysis_tools.calculate_vwap(historical_data)
    historical_data = calculate_vwap_ema(historical_data)
    historical_data = calculate_rsi(historical_data)
    slope, intercept, trendline_prediction = apply_trendline(historical_data, days=PREDICTION_DAYS)
    avg_trendline = np.mean(trendline_prediction)

    # Get final prediction as a weighted average
    vwap_ema = historical_data['VWAP_EMA'].iloc[-1]
    vwap = historical_data['VWAP'].iloc[-1]
    prediction = weighted_average_prediction(vwap, vwap_ema, trendline_prediction)

    # Calculate confidence interval based on recent volatility
    volatility = calculate_volatility(historical_data)
    confidence_interval = (prediction - volatility, prediction + volatility)

    return prediction, confidence_interval, slope

def main(prediction_days):
    global PREDICTION_DAYS
    PREDICTION_DAYS = prediction_days  # Set the global prediction days variable

    today = datetime.now() + timedelta(days=1)
    end_date = today.strftime("%Y-%m-%d")
    start_date = (today - timedelta(days=60)).strftime("%Y-%m-%d")
    interval = '1d'

    print(f"\nDate range: {start_date} to {end_date} and {interval} chart")

    for index, row in portfolio_data.iterrows():
        symbol = row['Symbol']
        print(f"\nHistorical data for {symbol}:")

        historical_data, fibonacci_levels = analyze_historical_data(symbol, start_date, end_date, interval)

        if historical_data is not None:
            current_vwap = historical_data['VWAP'].iloc[-1]
            predicted_vwap, confidence_interval, slope = predict_next_period(symbol, start_date, end_date, interval)

            current_price = historical_data['Close'].iloc[-1]
            print(f"Current Price: ${current_price:.2f}")
            print(f"Current VWAP: {current_vwap:.2f} (Predicted AVG. VWAP next {PREDICTION_DAYS} days: {predicted_vwap:.2f})")
            print(f"Confidence Interval: ({confidence_interval[0]:.2f}, {confidence_interval[1]:.2f})")
            print(f"Slope of trendline: {slope:.4f}")

            for level, price in fibonacci_levels.items():
                print(f"Fibonacci Level {level}: ${price:.2f} - {'Price is bullish' if current_vwap < price else 'Price is bearish'}")
        else:
            print(f"Could not analyze historical data for {symbol}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Stock Prediction Analysis')
    parser.add_argument('--days', type=int, default=20, help='Number of days for prediction (default: 20)')
    args = parser.parse_args()
    
    main(args.days)
