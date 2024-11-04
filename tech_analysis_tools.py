from datetime import datetime, timedelta
import pandas as pd
import numpy as np

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

def calculate_macd(data, fast_length=8, slow_length=21, signal_length=5):
    ema_fast = calculate_ema(data, fast_length)
    ema_slow = calculate_ema(data, slow_length)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_length, adjust=False).mean()
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

def calculate_parabolic_sar(data, step=0.02, max_step=0.2):
    """
    Calculate Parabolic SAR for the given data.
    """
    high = data['High']
    low = data['Low']
    close = data['Close']
    
    # Initialize variables
    af = step
    uptrend = True
    ep = low.iloc[0]  # Extreme point
    sar = high.iloc[0]  # SAR value
    sar_values = [sar]
    
    for i in range(1, len(close)):
        if uptrend:
            sar = sar + af * (ep - sar)
            if close.iloc[i] < sar:
                uptrend = False
                sar = ep
                af = step
                ep = low.iloc[i]
        else:
            sar = sar - af * (sar - ep)
            if close.iloc[i] > sar:
                uptrend = True
                sar = ep
                af = step
                ep = high.iloc[i]
        
        if uptrend:
            if high.iloc[i] > ep:
                ep = high.iloc[i]
                af = min(af + step, max_step)
        else:
            if low.iloc[i] < ep:
                ep = low.iloc[i]
                af = min(af + step, max_step)
        
        sar_values.append(sar)
    
    data['Parabolic_SAR'] = sar_values
    return data

def analyze_parabolic_sar(data):
        # Calculate Parabolic SAR
    latest_sar = data['Parabolic_SAR'].iloc[-1]
    previous_sar = data['Parabolic_SAR'].iloc[-2]
    latest_close = data['Close'].iloc[-1]
    
    if latest_close > latest_sar and previous_sar >= data['Close'].iloc[-2]:
        return "Reversal to Uptrend (Buy Signal)"
    elif latest_close < latest_sar and previous_sar <= data['Close'].iloc[-2]:
        return "Reversal to Downtrend (Sell Signal)"
    else:
        return "No Clear Reversal"


def calculate_bollinger_bands(data, window=20, num_std_dev=2):
    """
    Calculate Bollinger Bands for the given data.

    :param data: DataFrame containing the stock price data.
    :param window: The window size for the moving average (default is 20).
    :param num_std_dev: Number of standard deviations for the bands (default is 2).
    :return: Series for upper and lower Bollinger Bands.
    """
    rolling_mean = data['Close'].rolling(window).mean()
    rolling_std = data['Close'].rolling(window).std()

    bollinger_upper = rolling_mean + (rolling_std * num_std_dev)
    bollinger_lower = rolling_mean - (rolling_std * num_std_dev)

    return bollinger_upper, bollinger_lower


def calculate_stochastic_oscillator(data, window=14, smooth_k=3, smooth_d=3):
    """
    Calculate Stochastic Oscillator for the given data.

    :param data: DataFrame containing the stock price data.
    :param window: The look-back period for %K (default is 14).
    :param smooth_k: The smoothing period for %K (default is 3).
    :param smooth_d: The smoothing period for %D (default is 3).
    :return: Series for %K and %D.
    """
    low_min = data['Low'].rolling(window=window).min()
    high_max = data['High'].rolling(window=window).max()

    stochastic_k = 100 * ((data['Close'] - low_min) / (high_max - low_min))
    stochastic_k = stochastic_k.rolling(window=smooth_k).mean()
    stochastic_d = stochastic_k.rolling(window=smooth_d).mean()

    return stochastic_k, stochastic_d


def calculate_tax_implications(purchase_date, purchase_price, current_price, quantity):
    """
    Calculate potential tax implications.
    """
    purchase_date = datetime.strptime(purchase_date, "%Y-%m-%d")
    holding_period = (datetime.now() - purchase_date).days
    gain_or_loss = (current_price - purchase_price) * quantity
    gain_or_loss_perc = (gain_or_loss / (purchase_price * quantity)) * 100

    if holding_period < 365:
        tax_rate = 0.30
        holding_type = "Short-term"
    else:
        tax_rate = 0.15
        holding_type = "Long-term"

    tax_implication = gain_or_loss * tax_rate
    return holding_type, gain_or_loss, tax_implication, gain_or_loss_perc


def is_hammer(data, index):
    body = abs(data['Close'].iloc[index] - data['Open'].iloc[index])
    lower_shadow = data['Open'].iloc[index] - data['Low'].iloc[index]
    upper_shadow = data['High'].iloc[index] - data['Close'].iloc[index]
    
    return (lower_shadow > 2 * body) and (upper_shadow <= body)

