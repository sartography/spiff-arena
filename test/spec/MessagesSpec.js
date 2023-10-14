import TestContainer from 'mocha-test-container-support';
import {
  BpmnPropertiesPanelModule,
  BpmnPropertiesProviderModule,
} from 'bpmn-js-properties-panel';
import {
  bootstrapPropertiesPanel,
  expectSelected,
  findEntry,
  findGroupEntry,
  // findInput,
  findSelect,
  findTextarea,
  // findButtonByClass,
  // pressButton,
  // findDivByClass,
} from './helpers';
import spiffModdleExtension from '../../app/spiffworkflow/moddle/spiffworkflow.json';
import messages from '../../app/spiffworkflow/messages';

describe('Messages should work', function () {
  const xml = require('./bpmn/collaboration.bpmn').default;
  let container;

  beforeEach(function () {
    container = TestContainer.get(this);
  });

  beforeEach(
    bootstrapPropertiesPanel(xml, {
      container,
      debounceInput: false,
      additionalModules: [
        messages,
        BpmnPropertiesPanelModule,
        BpmnPropertiesProviderModule,
      ],
      moddleExtensions: {
        spiffworkflow: spiffModdleExtension,
      },
    })
  );

  it('should allow you to see the collaborations section', async function () {
    // THEN - a select Data Object section should appear in the properties panel
    const entry = findGroupEntry('correlation_keys', container);
    expect(entry).to.exist;
    await expectSelected('my_collaboration');
  });

  it('should show a Message Properties group when a send task is selected', async function () {
    // Select the send Task
    const sendShape = await expectSelected('ActivitySendLetter');
    expect(sendShape, "Can't find Send Task").to.exist;

    // THEN - a select Data Object section should appear in the properties panel
    const entry = findGroupEntry('messages', container);
    expect(entry, "Can't find the message group in the properties panel").to
      .exist;
    await expectSelected('my_collaboration');
  });

  it('should show a list of messages in a drop down inside the message group', async function () {
    // Select the send Task
    const sendShape = await expectSelected('ActivitySendLetter');
    expect(sendShape, "Can't find Send Task").to.exist;

    // THEN - there are two options to choose from.
    const entry = findEntry('selectMessage', container);
    expect(entry, "Can't find the message select list").to.exist;

    // AND - There should be two entries in it, one for each message.
    const selector = findSelect(entry);
    expect(selector).to.exist;
    expect(selector.length).to.equal(2);
    await expectSelected('my_collaboration');
  });

  it('should show the payload inside the message group', async function () {
    // Select the second Task
    const sendShape = await expectSelected('ActivitySendLetter');
    expect(sendShape, "Can't find Send Task").to.exist;
    
    // THEN - there is a payload.
    const payload = findEntry('messagePayload', container);
    expect(payload, "Can't find the message payload").to.exist;

    const textArea = findTextarea(
      'bio-properties-panel-messagePayload',
      payload
    );
    expect(textArea, "Can't find the payload textarea").to.exist;
    expect(textArea.value, "Can't find payload value").to.exist;
    expect(textArea.value).to.include("'to': { 'name': my_lover_variable }");
    await expectSelected('my_collaboration');
  });

  it('should show the correlations inside the message group', async function () {
    // Select the second Task
    const sendShape = await expectSelected('ActivitySendLetter');
    expect(sendShape, "Can't find Send Task").to.exist;

    // THEN - there are correlations.
    const correlations = findGroupEntry('correlationProperties', container);
    expect(correlations, "Can't find the message correlations").to.exist;
    await expectSelected('my_collaboration');
  });

  // it('should add a new correlation when clicked', async function () {
  //   // Select the second Task
  //   const sendShape = await expectSelected('ActivitySendLetter');
  //   expect(sendShape, "Can't find Send Task").to.exist;
  //
  //   const buttonClass =
  //     'bio-properties-panel-group-header-button bio-properties-panel-add-entry';
  //   const button = findButtonByClass(buttonClass, container);
  //   pressButton(button);
  //
  // });
  //
  // it('should add a new Correlation Key when clicked', async function () {
  //   const divClass = 'bio-properties-panel-list';
  //   const divs = findDivByClass(divClass, container);
  //
  //   const buttonClass =
  //     'bio-properties-panel-group-header-button bio-properties-panel-add-entry';
  //   const button = findButtonByClass(buttonClass, container);
  //   pressButton(button);
  //
  //   // THEN - a select Data Object section should appear in the properties panel
  //   const entry = findGroupEntry('correlation_keys', container);
  //   expect(entry).to.exist;
  //
  //   const divs2 = findDivByClass(divClass, container);
  // });
});
