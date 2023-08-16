import {
  BpmnPropertiesPanelModule,
  BpmnPropertiesProviderModule,
} from 'bpmn-js-properties-panel';
import TestContainer from 'mocha-test-container-support';
import {
  bootstrapPropertiesPanel,
  changeInput,
  expectSelected,
  findEntry,
  findSelect,
} from './helpers';
import spiffModdleExtension from '../../app/spiffworkflow/moddle/spiffworkflow.json';
import DataObject from '../../app/spiffworkflow/DataObject';

describe('Properties Panel for Data Objects', function () {
  const xml = require('./bpmn/data_objects_in_pools.bpmn').default;
  let container;

  beforeEach(function () {
    container = TestContainer.get(this);
  });

  beforeEach(
    bootstrapPropertiesPanel(xml, {
      container,
      debounceInput: false,
      additionalModules: [
        DataObject,
        BpmnPropertiesPanelModule,
        BpmnPropertiesProviderModule,
      ],
      moddleExtensions: {
        spiffworkflow: spiffModdleExtension,
      },
    })
  );

  it('should allow you to select other data objects within the same participant', async function () {
    // IF - a data object reference is selected
    const doREF = await expectSelected('pool1Do1_REF');
    expect(doREF).to.exist;

    // THEN - a select Data Object section should appear in the properties panel
    const entry = findEntry('selectDataObject', container);
    const selector = findSelect(entry);
    changeInput(selector, 'pool1Do2');
    // then this data reference object now references that data object.
    const { businessObject } = doREF;
    expect(businessObject.get('dataObjectRef').id).to.equal('pool1Do2');
  });

  it('should NOT allow you to select data objects within other participants', async function () {
    // IF - a data object reference is selected
    const doREF = await expectSelected('pool1Do1_REF');
    expect(doREF).to.exist;

    // THEN - a select Data Object section should appear in the properties panel but pool2Do1 should not be an option
    const entry = findEntry('selectDataObject', container);
    const selector = findSelect(entry);
    expect(selector.length).to.equal(2);
    expect(selector[0].value === 'pool1Do2');
    expect(selector[1].value === 'pool1Do1');
  });

});