def is_shooting_star(data, index):
    body = abs(data['Close'].iloc[index] - data['Open'].iloc[index])
    upper_shadow = data['High'].iloc[index] - data['Close'].iloc[index]
    lower_shadow = data['Open'].iloc[index] - data['Low'].iloc[index]
    
    return (upper_shadow > 2 * body) and (lower_shadow <= body)

def is_engulfing(data, index):
    current_body = abs(data['Close'].iloc[index] - data['Open'].iloc[index])
    previous_body = abs(data['Close'].iloc[index - 1] - data['Open'].iloc[index - 1])
    
    return (data['Open'].iloc[index] < data['Close'].iloc[index] and
            data['Open'].iloc[index - 1] > data['Close'].iloc[index - 1] and
            data['Open'].iloc[index] < data['Close'].iloc[index - 1] and
            data['Close'].iloc[index] > data['Open'].iloc[index - 1])

def is_doji(data, index):
    body = abs(data['Close'].iloc[index] - data['Open'].iloc[index])
    return body <= (data['High'].iloc[index] - data['Low'].iloc[index]) * 0.1

def analyze_candlestick_patterns(data):
    signals = []
    for i in range(1, len(data)):
        if is_hammer(data, i):
            signals.append("Hammer (Buy Signal)")
        elif is_shooting_star(data, i):
            signals.append("Shooting Star (Sell Signal)")
        elif is_engulfing(data, i):
            if data['Open'].iloc[i] < data['Close'].iloc[i]:
                signals.append("Bullish Engulfing (Buy Signal)")
            else:
                signals.append("Bearish Engulfing (Sell Signal)")
        elif is_doji(data, i):
            if data['Close'].iloc[i] > data['Open'].iloc[i]:
                signals.append("Doji Bullish (Buy Signal)")
            else:
                signals.append("Doji Bearish (Sell Signal)")

    if signals:
        return signals[-1]  # Return only the most recent candlestick pattern signal
    return "No pattern found"  # Return a message when no pattern is found

def calculate_adx(data, window=30):
    high = data['High']
    low = data['Low']
    close = data['Close']

    plus_dm = high.diff()
    minus_dm = low.diff()

    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0

    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    true_range = tr1.combine(tr2, max).combine(tr3, max)

    atr = true_range.rolling(window=window).mean()

    plus_di = 100 * (plus_dm.rolling(window=window).mean() / atr)
    minus_di = 100 * (abs(minus_dm).rolling(window=window).mean() / atr)

    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
    adx = dx.rolling(window=window).mean()

    return adx

def analyze_adx(data, adx_threshold=25):
    adx = calculate_adx(data)
    latest_adx = adx.iloc[-1]

    if latest_adx >= adx_threshold:
        return f"Strong Trend (ADX: {latest_adx:.2f})"
    else:
        return f"Weak/No Trend (ADX: {latest_adx:.2f})"


def detect_rsi_divergence(data):
    rsi = calculate_rsi(data)
    price_highs = data['High'].rolling(window=3).apply(lambda x: x.iloc[1] if (x.iloc[1] > x.iloc[0] and x.iloc[1] > x.iloc[2]) else np.nan, raw=False)
    rsi_highs = rsi.rolling(window=3).apply(lambda x: x.iloc[1] if (x.iloc[1] > x.iloc[0] and x.iloc[1] > x.iloc[2]) else np.nan, raw=False)

    last_signal = "No Divergence"

    for i in range(2, len(rsi)):
        price_high = price_highs.iloc[i]
        rsi_high = rsi_highs.iloc[i]

        # Check if price_high and rsi_high are not NaN
        if pd.notna(price_high) and pd.notna(rsi_high):
            # Bearish divergence: Price makes a higher high, RSI makes a lower high
            if data['High'].iloc[i] > data['High'].iloc[i-2] and rsi.iloc[i] < rsi.iloc[i-2]:
                last_signal = "Bearish Divergence (Sell Signal)"
            # Bullish divergence: Price makes a lower low, RSI makes a higher low
            elif data['Low'].iloc[i] < data['Low'].iloc[i-2] and rsi.iloc[i] > rsi.iloc[i-2]:
                last_signal = "Bullish Divergence (Buy Signal)"
    
    # Return the last signal or "No Divergence"
    return last_signal


