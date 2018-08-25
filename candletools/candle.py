#
# vim: set tabstop=4 noexpandtab:
#
# Copyright (c) 2018 David Jander
#

class Candle:
	"""Abstract price action candle class. Parses data from cryptocompare
	objects.
	FIXME: Make independent from cryptocompare data format."""
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
		"""Ascii art plotting of candle sticks."""
		# FIXME: Autodetect terminal window width. Needs min. 120 char wide lines.
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
