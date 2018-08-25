#
# vim: set tabstop=4 noexpandtab:
#
# Copyright (c) 2018 David Jander
#

import requests
from candletools.candle import Candle

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
		if len(candles) < n:
			candles = self.get_candles(n - len(candles), endts=data[0]["time"]) + candles
		return candles
