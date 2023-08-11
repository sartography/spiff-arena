import {
  bootstrapPropertiesPanel, changeInput,
  expectSelected,
  findEntry, findInput, findSelect,
} from './helpers';
import { BpmnPropertiesPanelModule, BpmnPropertiesProviderModule } from 'bpmn-js-properties-panel';
import spiffModdleExtension from '../../app/spiffworkflow/moddle/spiffworkflow.json';
import TestContainer from 'mocha-test-container-support';
import DataObject from '../../app/spiffworkflow/DataObject';

describe('Properties Panel for Data Objects', function() {
  let xml = require('./bpmn/diagram.bpmn').default;
  let container;

  beforeEach(function() {
    container = TestContainer.get(this);
  });

  beforeEach(bootstrapPropertiesPanel(xml, {
    container,
    debounceInput: false,
    additionalModules: [
      DataObject,
      BpmnPropertiesPanelModule,
      BpmnPropertiesProviderModule,
    ],
    moddleExtensions: {
      spiffworkflow: spiffModdleExtension
    },
  }));

  it('should allow you to see a list of data objects', async function() {

    // IF - a data object reference is selected
    let my_data_ref_1 = await expectSelected('my_data_ref_1');
    expect(my_data_ref_1).to.exist;

    // THEN - a select Data Object section should appear in the properties panel
    let entry = findEntry('selectDataObject', container);
    expect(entry).to.exist;

    // AND - That that properties' pane selection should contain a dropdown with a value in it.
    let selector = findSelect(entry);
    expect(selector).to.exist;
    expect(selector.length).to.equal(3);
  });


  it('selecting a different data object should change the data model.', async function() {

    // IF - a data object reference is selected
    let my_data_ref_1 = await expectSelected('my_data_ref_1');

    let entry = findEntry('selectDataObject', container);
    let selector = findSelect(entry);
    let businessObject = my_data_ref_1.businessObject;

    // AND we select a dataObjectReference (we know it has this value, because we created the bpmn file)
    changeInput(selector, 'my_third_data_object');

    // then this data reference object now references that data object.
    expect(businessObject.get('dataObjectRef').id).to.equal('my_third_data_object');
  });

  it('renaming a data object, changes to the label of references', async function() {

    // IF - a process is selected, and the name of a data object is changed.
    let entry = findEntry('ProcessTest-dataObj-2-id', container);
    let textInput = findInput('text', entry);
    changeInput(textInput, 'my_nifty_new_name');
    let my_data_ref_1 = await expectSelected('my_data_ref_1');

    // THEN - both the data object itself, and the label of any references are updated.
    expect(my_data_ref_1.businessObject.dataObjectRef.id).to.equal('my_nifty_new_name');
    expect(my_data_ref_1.businessObject.name).to.equal('My Nifty New Name');
  });

  it('renaming a data object creates a lable without losing the numbers', async function() {

    // IF - a process is selected, and the name of a data object is changed.
    let entry = findEntry('ProcessTest-dataObj-2-id', container);
    let textInput = findInput('text', entry);
    changeInput(textInput, 'MyObject1');
    let my_data_ref_1 = await expectSelected('my_data_ref_1');

    // THEN - both the data object itself, and the label of any references are updated.
    expect(my_data_ref_1.businessObject.dataObjectRef.id).to.equal('MyObject1');
    expect(my_data_ref_1.businessObject.name).to.equal('My Object 1');
  });

});
