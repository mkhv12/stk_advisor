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
import argparse
import pprint  # Import pprint for pretty printing

# Suppress the specific warning from yfinance
warnings.filterwarnings("ignore", category=FutureWarning, module="yfinance")

# Initialize colorama
colorama.init()

# Load portfolio data from Excel
portfolio_data = pd.read_excel('portfolio.xlsx')

def fetch_stock_data(ticker, start_date, end_date, interval, progress=False):
    stock_data = yf.download(ticker, start=start_date, end=end_date, interval=interval, progress=progress)
    return stock_data

def analyze_stock(data, weights):
    # Calculate RSI
    data.loc[:, 'RSI'] = tech_analysis_tools.calculate_rsi(data)

    # Calculate MACD
    macd_histogram, macd_line, signal_line = tech_analysis_tools.calculate_macd(data)

    # Calculate VWAP
    data.loc[:, 'VWAP'] = tech_analysis_tools.calculate_vwap(data)

    # Calculate Parabolic SAR
    data = tech_analysis_tools.calculate_parabolic_sar(data)

    # Analyze Parabolic SAR
    parabolic_sar_status = tech_analysis_tools.analyze_parabolic_sar(data)

    # Check for Golden Cross
    golden_cross = tech_analysis_tools.check_golden_cross(data)

    # Analyze Volume Trend
    volume_trend = tech_analysis_tools.analyze_volume_trend(data)

    # Calculate Bollinger Bands
    data.loc[:, 'Bollinger_Upper'], data.loc[:, 'Bollinger_Lower'] = tech_analysis_tools.calculate_bollinger_bands(data)

    # Calculate Stochastic Oscillator
    data.loc[:, 'Stochastic_%K'], data.loc[:, 'Stochastic_%D'] = tech_analysis_tools.calculate_stochastic_oscillator(data)

    # # Get the latest values
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

    # Analyze Bollinger Bands status
    bollinger_upper = data['Bollinger_Upper'].iloc[-1]
    bollinger_lower = data['Bollinger_Lower'].iloc[-1]
    if current_price >= bollinger_upper:
        bollinger_status = 'Price near Upper Bollinger Band (Sell Signal)'
    elif current_price <= bollinger_lower:
        bollinger_status = 'Price near Lower Bollinger Band (Buy Signal)'
    else:
        bollinger_status = 'Price within Bollinger Bands (Neutral)'

    # Analyze Stochastic Oscillator status
    stochastic_k = data['Stochastic_%K'].iloc[-1]
    stochastic_d = data['Stochastic_%D'].iloc[-1]
    if stochastic_k > 80 and stochastic_d > 80:
        stochastic_status = 'Overbought (Sell Signal)'
    elif stochastic_k < 20 and stochastic_d < 20:
        stochastic_status = 'Oversold (Buy Signal)'
    else:
        stochastic_status = 'Neutral'

    # Analyze Volume Trend
    candlestick_pattern = tech_analysis_tools.analyze_candlestick_patterns(data)

    # Calculate weighted scores for buy and sell signals
    weighted_buy_score = 0
    weighted_sell_score = 0
    weighted_hold_score = 0
    
    indicators = {
        'RSI_Status': rsi_status,
        'MACD_Status': macd_status,
        'MACD_Histogram_Status': macd_histogram_status,
        'VWAP_Status': vwap_status,
        'Golden_Cross_Status': golden_cross_status,
        'Parabolic_SAR_Status': parabolic_sar_status,
        'Volume_Trend': volume_trend,
        'Bollinger_Status': bollinger_status,
        'Stochastic_Status': stochastic_status,
        'CandleStick_Pattern_Status': candlestick_pattern
    }


    for indicator, status in indicators.items():
        if 'Buy Signal' in status:
            weighted_buy_score += weights[indicator]
        elif 'Sell Signal' in status:
            weighted_sell_score += weights[indicator]
        else:
            weighted_hold_score += weights[indicator]

    #print(f"{weighted_buy_score} / {weighted_sell_score}")
    # Determine the final decision based on weighted scores
    # x = 1.0 # to make sure that multiple technicals are making the decision in addition to weight
    # if weighted_buy_score > weighted_sell_score and weighted_buy_score > x:
    #     decision = "Consider Buy"
    # elif weighted_sell_score > weighted_buy_score and weighted_sell_score > x:
    #     decision = "Consider Sell"
    # else:
    #     decision = "Hold"

    #print(f"\n{weighted_buy_score} / {weighted_sell_score} / {weighted_hold_score}")
    if weighted_buy_score > weighted_sell_score and weighted_buy_score > weighted_hold_score:
        decision = "Consider Buy"
    elif weighted_sell_score > weighted_buy_score and weighted_sell_score > weighted_hold_score:
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
        'Parabolic_SAR_Status': parabolic_sar_status,
        'Bollinger_Status': bollinger_status,
        'Stochastic_Status': stochastic_status,
        'CandleStick_Pattern_Status': candlestick_pattern,
        'Decision': decision,
        'Current_Price': current_price
    }


