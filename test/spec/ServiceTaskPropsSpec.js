import {
  BpmnPropertiesPanelModule,
  BpmnPropertiesProviderModule,
} from 'bpmn-js-properties-panel';
import { getBusinessObject } from 'bpmn-js/lib/util/ModelUtil';
import TestContainer from 'mocha-test-container-support';
import { getBpmnJS } from 'bpmn-js/test/helper';
import spiffModdleExtension from '../../app/spiffworkflow/moddle/spiffworkflow.json';
import {
  bootstrapPropertiesPanel,
  changeInput,
  expectSelected,
  findEntry,
  findGroupEntry,
  findInput, findSelect,
} from './helpers';
import extensions from '../../app/spiffworkflow/extensions';

describe('Properties Panel for Service Tasks', function () {
  const diagramXml = require('./bpmn/service.bpmn').default;
  let container;

  beforeEach(function () {
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
        spiffworkflow: spiffModdleExtension,
      },
    });
  }

  function addServicesToModeler(bpmnModeler) {
    /**
     * This will inject available services into the modeler which should be
     * available as a dropdown list when selecting which service you want to call.
     *
     */
    bpmnModeler.on('spiff.service_tasks.requested', (event) => {
      event.eventBus.fire('spiff.service_tasks.returned', {
        serviceTaskOperators: [
          {
            id: 'ExampleService',
            parameters: [
              {
                id: 'name',
                type: 'string',
              },
            ],
          },
          {
            id: 'ExampleService2',
            parameters: [
              {
                id: 'number',
                type: 'integer',
              },
            ],
          },
        ],
      });
    });
  }

  it('should display a panel for selecting service', async function () {
    await preparePropertiesPanelWithXml(diagramXml)();

    const modeler = getBpmnJS();
    addServicesToModeler(modeler);

    // IF - you select a service task
    const serviceTask = await expectSelected('my_service_task');
    expect(serviceTask).to.exist;

    // THEN - a property panel exists with a section for editing web forms
    const group = findGroupEntry('service_task_properties', container);
    expect(group).to.exist;
  });

  it('should display a list of services to select from.', async function () {
    await preparePropertiesPanelWithXml(diagramXml)();
    const modeler = getBpmnJS();
    addServicesToModeler(modeler);

    // IF - you select a service task
    const serviceTask = await expectSelected('my_service_task');
    const group = findGroupEntry('service_task_properties', container);
    const entry = findEntry('selectOperatorId', group)

    // THEN - a select list appears and is populated by a list of known services
    const selectList = findSelect(entry);
    expect(selectList).to.exist;
    expect(selectList.options.length).to.equal(2)
    expect(selectList.options[0].label).to.equal('ExampleService')
    expect(selectList.options[1].label).to.equal('ExampleService2')
  });



});
