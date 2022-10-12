import {
  query as domQuery,
} from 'min-dom';
import {
  bootstrapPropertiesPanel, changeInput,
  expectSelected, findEntry, findGroupEntry, findInput
} from './helpers';
import { BpmnPropertiesPanelModule, BpmnPropertiesProviderModule } from 'bpmn-js-properties-panel';
import spiffModdleExtension from '../../app/spiffworkflow/moddle/spiffworkflow.json';
import TestContainer from 'mocha-test-container-support';
import { fireEvent } from '@testing-library/preact';
import { findDataObject, findDataObjects } from '../../app/spiffworkflow/DataObject/DataObjectHelpers';
import dataObject from '../../app/spiffworkflow/DataObject';

describe('Properties Panel for a Process', function() {
  let xml = require('./bpmn/diagram.bpmn').default;
  let container;

  beforeEach(function() {
    container = TestContainer.get(this);
  });

  beforeEach(bootstrapPropertiesPanel(xml, {
    container,
    debounceInput: false,
    additionalModules: [
      dataObject,
      BpmnPropertiesPanelModule,
      BpmnPropertiesProviderModule,
    ],
    moddleExtensions: {
      spiffworkflow: spiffModdleExtension
    },
  }));

  it('should allow you to edit the data objects', async function() {

    // IF - a process is selected
    await expectSelected('ProcessTest');

    // THEN - there is a section where you can modify data objects.
    let entry = findGroupEntry('editDataObjects', container);
    expect(entry).to.exist;
  });

  it('should be possible to change a data objects id', async function() {

    // IF - a process is selected and the id of a data object is changed
    const process_svg = await expectSelected('ProcessTest');

    let newId = 'a_brand_new_id';

    // ID here is [process id]-dataObj-[data object index]-id
    let myDataObjEntry = findEntry('ProcessTest-dataObj-0-id');
    let textBox = findInput('text', myDataObjEntry);
    changeInput(textBox, newId);

    // THEN - there is a section where you can modify data objects.
    let dataObject = findDataObject(process_svg.businessObject, newId);
    expect(dataObject.id).to.equal(newId);
  });

  it('should be possible to remove a data object', async function() {

    // IF - a process is selected and the delete button is clicked.
    const process_svg = await expectSelected('ProcessTest');
    const data_id = 'my_data_object';
    let dataObject = findDataObject(process_svg.businessObject, data_id);
    expect(dataObject).to.exist;
    let myDataObjEntry = findEntry('ProcessTest-dataObj-2');
    let deleteButton = domQuery('.bio-properties-panel-remove-entry', myDataObjEntry);
    fireEvent.click(deleteButton);

    // THEN - there should not be a 'my_data_object' anymore.
    dataObject = findDataObject(process_svg.businessObject, data_id);
    expect(dataObject).to.not.exist;

  });

  it('should be possible to add a data object', async function() {

    // IF - a process is selected and the add button is clicked.
    const process_svg = await expectSelected('ProcessTest');
    let entry = findGroupEntry('editDataObjects', container);
    let addButton = domQuery('.bio-properties-panel-add-entry', entry);
    fireEvent.click(addButton);

    // THEN - there should now be 4 data objects instead of just 3.
    expect(findDataObjects(process_svg.businessObject).length).to.equal(4);

  });


});
