#!/usr/bin/env python3
#
# vim: set tabstop=4 noexpandtab:
#
# Copyright (c) 2018 David Jander
#

import os
import sys
from candletools.candle import Candle
from candletools.indicators import Sma, Ema
from strategies.base import StopLoss, BaseStrategy
from strategies.tradingview import OutsideBarStrategy, PivotalReversalStrategy
from datasource.cryptocompare import Coindata

class SmaCrossStrategy(BaseStrategy):
	def __init__(self, candles, pyramiding=1, sma1=21, sma2=55):
		super().__init__(candles, pyramiding)
		self.ma1 = Sma(sma1)
		self.ma2 = Sma(sma2)
		self.golden = False

	def run(self):
		for i in range(len(self.candles)):
			c = self.candles[i]
			self.ma1.consume_candle(c)
			self.ma2.consume_candle(c)
			s1 = self.ma1.get_value()
			s2 = self.ma2.get_value()
			if s1 is None or s2 is None:
				continue
			if s1 > s2 and not self.golden:
				self.golden = True
				self.go_long(c)
			elif s1 < s2 and self.golden:
				self.golden = False
				self.go_short(c)
			if not self.funds_ok():
				break

class MacdStrategy(SmaCrossStrategy):
	def __init__(self, candles, pyramiding=1, ema=12, sma=26):
		super().__init__(candles, pyramiding, sma1=ema, sma2=sma)
		self.ma1 = Ema(ema)
		self.golden = False

if __name__ == "__main__":
	args = sys.argv[1:]
	if len(args) < 4:
		print("Usage: ./backtest.py <token> <fiat> <tf> <n> [<strategy>]")
		print("\n  where <token> is the name of the asset (btc, eth, etc...),")
		print("        <fiat> is the fiat currency to trade against (usd, eur, etc...")
		print("        <tf> is the time-frame (1h, 12h, 1D, ...)")
		print("        <n> is the amount of candles to get from server")
		print("        <strategy> (optional, default: PivotalReversalStrategy)")
		print("                   any of: OutsideBarStrategy, PivotalReversalStrategy...")
		sys.exit(0)
	tok = args[0].upper()
	fiat = args[1].upper()
	tf = args[2]
	cd = Coindata(tok, fiat, tf)
	n = int(args[3])
	if len(args) > 4:
		sname = args[4]
		if not sname in globals():
			print("No strategy class found with name: {}".format(sname))
			sys.exit(1)
	else:
		sname = "PivotalReversalStrategy"
	candles = cd.get_candles(n)
	#s = OutsideBarStrategy(candles)
	s = globals()[sname](candles)
	s.run()
	for c in candles:
		c.plot(s.pmin, s.pmax)
	print("Trades:")
	for i in range(len(s.trades)):
		t = s.trades[i]
		print("  Trade {:3d}: type: {:5s}, equity: {:5.2f}, delta: {:3.2f}".format(i, t[0], t[1], t[2]))
	print("Strategy performance over {} candles of {}:".format(len(candles), cd.tf))
	print("  position at end: {}".format(s.position))
	print("  capital at end:  {}".format(s.capital))
	print("  Closing all positions: {:5.2f}".format(s.capital + s.position * candles[-1].close))
	print("  Number of losing trades: {}".format(s.losers))
	print("  Number of winning trades:{}".format(s.winners))
	print("  Total capital lost in losing trades:{:5.2f}".format(s.total_loss))
	print("  Total capital won in winning trades:{:5.2f}".format(s.total_win))
	print("  Total pnl:{:5.2f}".format(s.equity - s.startcapital))
