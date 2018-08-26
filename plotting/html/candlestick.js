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

	_make_wick(p0, p1, x, w, color) {
		let wick = document.createElementNS(svgns, "line");
		let wickw = Math.max(w * 0.05, 1);
		wick.setAttributeNS(null, "y1", this.chart.p2y(p0));
		wick.setAttributeNS(null, "y2", this.chart.p2y(p1));
		wick.setAttributeNS(null, "x1", x + w / 2);
		wick.setAttributeNS(null, "x2", x + w / 2);
		wick.setAttributeNS(null, "stroke", color);
		wick.setAttributeNS(null, "stroke-width", wickw);
		return wick;
	}

	create() {
		let svg = this.chart.svg;
		let d = this.data;
		var color, price1, price2
		if (d.close < d.open) {
			color = "red";
			price1 = d.close;
			price2 = d.open;
		} else {
			color = "green";
			price1 = d.open;
			price2 = d.close;
		}
		let price0 = d.low;
		let price3 = d.high;
		let p0 = this.chart.tp2xy(d.opents, price2);
		let p1 = this.chart.tp2xy(d.opents + d.length, price1);
		let body = document.createElementNS(svgns, "rect");
		let bh = p1[1] - p0[1];
		let bw = p1[0] - p0[0];
		let margin = bw * 0.1;
		body.setAttributeNS(null, "fill", color);
		body.setAttributeNS(null, "stroke", color);
		body.setAttributeNS(null, "x", p0[0] + margin / 2);
		body.setAttributeNS(null, "y", p0[1]);
		body.setAttributeNS(null, "width", bw - margin);
		body.setAttributeNS(null, "height", bh);
		svg.appendChild(body);
		this.body = body;
		this.lwick = this._make_wick(price0, price1, p0[0], bw, color);
		svg.appendChild(this.lwick);
		let hwick = document.createElementNS(svgns, "line");
		this.hwick = this._make_wick(price2, price3, p0[0], bw, color);
		svg.appendChild(this.hwick);
	}
}

class Chart {
	constructor(svg, begintime, endtime, minprice, maxprice) {
		this.svg = svg;
		this.begintime = begintime;
		this.endtime = endtime;
		this.minprice = minprice;
		this.maxprice = maxprice;
		this.objects = [];
		this.set_size();
	}

	set_size() {
		this.width = this.svg.clientWidth;
		this.height = this.svg.clientHeight;
	}

	clear() {
		this.svg.innerHTML = ""; // FIXME: Inefficient
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

function main()
{
	let svg = document.getElementById("svg-main");
	let chart = new Chart(svg, 1534158000, 1535281200, 5000, 8000);
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
}

return {
	main
};

})();
