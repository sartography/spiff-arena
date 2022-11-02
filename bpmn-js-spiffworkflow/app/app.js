import BpmnModeler from 'bpmn-js/lib/Modeler';
import {
  BpmnPropertiesPanelModule,
  BpmnPropertiesProviderModule,
} from 'bpmn-js-properties-panel';
import diagramXML from '../test/spec/bpmn/user_form.bpmn';
import spiffworkflow from './spiffworkflow';
import setupFileOperations from './fileOperations';

const modelerEl = document.getElementById('modeler');
const panelEl = document.getElementById('panel');
const spiffModdleExtension = require('./spiffworkflow/moddle/spiffworkflow.json');

let bpmnModeler;

/**
 * This provides an example of how to instantiate a BPMN Modeler configured with
 * all the extensions and modifications in this application.
 */
try {
  bpmnModeler = new BpmnModeler({
    container: modelerEl,
    propertiesPanel: {
      parent: panelEl,
    },
    additionalModules: [
      spiffworkflow,
      BpmnPropertiesPanelModule,
      BpmnPropertiesProviderModule,
    ],
    moddleExtensions: {
      spiffworkflowModdle: spiffModdleExtension,
    },
  });
} catch (error) {
  if (error.constructor.name === 'AggregateError') {
    console.log(error.message);
    console.log(error.name);
    console.log(error.errors);
  }
  throw error;
}

// import XML
bpmnModeler.importXML(diagramXML).then(() => {});

/**
 * It is possible to populate certain components using API calls to
 * a backend.  Here we mock out the API call, but this gives you
 * a sense of how things might work.
 *
 */
bpmnModeler.on('spiff.service_tasks.requested', (event) => {
  event.eventBus.fire('spiff.service_tasks.returned', {
    serviceTaskOperators: [
      {
        id: 'Chuck Norris Fact Service',
        parameters: [
          {
            id: 'category',
            type: 'string',
          },
        ],
      },
      {
        id: 'Fact about a Number',
        parameters: [
          {
            id: 'number',
            type: 'integer',
          },
        ],
      },
    ],
  });
});

/**
 * Python Script authoring is best done in some sort of editor
 * here is an example that will connect a large CodeMirror editor
 * to the "Launch Editor" buttons (Script Tasks, and the Pre and Post
 * scripts on all other tasks.
 */
const myCodeMirror = CodeMirror(document.getElementById('code_editor'), {
  lineNumbers: true,
  mode: 'python',
});

const saveCodeBtn = document.getElementById('saveCode');
let launchCodeEvent = null;

bpmnModeler.on('script.editor.launch', (newEvent) => {
  launchCodeEvent = newEvent;
  myCodeMirror.setValue(launchCodeEvent.script);
  setTimeout(function() {
    myCodeMirror.refresh();
  },1);  // We have to wait a moment before calling refresh.
  document.getElementById('code_overlay').style.display = 'block';
  document.getElementById('code_editor').focus();
});

saveCodeBtn.addEventListener('click', (_event) => {
  const { scriptType, element } = launchCodeEvent;
  launchCodeEvent.eventBus.fire('script.editor.update', { element, scriptType, script: myCodeMirror.getValue()} )
  document.getElementById('code_overlay').style.display = 'none';
});


/**
 * Like Python Script Editing, it can be nice to edit your Markdown in a
 * good editor as well.
 */
var simplemde = new SimpleMDE({ element: document.getElementById("markdown_textarea") });
let launchMarkdownEvent = null;
bpmnModeler.on('markdown.editor.launch', (newEvent) => {
  launchMarkdownEvent = newEvent;
  simplemde.value(launchMarkdownEvent.markdown);
  document.getElementById('markdown_overlay').style.display = 'block';
  document.getElementById('markdown_editor').focus();
});

const saveMarkdownBtn = document.getElementById('saveMarkdown');
saveMarkdownBtn.addEventListener('click', (_event) => {
  const { element } = launchMarkdownEvent;
  launchMarkdownEvent.eventBus.fire('markdown.editor.update', { element, markdown:simplemde.value() });
  document.getElementById('markdown_overlay').style.display = 'none';
});

// This handles the download and upload buttons - it isn't specific to
// the BPMN modeler or these extensions, just a quick way to allow you to
// create and save files, so keeping it outside the example.
setupFileOperations(bpmnModeler);
