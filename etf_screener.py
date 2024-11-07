import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd

def get_etf_tickers():
    url = "https://finance.yahoo.com/markets/etfs/most-active/"  # Example URL (may need updating)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    tickers = []
    # Find the table containing ETF symbols
    table = soup.find("table")  # Find the first table on the page
    if table:
        for row in table.find_all("tr"):
            columns = row.find_all("td")
            if columns:
                # Assuming the first column in each row is the ticker symbol
                ticker = columns[0].text.strip()
                tickers.append(ticker)
    
    return tickers

def fetch_etf_data(tickers):
    etf_data = []
    for ticker in tickers:
        try:
            etf = yf.Ticker(ticker)
            info = etf.info
            etf_data.append({
                'Ticker': ticker,
                'NAV': info.get('navPrice'),
                'Price': info.get('regularMarketPrice'),
                'Sector': info.get('sector'),
                'Expense Ratio': info.get('expenseRatio'),
            })
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
    return etf_data

def filter_etfs(etf_data, min_nav=0, max_nav=float('inf'), sector=None, max_expense_ratio=0.5):
    return [
        etf for etf in etf_data 
        if etf['NAV'] and min_nav <= etf['NAV'] <= max_nav
        and (sector is None or etf['Sector'] == sector)
        and etf['Expense Ratio'] and etf['Expense Ratio'] <= max_expense_ratio
    ]

def main():
    # Fetch ETF tickers
    etf_tickers = get_etf_tickers()

    print(etf_tickers)
    # Fetch ETF data for tickers
    etf_data = fetch_etf_data(etf_tickers)

    # Filter the ETFs based on NAV and other criteria
    filtered_etfs = filter_etfs(etf_data, min_nav=50, max_nav=200, sector="Technology")

    # # Convert to DataFrame and save as CSV
    # df = pd.DataFrame(filtered_etfs)
    # print(df)
    # df.to_csv("filtered_etfs.csv", index=False)

if __name__ == "__main__":
    main()
