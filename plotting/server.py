#!/usr/bin/env python3
#
# vim: set tabstop=4 noexpandtab:
#
# Copyright (c) 2018 David Jander
#

import asyncio
import sys
import os
import functools
from aiohttp import web

class HTTPServer:
	def __init__(self, port=8080):
		self.app = web.Application()
		pwd = os.path.normpath(os.path.dirname(__file__))
		self.app.router.add_static('/html', os.path.join(pwd, 'html'))
		self.app.router.add_get('/', lambda r: web.HTTPFound('/html/index.html'))
		self.loop = asyncio.get_event_loop()
		self.loop.create_task(self.init_from_loop(port))

	async def init_from_loop(self, port):
		await self.loop.create_server(self.app.make_handler(), '0.0.0.0', port)

	def register_websocket(self, path, handler):
		corohandler = asyncio.coroutine(functools.partial(self.websocket_proxy, handler, path))
		self.app.router.add_route('GET', path, corohandler)

	async def websocket_proxy(self, handler, path, request):
		websocket = web.WebSocketResponse()
		ready = websocket.can_prepare(request)
		if not ready.ok:
			return self.default_root_response()
		await websocket.prepare(request)
		await handler(websocket, path)
		return websocket

if __name__ == "__main__":
	s = HTTPServer()
	loop = asyncio.get_event_loop()
	loop.run_forever()
