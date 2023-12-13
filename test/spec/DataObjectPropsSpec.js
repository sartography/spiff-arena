import {
  bootstrapPropertiesPanel,
  changeInput,
  expectSelected,
  findEntry,
  findInput,
  findSelect
} from './helpers';

import {
  inject,
} from 'bpmn-js/test/helper';

import {
  BpmnPropertiesPanelModule,
  BpmnPropertiesProviderModule
} from 'bpmn-js-properties-panel';

import spiffModdleExtension from '../../app/spiffworkflow/moddle/spiffworkflow.json';
import TestContainer from 'mocha-test-container-support';
import DataObject from '../../app/spiffworkflow/DataObject';

describe('Properties Panel for Data Objects', function () {
  let xml = require('./bpmn/diagram.bpmn').default;
  let container;

  beforeEach(function () {
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

  it('should allow you to see a list of data objects', async function () {

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

  it('selecting a different data object should change the data model.', async function () {

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

  // Notice: Test Case for Data Object ID Changes No Longer Required
  // With our new feature implementation, changing a Data Object ID is now independent of altering 
  // its Data Reference Name. This decoupling eliminates the need for the specific test case previously required for these changes.
  // it('renaming a data object, changes to the label of references', async function() {

  //   // IF - a process is selected, and the name of a data object is changed.
  //   let entry = findEntry('ProcessTest-dataObj-2-id', container);
  //   let textInput = findInput('text', entry);
  //   changeInput(textInput, 'my_nifty_new_name');
  //   let my_data_ref_1 = await expectSelected('my_data_ref_1');

  //   // THEN - both the data object itself, and the label of any references are updated.
  //   expect(my_data_ref_1.businessObject.dataObjectRef.id).to.equal('my_nifty_new_name');
  //   expect(my_data_ref_1.businessObject.name).to.equal('My Nifty New Name');
  // });

  it('renaming a data object creates a lable without losing the numbers', async function () {

    // IF - a process is selected, and the name of a data object is changed.
    let entry = findEntry('ProcessTest-dataObj-2-id', container);
    let textInput = findInput('text', entry);
    changeInput(textInput, 'MyObject1');
    let my_data_ref_1 = await expectSelected('my_data_ref_1');

    // THEN - both the data object itself, and the label of any references are updated.
    expect(my_data_ref_1.businessObject.dataObjectRef.id).to.equal('MyObject1');
    // Notice: Test Case for Data Object ID Changes No Longer Required
    // expect(my_data_ref_1.businessObject.name).to.equal('My Object 1');
  });

  it('renaming a data object ID, does not change the label of references', async function () {
    // IF - a process is selected, and the name of a data object is changed.
    let entry = findEntry('ProcessTest-dataObj-2-id', container);
    let textInput = findInput('text', entry);
    changeInput(textInput, 'my_nifty_new_name');
    let my_data_ref_1 = await expectSelected('my_data_ref_1');
    // THEN - both the data object itself, and the label of any references are updated.
    expect(my_data_ref_1.businessObject.dataObjectRef.id).to.equal('my_nifty_new_name');
    expect(my_data_ref_1.businessObject.name).not.to.equal('My Nifty New Name');
  });

  it('renaming a data object name, does change the label of references', async function () {

    let entry = findEntry('ProcessTest-dataObj-2-name', container);
    let textInput = findInput('text', entry);
    let newDataObjectName = 'A New Data Object Name';
    
    changeInput(textInput, newDataObjectName);

    let my_data_ref_1 = await expectSelected('my_data_ref_1');
    let my_data_ref_2 = await expectSelected('my_data_ref_2');
   
    // THEN - the label of any references are updated.
    expect(my_data_ref_1.businessObject.name).to.equal(newDataObjectName);
    expect(my_data_ref_2.businessObject.name).to.equal(newDataObjectName);

    // Test References with DataState
    let my_data_ref_3 = await expectSelected('my_data_ref_3');
    let my_data_ref_3_DataState = my_data_ref_3.businessObject.dataState.name;

    expect(my_data_ref_3.businessObject.name).to.equal(`${newDataObjectName} [${my_data_ref_3_DataState}]`);
  });

  it('renaming a data object reference state, does change the label its reference', async function () {

    let my_data_ref_1 = await expectSelected('my_data_ref_1');
    let dtObjCurrentName = my_data_ref_1.businessObject.name;
    let entry = findEntry('selectDataState-textField', container);
    let idInput = findInput('text', entry);
    let nwState = "New State";

    // Change Data State
    changeInput(idInput, nwState);

    // Expect new DataObjectRef Name to be like 'DataObjectRefName [DataState]'
    expect(my_data_ref_1.businessObject.name).to.equal(`${dtObjCurrentName} [${nwState}]`);
    expect(my_data_ref_1.businessObject.name).not.to.equal(dtObjCurrentName);
  });

  it('selecting a different data object should not change the data object reference name.', async function () {

    // IF - a data object reference is selected
    let my_data_ref_1 = await expectSelected('my_data_ref_1');

    let entry = findEntry('selectDataObject', container);
    let selector = findSelect(entry);
    let businessObject = my_data_ref_1.businessObject;

    changeInput(selector, 'my_third_data_object');

    expect(businessObject.get('dataObjectRef').id).to.equal('my_third_data_object');
    expect(businessObject.name).to.equal('D3');
    expect(businessObject.name).not.to.equal('my_data_object');
  });

  it('should not allow two dataObjects to have the same ID', inject(async function (canvas, modeling) {

    // Creating the first dataObject
    let rootShape = canvas.getRootElement();
    const dataObject1 = modeling.createShape({ type: 'bpmn:DataObject' },
      { x: 100, y: 100 }, rootShape);

    // Creating the second dataObject
    const dataObject2 = modeling.createShape({ type: 'bpmn:DataObject' },
      { x: 150, y: 100 }, rootShape);

    await expectSelected(dataObject2.id);

    let entry = findEntry('dataObjectId', container);
    let idInput = findInput('text', entry);

    const duplicateId = dataObject1.businessObject.id;
    changeInput(idInput, duplicateId);

    // Check that the ID change is not successful
    expect(dataObject2.businessObject.id).not.to.equal(duplicateId);

  }));

});
