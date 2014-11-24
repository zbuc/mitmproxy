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