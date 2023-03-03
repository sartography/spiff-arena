import { useService } from 'bpmn-js-properties-panel';
import {
  SelectEntry,
  isTextFieldEntryEdited,
  TextFieldEntry,
} from '@bpmn-io/properties-panel';
import {
  findCorrelationPropertiesAndRetrievalExpressionsForMessage,
  findCorrelationProperties,
  getMessageRefElement,
} from '../MessageHelpers';
import { removeFirstInstanceOfItemFromArrayInPlace } from '../../helpers';

/**
 * Allows the creation, or editing of messageCorrelations at the bpmn:sendTask level of a BPMN document.
 */
export function MessageCorrelationPropertiesArray(props) {
  const { moddle } = props;
  const { element } = props;
  const { commandStack } = props;
  const { translate } = props;

  const correlationPropertyObjectsForCurrentMessage =
    findCorrelationPropertiesAndRetrievalExpressionsForMessage(element);
  const allCorrelationPropertyModdleElements = findCorrelationProperties(
    element,
    moddle
  );
  const items = correlationPropertyObjectsForCurrentMessage.map(
    (correlationPropertyObject, index) => {
      const {
        correlationPropertyModdleElement,
        correlationPropertyRetrievalExpressionModdleElement,
      } = correlationPropertyObject;
      const id = `correlation-${index}`;
      const entries = MessageCorrelationPropertyGroup({
        idPrefix: id,
        correlationPropertyModdleElement,
        correlationPropertyRetrievalExpressionModdleElement,
        translate,
        moddle,
        element,
        commandStack,
      });
      return {
        id,
        label: correlationPropertyModdleElement.name,
        entries,
        autoFocusEntry: id,
        remove: removeFactory({
          element,
          correlationPropertyModdleElement,
          correlationPropertyRetrievalExpressionModdleElement,
          commandStack,
        }),
      };
    }
  );

  function add(event) {
    event.stopPropagation();

    let correlationPropertyElement;
    allCorrelationPropertyModdleElements.forEach((cpe) => {
      let foundElement = false;
      correlationPropertyObjectsForCurrentMessage.forEach((cpo) => {
        const cpme = cpo.correlationPropertyModdleElement;
        if (cpme.id === cpe.id) {
          foundElement = true;
        }
      });
      if (!foundElement) {
        correlationPropertyElement = cpe;
      }
    });

    // TODO: we should have some way to show an error if element is not found instead
    // we need to check this since the code assumes each message only has one ref
    // and will not display all properties if there are multiple
    if (correlationPropertyElement) {
      const newRetrievalExpressionElement = moddle.create(
        'bpmn:CorrelationPropertyRetrievalExpression'
      );
      const messageRefElement = getMessageRefElement(element);
      const newFormalExpression = moddle.create('bpmn:FormalExpression');
      newFormalExpression.body = '';

      newRetrievalExpressionElement.messageRef = messageRefElement;
      newRetrievalExpressionElement.messagePath = newFormalExpression;

      if (!correlationPropertyElement.correlationPropertyRetrievalExpression) {
        correlationPropertyElement.correlationPropertyRetrievalExpression = [];
      }
      correlationPropertyElement.correlationPropertyRetrievalExpression.push(
        newRetrievalExpressionElement
      );
      commandStack.execute('element.updateProperties', {
        element,
        properties: {},
      });
    } else {
      console.error(
        'ERROR: There are not any more correlation properties this message can be added to'
      );
    }
  }

  const returnObject = { items };
  if (allCorrelationPropertyModdleElements.length !== 0) {
    returnObject.add = add;
  }
  return returnObject;
}

function removeFactory(props) {
  const {
    element,
    correlationPropertyModdleElement,
    correlationPropertyRetrievalExpressionModdleElement,
    commandStack,
  } = props;

  return function (event) {
    event.stopPropagation();
    removeFirstInstanceOfItemFromArrayInPlace(
      correlationPropertyModdleElement.correlationPropertyRetrievalExpression,
      correlationPropertyRetrievalExpressionModdleElement
    );
    commandStack.execute('element.updateProperties', {
      element,
      properties: {},
    });
  };
}

