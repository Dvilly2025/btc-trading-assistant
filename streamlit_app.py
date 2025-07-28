# BTC Tactical Trading Assistant — Streamlit App Version

import ccxt
import pandas as pd
import ta
from datetime import datetime
import matplotlib.pyplot as plt
import streamlit as st

# === CONFIG ===
SYMBOL = "BTC/USDT"
TIMEFRAME = '2m'
LIMIT = 200

# === FETCH DATA ===
def fetch_data():
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=LIMIT)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

# === INDICATORS ===
def apply_indicators(df):
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    macd = ta.trend.MACD(df['close'])
    df['macd_hist'] = macd.macd_diff()
    df['vol_avg'] = df['volume'].rolling(10).mean()
    df['vol_spike'] = df['volume'] > df['vol_avg'] * 1.5
    return df

# === STRATEGY ===
def make_prediction(df):
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    rsi = latest['rsi']
    macd_up = latest['macd_hist'] > prev['macd_hist']
    vol_spike = latest['vol_spike']

    if rsi < 30 and macd_up and vol_spike:
        return 'UP', latest['timestamp']
    elif rsi > 70 and not macd_up and vol_spike:
        return 'DOWN', latest['timestamp']
    else:
        return None, latest['timestamp']

# === BACKTEST ===
def backtest_strategy(df):
    df = apply_indicators(df)
    entries = []
    for i in range(15, len(df) - 10):
        row, prev = df.iloc[i], df.iloc[i-1]
        rsi = row['rsi']
        macd_up = row['macd_hist'] > prev['macd_hist']
        vol_spike = row['vol_spike']

        if rsi < 30 and macd_up and vol_spike:
            entry = row['close']
            exit = df.iloc[i+10]['close']
            result = 'Win' if exit > entry else 'Loss'
            entries.append(result)

    win_rate = entries.count('Win') / len(entries) if entries else 0
    return len(entries), win_rate

# === STREAMLIT APP ===
st.set_page_config(page_title="BTC Trading Assistant", layout="wide")
st.title("🔮 BTC Tactical Trading Assistant")

# Fetch + prepare data
df = fetch_data()
df = apply_indicators(df)

# Plot
st.subheader("📈 BTC Price + Indicators")
fig, ax = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

ax[0].plot(df['timestamp'], df['close'], label='BTC Price', color='blue')
ax[0].legend()
ax[0].set_title("BTC Price")

ax[1].plot(df['timestamp'], df['rsi'], label='RSI", color='purple')
ax[1].axhline(70, color='red', linestyle='--')
ax[1].axhline(30, color='green', linestyle='--')
ax[1].legend()
ax[1].set_title("RSI")

ax[2].plot(df['timestamp'], df['macd_hist'], label='MACD Histogram', color='orange')
ax[2].axhline(0, color='gray', linestyle='--')
ax[2].legend()
ax[2].set_title("MACD Histogram")

plt.xticks(rotation=45)
st.pyplot(fig)

# Signal
signal, signal_time = make_prediction(df)
st.subheader("📡 Real-Time Prediction")
if signal:
    st.success(f"[{signal_time}] BTC is likely to go **{signal}** in next 20 minutes")
else:
    st.warning(f"[{signal_time}] No clear signal")

# Backtest results
st.subheader("📊 Backtest")
trades, win_rate = backtest_strategy(df)
st.write(f"Executed {trades} historical trades.")
st.write(f"Win Rate: {win_rate:.2%}")
