import { is } from 'bpmn-js/lib/util/ModelUtil';
import { useService } from 'bpmn-js-properties-panel';
import {
  ListGroup,
  TextFieldEntry,
  isTextFieldEntryEdited
} from '@bpmn-io/properties-panel';
import { getRoot } from './helpers';

/* This function creates a list of a particular event type at the process level using the item list
 * and add function provided by `getArray`.
 *
 * Usage:
 * const getArray = getArrayForType('bpmn:Signal', 'signalRef', 'Signal');
 * const signalGroup = createGroupForType('signals', 'Signals', getArray);
 */

function getListGroupForType(groupId, label, getArray) {

  return  function (props) {
    const { element, translate, moddle, commandStack } = props;
    const eventArray = {
      id: groupId,
      element,
      label: label,
      component: ListGroup,
      ...getArray({ element, moddle, commandStack, translate }),
    };

    if (eventArray.items) {
      return eventArray;
    }
  }
}

function getArrayForType(itemType, referenceType, prefix) {

  return function (props) {
    const { element, moddle, commandStack, translate } = props;
    const root = getRoot(element.businessObject);
    const matching = root.rootElements ? root.rootElements.filter(elem => elem.$type === itemType) : [];

    function removeModelReferences(flowElements, match) {
      flowElements.map(elem => {
        if (elem.eventDefinitions)
          elem.eventDefinitions = elem.eventDefinitions.filter(def => def.get(referenceType) != match);
        else if (elem.flowElements)
          removeModelReferences(elem.flowElements, match);
      });
    }

    function removeElementReferences(children, match) {
      children.map(child => {
        if (child.businessObject.eventDefinitions) {
          const bo = child.businessObject;
          bo.eventDefinitions = bo.eventDefinitions.filter(def => def.get(referenceType) != match);
          commandStack.execute('element.updateProperties', {
            element: child,
            moddleElement: bo,
            properties: {}
          });
        }
        if (child.children)
          removeElementReferences(child.children, match);
      });
    }

    function removeFactory(item) {
      return function (event) {
        event.stopPropagation();
        if (root.rootElements) {
          root.rootElements = root.rootElements.filter(elem => elem != item);
          // This updates visible elements
          removeElementReferences(element.children, item);
          // This handles everything else (eg collapsed subprocesses) but does not update the shapes
          // I can't figure out how to do that
          root.rootElements.filter(elem => elem.$type === 'bpmn:Process').map(
            process => removeModelReferences(process.flowElements, item)
          );
          commandStack.execute('element.updateProperties', {
            element,
            properties: {},
          });
        }
      }
    }

    const items = matching.map((item, idx) => {
      const itemId = `${prefix}-${idx}`;
      return {
        id: itemId,
        label: item.name,
        entries: getItemEditor({
          itemId,
          element,
          item,
          commandStack,
          translate,
        }),
        autoFocusEntry: itemId,
        remove: removeFactory(item),
      };
    });

    function add(event) {
      event.stopPropagation();
      const item = moddle.create(itemType);
      item.id = moddle.ids.nextPrefixed(`${prefix}_`);
      item.name = item.id;
      if (root.rootElements)
        root.rootElements.push(item);
      commandStack.execute('element.updateProperties', {
        element,
        properties: {},
      });
    };

    return { items, add };
  }
}

function getItemEditor(props) {
  const { itemId, element, item, commandStack, translate } = props;
  return [
    {
      id: `${itemId}-name`,
      component: ItemTextField,
      item,
      commandStack,
      translate,
    },
  ];
}

function ItemTextField(props) {
  const { itemId, element, item, commandStack, translate } = props;

  const debounce = useService('debounceInput');

  const setValue = (value) => {
    commandStack.execute('element.updateModdleProperties', {
      element,
      moddleElement: item,
      properties: {
        id: value,
        name: value,
      },
    });
  };

  const getValue = () => { return item.id; }

  return TextFieldEntry({
    element,
    id: `${itemId}-id-textField`,
    label: translate('ID'),
    getValue,
    setValue,
    debounce,
  });
}

export { getArrayForType, getListGroupForType };