def print_with_color(text, color):
    """
    Print text with specified color using colorama
    """
    color_code = getattr(Fore, color.upper(), Fore.WHITE)
    reset_code = Style.RESET_ALL
    print(f"{color_code}{text}{reset_code}")

def real_time_analysis(qdays, interval, weights):
    # Step 1: Define the date range
    date_back = datetime.now() - timedelta(days=qdays)
    today = datetime.now() + timedelta(days=1)
    start_date = date_back.strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    print("********************************************************************")
    print(f"\nDate range: {start_date} to {end_date} and {interval} chart\n")
    print("********************************************************************")

    # Loop through each row in the portfolio data
    for index, row in portfolio_data.iterrows():
        symbol = row['Symbol']
        status = row['STATUS']
        purchase_date = row['PURCHASE _DATE']
        purchase_price = row['PURCHASE_PRICE']
        purchase_qty = row['PURCHASE_QTY']

        # Analyze stock
        stock_data = fetch_stock_data(symbol, start_date, end_date, interval, progress=False)
        analysis = analyze_stock(stock_data, weights)

        print(f"\nAnalyzing {symbol}  ${analysis['Current_Price']:.2f}")

        if analysis:
            if analysis['Decision'] != "Hold":
                print(f"RSI Status: {analysis['RSI_Status']}")
                print(f"Stochastic Status: {analysis['Stochastic_Status']}")
                print(f"MACD Status: {analysis['MACD_Status']}")
                print(f"MACD Histogram: {analysis['MACD_Histogram_Status']}")
                print(f"CandleStick Pattern: {analysis['CandleStick_Pattern_Status']}")
                print(f"Golden Cross Status: {analysis['Golden_Cross_Status']}")
                print(f"Parabolic_SAR_Status: {analysis['Parabolic_SAR_Status']}")
                print(f"VWAP: {analysis['VWAP']:.2f} ({analysis['VWAP_Status']})")
                print(f"Bollinger Status: {analysis['Bollinger_Status']}")
                print(f"Volume Trend: {analysis['Volume_Trend']}")
                
                if analysis['Decision'] == "Consider Sell" and status == "HOLDING":
                    print_with_color(f"Decision: {analysis['Decision']}", "red")

                    if purchase_date and purchase_price and purchase_qty:
                        holding_type, gain_or_loss, tax_implication, gain_or_loss_perc = tech_analysis_tools.calculate_tax_implications(
                            purchase_date, purchase_price, analysis['Current_Price'], purchase_qty
                        )
                        print("***********")
                        print(f"Holding Type: {holding_type}")
                        print(f"Potential Gain/Loss: ${gain_or_loss:.2f} ({gain_or_loss_perc:.0f}%)")
                        print(f"Estimated Tax Implication: ${tax_implication:.2f}")
                        print("***********")
                elif analysis['Decision'] == "Consider Sell" and status != "HOLDING":
                    print_with_color(f"Decision: ****Possible Opportunity Coming****", "yellow")
                    
                if analysis['Decision'] == "Consider Buy":
                    print_with_color(f"Decision: {analysis['Decision']}", "green")
            else:
                print_with_color(f"Decision: {analysis['Decision']}", "cyan")
        else:
            print(f"Could not analyze {symbol}")

    print("\n")

