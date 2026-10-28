
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Signal Lab", layout="wide")
st.title("📈 Quotex Signal Lab")
st.warning("Demo research only — no guaranteed profit.")

market = st.selectbox("Market", ["Forex", "OTC"])
uploaded = st.file_uploader("Upload 1-minute candle CSV", type=["csv"])

st.write("CSV columns required: time, open, high, low, close")

if uploaded:
    df = pd.read_csv(uploaded)
    df.columns = [c.strip().lower() for c in df.columns]

    required = ["open", "high", "low", "close"]
    if not all(c in df.columns for c in required):
        st.error("CSV must contain open, high, low, close columns.")
    elif len(df) < 30:
        st.warning("Upload at least 30 candles.")
    else:
        close = pd.to_numeric(df["close"], errors="coerce")
        df["EMA9"] = close.ewm(span=9, adjust=False).mean()
        df["EMA21"] = close.ewm(span=21, adjust=False).mean()

        delta = close.diff()
        gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
        rs = gain / loss.replace(0, np.nan)
        df["RSI"] = 100 - 100 / (1 + rs)

        last = df.iloc[-1]
        if last["EMA9"] > last["EMA21"] and last["RSI"] >= 50:
            signal = "CALL"
        elif last["EMA9"] < last["EMA21"] and last["RSI"] <= 50:
            signal = "PUT"
        else:
            signal = "WAIT"

        st.subheader(f"Signal: {signal}")
        st.write(f"Market: {market}")
        st.write(f"RSI: {last['RSI']:.2f}")
        st.dataframe(df.tail(20), use_container_width=True)
        st.caption("Historical indicator only; not a guaranteed or live signal.")
      
