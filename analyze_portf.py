import ta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timedelta
from statsmodels.tsa.arima.model import ARIMA
import pandas as pd


def analyze_trends(historical_data):
    # Calculate Moving Averages
    historical_data['MA5'] = ta.trend.SMAIndicator(historical_data['Close'], window=5).sma_indicator()
    historical_data['MA50'] = ta.trend.SMAIndicator(historical_data['Close'], window=50).sma_indicator()

    # Calculate Fibonacci Retracement Levels
    high_price = historical_data['High'].max()
    low_price = historical_data['Low'].min()

    # Calculate VWAP
    historical_data = calculate_vwap(historical_data)

    fib_levels = [0.236, 0.382, 0.5, 0.618]  # Adjust as needed
    for level in fib_levels:
        retracement_price = low_price + level * (high_price - low_price)
        column_name = f'Fib_{int(level * 100)}%'
        historical_data[column_name] = retracement_price

    return historical_data


def calculate_vwap(data):
    data['TypicalPrice'] = (data['High'] + data['Low'] + data['Close']) / 3
    data['VolumePrice'] = data['TypicalPrice'] * data['Volume']
    data['CumulativeVolume'] = data['Volume'].cumsum()
    data['CumulativeVolumePrice'] = data['VolumePrice'].cumsum()
    data['VWAP'] = data['CumulativeVolumePrice'] / data['CumulativeVolume']
    return data.drop(['TypicalPrice', 'VolumePrice', 'CumulativeVolume', 'CumulativeVolumePrice'], axis=1)


def simple_trading_algorithm(historical_data):
    """
    A simple trading algorithm based on moving averages and Fibonacci retracement levels.
    Returns the decision based on the given historical data.
    """
    # Buy Signal: When the 5-day moving average crosses above the 50-day moving average
    buy_signal = (historical_data['MA5'] > historical_data['MA50']) & (historical_data['MA5'].shift(1) <= historical_data['MA50'].shift(1))

    # Sell Signal: When the 5-day moving average crosses below the 50-day moving average
    sell_signal = (historical_data['MA5'] < historical_data['MA50']) & (historical_data['MA5'].shift(1) >= historical_data['MA50'].shift(1))

    # Hold Signal: When no buying or selling conditions are met
    hold_signal = ~(buy_signal | sell_signal)

    # Fib Retracement Signal: When the Close price is above the 38% Fibonacci retracement level
    fib_signal = (historical_data['Close'] > historical_data['Fib_61%'])

    # Make a decision based on the direction of the Fibonacci retracement
    if fib_signal.any():
        if historical_data['Fib_61%'].iloc[-1] > historical_data['Fib_61%'].iloc[-2]:
            decision = 'Buy-' + f"Fibonacci retracement at 61% increased."
        elif historical_data['Fib_61%'].iloc[-1] < historical_data['Fib_61%'].iloc[-2]:
            decision = 'Sell-' + f"Fibonacci retracement at 61% decreased."
        else:
            decision = 'Hold-' + "Fibonacci retracement at 61% held steady."
    else:
        # If no Fib Retracement signal, follow the average signal logic
        # Combine signals into a 'Signal' column
        historical_data['Signal'] = 'Hold'
        historical_data.loc[buy_signal, 'Signal'] = 'Buy'
        historical_data.loc[sell_signal, 'Signal'] = 'Sell'

        # Calculate the average signal excluding 'FibRetrace'
        decision = historical_data[historical_data['Signal'] != 'FibRetrace']['Signal'].value_counts(normalize=True).idxmax()

        decision = decision + "-No significant change in Fibonacci retracement."

    # VWAP Signal: When the Close price is above the VWAP
    vwap_signal = historical_data['Close'] > historical_data['VWAP']

    # Make a decision based on the direction of the VWAP
    if vwap_signal.any():
        if historical_data['VWAP'].iloc[-1] > historical_data['VWAP'].iloc[-2]:
            decision += f"\n\nVWAP Signal: Buy-VWAP increased."
        elif historical_data['VWAP'].iloc[-1] < historical_data['VWAP'].iloc[-2]:
            decision += f"\n\nVWAP Signal: Sell-VWAP decreased."
        else:
            decision += "\n\nVWAP Signal: Hold-VWAP held steady."
    else:
        decision += "\n\nVWAP Signal: Hold-No significant change in VWAP."


    return decision


def analyze_sentiment(news_articles, threshold=0.1):
    analyzer = SentimentIntensityAnalyzer()
    sentiments = []

    for article in news_articles:
        text = article.title + " " + article.description
        sentiment_score = analyzer.polarity_scores(text)
        
        # Categorize sentiment based on the threshold
        if sentiment_score['compound'] > threshold:
            sentiments.append(1)  # 1 for positive
        elif sentiment_score['compound'] < -threshold:
            sentiments.append(-1)  # -1 for negative
        else:
            sentiments.append(0)  # 0 for neutral

    return sentiments

