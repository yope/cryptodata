#
# vim: set tabstop=4 noexpandtab:
#
# Copyright (c) 2018 David Jander
#

from .base import BaseStrategy, StopLoss

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
			if not self.funds_ok():
				break

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
			if not self.funds_ok():
				break


