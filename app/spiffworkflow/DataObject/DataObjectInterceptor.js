import CommandInterceptor from 'diagram-js/lib/command/CommandInterceptor';
import { is } from 'bpmn-js/lib/util/ModelUtil';
import { findDataObjects } from './DataObjectHelpers';
var HIGH_PRIORITY = 1500;

/**
 * This Command Interceptor functions like the BpmnUpdator in BPMN.js - It hooks into events
 * from Diagram.js and updates the underlying BPMN model accordingly.
 *
 * This handles some special cases we want to handle for DataObjects and DataObjectReferences,
 * for instance:
 * 1) Use existing data objects if possible when creating a new reference (don't create new objects each time)
 * 2) Don't automatically delete a data object when you delete the reference - unless all references are removed.
 * 3) Update the name of the DataObjectReference to match the id of the DataObject.
 * 4) Don't allow someone to move a DataObjectReference from one process to another process.
 */
export default class DataObjectInterceptor extends CommandInterceptor {
  constructor(eventBus, bpmnFactory, bpmnUpdater) {
    super(eventBus);

    /**
     * For DataObjectReferences only ...
     * Prevent this from calling the CreateDataObjectBehavior in BPMN-js, as it will
     * attempt to crete a dataObject immediately.  We can't create the dataObject until
     * we know where it is placed - as we want to reuse data objects of the parent when
     * possible */
    this.preExecute([ 'shape.create' ], HIGH_PRIORITY, function(event) {
      const context = event.context, shape = context.shape;
      if (is(shape, 'bpmn:DataObjectReference') && shape.type !== 'label') {
        event.stopPropagation();
      }
    });

    /**
     * Don't just create a new data object, use the first existing one if it already exists
     */
    this.executed([ 'shape.create' ], HIGH_PRIORITY, function(event) {
      const context = event.context, shape = context.shape;
      if (is(shape, 'bpmn:DataObjectReference') && shape.type !== 'label') {
        let process = shape.parent.businessObject;
        let existingDataObjects = findDataObjects(process);
        let dataObject;
        if (existingDataObjects.length > 0) {
          dataObject = existingDataObjects[0];
        } else {
          dataObject = bpmnFactory.create('bpmn:DataObject');
        }

        // Update the name of the reference to match the data object's id.
        shape.businessObject.name = dataObject.id;

        // set the reference to the DataObject
        shape.businessObject.dataObjectRef = dataObject;
      }
    });
  }
}

DataObjectInterceptor.$inject = [ 'eventBus', 'bpmnFactory', 'bpmnUpdater' ];
