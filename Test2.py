from datetime import datetime

import pandas as pd
import streamlit as st
import yfinance as yf


st.set_page_config(
	page_title="India Market Pulse",
	page_icon="IN",
	layout="wide",
)


NSE_WATCHLIST = {
	"Reliance Industries": "RELIANCE.NS",
	"Tata Consultancy Services": "TCS.NS",
	"HDFC Bank": "HDFCBANK.NS",
	"Infosys": "INFY.NS",
	"ICICI Bank": "ICICIBANK.NS",
	"Bharti Airtel": "BHARTIARTL.NS",
	"State Bank of India": "SBIN.NS",
	"Larsen & Toubro": "LT.NS",
	"ITC": "ITC.NS",
	"Axis Bank": "AXISBANK.NS",
}


@st.cache_data(ttl=300, show_spinner=False)
def load_market_data() -> tuple[pd.DataFrame, datetime]:
	"""Fetch the latest available quote for the NSE watchlist."""
	symbols = list(NSE_WATCHLIST.values())
	prices = yf.download(
		tickers=symbols,
		period="5d",
		interval="1d",
		auto_adjust=False,
		progress=False,
		threads=True,
	)

	if prices.empty:
		raise ValueError("No market data was returned. Please try again later.")

	close_prices = prices["Close"]
	if isinstance(close_prices, pd.Series):
		close_prices = close_prices.to_frame(name=symbols[0])

	rows = []
	for company, symbol in NSE_WATCHLIST.items():
		history = close_prices[symbol].dropna() if symbol in close_prices else pd.Series(dtype=float)
		if history.empty:
			continue

		current_price = float(history.iloc[-1])
		previous_price = float(history.iloc[-2]) if len(history) > 1 else current_price
		change = current_price - previous_price
		rows.append(
			{
				"Company": company,
				"Ticker": symbol.removesuffix(".NS"),
				"Price (INR)": current_price,
				"Change (INR)": change,
				"Change (%)": (change / previous_price * 100) if previous_price else 0.0,
			}
		)

	data = pd.DataFrame(rows).sort_values("Price (INR)", ascending=False).reset_index(drop=True)
	return data, datetime.now()


def format_change(value: float) -> str:
	return f"{'+' if value >= 0 else ''}{value:.2f}%"


st.title("India Market Pulse")
st.caption("Top 10 NSE shares by latest available share price")

refresh_col, status_col = st.columns([1, 5])
with refresh_col:
	if st.button("Refresh data", type="primary", use_container_width=True):
		load_market_data.clear()
		st.rerun()

try:
	market_data, updated_at = load_market_data()
except Exception as error:
	st.error(f"Unable to load market data: {error}")
	st.info("Check your internet connection and try refreshing.")
	st.stop()

with status_col:
	st.caption(f"Last updated: {updated_at.strftime('%d %b %Y, %I:%M %p')} (local time)")

if market_data.empty:
	st.warning("No quote data is available right now.")
	st.stop()

top_col, gain_col, loss_col = st.columns(3)
top_col.metric("Highest price", f"INR {market_data.iloc[0]['Price (INR)']:,.2f}", market_data.iloc[0]["Ticker"])
gainers = market_data[market_data["Change (%)"] > 0]
losers = market_data[market_data["Change (%)"] < 0]
gain_col.metric("Gainers", len(gainers))
loss_col.metric("Losers", len(losers))

st.subheader("Top 10 share prices")
display_data = market_data.copy()
display_data["Price (INR)"] = display_data["Price (INR)"].map(lambda value: f"INR {value:,.2f}")
display_data["Change (INR)"] = display_data["Change (INR)"].map(lambda value: f"{'+' if value >= 0 else ''}INR {value:,.2f}")
display_data["Change (%)"] = display_data["Change (%)"].map(format_change)
st.dataframe(display_data, hide_index=True, use_container_width=True)

st.subheader("Price comparison")
chart_data = market_data.set_index("Ticker")["Price (INR)"].sort_values(ascending=True)
st.bar_chart(chart_data, horizontal=True, color="#0f766e")

st.caption("Data source: Yahoo Finance via yfinance. Quotes may be delayed and are for information only.")