def detect_head_and_shoulders(data):
    """
    Detects Head and Shoulders (Bearish) or Inverse Head and Shoulders (Bullish) pattern.
    Returns a signal if pattern is found.
    """

    # Find local peaks and troughs (using rolling window approach)
    data['Peak'] = data['High'].rolling(window=3).apply(lambda x: x.iloc[1] if x.iloc[1] > x.iloc[0] and x.iloc[1] > x.iloc[2] else np.nan)
    data['Trough'] = data['Low'].rolling(window=3).apply(lambda x: x.iloc[1] if x.iloc[1] < x.iloc[0] and x.iloc[1] < x.iloc[2] else np.nan)

    # Collect the peaks and troughs for pattern detection
    peaks = data['Peak'].dropna()
    troughs = data['Trough'].dropna()

    if len(peaks) >= 3 and len(troughs) >= 3:
        # We assume peaks and troughs follow the pattern sequence
        left_shoulder_peak = peaks.iloc[-3]
        head_peak = peaks.iloc[-2]
        right_shoulder_peak = peaks.iloc[-1]

        left_shoulder_trough = troughs.iloc[-3]
        head_trough = troughs.iloc[-2]
        right_shoulder_trough = troughs.iloc[-1]

        # Head and Shoulders pattern detection (Bearish)
        if left_shoulder_peak < head_peak > right_shoulder_peak and left_shoulder_trough < head_trough < right_shoulder_trough:
            return "Head/Shoulders (Sell Signal)"

        # Inverse Head and Shoulders pattern detection (Bullish)
        elif left_shoulder_peak > head_peak < right_shoulder_peak and left_shoulder_trough > head_trough < right_shoulder_trough:
            return "Inverse Head/Shoulders (Buy Signal)"
    
    return "No Head/Shoulders"



def detect_double_top_bottom(data, lookback=5, tolerance=0.02):
    """
    Detects Double Top (Bearish) and Double Bottom (Bullish) patterns.

    :param data: DataFrame containing stock price data with 'High' and 'Low' columns.
    :param lookback: The number of periods to look back for the pattern.
    :param tolerance: The tolerance level for price similarity between peaks or troughs.
    :return: A string indicating the detected pattern, if any.
    """
    # Get local peaks
    peaks = data['High'].rolling(window=lookback).apply(
        lambda x: x.argmax() if not np.isnan(x).any() else np.nan, raw=True
    )
    troughs = data['Low'].rolling(window=lookback).apply(
        lambda x: x.argmin() if not np.isnan(x).any() else np.nan, raw=True
    )

    # Ensure peaks and troughs are aligned with indexes
    peaks = peaks.dropna().astype(int)  # Indices where peaks are found
    troughs = troughs.dropna().astype(int)  # Indices where troughs are found

    # Double Top Pattern
    if len(peaks) >= 2:
        peak1 = peaks.iloc[-2]
        peak2 = peaks.iloc[-1]
        price_diff = abs(data['High'].iloc[peak1] - data['High'].iloc[peak2])
        
        # Check if peaks are within the tolerance level
        if price_diff / data['High'].iloc[peak1] < tolerance:
            return "Double Top (Sell Signal)"

    # Double Bottom Pattern
    if len(troughs) >= 2:
        trough1 = troughs.iloc[-2]
        trough2 = troughs.iloc[-1]
        price_diff = abs(data['Low'].iloc[trough1] - data['Low'].iloc[trough2])
        
        # Check if troughs are within the tolerance level
        if price_diff / data['Low'].iloc[trough1] < tolerance:
            return "Double Bottom (Buy Signal)"
    
    return "No Double Top/Bottom Pattern"




def analyze_price_drop(data, drop_threshold=0.30):
    """
    Check if the current price is a certain percentage below the max high in the provided data.
    
    :param data: DataFrame containing the stock price data.
    :param drop_threshold: The percentage drop threshold.
    :return: A message indicating if the price has dropped by the threshold percentage or more.
    """
    # Get the maximum high from the provided data
    max_high = data['High'].max()
    
    # Get the current close price
    current_price = data['Close'].iloc[-1]
    
    # Calculate the percentage drop from the max high
    drop_percentage = (max_high - current_price) / max_high
    
    return f"Max high is ${max_high:.2f} difference of {drop_percentage * 100:.1f}%"

    # # Determine if the price drop is greater than or equal to the threshold
    # if drop_percentage >= drop_threshold:
    #     return f"Price is {drop_percentage * 100:.0f}% more than max high"
    # else:
    #     return f"Price is less than {drop_threshold * 100:.0f}% below the max high"


