

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

