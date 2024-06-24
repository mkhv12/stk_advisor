import main_analysis


def backtest(ticker, start_date, end_date, interval, weights, profit_threshold=0.04, stop_loss_threshold=0.02):
    # Fetch stock data
    data = main_analysis.fetch_stock_data(ticker, start_date, end_date, interval, progress=False)

    if data.empty:
        print(f"No data found for {ticker}")
        return None

    # Prepare for backtesting
    initial_capital = 300 # Initial capital for backtesting
    position = 0  # Current position (number of shares held)
    cash = initial_capital  # Remaining cash
    signals = []
    entry_timestamp = None
    total_hold_time = []
    entry_price = None  # Track the price at which we entered the position
    count_profit_wins = 0

    # Loop through the data to generate signals and simulate trades
    for i in range(len(data)):
        subset_data = data.iloc[:i+1].copy()  # Current subset of data up to the current date
        if len(subset_data) < 2:
            continue

        analysis = main_analysis.analyze_stock(subset_data, weights)
        decision = analysis['Decision']

        current_price = subset_data['Close'].iloc[-1]
        date = subset_data.index[-1]

        if decision == "Consider Buy" and cash >= current_price:
            if position == 0:
                entry_timestamp = date  # Record entry timestamp if entering a new position
                entry_price = current_price
            position += cash // current_price
            cash %= current_price
            signals.append((date, "Buy", current_price))

        elif decision == "Consider Sell" and position > 0:
            # Check if the current price has moved by the threshold percentage
            price_increase = (current_price - entry_price) / entry_price
            price_decrease = (entry_price - current_price) / entry_price

            if price_increase >= profit_threshold or price_decrease >= stop_loss_threshold:
                cash += position * current_price
                position = 0
                exit_timestamp = date  # Record exit timestamp if exiting a position
                if exit_timestamp:
                    hold_time = exit_timestamp - entry_timestamp  # Calculate hold time
                    total_hold_time.append(hold_time.total_seconds() / (60 * 60 * 24))  # Convert to days and accumulate
                entry_timestamp = None  # Reset entry timestamp

                if current_price-entry_price > 0:
                    count_profit_wins += 1

                entry_price = None  # Reset entry price
                signals.append((date, "Sell", current_price))




    # Calculate final portfolio value
    final_portfolio_value = cash + position * data['Close'].iloc[-1]
    profit_or_loss = final_portfolio_value - initial_capital

    # Count the number of buy or sell signals, including volume trend analysis
    buy_or_sell_signals = [
        signal[1] for signal in signals
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
        'Total_Wins': count_profit_wins,  # Include sell signals count
        'Current_Price': current_price,  # Include sell signals count
        'Decision': decision,  # Include sell signals count
    }

