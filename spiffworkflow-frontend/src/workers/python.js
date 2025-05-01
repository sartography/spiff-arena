
importScripts("https://cdn.jsdelivr.net/pyodide/v0.27.5/full/pyodide.js");

self.onmessage = function(e) {
  self.postMessage("bob: " + e.data);
};