def backtest_analysis(qdays, interval, weights):
    # Step 1: Define the date range
    date_back = datetime.now() - timedelta(days=qdays)
    today = datetime.now() + timedelta(days=1)
    start_date = date_back.strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    symb_count_wins_signals = 0
    symb_percentage_total = 0

    print(f"\nDate range: {start_date} to {end_date} and {interval} chart")
    print("***********")

    # Loop through each row in the portfolio data
    for index, row in portfolio_data.iterrows():
        symbol = row['Symbol']

        analysis = back_test.backtest(symbol, start_date, end_date, interval, weights, profit_threshold=0.04, stop_loss_threshold=0.02)

        print(f"\nAnalyzing {symbol} ${analysis['Current_Price']:.2f}")

        # Loop through each signal and print it in a cleaner format
        # for signal in analysis['Signals']:
        #     timestamp, action, price = signal
        #     print(f"Date: {timestamp}, Action: {action}, Price: {price:.2f}")

        print(f"Total Buy Signals: {analysis['Count_Buy_Signals']}")
        print(f"Total Sell Signals: {analysis['Count_Sell_Signals']}")
        print(f"Profit or Loss: ${analysis['Profit_or_Loss']:.2f}")
        print(f"Average Hold Time: {analysis['Average_Hold_Time']:.0f} Day")

        if analysis['Count_Buy_Signals'] != 0:
            print(f"Total Wins:{analysis['Total_Wins']} ({(analysis['Total_Wins']/analysis['Count_Buy_Signals'])*100:.0f}%)")
            symb_percentage_total += (analysis['Total_Wins']/analysis['Count_Buy_Signals'])*100
            symb_count_wins_signals += 1
        else:
            print(f"Total Wins:{analysis['Total_Wins']} ({0}%)")
            symb_percentage_total += 0
            symb_count_wins_signals += 0

    print("\n")

    print(f"Overall Average Win Percentage = {symb_percentage_total/symb_count_wins_signals:.0f}%")
    
    print("\n")


def optimized_analysis():

    back_test.run_optimization()


def main(backtest=False, opt=False):
    # Default weights for real-time analysis
    #emphasis on reversal and strength

    weights = {
        'RSI_Status': 1.5,         
        'MACD_Status': 1.5,          
        'MACD_Histogram_Status': 0.5,   
        'VWAP_Status': 0.5,          
        'Golden_Cross_Status': 1.5,     
        'Parabolic_SAR_Status': 0.3, 
        'Volume_Trend': 0.5,            
        'Bollinger_Status': 0.5,       
        'Stochastic_Status': 0.3,
        'CandleStick_Pattern_Status': 1.5
    }


    if backtest:
        backtest_analysis(365, "1d", weights)
        backtest_analysis(90, "1h", weights)
        # backtest_analysis(59, "15m", weights)
        # backtest_analysis(59, "5m", weights)
    elif opt:
        # Run the optimization
        optimized_analysis()
    else:
        while True:
            real_time_analysis(365, "1d", weights)
            real_time_analysis(90, "1h", weights)
            #real_time_analysis(59, "15m", weights)  # max 59 days on 15m
            #real_time_analysis(59, "5m", weights)   # max 59 days on 15m
            print("***********************************************************")
            print("5 minutes before running again...")
            time.sleep(300)  # Sleep for 300 seconds (5 minutes)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Stock Analysis Tool')
    parser.add_argument('--backtest', action='store_true', help='Run backtesting and optimization')
    parser.add_argument('--opt', action='store_true', help='Optimize weights')
    args = parser.parse_args()

    main(backtest=args.backtest, opt=args.opt)
