//
// vim: set tabstop=4 noexpandtab shiftwidth=4:
//


var WS = (function() {
"use strict";

class WSock {
	constructor(cmdhandler) {
		this.cmdhandler = cmdhandler;
		this.ws = new WebSocket("ws://"+window.location.host+"/pricedata");
		this.ws.onopen = () => {
			this.on_open();
		};
		this.ws.onclose = () => {
			this.on_close();
		};
		this.ws.onmessage = (msg) => {
			this.on_message(msg);
		};
		this.ws.onerror = () => {
			this.on_error();
		};
	}

	on_open() {
		console.log("WS connected");
		this.send_command("get_chart");
		this.send_command("get_candles");
	}

	on_close() {
		console.log("WS closed");
	}

	on_error() {
		this.on_close();
	}

	on_message(msg) {
		console.log("WS message:", msg.data);
		let obj = JSON.parse(msg.data);
		this.cmdhandler.handle_object(obj);
	}

	send_object(obj) {
		this.ws.send(JSON.stringify(obj));
	}

	send_command(command) {
		this.send_object({
			command
		});
	}
}

return {
	WSock
};

})();
