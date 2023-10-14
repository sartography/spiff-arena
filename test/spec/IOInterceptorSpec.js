import { bootstrapPropertiesPanel } from './helpers';
import dataObjectInterceptor from '../../app/spiffworkflow/DataObject';
import { BpmnPropertiesPanelModule, BpmnPropertiesProviderModule } from 'bpmn-js-properties-panel';
import {
  inject,
} from 'bpmn-js/test/helper';
import { findDataObjects } from '../../app/spiffworkflow/DataObject/DataObjectHelpers';
import IoInterceptor from '../../app/spiffworkflow/InputOutput/IoInterceptor';
import InputOutput from '../../app/spiffworkflow/InputOutput';

describe('Input/Output Interceptor', function() {

  let xml = require('./bpmn/empty_diagram.bpmn').default;

  beforeEach(bootstrapPropertiesPanel(xml, {
    debounceInput: false,
    additionalModules: [
      InputOutput,
      BpmnPropertiesPanelModule,
      BpmnPropertiesProviderModule,
    ]
  }));

  it('New Data Input should create an IOSpecification with a single dataInput object', inject(function(canvas, modeling) {

    expect(canvas.getRootElement().businessObject.ioSpecification).to.be.undefined;

    // IF - a new dataObjectReference is created
    let rootShape = canvas.getRootElement();
    const dataInput = modeling.createShape({ type: 'bpmn:DataInput' },
      { x: 220, y: 220 }, rootShape);

    // THEN - the process should now have an IO Specification
    const iospec = canvas.getRootElement().businessObject.ioSpecification;
    expect(iospec).to.not.be.null;
    expect(iospec.dataInputs.length).to.equal(1);
    expect(iospec.inputSets[0].dataInputRefs.length).to.equal(1);
  }));


  it('IOSpecification always contain input sets and output sets if they exist at all.', inject(function(canvas, modeling) {

    expect(canvas.getRootElement().businessObject.ioSpecification).to.be.undefined;

    // IF - a new dataObjectReference is created
    let rootShape = canvas.getRootElement();
    const dataInput = modeling.createShape({type: 'bpmn:DataInput'},
      {x: 220, y: 220}, rootShape);

    // THEN - there are inputSets and outputSets
    const iospec = canvas.getRootElement().businessObject.ioSpecification;
    expect(iospec.inputSets).to.not.be.null;
    expect(iospec.outputSets).to.not.be.null;
  }));

    it('After removing all input sets, the ioSpecification should be null.', inject(function(canvas, modeling) {
    // IF - a new dataObjectReference is created and then deleted.
    let rootShape = canvas.getRootElement();
    const dataInput = modeling.createShape({type: 'bpmn:DataInput'},
      {x: 220, y: 220}, rootShape);
    modeling.removeShape(dataInput)
    expect(canvas.getRootElement().businessObject.ioSpecification).to.be.null;
  }));

  it('deleting a data input should remove it from the input set', inject(function(canvas, modeling) {
    let rootShape = canvas.getRootElement();
    const dataInput = modeling.createShape({type: 'bpmn:DataInput'},
      {x: 220, y: 220}, rootShape);
    const dataOutput = modeling.createShape({type: 'bpmn:DataOutput'},
      {x: 240, y: 220}, rootShape);
    modeling.removeShape(dataInput);
    const iospec = canvas.getRootElement().businessObject.ioSpecification;
    expect(iospec.dataInputs.length).to.equal(0);
    expect(iospec.inputSets[0].dataInputRefs.length).to.equal(0);
  }));
});
