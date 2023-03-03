import { is, isAny } from 'bpmn-js/lib/util/ModelUtil';
import { ListGroup, isTextFieldEntryEdited } from '@bpmn-io/properties-panel';
import { DataObjectSelect } from './DataObjectSelect';
import { DataObjectArray } from './DataObjectArray';

const LOW_PRIORITY = 500;

export default function DataObjectPropertiesProvider(
  propertiesPanel,
  translate,
  moddle,
  commandStack,
  elementRegistry
) {
  this.getGroups = function (element) {
    return function (groups) {
      if (is(element, 'bpmn:DataObjectReference')) {
        groups.push(
          createDataObjectSelector(element, translate, moddle, commandStack)
        );
      }
      if (
        isAny(element, ['bpmn:Process', 'bpmn:Participant']) ||
        (is(element, 'bpmn:SubProcess') && !element.collapsed)
      ) {
        groups.push(
          createDataObjectEditor(
            element,
            translate,
            moddle,
            commandStack,
            elementRegistry
          )
        );
      }
      return groups;
    };
  };
  propertiesPanel.registerProvider(LOW_PRIORITY, this);
}

DataObjectPropertiesProvider.$inject = [
  'propertiesPanel',
  'translate',
  'moddle',
  'commandStack',
  'elementRegistry',
];

/**
 * Create a group on the main panel with a select box (for choosing the Data Object to connect)
 * @param element
 * @param translate
 * @param moddle
 * @returns entries
 */
function createDataObjectSelector(element, translate, moddle, commandStack) {
  return {
    id: 'data_object_properties',
    label: translate('Data Object Properties'),
    entries: [
      {
        id: 'selectDataObject',
        element,
        component: DataObjectSelect,
        isEdited: isTextFieldEntryEdited,
        moddle,
        commandStack,
      },
    ],
  };
}

/**
 * Create a group on the main panel with a select box (for choosing the Data Object to connect) AND a
 * full Data Object Array for modifying all the data objects.
 * @param element
 * @param translate
 * @param moddle
 * @returns entries
 */
function createDataObjectEditor(
  element,
  translate,
  moddle,
  commandStack,
  elementRegistry
) {
  const dataObjectArray = {
    id: 'editDataObjects',
    element,
    label: 'Data Objects',
    component: ListGroup,
    ...DataObjectArray({ element, moddle, commandStack, elementRegistry }),
  };

  if (dataObjectArray.items) {
    return dataObjectArray;
  }
}