function MessageCorrelationPropertyGroup(props) {
  const {
    idPrefix,
    correlationPropertyModdleElement,
    correlationPropertyRetrievalExpressionModdleElement,
    translate,
    moddle,
    element,
    commandStack,
  } = props;
  return [
    {
      id: `${idPrefix}-correlation-key`,
      component: MessageCorrelationPropertySelect,
      isEdited: isTextFieldEntryEdited,
      idPrefix,
      correlationPropertyModdleElement,
      correlationPropertyRetrievalExpressionModdleElement,
      translate,
      moddle,
      element,
      commandStack,
    },
    {
      id: `${idPrefix}-expression`,
      component: MessageCorrelationExpressionTextField,
      isEdited: isTextFieldEntryEdited,
      idPrefix,
      correlationPropertyRetrievalExpressionModdleElement,
      translate,
    },
  ];
}

function MessageCorrelationPropertySelect(props) {
  const {
    idPrefix,
    correlationPropertyModdleElement,
    correlationPropertyRetrievalExpressionModdleElement,
    translate,
    parameter,
    moddle,
    element,
    commandStack,
  } = props;
  const debounce = useService('debounceInput');

  const setValue = (value) => {
    const allCorrelationPropertyModdleElements = findCorrelationProperties(
      correlationPropertyModdleElement,
      moddle
    );
    const newCorrelationPropertyElement =
      allCorrelationPropertyModdleElements.find((cpe) => cpe.id === value);

    if (!newCorrelationPropertyElement.correlationPropertyRetrievalExpression) {
      newCorrelationPropertyElement.correlationPropertyRetrievalExpression = [];
    }
    newCorrelationPropertyElement.correlationPropertyRetrievalExpression.push(
      correlationPropertyRetrievalExpressionModdleElement
    );
    removeFirstInstanceOfItemFromArrayInPlace(
      correlationPropertyModdleElement.correlationPropertyRetrievalExpression,
      correlationPropertyRetrievalExpressionModdleElement
    );
    commandStack.execute('element.updateProperties', {
      element,
      properties: {},
    });
  };

  const getValue = () => {
    return correlationPropertyModdleElement.id;
  };

  const getOptions = () => {
    const allCorrelationPropertyModdleElements = findCorrelationProperties(
      correlationPropertyModdleElement,
      moddle
    );
    const correlationPropertyObjectsForCurrentMessage =
      findCorrelationPropertiesAndRetrievalExpressionsForMessage(element);
    const options = [];
    for (const cpe of allCorrelationPropertyModdleElements) {
      const foundElement = correlationPropertyObjectsForCurrentMessage.find(
        (cpo) => {
          const cpme = cpo.correlationPropertyModdleElement;
          return cpme.id === cpe.id;
        }
      );
      if (
        !foundElement ||
        foundElement.correlationPropertyModdleElement ===
          correlationPropertyModdleElement
      ) {
        options.push({
          label: cpe.name,
          value: cpe.id,
        });
      }
    }
    return options;
  };

  return SelectEntry({
    id: `${idPrefix}-select`,
    element: parameter,
    label: translate('Correlation Property'),
    getValue,
    setValue,
    getOptions,
    debounce,
  });
}

function MessageCorrelationExpressionTextField(props) {
  const {
    idPrefix,
    parameter,
    correlationPropertyRetrievalExpressionModdleElement,
    translate,
  } = props;

  const debounce = useService('debounceInput');

  const setValue = (value) => {
    correlationPropertyRetrievalExpressionModdleElement.messagePath.body =
      value;
  };

  const getValue = (_parameter) => {
    return correlationPropertyRetrievalExpressionModdleElement.messagePath.body;
  };

  return TextFieldEntry({
    element: parameter,
    id: `${idPrefix}-textField`,
    label: translate('Expression'),
    getValue,
    setValue,
    debounce,
  });
}
