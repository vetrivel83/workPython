from datetime import datetime

import pandas as pd
import streamlit as st
import yfinance as yf


SYMBOLS = """ADANIENT ADANIPORTS APOLLOHOSP ASIANPAINT AXISBANK BAJAJ-AUTO
BAJFINANCE BAJAJFINSV BEL BHARTIARTL BPCL BRITANNIA CIPLA COALINDIA
DRREDDY EICHERMOT ETERNAL GRASIM HCLTECH HDFCBANK HDFCLIFE HEROMOTOCO
HINDALCO HINDUNILVR ICICIBANK INDUSINDBK INFY IOC ITC JIOFIN JSWSTEEL
KOTAKBANK LT M&M MARUTI MAXHEALTH NESTLEIND NTPC ONGC POWERGRID RELIANCE
SBILIFE SBIN SHRIRAMFIN SUNPHARMA TATACONSUM TATAMOTORS TATASTEEL TCS
TECHM TITAN TRENT ULTRACEMCO WIPRO""".split()


def fetch_prices() -> pd.DataFrame:
	tickers = [f"{symbol}.NS" for symbol in SYMBOLS]
	data = yf.download(
		tickers,
		period="5d",
		interval="1d",
		auto_adjust=False,
		progress=False,
		threads=True,
	)
	close = data["Close"]
	if isinstance(close, pd.Series):
		close = close.to_frame()
	if len(close) < 2:
		raise RuntimeError("Not enough market data returned.")
	latest, previous = close.iloc[-1], close.iloc[-2]
	result = pd.DataFrame(
		{
			"Company / Share": [name.replace(".NS", "") for name in latest.index],
			"NSE Ticker": [name.replace(".NS", "") for name in latest.index],
			"Exchange": "NSE",
			"Current Price (INR)": latest.values,
			"Previous Close (INR)": previous.values,
			"Change (INR)": latest.values - previous.values,
			"Change (%)": ((latest.values - previous.values) / previous.values) * 100,
		}
	).dropna()
	return result.sort_values("Change (%)", ascending=False).reset_index(drop=True)


def fetch_52_week_low_prices() -> pd.DataFrame:
	tickers = [f"{symbol}.NS" for symbol in SYMBOLS]
	data = yf.download(
		tickers,
		period="1y",
		interval="1d",
		auto_adjust=False,
		progress=False,
		threads=True,
	)
	if data.empty:
		raise RuntimeError("No 52-week market data returned.")

	close = data["Close"]
	if isinstance(close, pd.Series):
		close = close.to_frame()
	current = close.iloc[-1]
	week_low = close.min()
	result = pd.DataFrame(
		{
			"Company / Share": [name.replace(".NS", "") for name in current.index],
			"NSE Ticker": [name.replace(".NS", "") for name in current.index],
			"Exchange": "NSE",
			"Current Price (INR)": current.values,
			"52 Week Low (INR)": week_low.values,
		}
	).dropna()
	result["Distance from Low (INR)"] = (
		result["Current Price (INR)"] - result["52 Week Low (INR)"]
	)
	result["Distance from Low (%)"] = (
		result["Distance from Low (INR)"] / result["52 Week Low (INR)"] * 100
	)
	return result.sort_values("Distance from Low (%)").head(50).reset_index(drop=True)


st.set_page_config(
	page_title="India Market Pulse",
	page_icon="IN",
	layout="wide",
)


def style_gain_loss(row: pd.Series) -> list[str]:
	if row["Category"] == "Gainer":
		return ["color: #166534; background-color: #dcfce7"] * len(row)
	return ["color: #b91c1c; background-color: #fee2e2"] * len(row)


menu_page = st.sidebar.selectbox(
	"Menu",
	("India Market Pulse", "Top 150 gain/loss", "Top 50 52-week low"),
)

if menu_page == "Top 150 gain/loss":
	st.title("Top 150 Gainers and Losers")
	st.caption("Gainers and losers from the available NSE share universe")
	try:
		with st.spinner("Loading market data..."):
			prices = fetch_prices()
		gainer_count = min(50, max(1, len(prices) // 2))
		gainers = prices.head(gainer_count).copy()
		gainers["Category"] = "Gainer"
		losers = prices.tail(len(prices) - gainer_count).sort_values("Change (%)", ascending=True).copy()
		losers["Category"] = "Loser"
		display_prices = pd.concat(
			(gainers, losers),
			ignore_index=True,
		)
		display_prices.insert(0, "Rank", range(1, len(display_prices) + 1))
		display_prices["Updated"] = datetime.now().strftime("%d %b %Y, %I:%M %p")
		st.dataframe(
			display_prices.style
			.apply(style_gain_loss, axis=1)
			.format(
				{
					"Current Price (INR)": "{:.2f}",
					"Previous Close (INR)": "{:.2f}",
					"Change (INR)": "{:+.2f}",
					"Change (%)": "{:+.2f}%",
				}
			),
			hide_index=True,
			use_container_width=True,
		)
	except Exception as error:
		st.error(f"Unable to load top 150 data: {error}")
	st.stop()


if menu_page == "Top 50 52-week low":
	st.title("Top 50 Shares Near 52-Week Low")
	st.caption("NSE shares currently closest to their lowest price over the last year")
	try:
		with st.spinner("Loading 52-week low data..."):
			low_prices = fetch_52_week_low_prices()
		low_prices.insert(0, "Rank", range(1, len(low_prices) + 1))
		low_prices["Updated"] = datetime.now().strftime("%d %b %Y, %I:%M %p")
		st.dataframe(
			low_prices.style.format(
				{
					"Current Price (INR)": "{:.2f}",
					"52 Week Low (INR)": "{:.2f}",
					"Distance from Low (INR)": "{:.2f}",
					"Distance from Low (%)": "{:.2f}%",
				}
			),
			hide_index=True,
			use_container_width=True,
		)
	except Exception as error:
		st.error(f"Unable to load 52-week low data: {error}")
	st.stop()


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
