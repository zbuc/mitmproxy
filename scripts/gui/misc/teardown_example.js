require([],function(){
  var i = domConstruct.create("input",{ value: "foo"},out,"only");
  addDestroyListener(function(){
    console.log("Destructor called: " + i.value);
  });
});