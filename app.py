
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Signal Lab", layout="wide")
st.title("Quotex Signal Lab")
st.warning("Research only. No guaranteed profit or live trading.")

market = st.selectbox("Market", ["Forex", "OTC"])
file = st.file_uploader("Upload 1-minute candle CSV", type=["csv"])

if file:
    df = pd.read_csv(file)
    df.columns = df.columns.str.strip().str.lower()

    if not all(c in df.columns for c in ["open", "high", "low", "close"]):
        st.error("CSV needs open, high, low, close columns.")
    elif len(df) < 30:
        st.error("Please upload at least 30 candles.")
    else:
        close = pd.to_numeric(df["close"], errors="coerce")
        df = df.loc[close.notna()].copy()
        close = pd.to_numeric(df["close"])

        df["ema9"] = close.ewm(span=9, adjust=False).mean()
        df["ema21"] = close.ewm(span=21, adjust=False).mean()

        delta = close.diff()
        gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
        rs = gain / loss.replace(0, np.nan)
        df["rsi"] = 100 - 100 / (1 + rs)

        df["signal"] = np.select(
            [
                (df["ema9"] > df["ema21"]) & (df["rsi"] >= 50),
                (df["ema9"] < df["ema21"]) & (df["rsi"] <= 50)
            ],
            ["CALL", "PUT"],
            default="WAIT"
        )

        df["next_close"] = close.shift(-1)
        df["outcome"] = "NOT TRADED"
        call = df["signal"] == "CALL"
        put = df["signal"] == "PUT"
        df.loc[call & (df["next_close"] > close), "outcome"] = "WIN"
        df.loc[call & (df["next_close"] < close), "outcome"] = "LOSS"
        df.loc[put & (df["next_close"] < close), "outcome"] = "WIN"
        df.loc[put & (df["next_close"] > close), "outcome"] = "LOSS"

        st.subheader("Latest signal")
        st.metric("Signal", df.iloc[-1]["signal"])
        st.metric("RSI", f'{df.iloc[-1]["rsi"]:.2f}')

        st.subheader("Historical backtest")
        tested = df.iloc[:-1]
        trades = tested[tested["signal"].isin(["CALL", "PUT"])]
        wins = int((trades["outcome"] == "WIN").sum())
        losses = int((trades["outcome"] == "LOSS").sum())
        total = wins + losses
        rate = wins / total * 100 if total else 0

        a, b, c = st.columns(3)
        a.metric("Evaluated signals", total)
        b.metric("Wins / Losses", f"{wins} / {losses}")
        c.metric("Win rate", f"{rate:.1f}%")

        st.caption(
            f"{market} | Illustrative next-candle comparison; "
            "not an exact Quotex settlement simulation."
        )
        st.dataframe(
            df[["close", "ema9", "ema21", "rsi", "signal", "outcome"]].tail(30),
            use_container_width=True
        )
        
