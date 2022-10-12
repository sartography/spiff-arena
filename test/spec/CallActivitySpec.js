import TestContainer from 'mocha-test-container-support';
import {
  BpmnPropertiesPanelModule,
  BpmnPropertiesProviderModule,
} from 'bpmn-js-properties-panel';
import { query as domQuery } from 'min-dom';
import { getBusinessObject } from 'bpmn-js/lib/util/ModelUtil';
import {
  bootstrapPropertiesPanel,
  changeInput,
  expectSelected,
  findGroupEntry,
} from './helpers';
import spiffModdleExtension from '../../app/spiffworkflow/moddle/spiffworkflow.json';
import callActivity from '../../app/spiffworkflow/callActivity';

describe('Call Activities should work', function () {
  const xml = require('./bpmn/call_activity.bpmn').default;
  let container;

  beforeEach(function () {
    container = TestContainer.get(this);
  });

  beforeEach(
    bootstrapPropertiesPanel(xml, {
      container,
      debounceInput: false,
      additionalModules: [
        callActivity,
        BpmnPropertiesPanelModule,
        BpmnPropertiesProviderModule,
      ],
      moddleExtensions: {
        spiffworkflow: spiffModdleExtension,
      },
    })
  );

  it('should allow you to view the called element section of a Call Activity', async function () {
    const shapeElement = await expectSelected('the_call_activity');
    expect(shapeElement, "Can't find Call Activity").to.exist;
    const entry = findGroupEntry('called_element', container);
    expect(entry).to.exist;
  });

  it('should allow you to edit the called element section of a Call Activity', async function () {
    const shapeElement = await expectSelected('the_call_activity');
    expect(shapeElement, "Can't find Call Activity").to.exist;
    const businessObject = getBusinessObject(shapeElement);
    expect(businessObject.get('calledElement')).to.equal('ProcessIdTBD1');

    const entry = findGroupEntry('called_element', container);
    expect(entry).to.exist;

    const textInput = domQuery('input', entry);
    changeInput(textInput, 'newProcessId');
    expect(businessObject.get('calledElement')).to.equal('newProcessId');
  });
});
