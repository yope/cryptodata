#!/usr/bin/env python3
#
# vim: set tabstop=4 noexpandtab:
#
# Copyright (c) 2018 David Jander
#

import requests
import os
import sys

class Candle:
	def __init__(self, obj, secs):
		self.high = obj["high"]
		self.low = obj["low"]
		self.open = obj["open"]
		self.close = obj["close"]
		self.volumefrom = obj["volumefrom"]
		self.volumeto = obj["volumeto"]
		self.opents = obj["time"]
		self.length = secs
		self.textabove = []
		self.textbelow = []

	def __repr__(self):
		ret = "<Candle {} secs from {}, open:{}, close:{}, low:{}, high:{}".format(self.length, self.opents, self.open, self.close, self.low, self.high)
		if self.textabove:
			ret += ", above:{}".format(";".join(self.textabove))
		if self.textbelow is not None:
			ret += ", below:{}".format(";".join(self.textbelow))
		ret += ">"
		return ret

	def hlc3(self):
		return (self.high + self.low + self.close) / 3.0

	def hl2(self):
		return (self.high + self.low) / 2.0

	def ohlc4(self):
		return (self.high + self.low + self.open + self.close) / 4.0

	def tr(self):
		return (self.high - self.low) # FIXME: Need close of prev candle?

	def add_annotation(self, text, above=False):
		if above:
			self.textabove.append(text)
		else:
			self.textbelow.append(text)

	def plot(self, pmin, pmax):
		prange = pmax - pmin
		cpp = 120.0 / prange
		offl = int(cpp * (self.low - pmin)) + 10
		if self.textbelow:
			tb = ";".join(self.textbelow)
			offl -= len(tb)
			offl -= 4
			offs = " " * offl
			offs += tb + " -> "
		else:
			offs = " " * offl
		if self.close > self.open:
			color = "\x1b[32m"
			lwick = "-" * int(cpp * (self.open - self.low))
			body = "#" * int(cpp * (self.close - self.open))
			hwick = "-" * int(cpp * (self.high - self.close))
		else:
			color = "\x1b[31m"
			lwick = "-" * int(cpp * (self.close - self.low))
			body = "#" * int(cpp * (self.open - self.close))
			hwick = "-" * int(cpp * (self.high - self.open))
		if len(body) < 1:
			body = "|"
		if self.textabove:
			tabove = " <- " + ";".join(self.textabove)
		else:
			tabove = ""
		print(offs + color + lwick + body + hwick + "\x1b[0m" + tabove)

class StopLoss:
	def __init__(self, strategy, level, typ):
		self.typ = typ
		self.strategy = strategy
		self.level = level

	def test_candle(self, c):
		stop = False
		if self.typ == "LONG" and c.low < self.level:
			stop = True
		elif self.typ == "SHORT" and c.high > self.level:
			stop = True
		if stop:
			print("Stopped out {} at {}, level {}".format(self.typ, c.low, self.level))
			self.strategy.stop_out(self)

class BaseStrategy:
	def __init__(self, candles, pyramiding=1):
		self.candles = candles
		self.pmin = 999999999999
		self.pmax = 0
		for c in candles:
			if c.high > self.pmax:
				self.pmax = c.high
			if c.low < self.pmin:
				self.pmin = c.low
		self.startcapital = self.capital = 1000
		self.position = 0
		self.equity = self.capital
		self.trades = []
		self.pfrac = 0.5
		self.pyramiding = pyramiding
		self.longshort = 0
		self.winners = 0
		self.losers = 0
		self.total_win = 0
		self.total_loss = 0
		self.stoploss = None

	def add_trade(self, c, typ, amount=None, price=None):
		if price is None:
			price = c.close
		if amount is None:
			x = self.pfrac * self.capital
		else:
			x = amount
		if typ == "SHORT":
			if self.position > 0: # Close long position before going short
				x += self.position * price
			self.capital += x
			self.position -= x / price
		elif typ == "LONG":
			if self.position < 0: # Close short position before going long
				x -= self.position * price
			self.capital -= x
			self.position += x / price
		else:
			print("ERROR: Unknown trade type {!r}".format(typ))
			return
		eq = self.capital + self.position * price
		delta = eq - self.equity
		self.trades.append((typ, eq, delta))
		if delta > 0:
			self.winners += 1
			self.total_win += delta
		elif delta < 0:
			self.losers += 1
			self.total_loss += delta
		self.equity = eq
		if c is not None:
			c.add_annotation(typ, above=(typ=="SHORT"))

	def go_long(self, c, amount=None, price=None):
		if self.longshort >= self.pyramiding:
			return False
		self.add_trade(c, "LONG", amount=amount, price=price)
		self.longshort += 1
		return True

	def go_short(self, c, amount=None, price=None):
		if self.longshort <= -(self.pyramiding - 1):
			return False
		self.add_trade(c, "SHORT", amount=amount, price=price)
		self.longshort -= 1
		return True

	def stop_out(self, stop):
		d = "SHORT" if self.position > 0 else "LONG"
		self.add_trade(None, d, abs(self.position), stop.level)
		self.stoploss = None

	def run(self):
		pass

