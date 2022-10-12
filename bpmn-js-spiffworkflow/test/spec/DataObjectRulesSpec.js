import { bootstrapPropertiesPanel } from './helpers';
import { BpmnPropertiesPanelModule, BpmnPropertiesProviderModule } from 'bpmn-js-properties-panel';
import dataObject from '../../app/spiffworkflow/DataObject';
import { inject } from 'bpmn-js/test/helper';

describe('BPMN Input / Output', function() {

  let xml = require('./bpmn/subprocess.bpmn').default;

  beforeEach(bootstrapPropertiesPanel(xml, {
    debounceInput: false,
    additionalModules: [
      dataObject,
      BpmnPropertiesPanelModule,
      BpmnPropertiesProviderModule,
    ]
  }));


  it('will prevent dragging data reference to a different process',
    inject(function(canvas, modeling, elementRegistry, dataObjectRules) {

      // IF - a data object reference exists on the root element, and a SubProcess Also Exists
      let rootShape = canvas.getRootElement();
      const dataObjectRefShape = modeling.createShape({ type: 'bpmn:DataObjectReference' },
        { x: 220, y: 220 }, rootShape);
      const subProcessElement = elementRegistry.get('my_subprocess');

      var canDrop = dataObjectRules.canDrop(
        [ dataObjectRefShape ],
        subProcessElement
      );

      expect(canDrop).to.be.false;

    }));
});
