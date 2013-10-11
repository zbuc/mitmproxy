define(["./RequestUtils","./ResponseUtils"],function(RequestUtils,ResponseUtils){
  
  //Simple matching function generator for View.matches(flow) that performs a match based on the supplied content type and filename.
  
  return function(contentType, filename, always){
    return function(flow) {
      if(RequestUtils.hasContent(flow.request) && !always){
        //A request with Content-Length > 0 could be "exoctic" flow not handled by the specialised view correctly.
        //use generic display to make sure that we cover everything. This behavior can be overriden by specifying always=true
        return false;
      }
      var contentType_ = flow.response ? ResponseUtils.getContentType(flow.response) : false;
      if (contentType && contentType_ && !!contentType_.match(contentType))
        return true;
      var filename_ = RequestUtils.getFilename(flow.request);
      if (filename && filename_ && !!filename_.match(filename))
        return true;
      return false;
    };
  };
});