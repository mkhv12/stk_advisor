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

def calculate_sma(data, window):
    return data['Close'].rolling(window=window).mean()

def check_golden_cross(data):
    sma_50 = calculate_sma(data, 50)
    sma_200 = calculate_sma(data, 200)
    golden_cross = (sma_50.iloc[-1] > sma_200.iloc[-1]) and (sma_50.iloc[-2] <= sma_200.iloc[-2])
    return golden_cross

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

    # Check for Golden Cross
    golden_cross = check_golden_cross(data)

    # Get the latest values
    latest_rsi = data['RSI'].iloc[-1]
    latest_macd_histogram = macd_histogram.iloc[-1]
    previous_macd_histogram = macd_histogram.iloc[-2]

    # Determine RSI status
    if latest_rsi > 70:
        rsi_status = 'Overbought (Sell Signal)'
    elif latest_rsi < 30:
        rsi_status = 'Oversold (Buy Signal)'
    else:
        rsi_status = 'Neutral'

    # Determine MACD status
    if macd_line.iloc[-1] > signal_line.iloc[-1]:
        macd_status = 'Bullish (Buy Signal)'
    else:
        macd_status = 'Bearish (Sell Signal)'

    # Determine MACD Histogram reversal
    if previous_macd_histogram < 0 and latest_macd_histogram >= 0:
        macd_histogram_status = 'Reversal to Bullish (Buy Signal)'
    elif previous_macd_histogram > 0 and latest_macd_histogram <= 0:
        macd_histogram_status = 'Reversal to Bearish (Sell Signal)'
    else:
        macd_histogram_status = 'No Reversal'

    # Determine if current price is above or below VWAP
    current_price = data['Close'].iloc[-1]
    vwap = data['VWAP'].iloc[-1]
    
    if current_price < vwap:
        vwap_status = "Current Price is Under VWAP (Buy Signal)"
    else:
        vwap_status = "Current Price is Over VWAP (Sell Signal)"

    # Golden Cross status
    if golden_cross:
        golden_cross_status = 'Golden Cross (Strong Buy Signal)'
    else:
        golden_cross_status = 'No Golden Cross'

    # Count the number of buy or sell signals
    buy_or_sell_signals = [rsi_status, macd_status, macd_histogram_status, vwap_status, golden_cross_status]
    count_buy_signals = sum(signal.endswith("(Buy Signal)") for signal in buy_or_sell_signals)
    count_sell_signals = sum(signal.endswith("(Sell Signal)") for signal in buy_or_sell_signals)

    # Determine whether to consider buy or sell based on the count of signals
    if count_buy_signals >= 3:
        decision = "Consider Buy"
    elif count_sell_signals >= 3:
        decision = "Consider Sell"
    else:
        decision = "Hold"

    return {
        'RSI': latest_rsi,
        'RSI_Status': rsi_status,
        'MACD_Status': macd_status,
        'MACD_Histogram_Status': macd_histogram_status,
        'VWAP': vwap,
        'VWAP_Status': vwap_status,
        'Golden_Cross_Status': golden_cross_status,
        'Decision': decision
    }

def main():
    # Step 1: Define the date range
    year_ago = datetime.now() - timedelta(days=365)  # Changed to 365 days for SMA calculation
    start_date = year_ago.strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    interval = '1d'  # Changed to '1d' for daily data suitable for Golden Cross analysis

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
            print(f"Golden Cross Status: {analysis['Golden_Cross_Status']}")
            print(f"Decision: {analysis['Decision']}")

        else:
            print(f"Could not analyze {symbol}")

if __name__ == "__main__":
    main()
