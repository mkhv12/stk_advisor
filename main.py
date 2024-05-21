import yfinance as yf
import pandas as pd
import warnings
from datetime import datetime, timedelta

# Suppress the specific warning from yfinance
warnings.filterwarnings("ignore", category=FutureWarning, module="yfinance")

# Load portfolio data from Excel
portfolio_data = pd.read_excel('portfolio.xlsx')

def calculate_rsi(data, window=14):
    delta = data['Close'].diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=window, min_periods=1).mean()
    avg_loss = loss.rolling(window=window, min_periods=1).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi

def calculate_ema(data, window):
    return data['Close'].ewm(span=window, adjust=False).mean()

def calculate_macd(data):
    ema12 = calculate_ema(data, 12)
    ema26 = calculate_ema(data, 26)
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_histogram = macd_line - signal_line
    return macd_histogram, macd_line, signal_line

def calculate_vwap(data):
    typical_price = (data['High'] + data['Low'] + data['Close']) / 3
    vwap = (typical_price * data['Volume']).cumsum() / data['Volume'].cumsum()
    return vwap

def fetch_stock_data(ticker, start_date, end_date, interval, progress=False):
    stock_data = yf.download(ticker, start=start_date, end=end_date, interval=interval, progress=progress)
    return stock_data

def analyze_stock(ticker, start_date, end_date, interval):
    # Fetch stock data
    data = fetch_stock_data(ticker, start_date, end_date, interval, progress=False)

    if data.empty:
        print(f"No data found for {ticker}")
        return None

    # Calculate RSI
    data['RSI'] = calculate_rsi(data)

    # Calculate MACD
    macd_histogram, macd_line, signal_line = calculate_macd(data)

    # Calculate VWAP
    data['VWAP'] = calculate_vwap(data)

    # Get the latest values
    latest_rsi = data['RSI'].iloc[-1]
    latest_macd_histogram = macd_histogram.iloc[-1]
    previous_macd_histogram = macd_histogram.iloc[-2]

    # Determine RSI status
    if latest_rsi > 70:
        rsi_status = 'Overbought'
    elif latest_rsi < 30:
        rsi_status = 'Oversold'
    else:
        rsi_status = 'Neutral'

    # Determine MACD status
    if macd_line.iloc[-1] > signal_line.iloc[-1]:
        macd_status = 'Bullish'
    else:
        macd_status = 'Bearish'

    # Determine MACD Histogram reversal
    if previous_macd_histogram < 0 and latest_macd_histogram >= 0:
        macd_histogram_status = 'Reversal to Bullish'
    elif previous_macd_histogram > 0 and latest_macd_histogram <= 0:
        macd_histogram_status = 'Reversal to Bearish'
    else:
        macd_histogram_status = 'No Reversal'

    # Determine if current price is above or below VWAP
    current_price = data['Close'].iloc[-1]
    vwap = data['VWAP'].iloc[-1]
    
    if current_price < vwap:
        vwap_status = "Current Price is Under VWAP (Buy Signal)"
    else:
        vwap_status = "Current Price is Over VWAP (Sell Signal)"

    return {
        'RSI': latest_rsi,
        'RSI_Status': rsi_status,
        'MACD_Status': macd_status,
        'MACD_Histogram_Status': macd_histogram_status,
        'VWAP': data['VWAP'].iloc[-1],
        'VWAP_Status': vwap_status
    }

def backtest_strategy(data):
    capital = 10000  # Initial capital
    shares = 0  # Number of shares held
    in_position = False  # Flag to track if currently in a position

    # Calculate RSI, MACD, and VWAP for the entire dataset
    data['RSI'] = calculate_rsi(data)
    data['MACD_Histogram'], data['MACD_Line'], data['MACD_Signal'] = calculate_macd(data)
    data['VWAP'] = calculate_vwap(data)

    # Iterate through the historical data
    for i in range(1, len(data)):
        row = data.iloc[i]
        prev_row = data.iloc[i - 1]

        # Buy signal: RSI is oversold, MACD Histogram shows a reversal to bullish, and current price is below VWAP
        if (row['RSI'] < 30 and prev_row['MACD_Histogram'] < 0 and row['MACD_Histogram'] >= 0 and 
            row['Close'] < row['VWAP'] and not in_position):
            shares = capital / row['Close']  # Buy all shares with available capital
            in_position = True  # Set flag to indicate position is open
        
        # Sell signal: RSI is overbought, MACD Histogram shows a reversal to bearish, or current price is above VWAP
        elif ((row['RSI'] > 70 or (prev_row['MACD_Histogram'] > 0 and row['MACD_Histogram'] <= 0) or 
               row['Close'] > row['VWAP']) and in_position):
            capital = shares * row['Close']  # Sell all shares and update capital
            shares = 0  # Reset shares to zero
            in_position = False  # Set flag to indicate no position

    # If still holding shares, sell them at the last available price
    if in_position:
        capital = shares * data['Close'].iloc[-1]

    final_portfolio_value = capital
    # Calculate return on investment (ROI)
    roi = (final_portfolio_value - 10000) / 10000 * 100
    
    return final_portfolio_value, roi

def main():
    # Step 1: Define the date range
    year_ago = datetime.now() - timedelta(days=42)  # 1 year before
    start_date = year_ago.strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    interval='1h'

    print(f"\nDate range: {start_date} to {end_date} and {interval} chart")

    # Loop through each row in the portfolio data
    for index, row in portfolio_data.iterrows():
        symbol = row['Symbol']
        
        print(f"\nAnalyzing {symbol}...")

        # Analyze stock
        analysis = analyze_stock(symbol, start_date, end_date, interval)

        if analysis:
            print(f"RSI Status: {analysis['RSI_Status']}")
            print(f"MACD Status: {analysis['MACD_Status']}")
            print(f"MACD Histogram: {analysis['MACD_Histogram_Status']}")
            print(f"VWAP: {analysis['VWAP']:.2f} ({analysis['VWAP_Status']})")
            
            # # Backtest strategy
            # data = fetch_stock_data(symbol, start_date, end_date, interval='1d', progress=False)
            # if not data.empty:
            #     final_portfolio_value, roi = backtest_strategy(data)
            #     print(f"Backtest - Final Portfolio Value: ${final_portfolio_value:.2f}")
            #     print(f"Backtest - Return on Investment (ROI): {roi:.2f}%")
            # else:
            #     print(f"Could not fetch data for backtesting {symbol}")
        else:
            print(f"Could not analyze {symbol}")

if __name__ == "__main__":
    main()
