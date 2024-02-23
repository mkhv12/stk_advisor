import yfinance as yf
import yahooquery as yq
import pandas as pd
import openpyxl
import ta
import feedparser
from analyze_portf import *


def get_hourly_data(symbol, start_date, end_date):
    # Download hourly data
    hourly_data = yf.download(symbol, start=start_date, end=end_date, interval='1h')

    # Extract the Share information using the Ticker() Function
    share_info = yq.Ticker(symbol).summary_detail[symbol]

    # Extracting the MarketPrice from the data
    today_open_price = share_info.get('open')
    today_close_price = share_info.get('previousClose')
    today_volume = share_info.get('volume')
    today_high = share_info.get('dayHigh')
    today_low = share_info.get('dayLow')

    # Create a DataFrame with today's market price and financial indicators
    today_data = pd.DataFrame(index=[datetime.now()], columns=['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])
    today_data['Open'] = today_open_price
    today_data['Close'] = today_close_price
    today_data['Adj Close'] = today_close_price
    today_data['Volume'] = today_volume
    today_data['High'] = today_high
    today_data['Low'] = today_low

    # Concatenate today's data with hourly_data
    combined_data = pd.concat([hourly_data, today_data])

    hourly_data = calculate_vwap(combined_data)
    
    return combined_data

def fetch_news_rss_by_sector(rss_url, sector_keywords):
    feed = feedparser.parse(rss_url)
    sector_news = [entry for entry in feed.entries if any(keyword.lower() in entry.title.lower() or keyword.lower() in entry.summary.lower() for keyword in sector_keywords)]

    return sector_news

portfolio_data = pd.read_excel('portfolio.xlsx')

def main():
    # Step 1: Get Historical Data
    three_month_ago = datetime.now() - timedelta(days=92)  # 3 months before
    start_date = three_month_ago.strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")

    # Loop through each row in the portfolio data
    for index, row in portfolio_data.iterrows():
        print("\n")
        symbol = row['Symbol']
        stock_sector_keywords = row['Stock_Sector'].split(',')  # Assuming Stock_Sector contains comma-separated keywords

        # Get historical data for the symbol
        historical_data = get_hourly_data(symbol, start_date, end_date)

        # Analyze trends and Fibonacci retracement
        analyzed_data = analyze_trends(historical_data)

        # Fetch news based on stock sector keywords
        rss_url = ('https://feeds.a.dj.com/rss/RSSMarketsMain.xml')
        news_articles_sector = fetch_news_rss_by_sector(rss_url, stock_sector_keywords)

        # Analyze news sentiment
        news_sentiments = analyze_sentiment(news_articles_sector)

        # Analyze portfolio using portfolio data, analyzed data, news sentiment, and forecast data
        analyze_portfolio(symbol, analyzed_data, news_sentiments)

        # Determine the overall trend
        overall_trend = determine_trend(analyzed_data)
        print(f"\nOverall Trend: {overall_trend}")

if __name__ == "__main__":
    main()
