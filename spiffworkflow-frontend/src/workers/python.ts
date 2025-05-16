// @ts-nocheck
/* eslint-disable no-restricted-globals */

// eslint-disable-next-line no-undef
importScripts('https://cdn.jsdelivr.net/pyodide/v0.27.5/full/pyodide.js');

const pyodideInitialLoad = (async () => {
  console.log('Loading Python...');
  const pyStart = Date.now();

  {
    const start = Date.now();
    // eslint-disable-next-line no-undef
    const pyodide = await loadPyodide({ fullStdLib: false });
    await pyodide.loadPackage('micropip');
    const micropip = pyodide.pyimport('micropip');
    await micropip.install(['Jinja2==3.1.6', 'spiff-arena-common==0.1.0']);

    // eslint-disable-next-line no-undef
    self.pyodide = pyodide;

    const end = Date.now();

    console.log(`Loaded Python packages in ${end - start}ms`);
  }

  {
    const start = Date.now();
    await self.pyodide.runPythonAsync(`

import jinja2
import json

from spiff_arena_common.jinja import JinjaHelpers

def jinja_form(schema, ui, form_data):
    if not schema or not ui:
        return schema, ui, None

    try:
        form_data = json.loads(form_data)
        env = jinja2.Environment(autoescape=True, lstrip_blocks=True, trim_blocks=True)
        env.filters.update(JinjaHelpers.get_helper_mapping())
        schema = env.from_string(schema).render(**form_data)
        ui = env.from_string(ui).render(**form_data)
    except Exception as e:
        return schema, ui, f"{e.__class__.__name__}: {e}"

    return schema, ui, None
`);
    const end = Date.now();

    console.log(`Loaded Python app code in ${end - start}ms`);
  }

  const end = Date.now();
  console.log(`Loaded Python in ${end - pyStart}ms`);
})();

const messageHandlers = {
  jinjaForm: async (e) => {
    const locals = self.pyodide.toPy(e.data);
    const [strSchema, strUI, err] = await self.pyodide.runPythonAsync(
      'jinja_form(strSchema, strUI, strFormData)',
      { locals },
    );

    self.postMessage({
      type: 'didJinjaForm',
      strSchema,
      strUI,
      err,
    });
  },
};

self.onmessage = async (e) => {
  await pyodideInitialLoad;

  messageHandlers[e.data.type]?.(e);
};
