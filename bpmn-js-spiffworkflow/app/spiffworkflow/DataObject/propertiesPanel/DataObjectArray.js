import { useService } from 'bpmn-js-properties-panel';
import {
  isTextFieldEntryEdited,
  TextFieldEntry,
} from '@bpmn-io/properties-panel';
import { without } from 'min-dash';
import { is } from 'bpmn-js/lib/util/ModelUtil';
import {findDataObjects, findDataReferenceShapes, idToHumanReadableName} from '../DataObjectHelpers';

/**
 * Provides a list of data objects, and allows you to add / remove data objects, and change their ids.
 * @param props
 * @constructor
 */
export function DataObjectArray(props) {
  const { moddle } = props;
  const { element } = props;
  const { commandStack } = props;
  const { elementRegistry } = props;
  let process;

  // This element might be a process, or something that will reference a process.
  if (is(element.businessObject, 'bpmn:Process')) {
    process = element.businessObject;
  } else if (element.businessObject.processRef) {
    process = element.businessObject.processRef;
  }

  const dataObjects = findDataObjects(process);
  const items = dataObjects.map((dataObject, index) => {
    const id = `${process.id}-dataObj-${index}`;
    return {
      id,
      label: dataObject.id,
      entries: DataObjectGroup({
        idPrefix: id,
        element,
        dataObject,
      }),
      autoFocusEntry: `${id}-dataObject`,
      remove: removeFactory({
        element,
        dataObject,
        process,
        commandStack,
        elementRegistry,
      }),
    };
  });

  function add(event) {
    event.stopPropagation();
    const newDataObject = moddle.create('bpmn:DataObject');
    const newElements = process.get('flowElements');
    newDataObject.id = moddle.ids.nextPrefixed('DataObject_');
    newElements.push(newDataObject);
    commandStack.execute('element.updateModdleProperties', {
      element,
      moddleElement: process,
      properties: {
        flowElements: newElements,
      },
    });
  }

  return { items, add };
}

function removeFactory(props) {
  const { element, dataObject, process, commandStack } = props;

  return function (event) {
    event.stopPropagation();
    commandStack.execute('element.updateModdleProperties', {
      element,
      moddleElement: process,
      properties: {
        flowElements: without(process.get('flowElements'), dataObject),
      },
    });
    // When a data object is removed, remove all references as well.
    const references = findDataReferenceShapes(element, dataObject.id);
    for (const ref of references) {
      commandStack.execute('shape.delete', { shape: ref });
    }
  };
}

function DataObjectGroup(props) {
  const { idPrefix, dataObject } = props;

  return [
    {
      id: `${idPrefix}-dataObject`,
      component: DataObjectTextField,
      isEdited: isTextFieldEntryEdited,
      idPrefix,
      dataObject,
    },
  ];
}

function DataObjectTextField(props) {
  const { idPrefix, element, parameter, dataObject } = props;

  const commandStack = useService('commandStack');
  const debounce = useService('debounceInput');

  const setValue = (value) => {
    commandStack.execute('element.updateModdleProperties', {
      element,
      moddleElement: dataObject,
      properties: {
        id: value,
      },
    });

    // Also update the label of all the references
    const references = findDataReferenceShapes(element, dataObject.id);
    for (const ref of references) {
      commandStack.execute('element.updateProperties', {
        element: ref,
        moddleElement: ref.businessObject,
        properties: {
          name: idToHumanReadableName(value),
        },
        changed: [ref], // everything is already marked as changed, don't recalculate.
      });
    }
  };

  const getValue = () => {
    return dataObject.id;
  };

  return TextFieldEntry({
    element: parameter,
    id: `${idPrefix}-id`,
    label: 'Data Object Id',
    getValue,
    setValue,
    debounce,
  });
}
