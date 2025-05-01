importScripts('https://cdn.jsdelivr.net/pyodide/v0.27.5/full/pyodide.js');

const pyodideInitialLoad = (async () => {
  console.log('Loading Python...');
  const start = Date.now();

  /*
  // to regen lock file:
  {
    const pyodide = await loadPyodide();
    await pyodide.loadPackage("micropip");
    const micropip = pyodide.pyimport("micropip");
    await micropip.install(["Jinja2"]);
    const frozen = micropip.freeze();
    //
    // copy/paste log output and save to pyodide-lock.json
    console.log(JSON.stringify(JSON.parse(frozen)));
  }
  */

  {
    const start = Date.now();
    self.pyodide = await loadPyodide({
      fulllStdLib: false,
      lockFileURL: '/pyodide-lock.json',
    });
    await self.pyodide.loadPackage(['Jinja2']);
    const end = Date.now();

    console.log(`Loaded Python packages in ${end - start}ms`);
  }

  {
    const start = Date.now();
    await self.pyodide.runPythonAsync(`

import jinja2
`);
    const end = Date.now();

    console.log(`Loaded Python app code in ${end - start}ms`);
  }

  const end = Date.now();
  console.log(`Loaded Python in ${end - start}ms`);
})();

const messageHandlers = {
  jinjaForm: async ({ data: { schema, uiSchema, formData }}) => {
    self.postMessage({
    });
  },
};

self.onmessage = async (e) => {
  await pyodideInitialLoad;

  messageHandlers[e.data.type]?.(e);
};
