

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

