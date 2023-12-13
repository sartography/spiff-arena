import {
  query as domQuery,
  queryAll as domQueryAll
} from 'min-dom';
import {
  bootstrapPropertiesPanel,
  expectSelected,
  findGroupEntry,
  changeInput,
  PROPERTIES_PANEL_CONTAINER,
} from './helpers';
import conditionsPanel from '../../app/spiffworkflow/conditions';
import { BpmnPropertiesPanelModule, BpmnPropertiesProviderModule } from 'bpmn-js-properties-panel';
import { getBusinessObject } from 'bpmn-js/lib/util/ModelUtil';

describe('BPMN Condition', function() {

  let xml = require('./bpmn/conditional_event.bpmn').default;

  beforeEach(bootstrapPropertiesPanel(xml, {
    debounceInput: false,
    additionalModules: [
      conditionsPanel,
      BpmnPropertiesPanelModule,
      BpmnPropertiesProviderModule,
    ]
  }));

  it('should add a condition panel when Conditional Event is selected', async function() {
    const shapeElement = await expectSelected('conditional_event');
    const businessObject = getBusinessObject(shapeElement);
    const conditions = findGroupEntry('conditions', PROPERTIES_PANEL_CONTAINER);
    expect(conditions).to.exist;

    const textInput = domQuery('textarea', conditions);
    expect(textInput.value).to.equal('cancel_task_2');
    changeInput(textInput, 'True');
  });
});

