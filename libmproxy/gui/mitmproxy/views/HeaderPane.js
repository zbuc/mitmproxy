define([
        "require", 
        "dojo/_base/declare", 
        "../util/_ReactiveTemplatedWidget",
        "../MainLayout",
        "../config",
        "jquery",
        "../util/smart-popover",
        "dojo/text!./templates/HeaderPane.html",
        "dojo/text!./templates/HeaderPane-MainMenu.html"],
function(require, declare, _ReactiveTemplatedWidget, MainLayout, config, $, _, template, template_menu) {

    var menu = new _ReactiveTemplatedWidget({templateString: template_menu, context: {config:config}});

	return declare([ _ReactiveTemplatedWidget ], {
		templateString: template,
        postCreate: function(){
            $(this.brandNode).smartPopover({
                placement: "bottom",
                html: true,
                title: "mitmproxy "+config.get("version"),
                content: menu.domNode.outerHTML,
                container: "body"
            });
        },
        destroy: function(){
            $(this.brandNode).popover("destroy");
        },
		showPane: function(id){
			MainLayout.showPane(id);
		}
	});
	
});