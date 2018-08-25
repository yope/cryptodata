#
# vim: set tabstop=4 noexpandtab:
#
# Copyright (c) 2018 David Jander
#

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
			print("Stopped out {} at {}, candle low {}".format(self.typ, self.level, c.low))
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
		# First close any opposite positions...
		if typ == "SHORT" and self.position > 0:
			self.capital += self.position * price
			self.position = 0
		elif typ == "LONG" and self.position < 0:
			self.capital += self.position * price
			self.position = 0
		if amount is None:
			x = self.pfrac * self.capital
		else:
			x = amount
		if typ == "SHORT":
			self.capital += x
			self.position -= x / price
		elif typ == "LONG":
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
			above = (typ=="SHORT")
			typ = "{}({})".format(typ, x)
			c.add_annotation(typ, above=above)

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
		self.add_trade(None, d, 0, stop.level)
		self.stoploss = None

	def funds_ok(self):
		if self.capital <= 0.0:
			print("Liquidated!!!!!")
			return False
		return True

	def run(self):
		pass
