import CommandInterceptor from 'diagram-js/lib/command/CommandInterceptor';
import { add as collectionAdd } from 'diagram-js/lib/util/Collections';
import { remove as collectionRemove } from 'diagram-js/lib/util/Collections';
import IdGenerator from 'diagram-js/lib/util/IdGenerator';
var HIGH_PRIORITY = 1500;

/**
 * This Command Interceptor functions like the BpmnUpdator in BPMN.js - It hooks into events
 * from Diagram.js and updates the underlying BPMN model accordingly.
 *
 * This handles the case where a new DataInput or DataOutput is added to
 * the diagram, it assures that a place exists for the new Data object to go, and it places it there.
 * There were a number of paces where I had to patch things in to get it to work correctly:
 *   * Create a InputOutputSpecification on the BPMN Moddle if it doesn't exist.
 *   * Correctly connect a new DI (display element in BPMN xml) for the input/output element.
 *   * Create a new DataInput/DataOutput Object (maybe incorrectly)
 * Also handles delete, where it removes the objects from the BPMN Moddle (both the actual input/output and the DI)
 * fixme:  Assure that we need to create a new DataInput object here, already in IoPalette's call to ElementFactory
 * fixme:  If all inputs and outputs are deleted, remove the InputOutputSpecification completely.
 */
export default class IoInterceptor extends CommandInterceptor {
  constructor(eventBus, bpmnFactory, bpmnUpdater) {
    super(eventBus);

    this.execute([ 'shape.create' ], HIGH_PRIORITY, function(event) {
      let context = event.context;
      if ([ 'bpmn:DataInput', 'bpmn:DataOutput' ].includes(context.shape.type)) {
        let type = context.shape.type;
        let type_name = type.split(':')[1];
        let process = context.parent.businessObject;
        let ioSpec = assureIOSpecificationExists(process, bpmnFactory);
        let di = context.shape.di;
        let generator = new IdGenerator(type_name);
        let dataIO = bpmnFactory.create(type, { id: generator.next() });
        context.shape.businessObject = dataIO;
        dataIO.$parent = ioSpec;
        di.businessObject = dataIO;
        di.bpmnElement = dataIO;
        di.id = dataIO.id + 'DI';
        bpmnUpdater.updateBounds(context.shape);

        if (type == 'bpmn:DataInput') {
          collectionAdd(ioSpec.inputSets[0].get('dataInputRefs'), dataIO);
          collectionAdd(ioSpec.get('dataInputs'), dataIO);
        } else {
          collectionAdd(ioSpec.outputSets[0].get('dataOutputRefs'), dataIO);
          collectionAdd(ioSpec.get('dataOutputs'), dataIO);
        }
      }
    });

    this.execute([ 'shape.delete' ], HIGH_PRIORITY, function(event) {
      let context = event.context;
      if ([ 'bpmn:DataInput', 'bpmn:DataOutput' ].includes(context.shape.type)) {
        let type = context.shape.type;
        let process = context.shape.parent.businessObject;
        let ioSpec = assureIOSpecificationExists(process, bpmnFactory);
        if (type == 'bpmn:DataInput') {
          collectionRemove(ioSpec.inputSets[0].get('dataInputRefs'), context.shape.businessObject);
          collectionRemove(ioSpec.get('dataInputs'), context.shape.businessObject);
        } else {
          collectionRemove(ioSpec.outputSets[0].get('dataOutputRefs'), context.shape.businessObject);
          collectionRemove(ioSpec.get('dataOutputs'), context.shape.businessObject);
        }
        if (context.shape.di.$parent) {
          collectionRemove(context.shape.di.$parent.planeElement, context.shape.di);
        }
        if (ioSpec.dataInputs.length === 0 && ioSpec.dataOutputs.length === 0) {
          process.ioSpecification = null;
        }
      }
    });

    // Stop propagation on executed, to avoid the BpmnUpdator.js from causing errors.
    this.executed([ 'shape.delete', 'shape.create' ], HIGH_PRIORITY, function(event) {
      if ([ 'bpmn:DataInput', 'bpmn:DataOutput' ].includes(event.context.shape.type)) {
        event.stopPropagation(); // Don't let the main code execute, it will fail.
      }
    });
  }
}

/**
 *       <bpmndi:BPMNShape id="dataInput_1" bpmnElement="ID_3">
 *         <dc:Bounds x="152" y="195" width="36" height="50" />
 *         <bpmndi:BPMNLabel>
 *           <dc:Bounds x="142" y="245" width="56" height="14" />
 *         </bpmndi:BPMNLabel>
 *       </bpmndi:BPMNShape>
 * @param process
 * @param bpmnFactory
 * @returns {bpmn:InputOutputSpecification}
 */

function assureIOSpecificationExists(process, bpmnFactory) {
  let ioSpecification = process.get('ioSpecification');

  if (!ioSpecification) {
    let inputSet = bpmnFactory.create('bpmn:InputSet');
    let outputSet = bpmnFactory.create('bpmn:OutputSet');

    // Create the BPMN
    ioSpecification = bpmnFactory.create('bpmn:InputOutputSpecification', {
      dataInputs: [],
      inputSets: [inputSet],
      dataOutputs: [],
      outputSets: [outputSet],
    });
    ioSpecification.$parent = process;
    process.ioSpecification = ioSpecification;
  }
  return ioSpecification;
}



IoInterceptor.$inject = [ 'eventBus', 'bpmnFactory', 'bpmnUpdater' ];

