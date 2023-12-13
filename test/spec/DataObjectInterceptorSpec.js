import { bootstrapPropertiesPanel } from './helpers';
import dataObjectInterceptor from '../../app/spiffworkflow/DataObject';
import { BpmnPropertiesPanelModule, BpmnPropertiesProviderModule } from 'bpmn-js-properties-panel';
import {
  inject,
} from 'bpmn-js/test/helper';
import {
  findDataObjects,
  findDataObjectReferenceShapes,
  idToHumanReadableName,
} from '../../app/spiffworkflow/DataObject/DataObjectHelpers';

describe('DataObject Interceptor', function () {

  let xml = require('./bpmn/empty_diagram.bpmn').default;

  beforeEach(bootstrapPropertiesPanel(xml, {
    debounceInput: false,
    additionalModules: [
      dataObjectInterceptor,
      BpmnPropertiesPanelModule,
      BpmnPropertiesProviderModule,
    ]
  }));

  it('New Data Object References should create a data object if none exist.', inject(function (canvas, modeling) {

    // IF - a new dataObjectReference is created
    let rootShape = canvas.getRootElement();
    const dataObjectRefShape1 = modeling.createShape({ type: 'bpmn:DataObjectReference' },
      { x: 220, y: 220 }, rootShape);

    // THEN - a new DataObject is also created.
    const dataObjects = findDataObjects(rootShape.businessObject);
    expect(dataObjects.length).to.equal(1);
    expect(dataObjects[0]).to.equal(dataObjectRefShape1.businessObject.dataObjectRef);

  }));

  it('New Data Object References should connect to the first available data Object if it exists', inject(function (canvas, modeling) {

    // IF - two dataObjectReferences are created
    let rootShape = canvas.getRootElement();
    const dataObjectRefShape1 = modeling.createShape({ type: 'bpmn:DataObjectReference' },
      { x: 220, y: 220 }, rootShape);
    const dataObjectRefShape2 = modeling.createShape({ type: 'bpmn:DataObjectReference' },
      { x: 320, y: 220 }, rootShape);

    // THEN - only one new DataObject is created, and both references point to it..
    const dataObjects = findDataObjects(rootShape.businessObject);
    expect(dataObjects.length).to.equal(1);
    expect(dataObjects[0]).to.equal(dataObjectRefShape1.businessObject.dataObjectRef);
    expect(dataObjects[0]).to.equal(dataObjectRefShape2.businessObject.dataObjectRef);

  }));

  it('Deleting a data object reference does not delete the data object, unless it is the last reference', inject(function (canvas, modeling) {

    // IF - two dataObjectReferences are created
    let rootShape = canvas.getRootElement();
    const dataObjectRefShape1 = modeling.createShape({ type: 'bpmn:DataObjectReference' },
      { x: 220, y: 220 }, rootShape);
    const dataObjectRefShape2 = modeling.createShape({ type: 'bpmn:DataObjectReference' },
      { x: 320, y: 220 }, rootShape);

    // AND one is deleted
    modeling.removeShape(dataObjectRefShape1)

    // THEN - there is still a data object
    const dataObjects = findDataObjects(rootShape.businessObject);
    expect(dataObjects.length).to.equal(1);
  }));

  it('Deleting all the data references will also delete the data object', inject(function (canvas, modeling) {

    // IF - two dataObjectReferences are created
    let rootShape = canvas.getRootElement();
    const dataObjectRefShape1 = modeling.createShape({ type: 'bpmn:DataObjectReference' },
      { x: 220, y: 220 }, rootShape);
    const dataObjectRefShape2 = modeling.createShape({ type: 'bpmn:DataObjectReference' },
      { x: 320, y: 220 }, rootShape);

    // AND both are deleted
    modeling.removeShape(dataObjectRefShape1);
    modeling.removeShape(dataObjectRefShape2);

    // THEN - there is no data object
    const dataObjects = findDataObjects(rootShape.businessObject);
    expect(dataObjects.length).to.equal(0);
  }));

  it('Creating a new Reference will update the name to match the DataObject', inject(function (canvas, modeling) {

    // IF - a Data Reference Exists
    let rootShape = canvas.getRootElement();
    const dataObjectRefShape1 = modeling.createShape({ type: 'bpmn:DataObjectReference' },
      { x: 220, y: 220 }, rootShape);

    const dataObjects = findDataObjects(rootShape.businessObject);
    const human_readable_name = idToHumanReadableName(dataObjects[0].id)
    expect(dataObjectRefShape1.businessObject.name).to.equal(human_readable_name);
  }));

  it('should allow you to add a data object to a subprocess', inject(function (canvas, modeling, elementRegistry) {

    // IF - A data object reference is added to a sup-process
    let subProcessShape = elementRegistry.get('my_subprocess');
    let subProcess = subProcessShape.businessObject;
    let dataObjects = findDataObjects(subProcess);
    expect(dataObjects.length).to.equal(0);

    const dataObjectRefShape = modeling.createShape({ type: 'bpmn:DataObjectReference' },
      { x: 220, y: 220 }, subProcessShape);

    // THEN - a new data object is visible in that SubProcess
    dataObjects = findDataObjects(subProcess);
    expect(dataObjects.length).to.equal(1);
  }));

  it('Data objects in a process should be visible in a subprocess', inject(function (canvas, modeling, elementRegistry) {

    let subProcessShape = elementRegistry.get('my_subprocess');
    let subProcess = subProcessShape.businessObject;
    let dataObjects = findDataObjects(subProcess);
    expect(dataObjects.length).to.equal(0);

    let rootShape = canvas.getRootElement();
    const dataObjectRefShape = modeling.createShape({ type: 'bpmn:DataObjectReference' },
      { x: 220, y: 220 }, rootShape);

    dataObjects = findDataObjects(subProcess);
    expect(dataObjects.length).to.equal(1);
  }));

  it('Data objects in a subprocess should not be visible in a process', inject(function (canvas, modeling, elementRegistry) {

    let subProcessShape = elementRegistry.get('my_subprocess');
    let subProcess = subProcessShape.businessObject;
    const dataObjectRefShape = modeling.createShape({ type: 'bpmn:DataObjectReference' },
      { x: 220, y: 220 }, subProcessShape);

    let dataObjects = findDataObjects(subProcess);
    expect(dataObjects.length).to.equal(1);

    let rootShape = canvas.getRootElement();
    dataObjects = findDataObjects(rootShape);
    expect(dataObjects.length).to.equal(0);
  }));

  it('References inside subprocesses should be visible in a process', inject(function (canvas, modeling, elementRegistry) {

    let rootShape = canvas.getRootElement();
    const refOne = modeling.createShape({ type: 'bpmn:DataObjectReference' },
      { x: 220, y: 220 }, rootShape);

    let subProcessShape = elementRegistry.get('my_subprocess');
    let subProcess = subProcessShape.businessObject;
    const refTwo = modeling.createShape({ type: 'bpmn:DataObjectReference' },
      { x: 320, y: 220 }, subProcessShape);

    let dataObjects = findDataObjects(subProcess);
    expect(dataObjects.length).to.equal(1);
    let references = findDataObjectReferenceShapes(rootShape.children, dataObjects[0].id);
    expect(references.length).to.equal(2);

  }));

});
