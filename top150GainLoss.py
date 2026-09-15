"""Show the top 50 gainers and losers from a liquid Indian share universe."""

import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk

import pandas as pd
import yfinance as yf


SYMBOLS = """ADANIENT ADANIPORTS APOLLOHOSP ASIANPAINT AXISBANK BAJAJ-AUTO
BAJFINANCE BAJAJFINSV BEL BHARTIARTL BPCL BRITANNIA CIPLA COALINDIA
DRREDDY EICHERMOT ETERNAL GRASIM HCLTECH HDFCBANK HDFCLIFE HEROMOTOCO
HINDALCO HINDUNILVR ICICIBANK INDUSINDBK INFY IOC ITC JIOFIN JSWSTEEL
KOTAKBANK LT M&M MARUTI MAXHEALTH NESTLEIND NTPC ONGC POWERGRID RELIANCE
SBILIFE SBIN SHRIRAMFIN SUNPHARMA TATACONSUM TATAMOTORS TATASTEEL TCS
TECHM TITAN TRENT ULTRACEMCO WIPRO""".split()


def fetch_prices():
	tickers = [f"{symbol}.NS" for symbol in SYMBOLS]
	data = yf.download(tickers, period="5d", interval="1d", auto_adjust=False,
					   progress=False, threads=True)
	close = data["Close"]
	if isinstance(close, pd.Series):
		close = close.to_frame()
	if len(close) < 2:
		raise RuntimeError("Not enough market data returned.")
	latest, previous = close.iloc[-1], close.iloc[-2]
	result = pd.DataFrame({
		"Share": [name.replace(".NS", "") for name in latest.index],
		"Price": latest.values,
		"Change": ((latest.values - previous.values) / previous.values) * 100,
	}).dropna()
	return result.sort_values("Change", ascending=False)


class MarketPage:
	def __init__(self, window):
		self.window = window
		window.title("Indian Market: Top 50 Gainers and Losers")
		window.geometry("700x700")

		menu = tk.Menu(window)
		page_menu = tk.Menu(menu, tearoff=False)
		page_menu.add_command(label="Refresh market data", command=self.refresh)
		page_menu.add_command(label="Flip to Test2.py", command=self.open_test2)
		page_menu.add_separator()
		page_menu.add_command(label="Exit", command=window.destroy)
		menu.add_cascade(label="Pages", menu=page_menu)
		window.config(menu=menu)

		self.status = ttk.Label(window, text="Loading market data...")
		self.status.pack(pady=8)
		self.table = ttk.Treeview(window, columns=("share", "price", "change"),
								  show="headings")
		self.table.tag_configure("gain", foreground="#166534")
		self.table.tag_configure("loss", foreground="#b91c1c")
		for column, title in (("share", "Share"), ("price", "Price (₹)"),
							  ("change", "Change (%)")):
			self.table.heading(column, text=title)
			self.table.column(column, width=210, anchor="center")
		self.table.pack(fill="both", expand=True, padx=12, pady=8)
		self.refresh()

	def refresh(self):
		try:
			prices = fetch_prices()
			rows = pd.concat((prices.head(50), prices.tail(50)))
			for item in self.table.get_children():
				self.table.delete(item)
			for _, row in rows.iterrows():
				self.table.insert("", "end", values=(row.Share, f"{row.Price:.2f}",
															   f"{row.Change:+.2f}%"),
															 tags=("gain" if row.Change >= 0 else "loss",))
			self.status.config(text="Top 50 gainers, then top 50 losers | Yahoo Finance")
		except Exception as error:
			self.status.config(text="Could not load market data")
			messagebox.showerror("Data error", str(error))

	@staticmethod
	def open_test2():
		path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Test2.py")
		if not os.path.exists(path):
			messagebox.showerror("Navigation error", "Test2.py was not found.")
			return
		subprocess.Popen([sys.executable, path])


if __name__ == "__main__":
	root = tk.Tk()
	MarketPage(root)
	root.mainloop()