def determine_trend(historical_data):
    # Calculate short-term and long-term moving averages
    short_term_ma = historical_data['Close'].rolling(window=5).mean()
    long_term_ma = historical_data['Close'].rolling(window=50).mean()

    # Trend based on moving averages
    if short_term_ma.iloc[-1] > long_term_ma.iloc[-1]:
        trend = "Uptrend"
    elif short_term_ma.iloc[-1] < long_term_ma.iloc[-1]:
        trend = "Downtrend"
    else:
        trend = "Sideways"

    # Check if the close price is above the 50% Fibonacci retracement level
    fib_50_signal = historical_data['Close'] > historical_data['Fib_61%']

    # Check if the close price is above the VWAP
    vwap_signal = historical_data['Close'] > historical_data['VWAP']

    # Consider Fibonacci and VWAP signals for additional confirmation
    if fib_50_signal.any() and vwap_signal.any():
        trend += ", Confirmed by Fibonacci and VWAP"
    elif fib_50_signal.any():
        trend += ", Confirmed by Fibonacci"
    elif vwap_signal.any():
        trend += ", Confirmed by VWAP"

    return trend

def analyze_portfolio(symbol, analyzed_data, news_sentiments):
    # Check if news sentiment data is available
    if news_sentiments:
        avg_sentiment = sum(news_sentiments) / len(news_sentiments)

        # Make a decision based on sentiment, moving averages, and Fibonacci retracement
        if (avg_sentiment > 0) and (analyzed_data['Close'] > analyzed_data['MA5']).all() and (analyzed_data['Close'] > analyzed_data['MA50']).all():
            decision = "Hold"  # or "Buy" based on additional criteria
            explanation = "Positive news sentiment, and the stock price is above both the 10-day and 100-day moving averages. Consider holding."
        elif (avg_sentiment < 0) or (analyzed_data['Close'] <= analyzed_data['MA5']).all() or (analyzed_data['Close'] <= analyzed_data['MA50']).all():
            decision = "Sell"
            explanation = "Negative news sentiment or the stock price is not performing well. Consider selling."
        elif (analyzed_data['Close'] > analyzed_data['Fib_38%']).all() and (analyzed_data['Close'] > analyzed_data['Fib_50%']).all():
            decision = "Hold"
            explanation = "The stock price is above the 38% and 50% Fibonacci retracement levels. Consider holding."
        elif (analyzed_data['Close'] < analyzed_data['Fib_38%']).all() and (analyzed_data['Close'] < analyzed_data['Fib_50%']).all():
            decision = "Sell"
            explanation = "The stock price is below the 38% and 50% Fibonacci retracement levels. Consider selling."
        else:
            decision = "Hold"
            explanation = "No clear signal. Consider holding or reevaluating."

    else:
        # Provide advice based on technical analysis alone
        if (analyzed_data['Close'] > analyzed_data['MA5']).all() and (analyzed_data['Close'] > analyzed_data['MA50']).all():
            decision = "Hold"  # or "Buy" based on additional criteria
            explanation = "The stock price is above both the 5-day and 20-day moving averages. Consider holding."
        elif (analyzed_data['Close'] > analyzed_data['Fib_38%']).all():
            decision = "Hold"  # or "Buy" based on additional criteria
            explanation = "The stock price is above the 38% Fibonacci retracement level. Consider holding."
        elif (analyzed_data['Close'] < analyzed_data['MA5']).all() and (analyzed_data['Close'] < analyzed_data['MA50']).all():
            decision = "Sell"
            explanation = "The stock price is below both the 5-day and 20-day moving averages. Consider selling."
        elif (analyzed_data['Close'] < analyzed_data['Fib_38%']).all():
            decision = "Sell"
            explanation = "The stock price is below the 38% Fibonacci retracement level. Consider selling."
        else:
            decision = "Sell"
            explanation = "The stock price is not performing well. Consider selling. Additional criteria may apply."


    # Analyze portfolio using portfolio data, analyzed data, news sentiment, and forecast data
    average_signal = simple_trading_algorithm(analyzed_data)

    print(f"\n{symbol}")

    print(f"SMA & NEws Sentiment - Signal: {decision}-{explanation}\n")
    #print(f"Explanation: {explanation}\n")

    # Apply the simple trading algorithm
    #average_signal = simple_trading_algorithm(analyzed_data)
    print(f"Fib Signal: {average_signal}")


