//
// vim: set tabstop=4 noexpandtab shiftwidth=4:
//


var CS = (function() {
"use strict";

const svgns="http://www.w3.org/2000/svg";

class BaseObject {
	constructor(chart) {
		this.chart = chart;
	}

	redraw() {
	}

	resize() {
	}
}

class Candle extends BaseObject {
	constructor(chart, data) {
		super(chart);
		this.data = data;
		this.create();
		this.chart.add_object(this);
	}

	_resize_wick(wick, p0, p1, x, w) {
		let wickw = Math.max(w * 0.05, 1);
		wick.setAttributeNS(null, "y1", this.chart.p2y(p0));
		wick.setAttributeNS(null, "y2", this.chart.p2y(p1));
		wick.setAttributeNS(null, "x1", x + w / 2);
		wick.setAttributeNS(null, "x2", x + w / 2);
		wick.setAttributeNS(null, "stroke-width", wickw);
	}

	_make_wick(color) {
		let wick = document.createElementNS(svgns, "line");
		wick.setAttributeNS(null, "stroke", color);
		return wick;
	}

	_create_text(text, color) {
		let t = document.createElementNS(svgns, "text");
		t.innerHTML = text;
		t.setAttributeNS(null, "fill", color);
		t.setAttributeNS(null, "stroke", null);
		t.setAttributeNS(null, "font-size", 10);
		return t;
	}

	create() {
		let svg = this.chart.svg;
		var color;
		if (this.data.close < this.data.open)
			color = "red";
		else
			color = "green";
		this.body = document.createElementNS(svgns, "rect");
		this.body.setAttributeNS(null, "fill", color);
		this.body.setAttributeNS(null, "stroke", color);
		svg.appendChild(this.body);
		this.lwick = this._make_wick(color);
		svg.appendChild(this.lwick);
		this.hwick = this._make_wick(color);
		svg.appendChild(this.hwick);
		this.t_below = [];
		this.t_above = [];
		for (let i = 0, il = this.data.textbelow.length; i < il; i++) {
			let t = this._create_text(this.data.textbelow[i], "blue");
			this.t_below.push(t);
			svg.appendChild(t);
		}
		for (let i = 0, il = this.data.textabove.length; i < il; i++) {
			let t = this._create_text(this.data.textabove[i], "blue");
			this.t_above.push(t);
			svg.appendChild(t);
		}
		this.resize();
	}

	resize() {
		let d = this.data;
		var price1, price2
		if (d.close < d.open) {
			price1 = d.close;
			price2 = d.open;
		} else {
			price1 = d.open;
			price2 = d.close;
		}
		let price0 = d.low;
		let price3 = d.high;
		let p0 = this.chart.tp2xy(d.opents, price2);
		let p1 = this.chart.tp2xy(d.opents + d.length, price1);
		let bh = p1[1] - p0[1];
		let bw = p1[0] - p0[0];
		let margin = bw * 0.2;
		this.body.setAttributeNS(null, "x", p0[0] + margin / 2);
		this.body.setAttributeNS(null, "y", p0[1]);
		this.body.setAttributeNS(null, "width", bw - margin);
		this.body.setAttributeNS(null, "height", bh);
		this._resize_wick(this.lwick, price0, price1, p0[0], bw);
		this._resize_wick(this.hwick, price2, price3, p0[0], bw);
		let ymin = this.chart.p2y(price0);
		let ymax = this.chart.p2y(price3);
		for (let i = 0, il = this.t_below.length; i < il; i++) {
			let t = this.t_below[i];
			t.setAttributeNS(null, "x", p0[0]);
			t.setAttributeNS(null, "y", ymin + 10 + i * 10);
		}
		for (let i = 0, il = this.t_above.length; i < il; i++) {
			let t = this.t_above[i];
			t.setAttributeNS(null, "x", p0[0]);
			t.setAttributeNS(null, "y", ymax - i * 10);
		}
	}
}

class Chart {
	constructor(svg, begintime, endtime, minprice, maxprice) {
		this.svg = svg;
		this.axg = svg.firstElementChild;
		this.objects = [];
		this.set_window(begintime, endtime, minprice, maxprice);
	}

	set_window(begintime, endtime, minprice, maxprice) {
		this.begintime = begintime;
		this.endtime = endtime;
		this.minprice = minprice;
		this.maxprice = maxprice;
		this.handle_resize();
		this.redraw_axes();
	}

	set_size() {
		this.outer_width = this.svg.clientWidth;
		this.width = this.outer_width - 200;
		this.outer_height = this.svg.clientHeight;
		this.height = this.outer_height - 20;
		this.svg.setAttributeNS(null, "width", this.width);
		this.svg.setAttributeNS(null, "height", this.height);
	}

	make_text(x, y, color, text) {
		let t = document.createElementNS(svgns, "text");
		t.setAttributeNS(null, "x", x);
		t.setAttributeNS(null, "y", y);
		t.innerHTML = text;
		t.setAttributeNS(null, "fill", color);
		t.setAttributeNS(null, "stroke", null);
		t.setAttributeNS(null, "font-size", 10);
		return t;
	}

	redraw_axes() {
		let prange = this.maxprice - this.minprice;
		let steps = 20.0
		let dp = prange / steps;
		this.axg.innerHTML = "";
		for (let i = 0; i < steps; i ++) {
			let p = this.minprice + i * dp;
			let y = this.p2y(p);
			let l = document.createElementNS(svgns, "line");
			l.setAttributeNS(null, "x1", 0);
			l.setAttributeNS(null, "x2", this.width);
			l.setAttributeNS(null, "y1", y);
			l.setAttributeNS(null, "y2", y);
			l.setAttributeNS(null, "stroke", "#e0e0e0");
			this.axg.appendChild(l);
			let t = this.make_text(this.width, y, "black", p.toFixed(8));
			this.axg.appendChild(t);
		}
	}

	redraw() {
		for (let i = 0, il = this.objects.length; i < il; i++) {
			let obj = this.objects[i];
			if (undefined === obj)
				continue;
			obj.redraw();
		}
	}

	handle_resize() {
		this.set_size();
		for (let i = 0, il = this.objects.length; i < il; i++) {
			let obj = this.objects[i];
			if (undefined === obj)
				continue;
			obj.resize();
		}
	}

	add_object(obj) {
		this.objects.push(obj);
	}

	tp2xy(time, price) {
		let dt = this.endtime - this.begintime;
		let x = (time - this.begintime) * this.width / dt;
		let y = this.p2y(price);
		return [x, y];
	}
	
	p2y(price) {
		let dp = this.maxprice - this.minprice;
		let y = (price - this.minprice) * this.height / dp;
		y = this.height - y;
		return y;
	}
}

class CommandHandler {
	constructor(chart) {
		this.chart = chart;
	}

	_norm_price(p, lim, rfunc) {
		let i = 0, j = 0;
		while (p < lim) {
			p *= 10.0;
			i ++;
		}
		while (p > lim) {
			p /= 10.0;
			j ++;
		}
		p = rfunc(p);
		while (j--)
			p *= 10.0;
		while (i--)
			p /= 10.0;
		return p;
	}

	handle_object(obj) {
		switch(obj.class) {
		case "candle":
			let c = new Candle(this.chart, obj.data);
			break;
		case "chart":
			let minp = this._norm_price(obj.minprice, 10, Math.floor);
			let maxp = this._norm_price(obj.maxprice, 10, Math.ceil);
			this.chart.set_window(obj.begintime, obj.endtime, minp, maxp);
			break;
		default:
			console.log("Undefined command object:", obj.class);
		}
	}
}

function main()
{
	let svg = document.getElementById("svg-main");
	let chart = new Chart(svg, 1534158000, 1535281200, 5000, 8000);
	let cmdh = new CommandHandler(chart);

	let ws = new WS.WSock(cmdh);
/*
	let c0 = new Candle(chart, {
		open:6323.43, close:6458.91, low:6248.39, high:6501.13,
		opents:1534806000, length:43200
	});
	let c1 = new Candle(chart, {
		open:6458.91, close:6489.23, low:6400.35, high:6506.69,
		opents:1534849200, length:43200
	});
	let c2 = new Candle(chart, {
		open:6489.54, close:6671.47, low:6453.41, high:6890.79,
		opents:1534892400, length:43200
	});
	let c3 = new Candle(chart, {
		open:6671.47, close:6367.21, low:6264.34, high:6697.93,
		opents:1534935600, length:43200
	});
	*/
}

return {
	main
};

})();
