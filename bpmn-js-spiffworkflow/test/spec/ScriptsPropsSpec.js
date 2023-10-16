import { query as domQuery } from 'min-dom';

import {
  BpmnPropertiesPanelModule,
  BpmnPropertiesProviderModule,
} from 'bpmn-js-properties-panel';
import { getBusinessObject } from 'bpmn-js/lib/util/ModelUtil';
import spiffModdleExtension from '../../app/spiffworkflow/moddle/spiffworkflow.json';
import {
  bootstrapPropertiesPanel,
  changeInput,
  expectSelected,
  findEntry,
  PROPERTIES_PANEL_CONTAINER,
} from './helpers';
import extensions from '../../app/spiffworkflow/extensions';

describe('Properties Panel Script Tasks', function () {
  const xml = require('./bpmn/diagram.bpmn').default;

  beforeEach(
    bootstrapPropertiesPanel(xml, {
      debounceInput: false,
      additionalModules: [
        extensions,
        BpmnPropertiesPanelModule,
        BpmnPropertiesProviderModule,
      ],
      moddleExtensions: {
        spiffworkflow: spiffModdleExtension,
      },
    })
  );

  it('should display a script editing panel when a script task is selected', async function () {
    // IF - you select a script task
    expectSelected('my_script_task');

    // THEN - a properties panel exists with a section for editing that script
    const entry = findEntry(
      'pythonScript_bpmn:script',
      PROPERTIES_PANEL_CONTAINER
    );
    expect(entry).to.exist;
    const scriptInput = domQuery('textarea', entry);
    expect(scriptInput).to.exist;
  });

  it('should update the bpmn:script tag when you modify the script field', async function () {
    // IF - a script tag is selected, and you change the script in the properties panel
    const scriptTask = await expectSelected('my_script_task');
    const entry = findEntry(
      'pythonScript_bpmn:script',
      PROPERTIES_PANEL_CONTAINER
    );
    const scriptInput = domQuery('textarea', entry);
    changeInput(scriptInput, 'x = 100');

    // THEN - the script tag in the BPMN Business object / XML is updated as well.
    const businessObject = getBusinessObject(scriptTask);
    expect(businessObject.get('script')).to.equal('x = 100');
    expect(scriptInput.value).to.equal('x = 100');
  });

  it('should parse the spiffworkflow:prescript tag when you open an existing file', async function () {
    await expectSelected('task_confirm');
    const entry = findEntry(
      'pythonScript_spiffworkflow:PreScript',
      PROPERTIES_PANEL_CONTAINER
    );
    const scriptInput = domQuery('textarea', entry);
    expect(scriptInput.value).to.equal('x=1');
  });
});
