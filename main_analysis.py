import sys
import yfinance as yf
import pandas as pd
import warnings
from datetime import datetime, timedelta
import colorama
from colorama import Fore, Style
import time
import tech_analysis_tools 
import back_test 


# Suppress the specific warning from yfinance
warnings.filterwarnings("ignore", category=FutureWarning, module="yfinance")

# Initialize colorama
colorama.init()

# Load portfolio data from Excel
portfolio_data = pd.read_excel('portfolio.xlsx')


def fetch_stock_data(ticker, start_date, end_date, interval, progress=False):
    stock_data = yf.download(ticker, start=start_date, end=end_date, interval=interval, progress=progress)
    return stock_data

def analyze_stock(data):
    # Calculate RSI
    data.loc[:, 'RSI'] = tech_analysis_tools.calculate_rsi(data)

    # Calculate MACD
    macd_histogram, macd_line, signal_line = tech_analysis_tools.calculate_macd(data)

    # Calculate VWAP
    data.loc[:, 'VWAP'] = tech_analysis_tools.calculate_vwap(data)

    # Check for Golden Cross
    golden_cross = tech_analysis_tools.check_golden_cross(data)

    # Analyze Volume Trend
    volume_trend = tech_analysis_tools.analyze_volume_trend(data)

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
    if count_buy_signals >= 4:
        decision = "Consider Buy"
    elif count_sell_signals >= 4:
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

def calculate_tax_implications(purchase_date, purchase_price, current_price, quantity):
    """
    Calculate potential tax implications.
    """
    purchase_date = datetime.strptime(purchase_date, "%Y-%m-%d")
    holding_period = (datetime.now() - purchase_date).days
    gain_or_loss = (current_price - purchase_price) * quantity
    gain_or_loss_perc = (gain_or_loss / (purchase_price * quantity)) * 100

    # Assuming tax rates: short-term is 30%, long-term is 15%
    if holding_period < 365:
        tax_rate = 0.30
        holding_type = "Short-term"
    else:
        tax_rate = 0.15
        holding_type = "Long-term"

    tax_implication = gain_or_loss * tax_rate
    return holding_type, gain_or_loss, tax_implication, gain_or_loss_perc

def print_with_color(text, color):
    """
    Print text with specified color using colorama
    """
    color_code = getattr(Fore, color.upper(), Fore.WHITE)
    reset_code = Style.RESET_ALL
    print(f"{color_code}{text}{reset_code}")


def main(perform_backtesting, qdays, interval):
    # Step 1: Define the date range
    date_back = datetime.now() - timedelta(days=qdays)
    today = datetime.now() + timedelta(days=1)
    start_date = date_back.strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    #interval = '1h'

    count_profit = 0
    count_loss = 0
    total_hold_time = 0
    hold_time = 0
    end_value= 0

    
    print(f"\nDate range: {start_date} to {end_date} and {interval} chart")
    print("***********")

    # Loop through each row in the portfolio data
    for index, row in portfolio_data.iterrows():
        symbol = row['Symbol']
        status = row['STATUS']
        purchase_date = row['PURCHASE _DATE']
        purchase_price = row['PURCHASE_PRICE']
        purchase_qty = row['PURCHASE_QTY']
        hold_time_count = 0

        # Analyze stock
        stock_data = fetch_stock_data(symbol, start_date, end_date, interval, progress=False)
        analysis = analyze_stock(stock_data)

        print(f"\nAnalyzing {symbol}  ${analysis['Current_Price']:.2f}")

        if not perform_backtesting:
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

                        if status == "HOLDING" and purchase_date and purchase_price and purchase_qty:
                            holding_type, gain_or_loss, tax_implication, gain_or_loss_perc = calculate_tax_implications(
                                purchase_date, purchase_price, analysis['Current_Price'], purchase_qty
                            )
                            print("***********")
                            print(f"Holding Type: {holding_type}")
                            print(f"Potential Gain/Loss: ${gain_or_loss:.2f} ({gain_or_loss_perc:.0f}%)")
                            print(f"Estimated Tax Implication: ${tax_implication:.2f}")
                            print("***********")

                    if analysis['Decision'] == "Consider Buy":
                        print_with_color(f"Decision: {analysis['Decision']}", "green")
                else:
                    print_with_color(f"Decision: {analysis['Decision']}", "cyan")
            else:
                print(f"Could not analyze {symbol}")

        # Perform backtesting if flag is set
        if perform_backtesting:
            backtest_result = back_test.backtest(symbol, start_date, end_date, interval)

            if backtest_result:
                print(f"\nBacktesting Results for {symbol}:")
                print(f"Initial Capital: ${backtest_result['Initial_Capital']:.2f}")
                print(f"Final Portfolio Value: ${backtest_result['Final_Portfolio_Value']:.2f}")
                print(f"Profit or Loss: ${backtest_result['Profit_or_Loss']:.2f}")
                print("Trade Signals:")
                for signal in backtest_result['Signals']:
                    print(f"Date: {signal[0]}, Action: {signal[1]}, Price: ${signal[2]:.2f}")
                    if signal[1] == "Buy":
                        buy_price = signal[2]
                    if signal[1] =="Sell":
                        print(f"Total Hold Time: {backtest_result['Total_Hold_Time'][hold_time_count]:.0f}")
                        
                        if signal[2] > buy_price:
                            count_profit += 1
                            end_value += backtest_result['Profit_or_Loss']
                        elif signal[2] < buy_price:
                            count_loss += 1
                            end_value -= backtest_result['Profit_or_Loss']

                        
                        hold_time += backtest_result['Total_Hold_Time'][hold_time_count]
                        hold_time_count += 1

                total_hold_time += hold_time

            else:
                print(f"Could not perform backtesting for {symbol}")


    if perform_backtesting:
        print("\n")
        perc_profit = (count_profit/(count_profit+count_loss))*100
        print(f"Total QTY Profit {count_profit} ({perc_profit:.0f}%)")
        print(f"Total QTY Loss {count_loss}")
        print(f"Average Hold Time {round((total_hold_time)/(count_profit+count_loss),0):.0f} Days")
        print(f"Total Profit ${round(end_value,0):.2f}")

    print("\n")

if __name__ == "__main__":
    while True:
        if len(sys.argv) > 1 and sys.argv[1].lower() == "true":
            main(True, 700, "1h")  # Set to True to enable backtesting
            main(True, 30, "15m") 
        else:
           main(False, 700, "1h")   # Set to True to enable backtesting
           main(False, 30, "15m")  

        print("***********************************************************")
        print("5 minutes before running again...")
        time.sleep(300)  # Sleep for 300 seconds (5 minutes)