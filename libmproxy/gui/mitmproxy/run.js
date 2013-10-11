if (define && define.amd) //AMDize jQuery
	define.amd.jQuery = true;

require(
[		"mitmproxy/MainLayout",
		"mitmproxy/traffic",
		"mitmproxy/util/versionCheck",
		"mitmproxy/util/sampleFlow",
		"mitmproxy/util/requestAuthenticator"
], function(MainLayout, flowStore, versionCheck, sampleFlow) {

	//Debug
	window.mitmproxy = {
		flowStore: flowStore,
		sampleFlow: sampleFlow,
		MainLayout: MainLayout
	};

    /* Super Ugly Workaround to refresh the grid
    manually as long as the mitmproxy isn't finished yet */
    window.setInterval(function(){
        var grid = mitmproxy.MainLayout.trafficPane.grid;
        if(grid._total == 0){
           grid.refresh();
        } else {
            flowStore.notify();
        }
    },1000);

	window.setTimeout(versionCheck, 3000);
});