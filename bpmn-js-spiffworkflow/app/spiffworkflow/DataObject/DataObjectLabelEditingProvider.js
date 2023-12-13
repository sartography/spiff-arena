import { is } from 'bpmn-js/lib/util/ModelUtil';
import { findDataObject, updateDataObjectReferencesName } from './DataObjectHelpers';

export default function DataObjectLabelEditingProvider(eventBus, directEditing, commandStack, modeling) {

    let el;

    // listen to dblclick on non-root elements
    eventBus.on('element.dblclick', function (event) {
        const { element } = event;
        if (is(element.businessObject, 'bpmn:DataObjectReference')) {
            let label = element.businessObject.name;
            label = label.replace(/\s*\[.*?\]\s*$/, '');
            modeling.updateLabel(element, label);
            directEditing.activate(element);
            el = element;
        }
    });

    eventBus.on('directEditing.complete', function (event) {

        const element = el;

        if (element && is(element.businessObject, 'bpmn:DataObjectReference')) {

            setTimeout(() => {
                const process = element.parent.businessObject;
                const dataObject = findDataObject(process, element.businessObject.dataObjectRef.id);
                const dataState = element.businessObject.dataState && element.businessObject.dataState.name;

                let newLabel = element.businessObject.name;

                commandStack.execute('element.updateModdleProperties', {
                    element,
                    moddleElement: dataObject,
                    properties: {
                        name: newLabel,
                    },
                });

                // Update references name
                updateDataObjectReferencesName(element.parent, newLabel, dataObject.id, commandStack);

                // Append the data state if it exists
                if (dataState) {
                    newLabel += ` [${dataState}]`;
                }

                // Update the label with the data state
                modeling.updateLabel(element, newLabel);
                el = undefined;
            }, 100);
        }
    });
}

DataObjectLabelEditingProvider.$inject = [
    'eventBus',
    'directEditing',
    'commandStack',
    'modeling'
];