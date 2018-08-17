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
		self.textabove = None
		self.textbelow = None

	def __repr__(self):
		ret = "<Candle {} secs from {}, open:{}, close:{}, low:{}, high:{}".format(self.length, self.opents, self.open, self.close, self.low, self.high)
		if self.textabove is not None:
			ret += ", above:{}".format(self.textabove)
		if self.textbelow is not None:
			ret += ", below:{}".format(self.textbelow)
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
			self.textabove = text
		else:
			self.textbelow = text

class BaseStrategy:
	def __init__(self, candles, pyramiding=1):
		self.candles = candles
		self.capital = 1000
		self.position = 0
		self.pfrac = 0.2
		self.pyramiding = pyramiding
		self.longshort = 0

	def go_long(self, c):
		if self.longshort >= self.pyramiding:
			return
		x = self.pfrac * self.capital
		self.capital -= x
		self.position += x / c.hl2()
		c.add_annotation("LONG")
		self.longshort += 1

	def go_short(self, c):
		if self.longshort <= -self.pyramiding:
			return
		x = self.pfrac * self.capital
		self.capital += x
		self.position -= x / c.hl2()
		c.add_annotation("SHORT", above=True)
		self.longshort -= 1

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
	cd = Coindata("BTC", "USD", "1D")
	candles = cd.get_candles(100)
	s = OutsideBarStrategy(candles)
	s.run()
	for c in candles:
		print(repr(c))
	print("Strategy performance:")
	print("position at end: {}".format(s.position))
	print("capital at end:  {}".format(s.capital))
	print("Closing all positions: {}".format(s.capital + s.position * candles[-1].close))
