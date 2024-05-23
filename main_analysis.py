import yfinance as yf
import pandas as pd
import warnings
from datetime import datetime, timedelta
import colorama
from colorama import Fore, Style


# Suppress the specific warning from yfinance
warnings.filterwarnings("ignore", category=FutureWarning, module="yfinance")

# Initialize colorama
colorama.init()

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

def calculate_vma(data, window=20):
    return data['Volume'].rolling(window=window).mean()

def analyze_volume_trend(data, window=20):
    data['VMA'] = calculate_vma(data, window)
    latest_volume = data['Volume'].iloc[-1]
    vma = data['VMA'].iloc[-1]

    if latest_volume > vma:
        volume_trend = 'Increasing Volume (Buy Signal)'
    else:
        volume_trend = 'Decreasing Volume (Sell Signal)'

    return volume_trend

def analyze_stock(data):
    # Calculate RSI
    data.loc[:, 'RSI'] = calculate_rsi(data)

    # Calculate MACD
    macd_histogram, macd_line, signal_line = calculate_macd(data)

    # Calculate VWAP
    data.loc[:, 'VWAP'] = calculate_vwap(data)

    # Check for Golden Cross
    golden_cross = check_golden_cross(data)

    # Analyze Volume Trend
    volume_trend = analyze_volume_trend(data)

    # Get the latest values
    latest_rsi = data['RSI'].iloc[-1]
    latest_macd_histogram = macd_histogram.iloc[-1]

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
    macd_histogram_status = 'No Reversal'
    if len(macd_histogram) > 1:
        previous_macd_histogram = macd_histogram.iloc[-2]
        if previous_macd_histogram < 0 and latest_macd_histogram >= 0:
            macd_histogram_status = 'Reversal to Bullish (Buy Signal)'
        elif previous_macd_histogram > 0 and latest_macd_histogram <= 0:
            macd_histogram_status = 'Reversal to Bearish (Sell Signal)'

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
    buy_or_sell_signals = [
        rsi_status, macd_status, macd_histogram_status, 
        vwap_status, golden_cross_status, volume_trend
    ]
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
        'Volume_Trend': volume_trend,
        'Decision': decision,
        'Current_Price': current_price 
    }

def backtest(ticker, start_date, end_date, interval):
    # Fetch stock data
    data = fetch_stock_data(ticker, start_date, end_date, interval, progress=False)

    if data.empty:
        print(f"No data found for {ticker}")
        return None

    # Prepare for backtesting
    initial_capital = 10000  # Initial capital for backtesting
    position = 0  # Current position (number of shares held)
    cash = initial_capital  # Remaining cash
    signals = []
    entry_timestamp = None
    total_hold_time = 0

    # Loop through the data to generate signals and simulate trades
    for i in range(len(data)):
        subset_data = data.iloc[:i+1].copy()  # Current subset of data up to the current date
        if len(subset_data) < 2:
            continue

        analysis = analyze_stock(subset_data)
        decision = analysis['Decision']

        current_price = subset_data['Close'].iloc[-1]
        date = subset_data.index[-1]

        if decision == "Consider Buy" and cash >= current_price:
            if position == 0:
                entry_timestamp = date  # Record entry timestamp if entering a new position
            position += cash // current_price
            cash %= current_price
            signals.append((date, "Buy", current_price))

        elif decision == "Consider Sell" and position > 0:
            cash += position * current_price
            position = 0
            exit_timestamp = date  # Record exit timestamp if exiting a position
            if entry_timestamp:
                hold_time = exit_timestamp - entry_timestamp  # Calculate hold time
                total_hold_time += hold_time.total_seconds() / (60 * 60 * 24)  # Convert to days and accumulate
            entry_timestamp = None  # Reset entry timestamp
            signals.append((date, "Sell", current_price))

    # Calculate final portfolio value
    final_portfolio_value = cash + position * data['Close'].iloc[-1]
    profit_or_loss = final_portfolio_value - initial_capital

    # Count the number of buy or sell signals, including volume trend analysis
    buy_or_sell_signals = [
        signal[2] for signal in signals
    ]
    count_buy_signals = sum(signal == "Buy" for signal in buy_or_sell_signals)
    count_sell_signals = sum(signal == "Sell" for signal in buy_or_sell_signals)

    return {
        'Initial_Capital': initial_capital,
        'Final_Portfolio_Value': final_portfolio_value,
        'Profit_or_Loss': profit_or_loss,
        'Total_Hold_Time': total_hold_time,  # Include total hold time in the result
        'Signals': signals,
        'Count_Buy_Signals': count_buy_signals,  # Include buy signals count
        'Count_Sell_Signals': count_sell_signals,  # Include sell signals count
    }


