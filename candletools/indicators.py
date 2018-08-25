#
# vim: set tabstop=4 noexpandtab:
#
# Copyright (c) 2018 David Jander
#

from collections import deque

class Sma:
	"""Overly simplistic and braindead simple moving average implementation."""
	def __init__(self, n):
		self.length = n
		self.deq = deque(maxlen=n)

	def consume_candle(self, c):
		self.deq.append(c.hl2())

	def get_value(self):
		if len(self.deq) < self.length:
			return None
		return sum(self.deq) / self.length

class Ema(Sma):
	"""Exponential moving average. Equally simplistic and not at all efficient."""
	def get_value(self):
		if len(self.deq) < self.length:
			return None
		c = 2.0 / (self.length + 1)
		cema = self.deq[0]
		for v in self.deq:
			cema = (c * v) + ((1 - c) * cema)
		return cema
