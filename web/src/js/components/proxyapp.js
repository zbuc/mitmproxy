var React = require("react");
var ReactRouter = require("react-router");
var _ = require("lodash");

var common = require("./common.js");
var MainView = require("./mainview.js");
var Footer = require("./footer.js");
var header = require("./header.js");
var EventLog = require("./eventlog.js");
var store = require("../store/store.js");
var Query = require("../actions.js").Query;
var Key = require("../utils.js").Key;
var ContentViewAll = require("./flowview/contentview.js").all;
var PluginMixin = require("./flowview/contentview.js").PluginMixin;
var PluginList = require("./flowview/plugins.js").PluginList;


//TODO: Move out of here, just a stub.
var PluginOption = React.createClass({
    triggerClick: function (event) {
        var el = event.target;
        $.ajax({
            type: "POST",
            url: "/plugins/" + this.props.plugin.id,
            contentType: 'application/json',
            data: JSON.stringify(_.find(this.props.plugin.actions, function(o){return (o.id === el.getAttribute('id'))}))
        });
    },

    render: function () {
        var plugin = this.props.plugin; 

        var ret = [];
        _.forEach(plugin.actions, function (action) {
                ret.push(<div><label for={action.id}>{action.title}s</label>
                         <input type="checkbox" id={action.id} data-action={action.action}/></div>);
        }.bind(this));

        return (<span>{ret}</span>);
    }
});

var PluginOptions = React.createClass({
    getInitialState: function() {
        return { plugins: PluginList };
    },

    render: function () {

        var rows = [];
        console.log("plugin list...");
        console.log(PluginList);
        _.forEach(PluginList, function (plugin) {
            rows.push(<tr>
                        <td>{plugin.title}</td>
                        <td><PluginOption plugin={plugin}/></td>
                      </tr>);
        });

        return (
            <table className="plugins-table">
                <thead>
                    <tr><td>Name</td><td>Options</td></tr>
                </thead>

                <tbody>
                {rows}
                </tbody>
            </table>
        );
    }
});

var Plugins = React.createClass({
    render: function () {
        return (<div><section>Plugin Settings
                            <PluginOptions/>
                            </section>
</div>);
    }
});

var Reports = React.createClass({
    render: function () {
        return <div>ReportEditor</div>;
    }
});


var ProxyAppMain = React.createClass({
    mixins: [common.RouterState],
    childContextTypes: {
        settingsStore: React.PropTypes.object.isRequired,
        flowStore: React.PropTypes.object.isRequired,
        eventStore: React.PropTypes.object.isRequired,
        returnFocus: React.PropTypes.func.isRequired,
    },
    componentDidMount: function () {
        this.focus();
    },
    getChildContext: function () {
        return {
            settingsStore: this.state.settingsStore,
            flowStore: this.state.flowStore,
            eventStore: this.state.eventStore,
            returnFocus: this.focus,
        };
    },
    getInitialState: function () {
        var eventStore = new store.EventLogStore();
        var flowStore = new store.FlowStore();
        var settingsStore = new store.SettingsStore();

        // get the view plugin list and append to ContentView's `all`
        // so buttons will be available on the UI
        var pluginList;
        $.getJSON("/plugins")
                .done(function (message) {
                    console.log("Retrieved plugins: " +
                        JSON.stringify(message.data));
                    _.each(message.data, function(plugin){
                        if (plugin.type === 'view_plugins') {
                            var ViewPlugin = React.createClass({
                                displayName: plugin.id,
                                mixins: [PluginMixin],
                                statics: {
                                    matches: function (message) {
                                        return true;
                                    }
                                },
                                renderContent: function () {
                                    return <pre>{this.state.content}</pre>;
                                }
                            });

                            ContentViewAll.push(ViewPlugin);
                        }

                        if (plugin.type === 'action_plugins') {
                            PluginList.push(plugin);
                        }
                    });

                    // trigger rerender of plugin options -- this is necessary
                    // if page is loaded w/ "/plugins" url because of a race
                    // condition regarding PluginList

                    // i think i want to setState but not sure how to get ref to
                    // right object
                    console.log("XXX: I should trigger a re-render of the PluginOptions now, but I don't know how");
                }.bind(this))
                .fail(function () {
                    console.log("Could not fetch plugins");
                }.bind(this));


        // Default Settings before fetch
        _.extend(settingsStore.dict, {});
        return {
            settingsStore: settingsStore,
            flowStore: flowStore,
            eventStore: eventStore
        };
    },
    focus: function () {
        React.findDOMNode(this).focus();
    },
    getMainComponent: function () {
        return this.refs.view.refs.__routeHandler__;
    },
    onKeydown: function (e) {

        var selectFilterInput = function (name) {
            var headerComponent = this.refs.header;
            headerComponent.setState({active: header.MainMenu}, function () {
                headerComponent.refs.active.refs[name].select();
            });
        }.bind(this);

        switch (e.keyCode) {
            case Key.I:
                selectFilterInput("intercept");
                break;
            case Key.L:
                selectFilterInput("search");
                break;
            case Key.H:
                selectFilterInput("highlight");
                break;
            default:
                var main = this.getMainComponent();
                if (main.onMainKeyDown) {
                    main.onMainKeyDown(e);
                }
                return; // don't prevent default then
        }
        e.preventDefault();
    },
    render: function () {
        var eventlog;
        if (this.getQuery()[Query.SHOW_EVENTLOG]) {
            eventlog = [
                <common.Splitter key="splitter" axis="y"/>,
                <EventLog key="eventlog"/>
            ];
        } else {
            eventlog = null;
        }
        return (
            <div id="container" tabIndex="0" onKeyDown={this.onKeydown}>
                <header.Header ref="header"/>
                <RouteHandler ref="view" query={this.getQuery()}/>
                {eventlog}
                <Footer/>
            </div>
        );
    }
});


var Route = ReactRouter.Route;
var RouteHandler = ReactRouter.RouteHandler;
var Redirect = ReactRouter.Redirect;
var DefaultRoute = ReactRouter.DefaultRoute;
var NotFoundRoute = ReactRouter.NotFoundRoute;


var routes = (
    <Route path="/" handler={ProxyAppMain}>
        <Route name="flows" path="flows" handler={MainView}/>
        <Route name="flow" path="flows/:flowId/:detailTab" handler={MainView}/>
        <Route name="reports" handler={Reports}/>
        <Route name="plugins" handler={Plugins}/>
        <Redirect path="/" to="flows" />
    </Route>
);

module.exports = {
    routes: routes,
    PluginOptions: PluginOptions
};