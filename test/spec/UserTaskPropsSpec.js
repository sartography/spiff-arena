import {
  bootstrapPropertiesPanel, changeInput,
  expectSelected,
  findEntry, findGroupEntry, findInput
} from './helpers';

import spiffModdleExtension from '../../app/spiffworkflow/moddle/spiffworkflow.json';
import { BpmnPropertiesPanelModule, BpmnPropertiesProviderModule } from 'bpmn-js-properties-panel';
import { getBusinessObject } from 'bpmn-js/lib/util/ModelUtil';
import TestContainer from 'mocha-test-container-support';
import extensions from '../../app/spiffworkflow/extensions';

describe('Properties Panel for User Tasks', function() {
  const user_form_xml = require('./bpmn/user_form.bpmn').default;
  const diagram_xml = require('./bpmn/diagram.bpmn').default;
  let container;

  beforeEach(function() {
    container = TestContainer.get(this);
  });

  function preparePropertiesPanelWithXml(xml) {
    return bootstrapPropertiesPanel(xml, {
      container,
      debounceInput: false,
      additionalModules: [
        extensions,
        BpmnPropertiesPanelModule,
        BpmnPropertiesProviderModule,
      ],
      moddleExtensions: {
        spiffworkflow: spiffModdleExtension
      },
    });
  }

  it('should display a panel for setting the web form properties', async function() {
    await preparePropertiesPanelWithXml(user_form_xml)();

    // IF - you select a user task
    const userTask = await expectSelected('my_user_task');
    expect(userTask).to.exist;

    // THEN - a property panel exists with a section for editing web forms
    let group = findGroupEntry('user_task_properties', container);
    expect(group).to.exist;
  });

  it('should allow you to edit a web form property.', async function() {
    await preparePropertiesPanelWithXml(user_form_xml)();

    // IF - you select a user task and change the formJsonSchemaFilename text field
    const userTask = await expectSelected('my_user_task');
    let group = findGroupEntry('user_task_properties', container);
    let entry = findEntry('extension_formJsonSchemaFilename', group);
    let input = findInput('text', entry);
    expect(input).to.exist;
    changeInput(input, 'my_filename.json');

    // THEN - the input is updated.
    let businessObject = getBusinessObject(userTask);
    expect(businessObject.extensionElements).to.exist;
    let properties = businessObject.extensionElements.values[1];
    expect(properties.properties).to.exist;
    const property = properties.properties[0];
    expect(property.value).to.equal('my_filename.json');
    expect(property.name).to.equal('formJsonSchemaFilename');
  });

  it('should parse the spiffworkflow:properties tag when you open an existing file', async function() {
    await preparePropertiesPanelWithXml(diagram_xml)();

    // IF - a script tag is selected, and you change the script in the properties panel
    await expectSelected('task_confirm');
    let group = findGroupEntry('user_task_properties', container);
    let formJsonSchemaFilenameEntry = findEntry('extension_formJsonSchemaFilename', group);
    let formJsonSchemaFilenameInput = findInput('text', formJsonSchemaFilenameEntry);
    expect(formJsonSchemaFilenameInput.value).to.equal('give_me_a_number_form.json');

    let formUiSchemaFilenameEntry = findEntry('extension_formUiSchemaFilename', group);
    let formUiSchemaFilenameInput = findInput('text', formUiSchemaFilenameEntry);
    expect(formUiSchemaFilenameInput.value).to.equal('number_form_schema.json');
  });

});
