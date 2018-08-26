#!/usr/bin/env python3
#
# vim: set tabstop=4 noexpandtab:
#
# Copyright (c) 2018 David Jander
#

import os
import sys
import asyncio
from candletools.candle import Candle
from candletools.indicators import Sma, Ema
from strategies.base import StopLoss, BaseStrategy
from strategies.tradingview import OutsideBarStrategy, PivotalReversalStrategy
from datasource.cryptocompare import Coindata
from plotting.server import HTTPServer
from concurrent.futures import CancelledError

class SmaCrossStrategy(BaseStrategy):
	def __init__(self, candles, pyramiding=1, sma1=55, sma2=100):
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


class PlotWsHandler:
	def __init__(self, websock, pserver):
		print("New WS connection")
		self.pserver = pserver
		self.ws = websock

	async def coro_mainloop(self):
		while True:
			try:
				obj = await self.ws.receive_json()
			except CancelledError:
				break
			except (TypeError, ValueError):
				await self.ws.close()
				self.pserver.del_connection(self)
				return
			await self.on_message(obj)
		print("WS connection closed")
		await self.ws.close()
		self.pserver.del_connection(self)

	async def on_message(self, obj):
		print("Received WS message: {!r}".format(obj))
		await asyncio.sleep(0)
		if not "command" in obj:
			print("Unkknown object received: {!r}".format(obj))
			return
		cmd = obj["command"]
		if cmd == "get_candles":
			for c in self.pserver.candles:
				await self.ws.send_json({
					"class": "candle",
					"data": c.pack_data()
				})
		elif cmd == "get_chart":
			n = len(self.pserver.candles)
			cl = self.pserver.candles[-1].length
			dt = n * cl
			endtime = self.pserver.candles[-1].opents + cl
			begintime = endtime - dt - cl
			await self.ws.send_json({
				"class": "chart",
				"begintime": begintime,
				"endtime": endtime,
				"minprice": self.pserver.strategy.pmin,
				"maxprice": self.pserver.strategy.pmax
			})

class PlotServer:
	def __init__(self, candles, strategy):
		self.httpd = HTTPServer()
		self.loop = asyncio.get_event_loop()
		self.candles = candles
		self.strategy = strategy
		self.httpd.register_websocket("/pricedata", self.on_wsconnection)
		self.connections = []

	def run(self):
		self.loop.run_forever()

	async def on_wsconnection(self, websock, path):
		h = PlotWsHandler(websock, self)
		await h.coro_mainloop()

	def add_connection(self, client):
		self.connections.append(client)

	def del_connection(self, client):
		try:
			self.connections.remove(client)
		except ValueError:
			pass

	async def coro_queue(self, obj):
		for c in self.connections:
			await c.coro_queue(obj)

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

	s = PlotServer(candles, s)
	s.run()
