import { useService } from 'bpmn-js-properties-panel';
import {SpiffExtensionTextInput} from '../../extensions/propertiesPanel/SpiffExtensionTextInput';
import {
  isTextFieldEntryEdited,
  TextFieldEntry,
} from '@bpmn-io/properties-panel';
import { without } from 'min-dash';
import { is } from 'bpmn-js/lib/util/ModelUtil';
import {
  findDataObjects,
  findDataObjectReferenceShapes,
  updateDataObjectReferencesName,
  idToHumanReadableName,
  findDataObject,
} from '../DataObjectHelpers';

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
  if (is(element.businessObject, 'bpmn:Process') || is(element.businessObject, 'bpmn:SubProcess')) {
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
        commandStack,
        moddle,
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
    newDataObject.name = idToHumanReadableName(newDataObject.id);
    newDataObject.$parent = process;
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
    const references = findDataObjectReferenceShapes(element.children, dataObject.id);
    for (const ref of references) {
      commandStack.execute('shape.delete', { shape: ref });
    }
  };
}

function DataObjectGroup(props) {
  const { idPrefix, dataObject, element, moddle, commandStack } = props;

  return [
    {
      id: `${idPrefix}-dataObject`,
      component: DataObjectTextField,
      isEdited: isTextFieldEntryEdited,
      idPrefix,
      dataObject,
    },
    {
      id: `${idPrefix}-dataObjectName`,
      component: DataObjectNameTextField,
      isEdited: isTextFieldEntryEdited,
      idPrefix,
      dataObject,
    },
    {
      businessObject: dataObject,
      commandStack: commandStack,
      moddle: moddle,
      component: SpiffExtensionTextInput,
      name: 'spiffworkflow:Category',
      label: 'Data Object Category',
      description: 'Useful for setting permissions on groups of data objects.',
    },
  ];
}

function DataObjectTextField(props) {
  const { idPrefix, element, parameter, dataObject } = props;

  const commandStack = useService('commandStack');
  const debounce = useService('debounceInput');

  const setValue = (value) => {
    try {
      // Check if new dataObject Id is not unique
      if(findDataObject(element.businessObject, value) !== undefined){
        alert('Data Object ID Should be unique');
        return;
      }

      // let doName = idToHumanReadableName(value);
      commandStack.execute('element.updateModdleProperties', {
        element,
        moddleElement: dataObject,
        properties: {
          id: value,
          // name: doName
        },
      });
      // Update references name
      // updateDataObjectReferencesName(element, doName, value, commandStack);
    } catch (error) {
      console.log('Set Value Error : ', error);
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

function DataObjectNameTextField(props) {
  const { idPrefix, element, parameter, dataObject } = props;

  const commandStack = useService('commandStack');
  const debounce = useService('debounceInput');

  const setValue = (value) => {

    // Update references name
    updateDataObjectReferencesName(element, value, dataObject.id, commandStack);

    // Update dataObject name
    commandStack.execute('element.updateModdleProperties', {
      element,
      moddleElement: dataObject,
      properties: {
        name: value,
      },
    });
  };

  const getValue = () => {
    return dataObject.name;
  };

  return TextFieldEntry({
    element: parameter,
    id: `${idPrefix}-name`,
    label: 'Data Object Name',
    getValue,
    setValue,
    debounce,
  });
}
