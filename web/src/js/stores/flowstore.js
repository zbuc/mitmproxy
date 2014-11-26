function FlowStore(endpoint) {
    this._views = [];
    this.reset();
}
_.extend(FlowStore.prototype, {
    add: function (flow) {
        this._pos_map[flow.id] = this._flow_list.length;
        this._flow_list.push(flow);
        for (var i = 0; i < this._views.length; i++) {
            this._views[i].add(flow);
        }
    }
    update: function (flow) {
        this._flow_list[this._pos_map[flow.id]] = flow;
        for (var i = 0; i < this._views.length; i++) {
            this._views[i].update(flow);
        }
    },
    remove: function (flow_id) {
        this._flow_list.splice(this._pos_map[flow_id], 1);
        this._build_map();
        for (var i = 0; i < this._views.length; i++) {
            this._views[i].remove(flow_id);
        }
    },
    reset: function (flows) {
        this._flow_list = flows || [];
        this._build_map();
        for (var i = 0; i < this._views.length; i++) {
            this._views[i].recalculate(this._flow_list);
        }
    }
    _build_map: function () {
        this._pos_map = {};
        for (var i = 0; i < this._flow_list.length; i++) {
            var flow = this._flow_list[i];
            this._pos_map[flow.id] = i;
        }
    },
    open_view: function (filt, sort) {
        var view = new FlowView(this._flow_list, filt, sort);
        this._views.push(view);
        return view;
    },
    close_view: function (view) {
        this._views = _.without(this._views, view);
    }
});


function LiveFlowStore(endpoint) {
    FlowStore.call(this);
    this.updates_before_init = []; // (empty array is true in js)
    this.endpoint = endpoint || "/flows";
    this.conn = new Connection(this.endpoint + "/updates");
    this.conn.onopen = this._onopen;
    this.conn.onmessage = function (e) {
        var message = JSON.parse(e.data);
        this.handle_update(message.type, message.data);
    };
}
_.extend(LiveFlowStore.prototype, FlowStore.prototype, {
    hande_update: function (type, data) {
        console.log("LiveFlowStore.handle_update", type, data);
        if (this.updates_before_init) {
            console.log("defer update", type, data);
            this.updates_before_init.push(arguments);
        } else {
            this[type](data);
        }
    },
    handle_fetch: function (flows) {
        console.log("Flows fetched.")
        this.reset(flows);
        var updates = this.updates_before_init;
        this.updates_before_init = false;
        for (var i = 0; i < updates.length; i++) {
            this.handle_update.apply(this, updates[i]);
        }
    },
    _onopen: function () {
        //Update stream openend, fetch list of flows.
        console.log("Update Connection opened, fetching flows...")
        $.getJSON(this.endpoint, this.handle_fetch.bind(this));
    },
});

function SortByInsertionOrder() {
    this.i = 0;
    this.map = {};
    this.compare = this.compare.bind(this);
}
SortByInsertionOrder.prototype.key = function (flow) {
    if (!(flow.id in this.map)) {
        this.i++;
        this.map[flow.id] = this.i;
    }
    return this.map[flow.id];
}
SortByInsertionOrder.prototype.compare = function (a, b) {
    return this.key(a) - this.key(b);
}

var default_sort = new SortByInsertionOrder();

function FlowView(flows, filt, sort) {
    EventEmitter.call(this);
    filt = filt || function (flow) {
        return true;
    };
    sort = sort || default_sort;
    this.recalculate(flows, filt, sort);
}

_.extend(FlowView.prototype, EventEmitter.prototype, {
    recalculate: function (flows, filt, sort) {
        if (filt) {
            this.filt = filt;
        }
        if (sort) {
            this.sort = sort;
        }
        this.flows = flows.filter(this.filt);
        this.flows.sort(this.sort);
        this.emit("recalculate");
    },
    add: function (flow) {
        if (this.filt(flow)) {
            var idx = _.sortedIndex(this.flows, flow, this.sort);
            if (idx === this.flows.length) { //happens often, .push is way faster.
                this.flows.push(flow);
            } else {
                this.flows.splice(idx, 0, flow);
            }
            this.emit("add", flow, idx);
        }
    },
    update: function (flow) {
        var idx;
        var i = this.flows.length;
        // Search from the back, we usually update the latest flows.
        while (i--) {
            if (this.flows[i].id === flow.id) {
                idx = i;
                break;
            }
        }

        if (idx === -1) { //not contained in list
            this.add(flow);
        } else if (!this.filt(flow)) {
            this.remove(flow.id);
        } else {
            if (this.sort(this.flows[idx], flow) !== 0) { //sortpos has changed
                this.remove(this.flows[idx]);
                this.add(flow);
            } else {
                this.flows[idx] = flow;
                this.emit("update", flow, idx);
            }
        }
    },
    remove: function (flow_id) {
        var i = this.flows.length;
        while (i--) {
            if (this.flows[i].id === flow_id) {
                this.flows.splice(i, 1);
                this.emit("remove", flow_id, i);
                break;
            }
        }
    }
});

/*
function FlowView(start, count, filt, sort, url) {
    EventEmitter.call(this);

    this.start = start;
    this.count = count;
    this.filt = filt;
    this.sort = sort;

    url = (url || "/flowview") + "?" + $.param({
        start: this.start,
        count: this.count,
        filt: this.filt,
        sort: this.sort
    });

    Connection.call(this, url);

    this.flows = [];
    this.total = 0;
}

_.extend(FlowView.prototype, EventEmitter.prototype, Connection.prototype, {
    close: function () {
        Connection.prototype.close.call(this);
    },
    handle_message: function (type, data) {
        switch (type) {
            case "all_flows":
                this.flows = data.flows;
                this.total = data.total;
                break;
            case "add_flow":
                this.flows.splice(data.pos, 0, data.flow);
                if (this.flows.length > this.count) {
                    this.flows.pop();
                }
                break;
            case "update_flow":
                this.flows[data.pos] = data.flow;
                break;
            case "remove_flow":
                this.flows.splice(data.pos, 1);
                if (data.restock) {
                    this.flows.push(data.restock);
                } else {
                    this.total--;
                }
                break;
            case "update_total":
                this.total = data;
                break;
            default:
                console.error("Unknown message type: " + message.type);
        }
        this.emit(message.type, message);
    },
    onmessage: function (e) {
        message = JSON.parse(e.data);
        console.log("flowview: " + message.type, message.data);
        this.handle_message(message.type, message.data);
    }
});
*/