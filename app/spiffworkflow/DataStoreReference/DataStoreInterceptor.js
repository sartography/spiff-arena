import CommandInterceptor from 'diagram-js/lib/command/CommandInterceptor';
import { getDi, is } from 'bpmn-js/lib/util/ModelUtil';
import { isDataStoreReferenced, removeDataStore } from './DataStoreHelpers';

const HIGH_PRIORITY = 1500;

/**
 * 
 */
export default class DataStoreInterceptor extends CommandInterceptor {

  constructor(eventBus, bpmnFactory, commandStack, bpmnUpdater) {
    super(eventBus);

    /* 
     * 
     */
    // bpmnUpdater.updateSemanticParent = (businessObject, parentBusinessObject) => {
    //   if (is(businessObject, 'bpmn:DataStoreReference')) {
    //     console.log('updateSemanticParent', businessObject, parentBusinessObject);
    //     bpmnUpdater.__proto__.updateSemanticParent.call(bpmnUpdater, businessObject, parentBusinessObject);
    //   }
    // };

    /**
     * 
     */
    // this.preExecute(['shape.create'], HIGH_PRIORITY, function (event) {
    //   const { context } = event;
    //   const { shape } = context;
    //   if (is(shape, 'bpmn:DataStoreReference') && shape.type !== 'label') {
    //     // event.stopPropagation();*
    //     console.log('preExecute shape.create', shape, context);
    //   }
    // });

    /**
     * 
     */
    // this.executed(['shape.create'], HIGH_PRIORITY, function (event) {
    //   const { context } = event;
    //   const { shape } = context;
    //   if (is(shape, 'bpmn:DataStoreReference') && shape.type !== 'label') {
    //     console.log('executed shape.create', shape, context);
    //   }
    // });

    /**
     * 
     */
    // this.postExecuted(['shape.create'], HIGH_PRIORITY, function (event) {
    //   const { context } = event;
    //   const { shape } = context;
    //   if (is(shape, 'bpmn:DataStoreReference') && shape.type !== 'label') {
    //     console.log('postExecuted shape.create', shape, context);
    //   }
    // });

    /**
     * 
     */
    this.postExecuted(['shape.delete'], HIGH_PRIORITY, function (event) {
      const { context } = event;
      const { shape } = context;

      if (is(shape, 'bpmn:DataStoreReference')  && shape.type !== 'label') {
        const definitions = context.oldParent.businessObject.$parent;
        const dataStore = shape.businessObject.dataStoreRef;
        if (dataStore && !isDataStoreReferenced(context.oldParent.businessObject, dataStore.id)) {
          // Remove datastore if it's not linked with another datastore ref
          removeDataStore(definitions, dataStore.id);
        }
      }
    });
  }
}

DataStoreInterceptor.$inject = ['eventBus', 'bpmnFactory', 'commandStack', 'bpmnUpdater'];