def print_with_color(text, color):
    """
    Print text with specified color using colorama
    """
    color_code = getattr(Fore, color.upper(), Fore.WHITE)
    reset_code = Style.RESET_ALL
    print(f"{color_code}{text}{reset_code}")


def main(perform_backtesting=False):
    # Step 1: Define the date range
    date_back = datetime.now() - timedelta(days=365)
    today = datetime.now() + timedelta(days=1)
    start_date = date_back.strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    interval = '1d'

    count_profit = 0
    count_loss = 0
    total_hold_time = 0


    print(f"\nDate range: {start_date} to {end_date} and {interval} chart")

    # Loop through each row in the portfolio data
    for index, row in portfolio_data.iterrows():
        symbol = row['Symbol']

        # Analyze stock
        stock_data = fetch_stock_data(symbol, start_date, end_date, interval, progress=False)
        analysis = analyze_stock(stock_data)

        print(f"\nAnalyzing {symbol}  ${analysis['Current_Price']:.2f}")

        if analysis:
            if analysis['Decision'] != "Hold":
                    print(f"RSI Status: {analysis['RSI_Status']}")
                    print(f"MACD Status: {analysis['MACD_Status']}")
                    print(f"MACD Histogram: {analysis['MACD_Histogram_Status']}")
                    print(f"VWAP: {analysis['VWAP']:.2f} ({analysis['VWAP_Status']})")
                    print(f"Golden Cross Status: {analysis['Golden_Cross_Status']}")
                    print(f"Volume Trend: {analysis['Volume_Trend']}")
                    if analysis['Decision'] == "Consider Sell":
                        print_with_color(f"Decision: {analysis['Decision']}", "red")
                    if analysis['Decision'] == "Consider Buy":
                        print_with_color(f"Decision: {analysis['Decision']}", "green")
            else:
                print_with_color(f"Decision: {analysis['Decision']}", "cyan")
                

        else:
            print(f"Could not analyze {symbol}")

        # Perform backtesting if flag is set
        if perform_backtesting:
            backtest_result = backtest(symbol, start_date, end_date, interval)

            if backtest_result:
                print(f"\nBacktesting Results for {symbol}:")
                print(f"Initial Capital: ${backtest_result['Initial_Capital']:.2f}")
                print(f"Final Portfolio Value: ${backtest_result['Final_Portfolio_Value']:.2f}")
                print(f"Profit or Loss: ${backtest_result['Profit_or_Loss']:.2f}")
                print("Trade Signals:")
                for signal in backtest_result['Signals']:
                    print(f"Date: {signal[0]}, Action: {signal[1]}, Price: ${signal[2]:.2f}")

                print(f"Total Hold Time: {backtest_result['Total_Hold_Time']:.2f}")

                if backtest_result['Profit_or_Loss'] > 0.0:
                    count_profit += 1
                else:
                    count_loss += 1

                total_hold_time += backtest_result['Total_Hold_Time']

            else:
                print(f"Could not perform backtesting for {symbol}")


    if perform_backtesting:
        print("\n")
        print(f"Total QTY Profit {count_profit}")
        print(f"Total QTY Loss {count_loss}")
        print(f"Average Hold Time {round((total_hold_time/10)/21,0)} Months")

    print("\n")

if __name__ == "__main__":
    main(perform_backtesting=False)  # Set to True to enable backtesting
