
self.onmessage = function(e) {
  self.postMessage("bob: " + e.data);
};
