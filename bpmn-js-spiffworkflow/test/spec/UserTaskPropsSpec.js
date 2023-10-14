import {
  BpmnPropertiesPanelModule,
  BpmnPropertiesProviderModule,
} from 'bpmn-js-properties-panel';
import { getBpmnJS } from 'bpmn-js/test/helper';
import { getBusinessObject } from 'bpmn-js/lib/util/ModelUtil';
import TestContainer from 'mocha-test-container-support';
import spiffModdleExtension from '../../app/spiffworkflow/moddle/spiffworkflow.json';
import {getExtensionProperty, getExtensionValue} from '../../app/spiffworkflow/extensions/extensionHelpers';
import {
  bootstrapPropertiesPanel,
  changeInput,
  expectSelected, findButton,
  findEntry,
  findGroupEntry,
  findInput,
  findSelect, pressButton,
} from './helpers';
import extensions from '../../app/spiffworkflow/extensions';
import {query as domQuery} from 'min-dom';


describe('Properties Panel for User Tasks', function () {
  const user_form_xml = require('./bpmn/user_form.bpmn').default;
  const diagram_xml = require('./bpmn/diagram.bpmn').default;
  let container;

  beforeEach(function () {
    container = TestContainer.get(this);
  });

  function addOptionsToEventBus(bpmnModeler) {
    bpmnModeler.on('spiff.json_schema_files.requested', (event) => {
      event.eventBus.fire('spiff.json_schema_files.returned', {
        options: [
          { label: 'pizza_form.json', value: 'pizza_form.json' },
          { label: 'credit_card_form.json', value: 'credit_card_form.json' },
          { label: 'give_me_a_number_form.json', value: 'give_me_a_number_form.json' },
          { label: 'number_form_schema.json', value: 'number_form_schema.json' },
        ],
      });
    });
  }

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
        spiffworkflow: spiffModdleExtension,
      },
    });
  }

  it('should display a panel for setting the web form properties', async function () {
    await preparePropertiesPanelWithXml(user_form_xml)();

    // IF - you select a user task
    const userTask = await expectSelected('my_user_task');
    expect(userTask).to.exist;

    // THEN - a property panel exists with a section for editing web forms
    const group = findGroupEntry('user_task_properties', container);
    expect(group).to.exist;
  });

  it('should allow you to select a json file.', async function () {
    await preparePropertiesPanelWithXml(user_form_xml)();
    const modeler = getBpmnJS();
    addOptionsToEventBus(modeler);
    // IF - you select a user task and change the formJsonSchemaFilename text field
    const userTask = await expectSelected('my_user_task');
    const group = findGroupEntry('user_task_properties', container);
    const entry = findEntry('extension_formJsonSchemaFilename', group);
    const selectList = findSelect(entry);
    expect(selectList).to.exist;
    expect(selectList.options.length).to.equal(5); // including the empty option
    expect(selectList.options[0].label).to.equal('');
    expect(selectList.options[1].label).to.equal('pizza_form.json');
    expect(selectList.options[2].label).to.equal('credit_card_form.json');

    changeInput(selectList, 'pizza_form.json');

    // THEN - the input is updated.
    const businessObject = getBusinessObject(userTask);
    expect(businessObject.extensionElements).to.exist;
    const properties = businessObject.extensionElements.values[1];
    expect(properties.properties).to.exist;
    const property = properties.properties[0];
    expect(property.value).to.equal('pizza_form.json');
    expect(property.name).to.equal('formJsonSchemaFilename');
  });

  it('should parse the spiffworkflow:properties tag when you open an existing file', async function () {
    await preparePropertiesPanelWithXml(diagram_xml)();
    const modeler = getBpmnJS();
    addOptionsToEventBus(modeler);

    // IF - a user tag is selected, and you change the script in the properties panel
    await expectSelected('task_confirm');
    const group = findGroupEntry('user_task_properties', container);
    const formJsonSchemaFilenameEntry = findEntry('extension_formJsonSchemaFilename', group);
    const formJsonSchemaFilenameInput = findSelect(formJsonSchemaFilenameEntry);
    expect(formJsonSchemaFilenameInput.value).to.equal('give_me_a_number_form.json');
  });

  it('should update both the json and ui extensions if the json file is set', async function () {
    await preparePropertiesPanelWithXml(diagram_xml)();
    const modeler = getBpmnJS();

    addOptionsToEventBus(modeler);
    const userElement = await expectSelected('task_confirm');
    const group = findGroupEntry('user_task_properties', container);
    const button = findButton(
      'launch_editor_button_formJsonSchemaFilename',
      group
    );
    expect(button).to.exist;
    let launchEvent;
    let eventBus = modeler.get('eventBus');
    eventBus.on('spiff.file.edit', function (event) {
      launchEvent = event;
    });
    await pressButton(button);
    expect(launchEvent.value).to.exist;
    eventBus.fire('spiff.jsonSchema.update', {
      value: 'new-schema.json',
    });
    const jsonFile = getExtensionValue(userElement, 'formJsonSchemaFilename');
    const uiFile = getExtensionValue(userElement, 'formUiSchemaFilename');
    expect(jsonFile).to.equal('new-schema.json');
    expect(uiFile).to.equal('new-uischema.json');

  });

  it('should allow you to change the instructions to the end user', async function () {
    // If a user task is selected
    await preparePropertiesPanelWithXml(diagram_xml)();
    const modeler = getBpmnJS();
    addOptionsToEventBus(modeler);

    // AND the value of the instructions is changed
    const userElement = await expectSelected('task_confirm');
    const group = findGroupEntry('instructions', container);

    const input = domQuery('textarea', group);
    changeInput(input, '#Hello!');

    // THEN - the script tag in the BPMN Business object / XML is updated as well.
    const businessObject = getBusinessObject(userElement);
    // The change is reflected in the business object
    let instructions = getExtensionValue(
      userElement,
      'spiffworkflow:InstructionsForEndUser'
    );
    expect(instructions).to.equal('#Hello!');
  });
});
