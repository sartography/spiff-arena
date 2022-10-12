import { ListGroup } from '@bpmn-io/properties-panel';
import { DataObjectArray } from './DataObjectArray';

/**
 * Also allows you to select which Data Objects are available
 * in the process element.
 * @param element The selected process
 * @param moddle For updating the underlying xml object
 * @returns {[{component: (function(*)), isEdited: *, id: string, element},{component:
 * (function(*)), isEdited: *, id: string, element}]}
 */
export default function(element, moddle) {

  const groupSections = [];
  const dataObjectArray = {
    id: 'editDataObjects',
    element,
    label: 'Available Data Objects',
    component: ListGroup,
    ...DataObjectArray({ element, moddle })
  };

  if (dataObjectArray.items) {
    groupSections.push(dataObjectArray);
  }

  return groupSections;
}


