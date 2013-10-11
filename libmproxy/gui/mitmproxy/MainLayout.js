//TODO: Move all DOM interaction into asynchronous code to speed up initialization.
define([
		"exports",
		"dijit/layout/BorderContainer",
		"dijit/layout/StackContainer",
		"./views/HeaderPane",
		"./views/TrafficPane",
		"./views/ReportPane",
		"dojo/domReady!"
], function(exports, BorderContainer, StackContainer, HeaderPane, TrafficPane, ReportPane) {

	//appLayout covers everything
	var appLayout = new BorderContainer({
		design: "headline",
		liveSplitters: false,
		gutters: false
	}, "appLayout");

	var header = new HeaderPane({
		region: "top",
		id: "header",
		style: "width: 100%;"
	});

	//main covers the whole content area, but not the header
	var main = new StackContainer({
		id: "main",
		region: "center"
	});

	//populate appLayout
	appLayout.addChild(header);
	appLayout.addChild(main);


	//Traffic Pane, our default view with search sidebar and traffic table.
	var trafficPane = new TrafficPane({
		liveSplitters: false,
		gutters: false
	});

	//Report Pane
	var reportPane = new ReportPane({
		liveSplitters: false,
		gutters: false
	});

	//populate main
	main.addChild(trafficPane);
	main.addChild(reportPane);

	appLayout.startup();

	exports.mainContainer = main;
	exports.showPane = function(index) {
		main.selectChild(main.getChildren()[index]);
	};
	exports.header = header;

	exports.trafficPane = trafficPane;

	return exports;
});