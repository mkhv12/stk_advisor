import ta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timedelta
from statsmodels.tsa.arima.model import ARIMA
import pandas as pd


def analyze_trends(historical_data):
    # Calculate Moving Averages
    historical_data['MA5'] = ta.trend.SMAIndicator(historical_data['Close'], window=5).sma_indicator()
    historical_data['MA20'] = ta.trend.SMAIndicator(historical_data['Close'], window=20).sma_indicator()

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
    buy_signal = (historical_data['MA5'] > historical_data['MA20']) & (historical_data['MA5'].shift(1) <= historical_data['MA20'].shift(1))

    # Sell Signal: When the 5-day moving average crosses below the 50-day moving average
    sell_signal = (historical_data['MA5'] < historical_data['MA20']) & (historical_data['MA5'].shift(1) >= historical_data['MA20'].shift(1))

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
    # Calculate moving averages and Fibonacci retracement levels only once
    ma5_condition = (analyzed_data['Close'] > analyzed_data['MA5']).all()
    ma30_condition = (analyzed_data['Close'] > analyzed_data['MA20']).all()
    fib_38_condition = (analyzed_data['Close'] > analyzed_data['Fib_38%']).all()
    fib_50_condition = (analyzed_data['Close'] > analyzed_data['Fib_50%']).all()

    # Initialize decisions and explanations for news sentiment, SMA, and Fibonacci retracement
    news_sentiment_decision = "Hold"
    news_sentiment_explanation = "No news sentiment data available."

    sma_decision = "Hold"
    sma_explanation = "No clear signal based on SMA alone."

    fib_decision = "Hold"
    fib_explanation = "No clear signal based on Fibonacci retracement alone."

    # Check if news sentiment data is available
    if news_sentiments:
        avg_sentiment = sum(news_sentiments) / len(news_sentiments)

        # Make a decision based on sentiment
        if avg_sentiment > 0:
            news_sentiment_decision = "Hold"
            news_sentiment_explanation = "Positive news sentiment. Consider holding."
        elif avg_sentiment < 0:
            news_sentiment_decision = "Sell"
            news_sentiment_explanation = "Negative news sentiment. Consider selling."

    # Make a decision based on SMA
    if ma5_condition and ma30_condition:
        sma_decision = "Hold"
        sma_explanation = "The stock price is above both the 5-day and 20-day moving averages. Consider holding."
    elif (not ma5_condition) and (not ma30_condition):
        sma_decision = "Sell"
        sma_explanation = "The stock price is below both the 5-day and 20-day moving averages. Consider selling."

    # Make a decision based on Fibonacci retracement
    if fib_38_condition and fib_50_condition:
        fib_decision = "Hold"
        fib_explanation = "The stock price is above the 38% and 50% Fibonacci retracement levels. Consider holding."
    elif (not fib_38_condition) and (not fib_50_condition):
        fib_decision = "Sell"
        fib_explanation = "The stock price is below the 38% and 50% Fibonacci retracement levels. Consider selling."

    # Determine overall decision
    overall_decision = "Buy" if all(decision == "Hold" for decision in [news_sentiment_decision, sma_decision, fib_decision]) else "Hold"

    # Print the results
    print(f"\n{symbol}")
    
    # News Sentiment
    print(f"News Sentiment - Signal: {news_sentiment_decision}-{news_sentiment_explanation}\n")
    
    # SMA
    print(f"SMA Signal: {sma_decision}-{sma_explanation}")

    # Fibonacci Retracement
    print(f"Fib Signal: {fib_decision}-{fib_explanation}")

    # Overall Decision
    print(f"Overall Decision: {overall_decision}")




