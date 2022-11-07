import TestContainer from 'mocha-test-container-support';
import {
  BpmnPropertiesPanelModule,
  BpmnPropertiesProviderModule,
} from 'bpmn-js-properties-panel';
import { query as domQuery } from 'min-dom';
import { getBusinessObject } from 'bpmn-js/lib/util/ModelUtil';
import { inject } from 'bpmn-js/test/helper';
import {
  bootstrapPropertiesPanel,
  changeInput,
  expectSelected, findButton,
  findGroupEntry, pressButton,
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

  /** fixme: Reenable this when we add this button back in.
  it('should issue an event to the event bus if user clicks the edit button', inject(
      async function(eventBus) {
    const shapeElement = await expectSelected('the_call_activity');
    expect(shapeElement, "Can't find Call Activity").to.exist;
    const businessObject = getBusinessObject(shapeElement);
    expect(businessObject.get('calledElement')).to.equal('ProcessIdTBD1');

    const entry = findGroupEntry('called_element', container);
    const button = findButton('spiffworkflow-open-call-activity-button', entry);
    expect(button).to.exist;

    let launchEvent;
    eventBus.on('spiff.callactivity.edit', function (event) {
      launchEvent = event;
    });
    await pressButton(button);
    expect(launchEvent.processId).to.exist;
  }));
  */
});
