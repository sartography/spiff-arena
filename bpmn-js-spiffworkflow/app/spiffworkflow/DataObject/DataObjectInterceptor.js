import CommandInterceptor from 'diagram-js/lib/command/CommandInterceptor';
import { getDi, is } from 'bpmn-js/lib/util/ModelUtil';
import { remove as collectionRemove } from 'diagram-js/lib/util/Collections';
import {
  findDataObjects,
  findDataObjectReferences,
  idToHumanReadableName,
} from './DataObjectHelpers';

const HIGH_PRIORITY = 1500;

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

  constructor(eventBus, bpmnFactory, commandStack, bpmnUpdater) {
    super(eventBus);

    /* The default behavior is to move the data object into whatever object the reference is being created in.
     * If a data object already has a parent, don't change it.
     */
    bpmnUpdater.updateSemanticParent = (businessObject, parentBusinessObject) => {
      // Special case for participant - which is a valid place to drop a data object, but it needs to be added
      // to the particpant's Process (which isn't directly accessible in BPMN.io
      let realParent = parentBusinessObject;
      if (is(realParent, 'bpmn:Participant')) {
        realParent = realParent.processRef;
      }

      if (is(businessObject, 'bpmn:DataObjectReference')) {
        // For data object references, always update the flowElements when a parent is provided
        // The parent could be null if it's being deleted, and I could probably handle that here instead of
        // when the shape is deleted, but not interested in refactoring at the moment.
        if (realParent != null) {
          const flowElements = realParent.get('flowElements');
          const existingElement = flowElements.find(i => i.id === 1);
          if (!existingElement) {
            flowElements.push(businessObject);
          }
        }
      } else if (is(businessObject, 'bpmn:DataObject')) {
        // For data objects, only update the flowElements for new data objects, and set the parent so it doesn't get moved.
        if (typeof (businessObject.$parent) === 'undefined') {
          const flowElements = realParent.get('flowElements');
          flowElements.push(businessObject);
          businessObject.$parent = realParent;
        }
      } else {
        bpmnUpdater.__proto__.updateSemanticParent.call(bpmnUpdater, businessObject, parentBusinessObject);
      }
    };

    /**
     * For DataObjectReferences only ...
     * Prevent this from calling the CreateDataObjectBehavior in BPMN-js, as it will
     * attempt to crete a dataObject immediately.  We can't create the dataObject until
     * we know where it is placed - as we want to reuse data objects of the parent when
     * possible */
    this.preExecute(['shape.create'], HIGH_PRIORITY, function (event) {
      const { context } = event;
      const { shape } = context;
      if (is(shape, 'bpmn:DataObjectReference') && shape.type !== 'label') {
        event.stopPropagation();
      }
    });

    /**
     * Don't just create a new data object, use the first existing one if it already exists
     */
    this.executed(['shape.create'], HIGH_PRIORITY, function (event) {
      const { context } = event;
      const { shape } = context;
      if (is(shape, 'bpmn:DataObjectReference') && shape.type !== 'label') {
        const process = shape.parent.businessObject;
        const existingDataObjects = findDataObjects(process);
        let dataObject;
        if (existingDataObjects.length > 0) {
          dataObject = existingDataObjects[0];
        } else {
          dataObject = bpmnFactory.create('bpmn:DataObject');
        }
        // set the reference to the DataObject
        shape.businessObject.dataObjectRef = dataObject;
        shape.businessObject.$parent = process;
      }
    });

    /**
     * In order for the label to display correctly, we need to update it in POST step.
     */
    this.postExecuted(['shape.create'], HIGH_PRIORITY, function (event) {
      const { context } = event;
      const { shape } = context;
      // set the reference to the DataObject
      // Update the name of the reference to match the data object's id.
      if (is(shape, 'bpmn:DataObjectReference') && shape.type !== 'label') {
        commandStack.execute('element.updateProperties', {
          element: shape,
          moddleElement: shape.businessObject,
          properties: {
            name: idToHumanReadableName(shape.businessObject.dataObjectRef.id),
          },
        });
      }
    });

    /**
     * Don't remove the associated DataObject, unless all references to that data object
     * Difficult to do given placement of this logic in the BPMN Updater, so we have
     * to manually handle the removal.
     */
    this.executed(['shape.delete'], HIGH_PRIORITY, function (event) {
      const { context } = event;
      const { shape } = context;
      if (is(shape, 'bpmn:DataObjectReference') && shape.type !== 'label') {
        const dataObject = shape.businessObject.dataObjectRef;
        let parent = shape.businessObject.$parent;
        if (parent.processRef) {
          // Our immediate parent may be a pool, so we need to get the process
          parent = parent.processRef;
        }
        const flowElements = parent.get('flowElements');
        collectionRemove(flowElements, shape.businessObject);
        const references = findDataObjectReferences(flowElements, dataObject.id);
        if (references.length === 0) {
          const dataFlowElements = dataObject.$parent.get('flowElements');
          collectionRemove(dataFlowElements, dataObject);
        }
      }
    });
  }
}

DataObjectInterceptor.$inject = ['eventBus', 'bpmnFactory', 'commandStack', 'bpmnUpdater'];
