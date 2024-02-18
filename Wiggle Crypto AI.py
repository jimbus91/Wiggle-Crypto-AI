import pytz
import datetime
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import robin_stocks.robinhood as r
import matplotlib.ticker as mticker
from mplfinance.original_flavor import candlestick_ohlc

plt.style.use('dark_background')

def wiggle_indicator(data, window=20, buy_threshold=0.5, sell_threshold=-0.5):
    data = data.copy()
    data['ma'] = data['Close'].rolling(window=window).mean()
    data['wiggle'] = (data['Close'] - data['ma']) / data['Close'].rolling(window=window).std()
    data['signal'] = np.where(data['wiggle'] > buy_threshold, 1, 
                     np.where(data['wiggle'] < sell_threshold, -1, 0))
    return data

# Log in to Robinhood
r.login(username='email', password='password', expiresIn=86400, by_sms=True)

# Get account information
account_info = r.account.load_phoenix_account(info=None)

# Get your portfolio's total value:
buying_power = account_info['account_buying_power']['amount']
print(f"Your buying power is: ${buying_power}")

while True:
    crypto = input("Enter the crypto ticker symbol (or 'exit' to quit): ").upper()
    if crypto.lower() == 'exit':
        break
    ticker = crypto + "-USD"

    try:
        data = yf.download(ticker, interval="1m")
        if data.empty:
            raise ValueError("Empty DataFrame")
    except Exception as e:
        continue

    local_timezone = pytz.timezone('Etc/GMT+7')
    current_time = datetime.datetime.now(local_timezone)
    start_time = current_time - datetime.timedelta(days=1)
    
    last_day_data = data.loc[(data.index >= start_time)]
    
    wiggle_data = wiggle_indicator(last_day_data, window=5, buy_threshold=0.9, sell_threshold=-0.9)
    wiggle_data.reset_index(inplace=True)
    wiggle_data['date'] = wiggle_data['Datetime'].apply(mdates.date2num)
    
    fig, ax = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    candlestick_ohlc(ax[0], wiggle_data[['date', 'Open', 'High', 'Low', 'Close']].values, width=0.0005, colorup='green', colordown='red')
    ax[0].yaxis.set_major_formatter(mticker.FormatStrFormatter('%d'))
    ax[0].set_title(f'{crypto} Candlestick Plot')
    ax[0].set_ylabel('Price')
    ax[0].xaxis_date()
    ax[0].xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M', tz=local_timezone))
    
    wiggle_data_no_yellow = wiggle_data[wiggle_data['signal'] != 0]
    ax[1].scatter(wiggle_data_no_yellow['date'], wiggle_data_no_yellow['wiggle'], c=wiggle_data_no_yellow['signal'], cmap='RdYlGn', marker='o')
    ax[1].xaxis_date()
    ax[1].xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M', tz=local_timezone))
    ax[1].set_ylabel('Wiggle')
    ax[1].set_title(f'{crypto} Wiggle Indicator')
    
    ax[0].set_xlim(start_time, current_time)
    ax[1].set_xlim(start_time, current_time)

    plt.setp(ax[0].get_xticklabels(), rotation=45, ha='right')
    plt.setp(ax[1].get_xticklabels(), rotation=45, ha='right')
    
    # plt.show()    # Uncomment this plt.show() if you want to disable automatic trading

    # Optional Trading Section (Commented out by default)
    # if 1 in wiggle_data['signal'].values:
    #      r.orders.order_buy_crypto_by_price(ticker, 1)
    #      print(f'Placed an order to buy $1 worth of {ticker}')
    # elif -1 in wiggle_data['signal'].values:
    #      r.orders.order_sell_crypto_by_price(ticker, 1)
    #      print(f'Placed an order to sell $1 worth of {ticker}')

    plt.show()  # This ensures the chart is always shown regardless of the trading option

    # r.logout()   # Logout of Robinhood account