class OutsideBarStrategy(BaseStrategy):
	def run(self):
		for i in range(1, len(self.candles)):
			c = self.candles[i]
			c0 = self.candles[i-1]
			if (c.high > c0.high) and (c.low < c0.low):
				if c.close > c.open:
					self.go_long(c)
				elif c.close < c.open:
					self.go_short(c)

class PivotalReversalStrategy(BaseStrategy):
	def __init__(self, candles, pyramiding=1, leftbars=4, rightbars=2):
		super().__init__(candles, pyramiding)
		self.leftbars = leftbars
		self.rightbars = rightbars
		self.hprice = 100000000
		self.lprice = 0
		self.got_swl = False
		self.got_swh = False
		self.cph = None
		self.cpl = None

	def run(self):
		for i in range(self.leftbars + self.rightbars, len(self.candles)):
			c = self.candles[i]
			cp = self.candles[i - self.rightbars]
			print("Candle: {!r}".format(c))
			ldesc = 0
			rdesc = 0
			linc = 0
			rinc = 0
			if self.stoploss is not None:
				self.stoploss.test_candle(c)
			for j in range(self.leftbars):
				c0 = self.candles[i - j - self.rightbars - 1]
				if c0.high <= cp.high:
					linc += 1
				if c0.low >= cp.low:
					ldesc += 1
			for j in range(self.rightbars):
				c0 = self.candles[i - j]
				if c0.high <= cp.high:
					rdesc += 1
				if c0.low >= cp.low:
					rinc += 1
			if (linc == self.leftbars) and (rdesc == self.rightbars):
				self.got_swh = True
				self.cph = cp
				self.hprice = cp.high
				cp.add_annotation("SWH", above=True)
			if (ldesc == self.leftbars) and (rinc == self.rightbars):
				self.got_swl = True
				self.cpl = cp
				self.lprice = cp.low
				cp.add_annotation("SWL")
			if self.got_swl and c.high > self.hprice:
				if self.go_long(c, price=self.hprice):
					self.stoploss = StopLoss(self, self.lprice, "LONG")
					self.cpl.add_annotation("STOP")
					print("LONG at {} stop loss at {}".format(self.hprice, self.lprice))
					self.got_swl = False
			if self.got_swh and c.low < self.lprice:
				if self.go_short(c, price=self.lprice):
					self.stoploss = StopLoss(self, self.hprice, "SHORT")
					self.cph.add_annotation("STOP", above=True)
					print("SHORT at {} stop loss at {}".format(self.lprice, self.hprice))
					self.got_swh = False

class Coindata:
	def __init__(self, coin, fiat, tf):
		self.coin = coin
		self.fiat = fiat
		self.tf = tf
		self.baseurl = 'https://min-api.cryptocompare.com/data/'
		if tf.endswith("m"):
			self.secmul = 60
			self.apiunit = "minute"
			self.tfunits = int(tf[:-1])
		elif tf.endswith("h"):
			self.secmul = 3600
			self.apiunit = "hour"
			self.tfunits = int(tf[:-1])
		elif tf.endswith("D"):
			self.secmul = 3600 * 24
			self.apiunit = "day"
			self.tfunits = int(tf[:-1])
		elif tf.endswith("W"):
			self.secmul = 3600 * 24 * 7
			self.apiunit = "day"
			self.tfunits = int(tf[:-1]) * 7
		else:
			print("WARN: Timeframe unit not supported, assuming minutes")
			self.secmul = 60
			self.apiunit = "minute"
			self.tfunits = int(tf)

	def get_candles(self, n, endts=None):
		url = self.baseurl + "histo{}?fsym={}&tsym={}&limit={}".format(self.apiunit, self.coin, self.fiat, n)
		if endts is not None:
			url += "&toTs={}".format(endts)
		if self.tfunits > 1:
			url += "&aggregate={}".format(self.tfunits)
		r = requests.get(url).json()
		data = r["Data"]
		candles = [Candle(x, self.secmul * self.tfunits) for x in data]
		return candles

if __name__ == "__main__":
	cd = Coindata("BTC", "USD", "1h")
	candles = cd.get_candles(200)
	s = OutsideBarStrategy(candles)
	s.run()
	for c in candles:
		print(repr(c))
	print("Trades:")
	for i in range(len(s.trades)):
		t = s.trades[i]
		print("  Trade {:3d}: type: {:5s}, equity: {:5.2f}, delta: {:3.2f}".format(i, t[0], t[1], t[2]))
	print("Strategy performance:")
	print("  position at end: {}".format(s.position))
	print("  capital at end:  {}".format(s.capital))
	print("  Closing all positions: {:5.2f}".format(s.capital + s.position * candles[-1].close))
	print("  Number of losing trades: {}".format(s.losers))
	print("  Number of winning trades:{}".format(s.winners))
	print("  Total capital lost in losing trades:{:5.2f}".format(s.total_loss))
	print("  Total capital won in winning trades:{:5.2f}".format(s.total_win))
	print("  Total pnl:{:5.2f}".format(s.equity - s.startcapital))
